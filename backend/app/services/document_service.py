"""Document processing service for HalluGuard.

Provides PDF and TXT text extraction and intelligent text chunking.
"""

import io
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from app.config import settings
from app.schemas.verification import ChunkItem, DocumentMetadata, DocumentDetail

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for extracting and chunking text from various document formats."""

    def __init__(self) -> None:
        self._documents: dict[str, dict] = {}

    def get_document_store(self) -> dict[str, dict]:
        """Return reference to in-memory documents dictionary."""
        return self._documents

    @staticmethod
    def extract_text_from_pdf(source: bytes | io.BytesIO | Path | str) -> str:
        """Extract all text from a PDF document using PyMuPDF.

        Args:
            source: Raw PDF bytes, file-like BytesIO stream, or file path.

        Returns:
            Extracted text as a clean string.

        Raises:
            ValueError: If the PDF is corrupted, encrypted, or cannot be parsed.
        """
        try:
            import pymupdf  # official import
        except ImportError:
            import fitz as pymupdf  # fallback

        doc = None
        try:
            if isinstance(source, (str, Path)):
                path_obj = Path(source)
                if not path_obj.exists():
                    raise FileNotFoundError(f"PDF file not found: {source}")
                doc = pymupdf.open(str(path_obj))
            elif isinstance(source, (bytes, bytearray)):
                if len(source) == 0:
                    raise ValueError("Cannot extract text from empty PDF bytes.")
                doc = pymupdf.open(stream=source, filetype="pdf")
            elif isinstance(source, io.BytesIO):
                source.seek(0)
                doc = pymupdf.open(stream=source.read(), filetype="pdf")
            else:
                raise TypeError(f"Unsupported PDF source type: {type(source)}")

            if doc.is_encrypted:
                raise ValueError("PDF document is password protected / encrypted.")

            pages_text: list[str] = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if text and text.strip():
                    pages_text.append(text.strip())

            full_text = "\n\n".join(pages_text).strip()
            return full_text
        except (FileNotFoundError, ValueError, TypeError):
            raise
        except Exception as e:
            logger.error("Failed to extract text from PDF: %s", e, exc_info=True)
            raise ValueError(f"Failed to extract text from PDF document: {e}") from e
        finally:
            if doc is not None:
                doc.close()

    @staticmethod
    def extract_text_from_txt(source: bytes | str | Path) -> str:
        """Extract text from a TXT file or raw bytes.

        Supports UTF-8 with fallback to Latin-1/CP1252.

        Args:
            source: Raw bytes, string text, or file path.

        Returns:
            Extracted text string.
        """
        if isinstance(source, str):
            # Check if it's a file path
            path_obj = Path(source)
            if path_obj.exists() and path_obj.is_file():
                raw_bytes = path_obj.read_bytes()
            else:
                # Direct string content
                return source.strip()
        elif isinstance(source, Path):
            if not source.exists():
                raise FileNotFoundError(f"TXT file not found: {source}")
            raw_bytes = source.read_bytes()
        elif isinstance(source, (bytes, bytearray)):
            raw_bytes = bytes(source)
        else:
            raise TypeError(f"Unsupported TXT source type: {type(source)}")

        if not raw_bytes:
            return ""

        # Try UTF-8 (with BOM handling), fallback to latin-1
        for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                return raw_bytes.decode(encoding).strip()
            except (UnicodeDecodeError, LookupError):
                continue

        return raw_bytes.decode("utf-8", errors="replace").strip()

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> list[ChunkItem]:
        """Split a long text document into overlapping chunks.

        Attempts to break at paragraph or sentence boundaries where possible.

        Args:
            text: Full text to chunk.
            chunk_size: Target character length per chunk.
            chunk_overlap: Number of overlapping characters between consecutive chunks.

        Returns:
            List of ChunkItem objects with text, index, and character offsets.
        """
        if not text or not text.strip():
            return []

        text = text.strip()
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        chunks: list[ChunkItem] = []
        text_len = len(text)
        start = 0
        chunk_index = 0

        while start < text_len:
            end = min(start + chunk_size, text_len)

            # If not at the end of text, attempt to find a natural boundary
            if end < text_len:
                # Search backwards for paragraph break, sentence end, or whitespace
                boundary = -1
                search_region = text[max(start, end - 100) : end]
                
                # Check for double newline (paragraph)
                p_match = list(re.finditer(r"\n\s*\n", search_region))
                if p_match:
                    boundary = max(start, end - 100) + p_match[-1].end()
                else:
                    # Check for sentence end punctuation (. ! ?)
                    s_match = list(re.finditer(r"([.!?])\s+", search_region))
                    if s_match:
                        boundary = max(start, end - 100) + s_match[-1].end()
                    else:
                        # Check for single newline or space
                        w_match = list(re.finditer(r"\s+", search_region))
                        if w_match:
                            boundary = max(start, end - 100) + w_match[-1].end()

                if boundary > start:
                    end = boundary

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append(
                    ChunkItem(
                        chunk_index=chunk_index,
                        text=chunk_content,
                        char_start=start,
                        char_end=end,
                    )
                )
                chunk_index += 1

            if end >= text_len:
                break

            # Advance start considering overlap
            start = end - chunk_overlap
            if start <= chunks[-1].char_start:
                # Ensure forward progress
                start = chunks[-1].char_start + 1

        return chunks

    def ingest_document(
        self,
        filename: str,
        file_bytes: bytes,
        content_type: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> dict:
        """Extract text, chunk it, and register the document in storage."""
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        ext = Path(filename).suffix.lower()
        if ext == ".pdf" or "pdf" in content_type.lower():
            extracted_text = self.extract_text_from_pdf(file_bytes)
            file_type = "application/pdf"
        elif ext in (".txt", ".text") or "text" in content_type.lower():
            extracted_text = self.extract_text_from_txt(file_bytes)
            file_type = "text/plain"
        else:
            raise ValueError(f"Unsupported file type '{ext}'. Only PDF (.pdf) and TXT (.txt) are supported.")

        if not extracted_text.strip():
            raise ValueError("No text could be extracted from this document.")

        chunks = self.chunk_text(extracted_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        doc_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        is_persistent = False

        # Attempt durable Supabase persistence
        try:
            from app.services.supabase_service import supabase_service
            if supabase_service.is_configured:
                save_ok = supabase_service.save_document(
                    document_id=doc_id,
                    filename=filename,
                    file_type=file_type,
                    file_size_bytes=len(file_bytes),
                    chunk_count=len(chunks),
                    extracted_text=extracted_text,
                    chunks=chunks,
                    file_bytes=file_bytes,
                )
                if save_ok:
                    is_persistent = True
                else:
                    logger.warning("Supabase document persistence returned False. Operating in local fallback mode for %s.", doc_id)
        except Exception as e:
            logger.warning("Could not persist document to Supabase: %s. Operating in local mode.", e)

        doc_record = {
            "id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "file_size": len(file_bytes),
            "chunk_count": len(chunks),
            "extracted_text": extracted_text,
            "chunks": chunks,
            "created_at": created_at,
            "is_persistent": is_persistent,
        }

        self._documents[doc_id] = doc_record
        return doc_record

    def list_documents(self) -> list[dict]:
        """Return all registered documents, syncing from Supabase if configured."""
        try:
            from app.services.supabase_service import supabase_service
            if supabase_service.is_configured:
                remote_docs = supabase_service.list_documents()
                for rd in remote_docs:
                    rd_id = rd["id"]
                    if rd_id not in self._documents:
                        self._documents[rd_id] = rd
                    else:
                        self._documents[rd_id]["is_persistent"] = True
        except Exception as e:
            logger.warning("Failed to sync documents from Supabase: %s", e)

        return list(self._documents.values())

    def get_document(self, doc_id: str) -> dict | None:
        """Retrieve a registered document by ID, checking Supabase if not in memory."""
        if doc_id in self._documents:
            return self._documents[doc_id]

        try:
            from app.services.supabase_service import supabase_service
            if supabase_service.is_configured:
                remote_doc = supabase_service.get_document(doc_id)
                if remote_doc:
                    self._documents[doc_id] = remote_doc
                    return remote_doc
        except Exception as e:
            logger.warning("Failed to fetch document %s from Supabase: %s", doc_id, e)

        return None

    def delete_document(self, doc_id: str) -> bool:
        """Remove a registered document from both local memory and Supabase."""
        deleted_local = False
        if doc_id in self._documents:
            del self._documents[doc_id]
            deleted_local = True

        deleted_remote = False
        try:
            from app.services.supabase_service import supabase_service
            if supabase_service.is_configured:
                deleted_remote = supabase_service.delete_document(doc_id)
        except Exception as e:
            logger.warning("Failed to delete document %s from Supabase: %s", doc_id, e)

        return deleted_local or deleted_remote


document_service = DocumentService()

