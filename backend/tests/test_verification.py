"""Tests for POST /verify endpoint with real model inference."""

import pytest
from fastapi.testclient import TestClient

FRANCE_CONTEXT = (
    "France is a country in Europe. The capital of France is Paris. "
    "The population of France is 67 million."
)
FRANCE_QUESTION = "What is the capital of France and its population?"


def test_verify_hallucinated_answer(client: TestClient) -> None:
    """Test POST /verify with known incorrect France population claim (69 million vs 67 million)."""
    payload = {
        "question": FRANCE_QUESTION,
        "answer": "The capital of France is Paris. The population of France is 69 million.",
        "context": [FRANCE_CONTEXT],
    }

    response = client.post("/verify", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert data["question"] == FRANCE_QUESTION
    assert data["answer"] == payload["answer"]

    # Verify summary
    summary = data["summary"]
    assert summary["is_hallucinated"] is True
    assert summary["verdict"] in ("HALLUCINATED", "CONTRADICTED", "UNSUPPORTED")
    assert summary["span_count"] >= 1
    assert summary["max_confidence"] is not None
    # Confidence threshold for this detected hallucination
    assert summary["max_confidence"] >= 0.70

    # Verify detected spans
    spans = data["spans"]
    assert len(spans) >= 1
    detected_texts = [s["text"] for s in spans]
    # Check that the hallucinated statement is detected
    assert any("69 million" in t for t in detected_texts)
    for span in spans:
        assert span["start"] >= 0
        assert span["end"] > span["start"]
        assert span["confidence"] is not None


def test_verify_supported_answer(client: TestClient) -> None:
    """Test POST /verify with known correct supported answer (67 million)."""
    payload = {
        "question": FRANCE_QUESTION,
        "answer": "The capital of France is Paris. The population of France is 67 million.",
        "context": [FRANCE_CONTEXT],
    }

    response = client.post("/verify", json=payload)
    assert response.status_code == 200

    data = response.json()
    summary = data["summary"]
    assert summary["is_hallucinated"] is False
    assert summary["verdict"] in ("SUPPORTED", "CLEAN")
    assert summary["span_count"] == 0
    assert len(data["spans"]) == 0
    assert (
        "supported" in summary["message"].lower()
        or "grounded" in summary["message"].lower()
        or "clean" in summary["message"].lower()
    )


def test_verify_contradicted_ordinal_ranking(client: TestClient) -> None:
    """Test POST /verify with ordinal relational inversion requiring NLI proposition decomposition."""
    denali_ctx = (
        "Denali, formerly officially named Mount McKinley, is located in the Alaska Range in the "
        "interior of the U.S. state of Alaska. Its summit reaches 6,190 metres above sea level, "
        "making it the highest mountain peak in North America, followed by Mount Logan in Canada."
    )
    payload = {
        "question": "What is the ranking of Denali among North American mountain peaks?",
        "answer": "Denali is the second-highest mountain peak in North America, ranking just below Mount Logan.",
        "context": [denali_ctx],
    }

    response = client.post("/verify", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["summary"]["is_hallucinated"] is True
    assert data["summary"]["verdict"] in ("CONTRADICTED", "HALLUCINATED")
    assert len(data["contradicted_claims"]) >= 1
    assert any("second-highest" in c["text"] or "ranking" in c["text"] for c in data["contradicted_claims"])


def test_verify_oxford_comma_coordinated_list(client: TestClient) -> None:
    """Test POST /verify with multi-clause answer containing an Oxford comma serial list."""
    borneo_ctx = (
        "Borneo is the third-largest island in the world and the largest in Asia. "
        "The island is politically divided among three sovereign nations: Indonesia, Malaysia, and the sultanate of Brunei."
    )
    payload = {
        "question": "Which countries share the island of Borneo?",
        "answer": "Borneo is the third-largest island in the world, and its territory is politically divided among Indonesia, Malaysia, and Brunei.",
        "context": [borneo_ctx],
    }

    response = client.post("/verify", json=payload)
    assert response.status_code == 200

    data = response.json()
    # Fully supported statement must not fragment list or flag spurious hallucination
    assert data["summary"]["is_hallucinated"] is False
    assert data["summary"]["verdict"] in ("SUPPORTED", "CLEAN")


def test_verify_enhanced_response_fields(client: TestClient) -> None:
    """Test that all enhanced Phase 9 response fields are populated."""
    payload = {
        "question": FRANCE_QUESTION,
        "answer": "The capital of France is Paris. The population of France is 67 million.",
        "context": [FRANCE_CONTEXT],
    }

    response = client.post("/verify", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "contradicted_claims" in data
    assert "unsupported_claims" in data
    assert "supported_claims" in data
    assert "detector_breakdown" in data
    assert "retrieved_evidence" in data

    breakdown = data["detector_breakdown"]
    assert "lettucedetect_spans" in breakdown
    assert "nli_contradictions" in breakdown
    assert "fusion_verdict" in breakdown
    assert "fusion_source" in breakdown


def test_verify_string_context_format(client: TestClient) -> None:
    """Test POST /verify where context is provided as a single string instead of a list."""
    payload = {
        "question": FRANCE_QUESTION,
        "answer": "The capital of France is Paris. The population of France is 67 million.",
        "context": FRANCE_CONTEXT,  # single string
    }

    response = client.post("/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["is_hallucinated"] is False


def test_verify_empty_answer_handling(client: TestClient) -> None:
    """Test POST /verify with empty or whitespace-only answer (must reject with 422)."""
    # Empty string
    response = client.post(
        "/verify",
        json={"question": "Test", "answer": "", "context": ["Some context."]},
    )
    assert response.status_code == 422

    # Whitespace-only string
    response_ws = client.post(
        "/verify",
        json={"question": "Test", "answer": "   \n\t  ", "context": ["Some context."]},
    )
    assert response_ws.status_code == 422


def test_verify_invalid_request_handling(client: TestClient) -> None:
    """Test POST /verify with various invalid request payloads (must reject with 422)."""
    # Missing answer
    res_no_answer = client.post("/verify", json={"context": ["Some context."]})
    assert res_no_answer.status_code == 422

    # Missing context
    res_no_context = client.post("/verify", json={"answer": "Some answer."})
    assert res_no_context.status_code == 422

    # Empty context list
    res_empty_context = client.post(
        "/verify", json={"answer": "Some answer.", "context": []}
    )
    assert res_empty_context.status_code == 422

    # Invalid min_confidence (> 1.0)
    res_invalid_conf = client.post(
        "/verify",
        json={
            "answer": "Some answer.",
            "context": ["Some context."],
            "min_confidence": 1.5,
        },
    )
    assert res_invalid_conf.status_code == 422

    # Negative min_confidence (< 0.0)
    res_neg_conf = client.post(
        "/verify",
        json={
            "answer": "Some answer.",
            "context": ["Some context."],
            "min_confidence": -0.1,
        },
    )
    assert res_neg_conf.status_code == 422

