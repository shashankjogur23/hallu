"""Verification and context processing API router."""

import logging
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from app.config import settings
from app.schemas.verification import (
    VerificationRequest,
    VerificationResponse,
    ChunkResponse,
    RetrieveRequest,
    RetrieveResponse,
    VerificationHistoryItem,
    VerificationHistoryResponse,
)
from app.services.detector_service import detector_service
from app.services.hybrid_detector_service import hybrid_detector_service
from app.services.document_service import document_service
from app.services.retrieval_service import retrieval_service
from app.services.supabase_service import supabase_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Verification & Context"])

# In-memory history for current server session (synchronized with Supabase when available)
_session_history: list[VerificationHistoryItem] = []


@router.post(
    "/verify",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify answer for hallucinations against reference context using production hybrid detector",
    description=(
        "Analyzes an AI-generated answer against ground truth reference passages using a production "
        "hybrid system: LettuceDetect ModernBERT for token-level suspicious span detection and "
        "DeBERTa-v3 NLI for relational/contradiction verification. Returns fine-grained claim classification, "
        "exact character offsets, and component confidence breakdowns."
    ),
)
async def verify_hallucination(request: VerificationRequest) -> VerificationResponse:
    """Run hallucination detection over question, answer, and reference context."""
    if not hybrid_detector_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Verification models are not yet loaded. Please wait for startup or check server logs.",
        )

    verification_id = str(uuid.uuid4())
    context_list = (
        request.context if isinstance(request.context, list) else [request.context]
    )

    try:
        (
            spans,
            summary,
            contradicted_claims,
            unsupported_claims,
            supported_claims,
            detector_breakdown,
            exec_time,
        ) = hybrid_detector_service.verify(
            context=context_list,
            answer=request.answer,
            question=request.question,
            min_confidence=request.min_confidence,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        ) from ve
    except Exception as e:
        logger.error("Verification failed unexpectedly: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference processing error: {e}",
        ) from e

    # Persist asynchronously / safely to Supabase if configured
    try:
        supabase_service.save_verification(
            verification_id=verification_id,
            question=request.question,
            answer=request.answer,
            context=context_list,
            is_hallucinated=summary.is_hallucinated,
            hallucination_score=summary.max_confidence,
            span_count=summary.span_count,
            model_name=hybrid_detector_service.model_name,
            execution_time_ms=exec_time,
            spans=[s.model_dump() for s in spans],
        )
    except Exception as db_err:
        logger.warning("Supabase persistence failed non-fatally: %s", db_err)

    created_at = datetime.now(timezone.utc).isoformat()
    history_item = VerificationHistoryItem(
        id=verification_id,
        question=request.question,
        answer=request.answer,
        context=context_list,
        spans=spans,
        summary=summary,
        model=hybrid_detector_service.model_name,
        execution_time_ms=exec_time,
        created_at=created_at,
    )
    _session_history.insert(0, history_item)
    if len(_session_history) > 100:
        _session_history.pop()

    return VerificationResponse(
        id=verification_id,
        question=request.question,
        answer=request.answer,
        context=context_list,
        spans=spans,
        summary=summary,
        model=hybrid_detector_service.model_name,
        execution_time_ms=exec_time,
        contradicted_claims=contradicted_claims,
        unsupported_claims=unsupported_claims,
        supported_claims=supported_claims,
        detector_breakdown=detector_breakdown,
        retrieved_evidence=context_list,
    )


