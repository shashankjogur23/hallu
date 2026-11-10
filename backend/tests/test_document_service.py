"""Tests for DocumentService: PDF extraction, TXT extraction, and text chunking."""

import io
import tempfile
from pathlib import Path
import pytest
from app.services.document_service import DocumentService


def create_sample_pdf_bytes(text_lines: list[str]) -> bytes:
    """Helper to generate a valid PDF in memory using PyMuPDF."""
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf

    doc = pymupdf.open()
    page = doc.new_page()
    y = 72
    for line in text_lines:
        page.insert_text((50, y), line)
        y += 25
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_extraction_from_bytes() -> None:
    """Test extracting text from raw PDF bytes."""
    lines = [
        "HalluGuard Phase 2 Verification Document",
        "France is a country in Western Europe.",
        "The official population is 67 million.",
    ]
    pdf_bytes = create_sample_pdf_bytes(lines)

    extracted = DocumentService.extract_text_from_pdf(pdf_bytes)
    for line in lines:
        assert line in extracted


def test_pdf_extraction_from_file(tmp_path: Path) -> None:
    """Test extracting text from a PDF file path."""
    lines = ["Test Line 1", "Test Line 2 - Ground truth reference."]
    pdf_bytes = create_sample_pdf_bytes(lines)

    pdf_file = tmp_path / "sample.pdf"
    pdf_file.write_bytes(pdf_bytes)

    extracted = DocumentService.extract_text_from_pdf(pdf_file)
    assert "Test Line 1" in extracted
    assert "Test Line 2" in extracted


def test_pdf_extraction_empty_bytes() -> None:
    """Test that empty PDF bytes raises ValueError."""
    with pytest.raises(ValueError, match="empty"):
        DocumentService.extract_text_from_pdf(b"")


def test_txt_extraction_utf8(tmp_path: Path) -> None:
    """Test extracting text from a UTF-8 encoded text file."""
    content = "Hello world! Hallucination detection in French: vérification des faits."
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text(content, encoding="utf-8")

    extracted = DocumentService.extract_text_from_txt(txt_file)
    assert extracted == content


def test_txt_extraction_bytes() -> None:
    """Test extracting text directly from raw bytes with special characters."""
    content = "Sample reference text with umlauts: äöü and accents: éà."
    raw_bytes = content.encode("utf-8")

    extracted = DocumentService.extract_text_from_txt(raw_bytes)
    assert extracted == content


def test_txt_extraction_empty() -> None:
    """Test extracting text from empty input."""
    assert DocumentService.extract_text_from_txt("") == ""
    assert DocumentService.extract_text_from_txt(b"") == ""


def test_document_chunking_boundaries() -> None:
    """Test text chunking with natural boundary awareness and offsets."""
    text = (
        "Paragraph one introduces the context of hallucination detection in LLMs.\n\n"
        "Paragraph two discusses LettuceDetect and ModernBERT architecture.\n\n"
        "Paragraph three covers evaluation metrics and precision scores."
    )

    chunks = DocumentService.chunk_text(text, chunk_size=100, chunk_overlap=20)
    assert len(chunks) >= 2

    # Check offsets and chunk properties
    for i, chunk in enumerate(chunks):
        assert chunk.chunk_index == i
        assert len(chunk.text) > 0
        assert chunk.char_start >= 0
        assert chunk.char_end > chunk.char_start
        # Text at offsets in original string should match chunk content
        assert chunk.text in text


def test_document_chunking_invalid_parameters() -> None:
    """Test invalid chunking parameters raise ValueError."""
    with pytest.raises(ValueError):
        DocumentService.chunk_text("Some text", chunk_size=50, chunk_overlap=50)

    with pytest.raises(ValueError):
        DocumentService.chunk_text("Some text", chunk_size=-10, chunk_overlap=5)

    with pytest.raises(ValueError):
        DocumentService.chunk_text("Some text", chunk_size=50, chunk_overlap=-5)

