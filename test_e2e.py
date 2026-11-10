"""End-to-End Test for HalluGuard Backend & API Integration."""

import io
import time
import subprocess
import sys
import httpx
import pymupdf


def test_live_server() -> int:
    print("=" * 70)
    print("HalluGuard Phase 3 End-to-End HTTP Integration Test")
    print("=" * 70)

    base_url = "http://127.0.0.1:8000"
    client = httpx.Client(base_url=base_url, timeout=60.0)

    # 1. Health check
    print("\n[1/7] Testing GET /health...")
    res = client.get("/health")
    print(f"  Status: {res.status_code}")
    print(f"  Response: {res.json()}")
    assert res.status_code == 200
    assert res.json()["detector_loaded"] is True
    print("  ✓ Health check PASSED")

    # 2. Upload TXT document
    print("\n[2/7] Testing POST /documents/upload (TXT)...")
    txt_content = b"France is a country in Europe. The capital is Paris. Population is 67 million."
    files = {"file": ("france_info.txt", io.BytesIO(txt_content), "text/plain")}
    res = client.post("/documents/upload", files=files)
    print(f"  Status: {res.status_code}")
    txt_doc = res.json()
    print(f"  Document ID: {txt_doc['id']}, Chunks: {txt_doc['chunk_count']}")
    assert res.status_code == 201
    print("  ✓ TXT upload PASSED")

    # 3. Upload PDF document
    print("\n[3/7] Testing POST /documents/upload (PDF)...")
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Official European Demographics Report.")
    page.insert_text((50, 100), "France has a total population of 67 million people.")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("demographics.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res = client.post("/documents/upload", files=files)
    print(f"  Status: {res.status_code}")
    pdf_doc = res.json()
    print(f"  Document ID: {pdf_doc['id']}, Chunks: {pdf_doc['chunk_count']}")
    assert res.status_code == 201
    print("  ✓ PDF upload PASSED")

    # 4. List documents
    print("\n[4/7] Testing GET /documents...")
    res = client.get("/documents")
    docs_data = res.json()
    print(f"  Total documents: {docs_data['total_documents']}")
    print(f"  Storage notice: {docs_data['storage_notice']}")
    assert len(docs_data["documents"]) >= 2
    print("  ✓ List documents PASSED")

    # 5. Verify hallucinated answer
    print("\n[5/7] Testing POST /verify (Hallucinated answer: 69 million)...")
    payload = {
        "question": "What is the capital of France and its population?",
        "answer": "The capital of France is Paris. The population of France is 69 million.",
        "context": [txt_doc["extracted_text"]],
    }
    t0 = time.time()
    res = client.post("/verify", json=payload)
    elapsed = time.time() - t0
    data = res.json()
    print(f"  Status: {res.status_code} in {elapsed:.2f}s")
    print(f"  Verdict: {data['summary']['verdict']}")
    print(f"  Spans flagged: {data['summary']['span_count']}")
    print(f"  Max confidence: {data['summary']['max_confidence']}")
    for s in data["spans"]:
        print(f"    -> Span: {s['text']!r} ({s['start']}-{s['end']}) conf={s['confidence']}")
    assert data["summary"]["is_hallucinated"] is True
    assert data["summary"]["verdict"] == "HALLUCINATED"
    assert any("69 million" in s["text"] for s in data["spans"])
    print("  ✓ Hallucination verification PASSED")

    # 6. Verify supported answer
    print("\n[6/7] Testing POST /verify (Supported answer: 67 million)...")
    payload_clean = {
        "question": "What is the capital of France and its population?",
        "answer": "The capital of France is Paris. The population of France is 67 million.",
        "context": [txt_doc["extracted_text"]],
    }
    res = client.post("/verify", json=payload_clean)
    data_clean = res.json()
    print(f"  Status: {res.status_code}")
    print(f"  Verdict: {data_clean['summary']['verdict']}")
    print(f"  Spans flagged: {data_clean['summary']['span_count']}")
    assert data_clean["summary"]["is_hallucinated"] is False
    assert data_clean["summary"]["verdict"] == "CLEAN"
    assert len(data_clean["spans"]) == 0
    print("  ✓ Supported answer verification PASSED")

    # 7. Check verification history & stats
    print("\n[7/7] Testing GET /verifications/history & /verifications/stats...")
    res_hist = client.get("/verifications/history")
    hist_data = res_hist.json()
    print(f"  History count: {hist_data['total']}")
    print(f"  Storage notice: {hist_data['storage_notice']}")
    assert hist_data["total"] >= 2

    res_stats = client.get("/verifications/stats")
    stats_data = res_stats.json()
    print(f"  Stats: {stats_data}")
    assert stats_data["total_verifications"] >= 2
    assert stats_data["flagged_answers"] >= 1
    assert stats_data["clean_answers"] >= 1
    print("  ✓ Verification history & stats PASSED")

    print("\n" + "=" * 70)
    print("ALL LIVE HTTP INTEGRATION TESTS PASSED!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(test_live_server())

