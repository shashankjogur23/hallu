"""HalluGuard Phase 2 Comprehensive Integration Test Runner.

Executes all 10 verification criteria against the live FastAPI backend,
using the real LettuceDetect ModernBERT model and PyMuPDF engine.
"""

import sys
import time
import traceback
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.services.detector_service import detector_service
from app.services.document_service import DocumentService
from app.services.retrieval_service import RetrievalService
from app.services.supabase_service import SupabaseService


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_step(step_num: int, title: str) -> None:
    print(f"\n[{step_num}/10] {title}")


def main() -> int:
    print_header("HalluGuard Phase 2: Live Backend Integration Test")
    overall_start = time.time()
    results: dict[str, bool] = {}

    # ------------------------------------------------------------------
    # Step 1: FastAPI Application Startup & Model Loading via Lifespan
    # ------------------------------------------------------------------
    print_step(1, "Starting FastAPI Application & Loading LettuceDetect Model...")
    t0 = time.time()
    try:
        with TestClient(app) as client:
            startup_time = time.time() - t0
            print(f"  ✓ FastAPI application initialized with lifespan in {startup_time:.2f}s")
            print(f"  ✓ Model loaded status: {detector_service.is_loaded}")
            print(f"  ✓ Model path: {detector_service.model_path}")
            print(f"  ✓ Inference device: {detector_service.device}")
            assert detector_service.is_loaded, "Detector model was not loaded during startup!"
            results["1. FastAPI Startup & Model Loading"] = True

            # ------------------------------------------------------------------
            # Step 2: GET /health
            # ------------------------------------------------------------------
            print_step(2, "Testing GET /health Endpoint...")
            res = client.get("/health")
            print(f"  HTTP Status: {res.status_code}")
            health_data = res.json()
            print(f"  Response: {health_data}")
            assert res.status_code == 200
            assert health_data["status"] == "healthy"
            assert health_data["detector_loaded"] is True
            assert health_data["device"] == "cpu"
            results["2. GET /health"] = True

            # ------------------------------------------------------------------
            # Step 3: POST /verify with Known Incorrect France Population Claim
            # ------------------------------------------------------------------
            print_step(3, "Testing POST /verify with Incorrect Claim (69 million)...")
            france_context = (
                "France is a country in Europe. The capital of France is Paris. "
                "The population of France is 67 million."
            )
            france_question = "What is the capital of France and its population?"
            incorrect_answer = (
                "The capital of France is Paris. The population of France is 69 million."
            )

            res = client.post(
                "/verify",
                json={
                    "question": france_question,
                    "answer": incorrect_answer,
                    "context": [france_context],
                },
            )
            print(f"  HTTP Status: {res.status_code}")
            verify_data = res.json()
            print(f"  Verdict: {verify_data['summary']['verdict']}")
            print(f"  Is Hallucinated: {verify_data['summary']['is_hallucinated']}")
            print(f"  Spans Detected: {len(verify_data['spans'])}")
            print(f"  Summary Message: {verify_data['summary']['message']}")
            for idx, s in enumerate(verify_data["spans"], 1):
                print(f"    Span #{idx}: text={s['text']!r} offsets=({s['start']}, {s['end']}) conf={s['confidence']}")

            assert res.status_code == 200
            assert verify_data["summary"]["is_hallucinated"] is True
            assert verify_data["summary"]["verdict"] in ("HALLUCINATED", "CONTRADICTED", "UNSUPPORTED")
            assert len(verify_data["spans"]) >= 1
            assert any("69 million" in s["text"] for s in verify_data["spans"])
            results["3. POST /verify (Incorrect Claim)"] = True

            # ------------------------------------------------------------------
            # Step 4: POST /verify with Correct Supported Answer
            # ------------------------------------------------------------------
            print_step(4, "Testing POST /verify with Supported Answer (67 million)...")
            correct_answer = (
                "The capital of France is Paris. The population of France is 67 million."
            )

            res = client.post(
                "/verify",
                json={
                    "question": france_question,
                    "answer": correct_answer,
                    "context": [france_context],
                },
            )
            print(f"  HTTP Status: {res.status_code}")
            clean_data = res.json()
            print(f"  Verdict: {clean_data['summary']['verdict']}")
            print(f"  Is Hallucinated: {clean_data['summary']['is_hallucinated']}")
            print(f"  Spans Detected: {len(clean_data['spans'])}")
            print(f"  Summary Message: {clean_data['summary']['message']}")

            assert res.status_code == 200
            assert clean_data["summary"]["is_hallucinated"] is False
            assert clean_data["summary"]["verdict"] in ("SUPPORTED", "CLEAN")
            assert len(clean_data["spans"]) == 0
            results["4. POST /verify (Supported Answer)"] = True

            # ------------------------------------------------------------------
            # Step 4B: POST /verify with Relational Ordinal Contradiction (Denali)
            # ------------------------------------------------------------------
            print_step(4, "Testing POST /verify with Ordinal Ranking Contradiction (Denali Inversion)...")
            denali_ctx = (
                "Denali, formerly officially named Mount McKinley, is located in the Alaska Range in the "
                "interior of the U.S. state of Alaska. Its summit reaches 6,190 metres above sea level, "
                "making it the highest mountain peak in North America, followed by Mount Logan in Canada."
            )
            denali_ans = (
                "Denali is the second-highest mountain peak in North America, ranking just below Mount Logan."
            )

            res_denali = client.post(
                "/verify",
                json={
                    "question": "What is the ranking of Denali among North American mountain peaks?",
                    "answer": denali_ans,
                    "context": [denali_ctx],
                },
            )
            print(f"  HTTP Status: {res_denali.status_code}")
            denali_data = res_denali.json()
            print(f"  Verdict: {denali_data['summary']['verdict']}")
            print(f"  Is Hallucinated: {denali_data['summary']['is_hallucinated']}")
            print(f"  Contradicted Claims Count: {len(denali_data.get('contradicted_claims', []))}")
            for c in denali_data.get("contradicted_claims", []):
                print(f"    Claim: text={c['text']!r} conf={c['confidence']} source={c['source']}")
            print(f"  Detector Breakdown: {denali_data.get('detector_breakdown')}")

            assert res_denali.status_code == 200
            assert denali_data["summary"]["is_hallucinated"] is True
            assert denali_data["summary"]["verdict"] == "CONTRADICTED"
            assert len(denali_data["contradicted_claims"]) >= 1
            assert "detector_breakdown" in denali_data
            assert "supported_claims" in denali_data
            results["4B. Hybrid Relational Contradiction Verification"] = True

            # ------------------------------------------------------------------
            # Step 5: Invalid Request Handling
            # ------------------------------------------------------------------
            print_step(5, "Testing Invalid Request Handling (422 Unprocessable)...")
            # Missing context
            res1 = client.post("/verify", json={"answer": "Some answer."})
            print(f"  Missing context -> status: {res1.status_code}")
            assert res1.status_code == 422

            # Empty context list
            res2 = client.post("/verify", json={"answer": "Some answer.", "context": []})
            print(f"  Empty context list -> status: {res2.status_code}")
            assert res2.status_code == 422

            # Invalid confidence (> 1.0)
            res3 = client.post(
                "/verify",
                json={"answer": "A", "context": ["C"], "min_confidence": 2.0},
            )
            print(f"  Confidence > 1.0 -> status: {res3.status_code}")
            assert res3.status_code == 422
            results["5. Invalid Request Handling"] = True

            # ------------------------------------------------------------------
            # Step 6: Empty Answer Handling
            # ------------------------------------------------------------------
            print_step(6, "Testing Empty Answer Handling...")
            res_empty = client.post(
                "/verify",
                json={"answer": "", "context": ["Valid context."]},
            )
            print(f"  Empty answer -> status: {res_empty.status_code}")
            assert res_empty.status_code == 422

            res_ws = client.post(
                "/verify",
                json={"answer": "   \n\t  ", "context": ["Valid context."]},
            )
            print(f"  Whitespace-only answer -> status: {res_ws.status_code}")
            assert res_ws.status_code == 422
            results["6. Empty Answer Handling"] = True

            # ------------------------------------------------------------------
            # Step 7: PDF Text Extraction using PyMuPDF
            # ------------------------------------------------------------------
            print_step(7, "Testing PDF Text Extraction using PyMuPDF...")
            import pymupdf

            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((50, 72), "HalluGuard PDF Ingestion Test.")
            page.insert_text((50, 100), "Paris is the capital of France.")
            page.insert_text((50, 128), "Population recorded at 67 million.")
            pdf_bytes = doc.tobytes()
            doc.close()

            extracted_pdf_text = DocumentService.extract_text_from_pdf(pdf_bytes)
            print(f"  Generated PDF size: {len(pdf_bytes)} bytes")
            print(f"  Extracted text:\n    {extracted_pdf_text!r}")
            assert "HalluGuard PDF Ingestion Test." in extracted_pdf_text
            assert "Paris is the capital of France." in extracted_pdf_text
            results["7. PDF Text Extraction (PyMuPDF)"] = True

            # ------------------------------------------------------------------
            # Step 8: TXT Text Extraction
            # ------------------------------------------------------------------
            print_step(8, "Testing TXT Text Extraction...")
            txt_content = (
                "Ground truth knowledge base article:\n"
                "Artificial Intelligence models can produce hallucinations.\n"
                "HalluGuard verifies generated outputs against source texts."
            )
            extracted_txt = DocumentService.extract_text_from_txt(
                txt_content.encode("utf-8")
            )
            print(f"  Extracted TXT:\n    {extracted_txt!r}")
            assert "Artificial Intelligence models can produce hallucinations." in extracted_txt
            results["8. TXT Text Extraction"] = True

            # ------------------------------------------------------------------
            # Step 9: Context Chunking and Retrieval
            # ------------------------------------------------------------------
            print_step(9, "Testing Context Chunking and TF-IDF Retrieval...")
            long_doc = (
                "Section 1: Geography.\n"
                "France is located in Western Europe and features diverse landscapes.\n\n"
                "Section 2: Demographics.\n"
                "The total population of France is 67 million as of recent demographic surveys.\n\n"
                "Section 3: Economy.\n"
                "The currency used in France is the Euro, and its economy ranks among the largest."
            )

            # Chunk document
            chunks = DocumentService.chunk_text(long_doc, chunk_size=120, chunk_overlap=30)
            print(f"  Created {len(chunks)} text chunks:")
            for c in chunks:
                print(f"    Chunk #{c.chunk_index} ({c.char_start}-{c.char_end}): {c.text[:50]}...")

            # Retrieve top relevant context for question
            query = "What is the population count of France?"
            retrieved = RetrievalService.retrieve_relevant_contexts(
                query=query,
                contexts=[c.text for c in chunks],
                top_k=2,
            )
            print(f"\n  Query: {query!r}")
            print(f"  Retrieved Top-{len(retrieved)}:")
            for r in retrieved:
                print(f"    [score={r.score:.4f}] {r.text[:60]}...")

            assert len(retrieved) > 0
            assert "population" in retrieved[0].text.lower()
            assert "67 million" in retrieved[0].text
            assert retrieved[0].score > 0.0
            results["9. Chunking & Retrieval"] = True

            # ------------------------------------------------------------------
            # Step 10: Supabase Configuration & Missing Credential Handling
            # ------------------------------------------------------------------
            print_step(10, "Testing Supabase Configuration & Graceful Degradation...")
            supabase_svc = SupabaseService()
            print(f"  Supabase is_configured: {supabase_svc.is_configured}")

            # Test calling persistence methods when unconfigured
            save_result = supabase_svc.save_verification(
                verification_id="test-id-001",
                question="Q",
                answer="A",
                context=["C"],
                is_hallucinated=False,
                hallucination_score=None,
                span_count=0,
                model_name="test-model",
                execution_time_ms=10.0,
                spans=[],
            )
            print(f"  save_verification() result (safe non-blocking): {save_result}")

            history_result = supabase_svc.get_verification_history()
            print(f"  get_verification_history() result: {history_result}")

            doc_result = supabase_svc.save_document_metadata(
                document_id="doc-001",
                filename="demo.pdf",
                file_type="application/pdf",
                file_size_bytes=2048,
                chunk_count=2,
            )
            print(f"  save_document_metadata() result: {doc_result}")

            if not supabase_svc.is_configured:
                assert save_result is None
                assert history_result == []
                assert doc_result is None
                print("  ✓ Graceful degradation confirmed: local verification continues without error.")
            else:
                print("  ✓ Supabase is configured and connected.")
            results["10. Supabase & Missing Credentials"] = True

    except Exception as exc:
        print(f"\n❌ Test execution failed with exception: {exc}")
        traceback.print_exc()
        return 1

    # ------------------------------------------------------------------
    # Summary Table
    # ------------------------------------------------------------------
    total_elapsed = time.time() - overall_start
    print_header(f"Phase 2 Test Summary ({total_elapsed:.2f}s total)")
    all_passed = True
    for name, passed in results.items():
        status_mark = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"  {status_mark:8s} | {name}")

    print("=" * 70)
    if all_passed and len(results) >= 10:
        print(f"ALL {len(results)} VERIFICATION CRITERIA PASSED SUCCESSFULLY!")
        print("=" * 70)
        return 0
    else:
        print("SOME TESTS FAILED.")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())

