"""Tests for SupabaseService: missing-credential handling and non-blocking degradation."""

import pytest
from app.services.supabase_service import SupabaseService


def test_supabase_unconfigured_graceful_degradation() -> None:
    """Verify that an unconfigured Supabase service handles operations gracefully without throwing exceptions."""
    service = SupabaseService()
    # In test environment without explicit valid env vars, it should not be configured
    # or should safely report its configuration state

    # Test saving verification does not raise an exception
    res = service.save_verification(
        verification_id="test-uuid-1234",
        question="What is Paris?",
        answer="Paris is the capital of France.",
        context=["France capital is Paris."],
        is_hallucinated=False,
        hallucination_score=None,
        span_count=0,
        model_name="test-model",
        execution_time_ms=12.5,
        spans=[],
    )
    # When unconfigured, returns None safely
    if not service.is_configured:
        assert res is None

    # Test querying history does not crash
    history = service.get_verification_history()
    assert isinstance(history, list)
    if not service.is_configured:
        assert history == []

    # Test saving document metadata does not crash
    doc_res = service.save_document_metadata(
        document_id="doc-123",
        filename="test.pdf",
        file_type="application/pdf",
        file_size_bytes=1024,
        chunk_count=3,
    )
    if not service.is_configured:
        assert doc_res is None


def test_supabase_configured_property() -> None:
    """Verify is_configured boolean property reflects client state."""
    service = SupabaseService()
    assert isinstance(service.is_configured, bool)

