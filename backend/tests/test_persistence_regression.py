"""
Regression tests for durable document persistence (Phase 9.6 Tasks 1 & 2).
Covers:
- HIST-BUG-013: Document persistence surviving backend restart / fresh process.
- Supabase failure graceful fallback without false persistence reporting.
- Local-only mode status identification.
- Remote and local document deletion synchronization.
"""

import pytest
from unittest.mock import PropertyMock, patch
from app.services.document_service import DocumentService
from app.services.supabase_service import SupabaseService


def test_document_restart_persistence_simulation():
    """Verify that a newly instantiated DocumentService retrieves previously persisted documents from Supabase."""
    from app.services.supabase_service import supabase_service

    if not supabase_service.is_configured:
        pytest.skip("Supabase not configured in local environment; tested via mock in fallback test.")

    # Ingest document in initial process service
    service1 = DocumentService()
    test_text = "Durable persistence test content across simulated process restarts."
    doc1 = service1.ingest_document(
        filename="restart_test_doc.txt",
        file_bytes=test_text.encode("utf-8"),
        content_type="text/plain",
    )
    doc_id = doc1["id"]
    assert doc1["is_persistent"] is True, "Document should be persisted to Supabase"

    try:
        # Simulate backend process restart: create a brand new DocumentService with empty in-memory state
        service2 = DocumentService()
        assert len(service2._documents) == 0, "Fresh DocumentService memory must start empty"

        # List documents: should query Supabase and hydrate the fresh process
        docs = service2.list_documents()
        found = any(d["id"] == doc_id for d in docs)
        assert found is True, f"Fresh DocumentService did not retrieve document {doc_id} from Supabase"

        # Get document detail: should fetch full text and chunks from Supabase
        doc_detail = service2.get_document(doc_id)
        assert doc_detail is not None, "Failed to get document detail after simulated restart"
        assert doc_detail["extracted_text"] == test_text
        assert len(doc_detail["chunks"]) > 0
        assert doc_detail["is_persistent"] is True

    finally:
        # Clean up
        service1.delete_document(doc_id)


def test_persistence_failure_fallback_behavior():
    """Verify that if Supabase persistence fails, is_persistent is False and local operations continue safely."""
    service = DocumentService()
    test_text = "Fallback test content when remote persistence fails."

    # Mock supabase_service.save_document to simulate a failure
    with patch("app.services.supabase_service.supabase_service.save_document", return_value=False):
        doc = service.ingest_document(
            filename="fallback_test.txt",
            file_bytes=test_text.encode("utf-8"),
            content_type="text/plain",
        )

        doc_id = doc["id"]
        # 1. is_persistent must accurately reflect failure, not false success
        assert doc["is_persistent"] is False, "Failed Supabase write must not report is_persistent=True"

        # 2. Local operations must remain functional
        assert doc_id in service._documents
        detail = service.get_document(doc_id)
        assert detail is not None
        assert detail["extracted_text"] == test_text
        assert detail["is_persistent"] is False

        # Clean up
        service.delete_document(doc_id)


def test_local_only_mode_identification():
    """Verify that when Supabase is unconfigured, system operates in local-only mode with accurate status."""
    service = DocumentService()
    test_text = "Local-only test content without database credentials."

    with patch.object(SupabaseService, "is_configured", new_callable=PropertyMock, return_value=False):
        doc = service.ingest_document(
            filename="local_only.txt",
            file_bytes=test_text.encode("utf-8"),
            content_type="text/plain",
        )
        doc_id = doc["id"]

        # Must report is_persistent=False
        assert doc["is_persistent"] is False
        assert doc_id in service._documents

        # Listing and retrieval work locally without throwing exceptions
        all_docs = service.list_documents()
        assert any(d["id"] == doc_id for d in all_docs)

        detail = service.get_document(doc_id)
        assert detail is not None
        assert detail["extracted_text"] == test_text

        # Delete works cleanly
        deleted = service.delete_document(doc_id)
        assert deleted is True
        assert doc_id not in service._documents


def test_deletion_removes_both_local_and_remote():
    """Verify that document deletion deletes both local cache and triggers Supabase deletion."""
    service = DocumentService()
    test_text = "Deletion synchronization test."

    with patch("app.services.supabase_service.supabase_service.save_document", return_value=True), \
         patch("app.services.supabase_service.supabase_service.delete_document", return_value=True) as mock_delete:

        doc = service.ingest_document(
            filename="sync_delete.txt",
            file_bytes=test_text.encode("utf-8"),
            content_type="text/plain",
        )
        doc_id = doc["id"]
        assert doc_id in service._documents

        deleted = service.delete_document(doc_id)
        assert deleted is True
        assert doc_id not in service._documents
        mock_delete.assert_called_once_with(doc_id)
