"""Tests for RetrievalService: TF-IDF context ranking and relevance retrieval."""

import pytest
from app.services.retrieval_service import RetrievalService


def test_relevant_context_ranking() -> None:
    """Test that context retrieval ranks the semantically relevant passage first."""
    passages = [
        "The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris.",
        "The population of France is 67 million according to recent census data.",
        "French cuisine is renowned worldwide for its pastry, bread, and wine.",
        "Germany borders France to the northeast across the Rhine river.",
    ]

    query = "What is the population of France?"
    results = RetrievalService.retrieve_relevant_contexts(
        query=query, contexts=passages, top_k=2
    )

    assert len(results) == 2
    # The population passage should be ranked first with highest score
    top_result = results[0]
    assert "population" in top_result.text.lower()
    assert "67 million" in top_result.text
    assert top_result.score > 0.0
    assert results[0].score >= results[1].score


def test_retrieval_empty_contexts() -> None:
    """Test retrieval with empty context list."""
    results = RetrievalService.retrieve_relevant_contexts(
        query="Any query", contexts=[], top_k=3
    )
    assert results == []


def test_retrieval_empty_query() -> None:
    """Test retrieval with empty query returns default top-k candidates."""
    passages = ["Chunk A", "Chunk B", "Chunk C"]
    results = RetrievalService.retrieve_relevant_contexts(
        query="", contexts=passages, top_k=2
    )
    assert len(results) == 2
    assert results[0].text == "Chunk A"
    assert results[1].text == "Chunk B"

