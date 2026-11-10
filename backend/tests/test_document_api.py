"""Tests for Document upload API and verification history endpoints."""

import io
import pytest
from fastapi.testclient import TestClient


def create_sample_pdf_bytes(text: str) -> bytes:
    import pymupdf

    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_upload_txt_document(client: TestClient) -> None:
    """Test uploading a TXT document via POST /documents/upload."""
    txt_content = b"France is in Europe. The capital is Paris. Population is 67 million."
    files = {"file": ("reference.txt", io.BytesIO(txt_content), "text/plain")}

    response = client.post("/documents/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["filename"] == "reference.txt"
    assert data["file_type"] == "text/plain"
    assert data["chunk_count"] >= 1
    assert "Paris" in data["extracted_text"]


def test_upload_pdf_document(client: TestClient) -> None:
    """Test uploading a PDF document via POST /documents/upload."""
    pdf_bytes = create_sample_pdf_bytes("Ground truth knowledge base: AI safety and LettuceDetect.")
    files = {"file": ("manual.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

    response = client.post("/documents/upload", files=files)
    assert response.status_code == 201

    data = response.json()
    assert data["filename"] == "manual.pdf"
    assert data["file_type"] == "application/pdf"
    assert data["chunk_count"] >= 1


def test_list_and_get_and_delete_documents(client: TestClient) -> None:
    """Test full document lifecycle: upload, list, get, delete."""
    # 1. Upload
    content = b"Sample context for testing lifecycle."
    files = {"file": ("lifecycle.txt", io.BytesIO(content), "text/plain")}
    res_upload = client.post("/documents/upload", files=files)
    assert res_upload.status_code == 201
    doc_id = res_upload.json()["id"]

    # 2. List
    res_list = client.get("/documents")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert any(d["id"] == doc_id for d in list_data["documents"])

    # 3. Get detail
    res_get = client.get(f"/documents/{doc_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == doc_id

    # 4. Delete
    res_del = client.delete(f"/documents/{doc_id}")
    assert res_del.status_code == 200
    assert res_del.json()["deleted"] is True

    # 5. Verify 404 after delete
    res_get_del = client.get(f"/documents/{doc_id}")
    assert res_get_del.status_code == 404


def test_verification_history_and_stats(client: TestClient) -> None:
    """Test GET /verifications/history and GET /verifications/stats."""
    # Check history endpoint works
    res_hist = client.get("/verifications/history")
    assert res_hist.status_code == 200
    hist_data = res_hist.json()
    assert "verifications" in hist_data
    assert "is_persistent" in hist_data
    assert "storage_notice" in hist_data

    # Check stats endpoint works
    res_stats = client.get("/verifications/stats")
    assert res_stats.status_code == 200
    stats_data = res_stats.json()
    assert "total_verifications" in stats_data
    assert "flagged_answers" in stats_data
    assert "clean_answers" in stats_data

