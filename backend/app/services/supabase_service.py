"""Supabase integration service for HalluGuard.

Handles PostgreSQL persistence for documents, verification logs, and detected spans.
Gracefully degrades with non-blocking warnings if credentials are not configured.
"""

import logging
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service wrapping the Supabase client for database persistence."""

    def __init__(self) -> None:
        self._client: Any = None
        self._is_configured: bool = False
        self._init_client()

    def _init_client(self) -> None:
        """Initialize the Supabase client if credentials are provided."""
        if not settings.is_supabase_configured:
            logger.info(
                "Supabase is not configured. Running in local-only mode (verification is unaffected)."
            )
            self._is_configured = False
            self._client = None
            return

        try:
            from supabase import create_client, Client

            self._client = create_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_service_role_key,
            )
            self._is_configured = True
            logger.info("Supabase client initialized successfully.")
        except Exception as e:
            logger.warning(
                "Failed to initialize Supabase client: %s. Continuing in local-only mode.",
                e,
            )
            self._client = None
            self._is_configured = False

    @property
    def is_configured(self) -> bool:
        """Return True if Supabase client is connected and configured."""
        return self._is_configured

    def save_verification(
        self,
        verification_id: str,
        question: str | None,
        answer: str,
        context: list[str],
        is_hallucinated: bool,
        hallucination_score: float | None,
        span_count: int,
        model_name: str,
        execution_time_ms: float,
        spans: list[dict[str, Any]],
        document_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Persist a verification record and its detected spans to Supabase.

        If Supabase is not configured, this method returns None safely without error.
        """
        if not self._is_configured or self._client is None:
            logger.debug(
                "Supabase not configured. Skipping persistence for verification %s.",
                verification_id,
            )
            return None

        try:
            # 1. Insert main verification record
            record = {
                "id": verification_id,
                "document_id": document_id,
                "question": question,
                "answer": answer,
                "context": context,
                "is_hallucinated": is_hallucinated,
                "hallucination_score": hallucination_score,
                "span_count": span_count,
                "model_name": model_name,
                "execution_time_ms": execution_time_ms,
            }
            res = self._client.table("verifications").insert(record).execute()

            # 2. Insert spans if any
            if spans:
                spans_records = [
                    {
                        "verification_id": verification_id,
                        "span_text": s.get("text", ""),
                        "start_offset": s.get("start", 0),
                        "end_offset": s.get("end", 0),
                        "confidence": s.get("confidence"),
                        "category": s.get("category"),
                    }
                    for s in spans
                ]
                self._client.table("verification_spans").insert(spans_records).execute()

            logger.info("Saved verification %s to Supabase.", verification_id)
            return res.data[0] if res.data else record
        except Exception as e:
            logger.error(
                "Failed to save verification %s to Supabase: %s",
                verification_id,
                e,
                exc_info=True,
            )
            return None

    def get_verification_history(
        self, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch historical verification records from Supabase."""
        if not self._is_configured or self._client is None:
            return []

        try:
            res = (
                self._client.table("verifications")
                .select("*, verification_spans(*)")
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error("Failed to query verification history: %s", e)
            return []

    def save_document(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        chunk_count: int,
        extracted_text: str,
        chunks: list[Any],
        file_bytes: bytes | None = None,
    ) -> bool:
        """Persist full document text, chunks, and metadata into Supabase PostgreSQL.

        Returns True only if successfully stored.
        """
        if not self._is_configured or self._client is None:
            return False

        try:
            # Serialize chunks
            serialized_chunks = []
            for c in chunks:
                if hasattr(c, "model_dump"):
                    serialized_chunks.append(c.model_dump())
                elif hasattr(c, "dict"):
                    serialized_chunks.append(c.dict())
                elif isinstance(c, dict):
                    serialized_chunks.append(c)
                else:
                    serialized_chunks.append({
                        "chunk_index": getattr(c, "chunk_index", 0),
                        "text": getattr(c, "text", ""),
                        "char_start": getattr(c, "char_start", 0),
                        "char_end": getattr(c, "char_end", 0),
                    })

            record = {
                "id": document_id,
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size_bytes,
                "chunk_count": chunk_count,
                "metadata": {
                    "extracted_text": extracted_text,
                    "chunks": serialized_chunks,
                    "source": "api_upload",
                },
            }
            res = self._client.table("documents").insert(record).execute()
            if res.data:
                logger.info("Successfully persisted document %s to Supabase.", document_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to persist document %s to Supabase: %s", document_id, e, exc_info=True)
            return False

    def list_documents(self) -> list[dict[str, Any]]:
        """Fetch all documents from Supabase."""
        if not self._is_configured or self._client is None:
            return []

        try:
            res = (
                self._client.table("documents")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            raw_docs = res.data or []
            documents = []
            for d in raw_docs:
                meta = d.get("metadata") or {}
                extracted_text = meta.get("extracted_text", "")
                chunks = meta.get("chunks", [])
                documents.append({
                    "id": d["id"],
                    "filename": d["filename"],
                    "file_type": d["file_type"],
                    "file_size": d["file_size"],
                    "chunk_count": d["chunk_count"],
                    "extracted_text": extracted_text,
                    "chunks": chunks,
                    "created_at": d.get("created_at", ""),
                    "is_persistent": True,
                })
            return documents
        except Exception as e:
            logger.error("Failed to list documents from Supabase: %s", e)
            return []

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        """Fetch single document by ID from Supabase."""
        if not self._is_configured or self._client is None:
            return None

        try:
            res = (
                self._client.table("documents")
                .select("*")
                .eq("id", document_id)
                .execute()
            )
            if not res.data:
                return None
            d = res.data[0]
            meta = d.get("metadata") or {}
            return {
                "id": d["id"],
                "filename": d["filename"],
                "file_type": d["file_type"],
                "file_size": d["file_size"],
                "chunk_count": d["chunk_count"],
                "extracted_text": meta.get("extracted_text", ""),
                "chunks": meta.get("chunks", []),
                "created_at": d.get("created_at", ""),
                "is_persistent": True,
            }
        except Exception as e:
            logger.error("Failed to get document %s from Supabase: %s", document_id, e)
            return None

    def delete_document(self, document_id: str) -> bool:
        """Delete document from Supabase."""
        if not self._is_configured or self._client is None:
            return False

        try:
            res = (
                self._client.table("documents")
                .delete()
                .eq("id", document_id)
                .execute()
            )
            return bool(res.data)
        except Exception as e:
            logger.error("Failed to delete document %s from Supabase: %s", document_id, e)
            return False

    def save_document_metadata(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        chunk_count: int,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Persist document metadata into the documents table."""
        if not self._is_configured or self._client is None:
            return None

        try:
            record = {
                "id": document_id,
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size_bytes,
                "chunk_count": chunk_count,
                "metadata": metadata or {},
            }
            res = self._client.table("documents").insert(record).execute()
            return res.data[0] if res.data else record
        except Exception as e:
            logger.error("Failed to save document metadata: %s", e)
            return None


supabase_service = SupabaseService()