@router.get(
    "/verifications/history",
    response_model=VerificationHistoryResponse,
    summary="Get recent verification history",
    description="Returns list of previously executed verifications with persistent vs in-memory status notice.",
)
async def get_history(limit: int = 50) -> VerificationHistoryResponse:
    """Retrieve verification history from Supabase if configured, or from server session memory."""
    is_persistent = settings.is_supabase_configured

    if is_persistent:
        try:
            records = supabase_service.get_verification_history(limit=limit)
            items = []
            for r in records:
                spans = [
                    {
                        "start": s["start_offset"],
                        "end": s["end_offset"],
                        "text": s["span_text"],
                        "confidence": s["confidence"],
                        "category": s.get("category"),
                    }
                    for s in r.get("verification_spans", [])
                ]
                items.append(
                    VerificationHistoryItem(
                        id=r["id"],
                        question=r.get("question"),
                        answer=r["answer"],
                        context=r.get("context", []),
                        spans=spans,
                        summary={
                            "is_hallucinated": r["is_hallucinated"],
                            "span_count": r["span_count"],
                            "max_confidence": r.get("hallucination_score"),
                            "verdict": "HALLUCINATED" if r["is_hallucinated"] else "CLEAN",
                            "message": "Loaded from persistent database.",
                        },
                        model=r.get("model_name", detector_service.model_path),
                        execution_time_ms=r.get("execution_time_ms", 0.0),
                        created_at=r["created_at"],
                    )
                )
            return VerificationHistoryResponse(
                verifications=items,
                total=len(items),
                is_persistent=True,
                storage_notice="Verification records are persistently stored in Supabase PostgreSQL.",
            )
        except Exception as e:
            logger.warning("Failed to fetch from Supabase: %s. Falling back to session memory.", e)

    # In-memory session fallback
    return VerificationHistoryResponse(
        verifications=_session_history[:limit],
        total=len(_session_history),
        is_persistent=False,
        storage_notice="Supabase is not configured. Verification history is maintained in-memory for this server session only and resets on server restart.",
    )


@router.get(
    "/verifications/stats",
    summary="Get actual verification counts and summary statistics",
    description="Calculates statistics strictly from real verification records (never mocked or fabricated).",
)
async def get_stats() -> dict[str, int | float | bool | str]:
    """Return actual verification statistics from available records."""
    is_persistent = settings.is_supabase_configured
    history = _session_history

    if is_persistent:
        try:
            supabase_records = supabase_service.get_verification_history(limit=200)
            if supabase_records:
                total = len(supabase_records)
                flagged = sum(1 for r in supabase_records if r.get("is_hallucinated"))
                clean = total - flagged
                return {
                    "total_verifications": total,
                    "flagged_answers": flagged,
                    "clean_answers": clean,
                    "is_persistent": True,
                    "source": "supabase",
                }
        except Exception as e:
            logger.warning("Could not fetch stats from Supabase: %s", e)

    total = len(history)
    flagged = sum(1 for h in history if h.summary.is_hallucinated)
    clean = total - flagged
    return {
        "total_verifications": total,
        "flagged_answers": flagged,
        "clean_answers": clean,
        "is_persistent": False,
        "source": "session_memory",
    }


@router.post(
    "/context/chunk",
    response_model=ChunkResponse,
    summary="Chunk raw text into overlapping passages",
    description="Splits long document text into semantically cohesive, overlapping chunks with character offsets.",
)
async def chunk_document_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    document_name: str | None = None,
) -> ChunkResponse:
    """Chunk input text into smaller segments suitable for reference context."""
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Text content cannot be empty.",
        )

    try:
        chunks = document_service.chunk_text(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return ChunkResponse(
            document_name=document_name,
            total_chunks=len(chunks),
            chunks=chunks,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        ) from ve


@router.post(
    "/context/retrieve",
    response_model=RetrieveResponse,
    summary="Retrieve most relevant context chunks for a query",
    description="Ranks reference context chunks against a query using TF-IDF cosine similarity.",
)
async def retrieve_contexts(request: RetrieveRequest) -> RetrieveResponse:
    """Retrieve top relevant chunks for a given query."""
    retrieved = retrieval_service.retrieve_relevant_contexts(
        query=request.query,
        contexts=request.contexts,
        top_k=request.top_k,
    )
    return RetrieveResponse(
        query=request.query,
        retrieved_chunks=retrieved,
    )

