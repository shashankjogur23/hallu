"""Production Hybrid Hallucination Verification Service for HalluGuard.

Integrates:
1. LettuceDetect ModernBERT (Token-level sequence classification) for fine-grained span detection.
2. DeBERTa-v3 NLI (Cross-encoder sequence classification) for relational, ordinal, and entity contradiction verification.

Provides transparent 4-way decision logic:
- SUPPORTED: Answer is fully grounded and substantiated by reference context.
- CONTRADICTED: Answer directly conflicts with statements in reference context.
- UNSUPPORTED: Answer contains information not grounded/established by reference context.
- INSUFFICIENT EVIDENCE: Provided reference context is missing, empty, or inadequate.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from app.config import settings
from app.schemas.verification import (
    ClaimDetail,
    DetectorBreakdown,
    HallucinationSpan,
    VerificationSummary,
)
from app.services.detector_service import detector_service
from app.services.nli_service import nli_service

logger = logging.getLogger(__name__)


class HybridDetectorService:
    """Orchestrates LettuceDetect and DeBERTa-v3 NLI in a production hybrid pipeline."""

    def __init__(self) -> None:
        self._detector = detector_service
        self._nli = nli_service

    @property
    def is_loaded(self) -> bool:
        """Returns True if the primary detector is ready. NLI can gracefully degrade if disabled."""
        if not self._detector.is_loaded:
            return False
        if settings.nli_enabled and not self._nli.is_loaded:
            return False
        return True

    @property
    def model_name(self) -> str:
        """Combined model identifier string."""
        if settings.nli_enabled and self._nli.is_loaded:
            return f"{self._detector.model_path} + {self._nli.model_name}"
        return self._detector.model_path

    def load_models(self) -> None:
        """Loads both models once into memory during application startup."""
        logger.info("Initializing Hybrid Detector models...")
        # 1. Primary: LettuceDetect ModernBERT
        if not self._detector.is_loaded:
            self._detector.load_model()

        # 2. Secondary: DeBERTa-v3 NLI
        if settings.nli_enabled and not self._nli.is_loaded:
            try:
                self._nli.load_model()
            except Exception as e:
                logger.warning(
                    "Non-fatal: Failed to load DeBERTa-v3 NLI model. System will run in LettuceDetect-only mode: %s",
                    e,
                )

    def verify(
        self,
        context: List[str] | str,
        answer: str,
        question: Optional[str] = None,
        min_confidence: float = 0.0,
    ) -> Tuple[
        List[HallucinationSpan],
        VerificationSummary,
        List[ClaimDetail],
        List[ClaimDetail],
        List[ClaimDetail],
        DetectorBreakdown,
        float,
    ]:
        """Runs the hybrid verification pipeline.

        Returns:
            - spans: List of all detected suspicious spans (for backward compatibility)
            - summary: VerificationSummary with overall verdict
            - contradicted_claims: Claims conflicting with context
            - unsupported_claims: Claims fabricated / unestablished by context
            - supported_claims: Claims confirmed consistent with context
            - detector_breakdown: Granular outputs from each model
            - total_execution_time_ms: Total latency in milliseconds
        """
        t_total_start = time.perf_counter()

        # Normalize context
        if isinstance(context, str):
            context_list = [context.strip()] if context.strip() else []
        elif isinstance(context, list):
            context_list = [c.strip() for c in context if isinstance(c, str) and c.strip()]
        else:
            context_list = []

        # Validate inputs
        clean_answer = (answer or "").strip()
        if not clean_answer:
            raise ValueError("Answer text cannot be empty.")

        # Check for INSUFFICIENT EVIDENCE
        if not context_list:
            exec_time = round((time.perf_counter() - t_total_start) * 1000, 2)
            summary = VerificationSummary(
                is_hallucinated=True,
                span_count=0,
                max_confidence=None,
                verdict="INSUFFICIENT_EVIDENCE",
                message="No valid reference context was provided to verify the answer.",
            )
            breakdown = DetectorBreakdown(
                lettucedetect_spans=0,
                lettucedetect_verdict="INSUFFICIENT_EVIDENCE",
                nli_contradictions=0,
                nli_max_contradiction=0.0,
                fusion_verdict="INSUFFICIENT_EVIDENCE",
                fusion_source="no_context",
            )
            return [], summary, [], [], [], breakdown, exec_time

        combined_context = "\n\n".join(context_list)

        # -------------------------------------------------------------
        # 1. Primary Pass: LettuceDetect Token-Level Span Detection
        # -------------------------------------------------------------
        t_let_start = time.perf_counter()
        lettuce_spans_raw, lettuce_summary, _ = self._detector.predict(
            context=context_list,
            answer=clean_answer,
            question=question,
            min_confidence=min_confidence,
        )
        lettuce_latency_ms = round((time.perf_counter() - t_let_start) * 1000, 2)
        lettuce_has_spans = len(lettuce_spans_raw) > 0

        # -------------------------------------------------------------
        # 2. Secondary Pass: DeBERTa-v3 NLI Relational & Semantic Verification
        # -------------------------------------------------------------
        nli_latency_ms = 0.0
        nli_res: Dict[str, Any] = {
            "has_contradiction": False,
            "max_contradiction_score": 0.0,
            "max_entailment_score": 0.0,
            "contradictory_spans": [],
            "all_segments": [],
        }

        if settings.nli_enabled and self._nli.is_loaded:
            t_nli_start = time.perf_counter()
            try:
                nli_res = self._nli.analyze_answer(
                    context=combined_context,
                    answer=clean_answer,
                    question=question,
                )
            except Exception as e:
                logger.error("NLI analysis encountered non-fatal error: %s", e, exc_info=True)
            nli_latency_ms = round((time.perf_counter() - t_nli_start) * 1000, 2)

        # -------------------------------------------------------------
        # 3. Transparent Hybrid Decision Fusion (TASK 2)
        # -------------------------------------------------------------
        contradicted_claims: List[ClaimDetail] = []
        unsupported_claims: List[ClaimDetail] = []
        supported_claims: List[ClaimDetail] = []
        unified_spans: List[HallucinationSpan] = []

        nli_has_contra = nli_res["has_contradiction"]
        nli_contra_spans = nli_res["contradictory_spans"]

        # Collect Contradicted Claims (from NLI contradiction or LettuceDetect contradiction category)
        for cs in nli_contra_spans:
            claim = ClaimDetail(
                start=cs["start"],
                end=cs["end"],
                text=cs["text"],
                confidence=cs["confidence"],
                category="contradiction",
                source="nli_cross_encoder",
                explanation=f"Directly contradicts reference context (NLI contradiction score: {cs['confidence']:.2%}).",
            )
            contradicted_claims.append(claim)
            unified_spans.append(
                HallucinationSpan(
                    start=cs["start"],
                    end=cs["end"],
                    text=cs["text"],
                    confidence=cs["confidence"],
                    category="contradiction",
                )
            )

        # Collect Unsupported Claims from LettuceDetect
        for ls in lettuce_spans_raw:
            # Check if this span is already captured under contradiction
            is_subsumed = any(
                max(0, min(ls.end, c.end) - max(ls.start, c.start)) > 0
                for c in contradicted_claims
            )
            if not is_subsumed:
                cat = ls.category or "unsupported"
                if cat.lower() == "contradiction":
                    claim = ClaimDetail(
                        start=ls.start,
                        end=ls.end,
                        text=ls.text,
                        confidence=ls.confidence,
                        category="contradiction",
                        source="lettucedetect_token",
                        explanation="Token-level mismatch flagged as contradictory by LettuceDetect ModernBERT.",
                    )
                    contradicted_claims.append(claim)
                else:
                    claim = ClaimDetail(
                        start=ls.start,
                        end=ls.end,
                        text=ls.text,
                        confidence=ls.confidence,
                        category="unsupported",
                        source="lettucedetect_token",
                        explanation="Token-level span not grounded or substantiated by reference context.",
                    )
                    unsupported_claims.append(claim)

                unified_spans.append(ls)

        # Collect Supported Claims (segments where NLI predicts entailment and no overlap with flagged spans)
        all_flagged_intervals = [(s.start, s.end) for s in unified_spans]
        for seg in nli_res.get("all_segments", []):
            if seg["label"] == "entailment" and seg["prob_entailment"] >= 0.70:
                s_start, s_end = seg["start"], seg["end"]
                overlaps = any(
                    max(0, min(s_end, f_end) - max(s_start, f_start)) > 0
                    for f_start, f_end in all_flagged_intervals
                )
                if not overlaps and seg["segment_type"] in ("clause", "sentence", "proposition"):
                    supported_claims.append(
                        ClaimDetail(
                            start=s_start,
                            end=s_end,
                            text=seg["text"],
                            confidence=seg["prob_entailment"],
                            category="supported",
                            source="nli_cross_encoder",
                            explanation="Verified as substantiated by reference context.",
                        )
                    )

        # Deduplicate unified spans
        unified_spans = self._deduplicate_spans(unified_spans)

        # -------------------------------------------------------------
        # 4. Overall Verdict Determination
        # -------------------------------------------------------------
        if contradicted_claims and unsupported_claims:
            verdict = "CONTRADICTED"
            fusion_source = "hybrid_mixed_flagged"
            message = (
                f"Identified {len(contradicted_claims)} contradictory claim(s) "
                f"and {len(unsupported_claims)} unsupported claim(s) against reference context."
            )
            is_hallucinated = True
        elif contradicted_claims:
            verdict = "CONTRADICTED"
            fusion_source = "nli_salvaged" if not lettuce_has_spans else "hybrid_contradiction"
            message = f"Found {len(contradicted_claims)} claim(s) directly conflicting with reference context."
            is_hallucinated = True
        elif unsupported_claims:
            verdict = "UNSUPPORTED"
            fusion_source = "lettucedetect_primary"
            message = f"Detected {len(unsupported_claims)} claim(s) not substantiated by reference context."
            is_hallucinated = True
        else:
            verdict = "SUPPORTED"
            fusion_source = "unanimous_supported"
            message = "All claims in the answer are grounded and consistent with the provided reference context."
            is_hallucinated = False

        max_conf: Optional[float] = None
        if unified_spans:
            conf_vals = [s.confidence for s in unified_spans if s.confidence is not None]
            if conf_vals:
                max_conf = max(conf_vals)

        summary = VerificationSummary(
            is_hallucinated=is_hallucinated,
            span_count=len(unified_spans),
            max_confidence=max_conf,
            verdict=verdict,
            message=message,
        )

        detector_breakdown = DetectorBreakdown(
            lettucedetect_spans=len(lettuce_spans_raw),
            lettucedetect_verdict=lettuce_summary.verdict,
            nli_contradictions=len(nli_contra_spans),
            nli_max_contradiction=nli_res["max_contradiction_score"],
            fusion_verdict=verdict,
            fusion_source=fusion_source,
            lettucedetect_latency_ms=lettuce_latency_ms,
            nli_latency_ms=nli_latency_ms,
        )

        total_exec_time = round((time.perf_counter() - t_total_start) * 1000, 2)

        return (
            unified_spans,
            summary,
            contradicted_claims,
            unsupported_claims,
            supported_claims,
            detector_breakdown,
            total_exec_time,
        )

    def _deduplicate_spans(self, spans: List[HallucinationSpan]) -> List[HallucinationSpan]:
        """Removes duplicate or redundant spans, keeping higher-confidence or more specific spans."""
        if not spans:
            return []
        sorted_spans = sorted(spans, key=lambda s: s.start)
        unique: List[HallucinationSpan] = []
        for s in sorted_spans:
            is_dup = False
            for u in unique:
                if u.start == s.start and u.end == s.end:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(s)
        return unique


# Global singleton instance for production application use
hybrid_detector_service = HybridDetectorService()

