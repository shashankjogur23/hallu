"""Retrieval service for selecting relevant context chunks given a query.

Uses TF-IDF vectorization and cosine similarity for lightweight, fast,
local passage retrieval without external API or heavy embedding overhead.
"""

import logging
from typing import Sequence
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.schemas.verification import RetrievedChunk

logger = logging.getLogger(__name__)


class RetrievalService:
    """Service to rank and retrieve top relevant context chunks for a given query."""

    @staticmethod
    def retrieve_relevant_contexts(
        query: str,
        contexts: Sequence[str],
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[RetrievedChunk]:
        """Rank and return the top-k most relevant passages for a query.

        Args:
            query: Question or search string.
            contexts: List of candidate context passages.
            top_k: Maximum number of chunks to return.
            min_score: Minimum cosine similarity score (0.0 to 1.0) threshold.

        Returns:
            List of RetrievedChunk sorted by relevance score descending.
        """
        if not contexts:
            return []

        cleaned_contexts = [c.strip() for c in contexts if c and c.strip()]
        if not cleaned_contexts:
            return []

        if not query or not query.strip():
            # If query is empty, return up to top_k default chunks with 0.0 score
            return [
                RetrievedChunk(chunk_index=i, text=c, score=0.0)
                for i, c in enumerate(cleaned_contexts[:top_k])
            ]

        try:
            # Build TF-IDF matrix across all candidate contexts + the query
            corpus = list(cleaned_contexts) + [query.strip()]
            vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                lowercase=True,
            )
            tfidf_matrix = vectorizer.fit_transform(corpus)

            # Query vector is the last item
            context_vectors = tfidf_matrix[:-1]
            query_vector = tfidf_matrix[-1:]

            # Compute cosine similarity between query and each context
            scores: np.ndarray = cosine_similarity(query_vector, context_vectors)[0]

            # Rank by score descending
            ranked_indices = np.argsort(scores)[::-1]

            results: list[RetrievedChunk] = []
            for rank_idx in ranked_indices:
                score = float(scores[rank_idx])
                if score < min_score:
                    continue
                results.append(
                    RetrievedChunk(
                        chunk_index=int(rank_idx),
                        text=cleaned_contexts[rank_idx],
                        score=round(score, 4),
                    )
                )
                if len(results) >= top_k:
                    break

            # If all scores were 0 (e.g. completely disjoint vocab), still return top-k candidates
            if not results and cleaned_contexts:
                for i in range(min(top_k, len(cleaned_contexts))):
                    results.append(
                        RetrievedChunk(
                            chunk_index=i,
                            text=cleaned_contexts[i],
                            score=0.0,
                        )
                    )

            return results
        except Exception as e:
            logger.warning(
                "TF-IDF retrieval encountered error: %s. Falling back to default ordering.",
                e,
            )
            return [
                RetrievedChunk(chunk_index=i, text=c, score=0.0)
                for i, c in enumerate(cleaned_contexts[:top_k])
            ]


retrieval_service = RetrievalService()

