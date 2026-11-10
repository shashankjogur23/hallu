"""Document management and file upload API router."""

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.config import settings
from app.schemas.verification import (
    DocumentDetail,
    DocumentListResponse,
    DocumentMetadata,
)
from app.services.document_service import document_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=DocumentDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a reference document (PDF or TXT)",
    description="Extracts text using PyMuPDF or plain text decoder, automatically breaks it into semantically coherent chunks, and prepares it for retrieval and verification.",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF or TXT document to upload"),
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> DocumentDetail:
    """Upload and process a document file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is missing.",
        )

    content_type = file.content_type or "application/octet-stream"

    try:
        file_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {e}",
        ) from e

    try:
        doc = document_service.ingest_document(
            filename=file.filename,
            file_bytes=file_bytes,
            content_type=content_type,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        return DocumentDetail(
            id=doc["id"],
            filename=doc["filename"],
            file_type=doc["file_type"],
            file_size=doc["file_size"],
            chunk_count=doc["chunk_count"],
            extracted_text=doc["extracted_text"],
            chunks=doc["chunks"],
            created_at=doc["created_at"],
            is_persistent=doc["is_persistent"],
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        ) from ve
    except Exception as e:
        logger.error("Failed to ingest document %s: %s", file.filename, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing error: {e}",
        ) from e


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all uploaded reference documents",
    description="Returns metadata for all documents currently loaded in the system with persistent vs in-memory storage status.",
)
async def list_documents() -> DocumentListResponse:
    """List all registered reference documents."""
    docs = document_service.list_documents()
    metadata_list = [
        DocumentMetadata(
            id=d["id"],
            filename=d["filename"],
            file_type=d["file_type"],
            file_size=d["file_size"],
            chunk_count=d["chunk_count"],
            created_at=d["created_at"],
            is_persistent=d["is_persistent"],
        )
        for d in docs
    ]

    is_persistent = settings.is_supabase_configured
    notice = (
        "Documents are securely stored in Supabase PostgreSQL."
        if is_persistent
        else "Documents are held in-memory for the current server session. They will be cleared when the backend restarts."
    )

    return DocumentListResponse(
        documents=metadata_list,
        total_documents=len(metadata_list),
        is_persistent=is_persistent,
        storage_notice=notice,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetail,
    summary="Get full document details by ID",
)
async def get_document(document_id: str) -> DocumentDetail:
    """Retrieve full text and chunks of a specific document."""
    doc = document_service.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return DocumentDetail(
        id=doc["id"],
        filename=doc["filename"],
        file_type=doc["file_type"],
        file_size=doc["file_size"],
        chunk_count=doc["chunk_count"],
        extracted_text=doc["extracted_text"],
        chunks=doc["chunks"],
        created_at=doc["created_at"],
        is_persistent=doc["is_persistent"],
    )


@router.delete(
    "/{document_id}",
    summary="Delete an uploaded document",
)
async def delete_document(document_id: str) -> dict[str, str | bool]:
    """Remove a document from storage."""
    deleted = document_service.delete_document(document_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found.",
        )
    return {"deleted": True, "id": document_id}

