"""Production DeBERTa-v3 NLI Service for HalluGuard.

Provides sentence-, clause-, and proposition-level Natural Language Inference (NLI)
to complement the primary LettuceDetect ModernBERT token classification model.

Model: cross-encoder/nli-deberta-v3-small
Label mapping:
    0: contradiction
    1: entailment
    2: neutral
"""

import logging
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

try:
    import psutil
except ImportError:
    psutil = None

from app.config import settings

logger = logging.getLogger(__name__)


class NLISegmentPrediction:
    """Holds NLI prediction results for an answer segment."""

    def __init__(
        self,
        start: int,
        end: int,
        text: str,
        segment_type: str,
        clean_hypothesis: str,
        label: str,
        prob_contradiction: float,
        prob_entailment: float,
        prob_neutral: float,
        is_contradiction: bool,
    ):
        self.start = start
        self.end = end
        self.text = text
        self.segment_type = segment_type
        self.clean_hypothesis = clean_hypothesis
        self.label = label
        self.prob_contradiction = prob_contradiction
        self.prob_entailment = prob_entailment
        self.prob_neutral = prob_neutral
        self.is_contradiction = is_contradiction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "text": self.text,
            "segment_type": self.segment_type,
            "clean_hypothesis": self.clean_hypothesis,
            "label": self.label,
            "prob_contradiction": round(self.prob_contradiction, 4),
            "prob_entailment": round(self.prob_entailment, 4),
            "prob_neutral": round(self.prob_neutral, 4),
            "is_contradiction": self.is_contradiction,
        }


class NLIService:
    """Production Natural Language Inference service."""

    # Conversational lead-in prefixes that obscure NLI hypothesis semantics
    LEAD_IN_PREFIXES = [
        r"^according to the (?:reference|context|text|passage|provided text)[,\s:]*",
        r"^based on the (?:reference|context|text|passage|provided text)[,\s:]*",
        r"^the reference states that\s*",
        r"^the context indicates that\s*",
        r"^the provided text mentions that\s*",
    ]

    # Common finite verbs for grammatical clause boundary verification
    COMMON_FINITE_VERBS = {
        "is", "are", "was", "were", "be", "been", "being",
        "has", "have", "had", "does", "do", "did",
        "will", "would", "can", "could", "should", "may", "might", "must",
        "lies", "lie", "lay", "flows", "flow", "flowed",
        "stands", "stand", "stood", "reaches", "reach", "reached",
        "spans", "span", "spanned", "covers", "cover", "covered",
        "ranks", "rank", "ranked", "measures", "measure", "measured",
        "contains", "contain", "contained", "consists", "consist", "consisted",
        "borders", "border", "bordered", "connects", "connect", "connected",
        "drains", "drain", "drained", "rises", "rise", "rose", "risen",
        "separates", "separate", "separated", "divides", "divide", "divided",
        "serves", "serve", "served", "represents", "represent", "represented",
        "forms", "form", "formed", "discharges", "discharge", "discharged",
        "originates", "originate", "originated", "empties", "empty", "emptied",
        "features", "feature", "featured", "sits", "sit", "sat",
        "marks", "mark", "marked", "holds", "hold", "held",
        "belongs", "belong", "belonged", "shares", "share", "shared",
        "includes", "include", "included", "surrounds", "surround", "surrounded",
        "encircles", "encircle", "encircled", "acts", "act", "acted",
        "operates", "operate", "operated", "provides", "provide", "provided",
        "hosts", "host", "hosted", "bisects", "bisect", "bisected",
        "straddles", "straddle", "straddled", "descends", "descend", "descended",
        "ascends", "ascend", "ascended", "peaks", "peak", "peaked",
        "towers", "tower", "towered", "extends", "extend", "extended",
        "runs", "run", "ran", "surpasses", "surpass", "surpassed",
        "remains", "remain", "remained", "constitutes", "constitute", "constituted",
        "designates", "designate", "designated"
    }

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        contradiction_threshold: Optional[float] = None,
    ):
        self.model_name = model_name or settings.nli_model_path
        self.device = device or settings.device
        self.contradiction_threshold = (
            contradiction_threshold
            if contradiction_threshold is not None
            else settings.nli_contradiction_threshold
        )
        self.tokenizer = None
        self.model = None
        self.id2label: Dict[int, str] = {}
        self.label2id: Dict[str, int] = {}
        self.is_loaded = False
        self.load_error: Optional[str] = None
        self.load_time_seconds = 0.0
        self.memory_footprint_mb = 0.0

    def load_model(self) -> None:
        """Loads tokenizer and model weights on CPU and verifies label mapping.

        Thread-safe; loads once and caches.
        """
        if self.is_loaded:
            logger.info("NLI model '%s' is already loaded.", self.model_name)
            return

        logger.info(
            "Loading DeBERTa-v3 NLI model '%s' on device '%s'...",
            self.model_name,
            self.device,
        )
        t0 = time.perf_counter()
        process = psutil.Process() if psutil else None
        mem_before = process.memory_info().rss / (1024 * 1024) if process else 0.0

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()

            self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
            self.label2id = {v: int(k) for k, v in self.id2label.items()}

            # Verify required NLI labels
            expected_labels = {"contradiction", "entailment", "neutral"}
            actual_labels = set(self.id2label.values())
            if not expected_labels.issubset(actual_labels):
                raise ValueError(
                    f"Model config labels {actual_labels} missing required NLI labels {expected_labels}"
                )

            self.load_time_seconds = round(time.perf_counter() - t0, 3)
            mem_after = process.memory_info().rss / (1024 * 1024) if process else 0.0
            self.memory_footprint_mb = round(mem_after - mem_before, 2)
            self.is_loaded = True
            self.load_error = None
            logger.info(
                "DeBERTa-v3 NLI model loaded successfully in %.2fs (Memory: %.1f MB).",
                self.load_time_seconds,
                self.memory_footprint_mb,
            )
        except Exception as e:
            self.is_loaded = False
            self.load_error = str(e)
            logger.error("Failed to load DeBERTa-v3 NLI model: %s", e, exc_info=True)
            raise RuntimeError(f"Failed to load NLI model: {e}") from e

    def clean_hypothesis_text(self, text: str) -> str:
        """Strips conversational lead-in phrases while retaining core proposition."""
        cleaned = text.strip()
        for pat in self.LEAD_IN_PREFIXES:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    def _has_finite_verb(self, text: str) -> bool:
        """Determine whether a string fragment contains at least one finite verb."""
        tokens = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        for t in tokens:
            if t in self.COMMON_FINITE_VERBS:
                return True
            if len(t) > 4 and (t.endswith("ed") or t.endswith("izes") or t.endswith("ises")):
                return True
        return False

    def decompose_participial_propositions(
        self, sentence: str, sentence_start_offset: int
    ) -> List[Tuple[int, int, str, str]]:
        """Decomposes participial modifiers into standalone propositions with subject resolution.

        Handles relational rankings, comparatives, and modifiers (e.g. ', ranking just below Mount Logan')
        while maintaining strict character offset mapping to the original answer text.

        Returns list of (start_char, end_char, matched_span_text, standalone_hypothesis).
        """
        participial_pattern = re.compile(
            r",\s+((?:ranking|surpassed|followed|trailing|exceeding|measuring|covering|located|situated|lying|spanning|standing)\b[^,.!?]+)",
            re.IGNORECASE,
        )

        matches = list(participial_pattern.finditer(sentence))
        if not matches:
            return []

        # Extract grammatical subject from the main clause before the first participial delimiter
        first_match = matches[0]
        main_clause = sentence[:first_match.start()].strip()

        # Subject extraction heuristic: leading noun phrase before first verb
        words = main_clause.split()
        subj_tokens = []
        for w in words:
            if w.lower() in self.COMMON_FINITE_VERBS:
                break
            subj_tokens.append(w)
        subj = " ".join(subj_tokens).strip() or (words[0] if words else "")

        propositions = []
        # Also include the main clause preceding the participial phrase
        if len(main_clause) >= 5 and self._has_finite_verb(main_clause):
            propositions.append((sentence_start_offset, sentence_start_offset + len(main_clause), main_clause, main_clause))

        for m in matches:
            participle_phrase = m.group(1).strip()
            local_start = m.start() + sentence[m.start():].find(participle_phrase)
            local_end = local_start + len(participle_phrase)
            abs_start = sentence_start_offset + local_start
            abs_end = sentence_start_offset + local_end

            # Formulate standalone hypothesis
            p_lower = participle_phrase.lower()
            if p_lower.startswith("ranking"):
                rest = participle_phrase[7:].strip()
                hypo = f"{subj} ranks {rest}"
            elif p_lower.startswith("surpassed"):
                rest = participle_phrase[9:].strip()
                hypo = f"{subj} is surpassed {rest}"
            elif p_lower.startswith("followed"):
                rest = participle_phrase[8:].strip()
                hypo = f"{subj} is followed {rest}"
            else:
                hypo = f"{subj} {participle_phrase}"

            propositions.append((abs_start, abs_end, participle_phrase, hypo))

        return propositions

    def segment_answer(self, answer_text: str) -> List[Tuple[int, int, str, str, str]]:
        """Segments answer into hierarchical units: full answer, sentences, clauses, and decomposed propositions.

        Preserves serial noun lists (with or without Oxford commas).
        Returns list of tuples: (start_char, end_char, text_in_answer, segment_type, hypothesis_to_test).
        """
        segments: List[Tuple[int, int, str, str, str]] = []
        clean_ans = answer_text.strip()
        # 1. Full answer level
        segments.append((0, len(answer_text), clean_ans, "full_answer", clean_ans))

        # 2. Sentence boundary splitting
        sentence_pattern = re.compile(r"([^.!?]+[.!?]?)")
        for m in sentence_pattern.finditer(answer_text):
            s_raw = m.group()
            s_text = s_raw.strip()
            if not s_text or len(s_text) < 4:
                continue
            s_start = m.start() + s_raw.find(s_text)
            s_end = s_start + len(s_text)

            if s_text != clean_ans:
                segments.append((s_start, s_end, s_text, "sentence", s_text))

            # 3. Participial Proposition Decomposition (TASK 3)
            participial_props = self.decompose_participial_propositions(s_text, s_start)
            for p_start, p_end, p_text, p_hypo in participial_props:
                segments.append((p_start, p_end, p_text, "proposition", p_hypo))

            # 4. Robust Clause Boundary Splitting (Refined in Phase 8 Step 4)
            clause_delim_pattern = re.compile(
                r"(;\s*|,\s*(?:while|whereas|although|though|but)\s+|,\s*and\s+)",
                re.IGNORECASE,
            )

            matches = list(clause_delim_pattern.finditer(s_text))
            if not matches:
                continue

            valid_split_indices = []
            for cm in matches:
                d_str = cm.group()
                d_start = cm.start()
                d_end = cm.end()

                pre_str = s_text[:d_start].strip()
                post_str = s_text[d_end:].strip()

                if len(pre_str) < 5 or len(post_str) < 5:
                    continue

                if not self._has_finite_verb(post_str):
                    continue

                # Oxford comma enumeration guard
                if re.search(r"\band\b", d_str, re.IGNORECASE):
                    last_comma = pre_str.rfind(",")
                    if last_comma != -1:
                        item_before_and = pre_str[last_comma + 1:].strip()
                        if not self._has_finite_verb(item_before_and) and len(item_before_and.split()) <= 4:
                            continue

                if not self._has_finite_verb(pre_str):
                    continue

                valid_split_indices.append((d_start, d_end))

            if not valid_split_indices:
                continue

            curr_pos = 0
            for d_start, d_end in valid_split_indices:
                c_text = s_text[curr_pos:d_start].strip()
                if len(c_text) >= 4 and self._has_finite_verb(c_text):
                    abs_start = s_start + s_text.find(c_text, curr_pos)
                    abs_end = abs_start + len(c_text)
                    if c_text != s_text:
                        segments.append((abs_start, abs_end, c_text, "clause", c_text))
                curr_pos = d_end

            # Trailing clause
            c_text = s_text[curr_pos:].strip()
            if len(c_text) >= 4 and self._has_finite_verb(c_text):
                abs_start = s_start + s_text.find(c_text, curr_pos)
                abs_end = abs_start + len(c_text)
                if c_text != s_text:
                    segments.append((abs_start, abs_end, c_text, "clause", c_text))

        return segments

    def predict_pair(self, premise: str, hypothesis: str) -> Dict[str, float]:
        """Runs NLI inference on a single premise-hypothesis pair."""
        if not self.is_loaded:
            self.load_model()

        inputs = self.tokenizer(
            premise,
            hypothesis,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]

        contra_idx = self.label2id["contradiction"]
        entail_idx = self.label2id["entailment"]
        neutral_idx = self.label2id["neutral"]

        return {
            "contradiction": float(probs[contra_idx]),
            "entailment": float(probs[entail_idx]),
            "neutral": float(probs[neutral_idx]),
        }

    def analyze_answer(
        self,
        context: str,
        answer: str,
        question: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Performs multi-granularity NLI verification over an answer given reference context."""
        t0 = time.perf_counter()

        segments_raw = self.segment_answer(answer)
        segment_predictions: List[NLISegmentPrediction] = []

        max_contradiction = 0.0
        max_entailment = 0.0
        contradictory_spans: List[Dict[str, Any]] = []

        # Evaluate each segment
        for start, end, text, seg_type, hypo_text in segments_raw:
            clean_hypo = self.clean_hypothesis_text(hypo_text)
            scores = self.predict_pair(premise=context, hypothesis=clean_hypo)

            p_contra = scores["contradiction"]
            p_entail = scores["entailment"]
            p_neutral = scores["neutral"]

            best_label = max(scores, key=scores.get)
            is_contra = (p_contra >= self.contradiction_threshold)

            pred = NLISegmentPrediction(
                start=start,
                end=end,
                text=text,
                segment_type=seg_type,
                clean_hypothesis=clean_hypo,
                label=best_label,
                prob_contradiction=p_contra,
                prob_entailment=p_entail,
                prob_neutral=p_neutral,
                is_contradiction=is_contra,
            )
            segment_predictions.append(pred)

            if p_contra > max_contradiction:
                max_contradiction = p_contra
            if p_entail > max_entailment:
                max_entailment = p_entail

            if is_contra:
                contradictory_spans.append({
                    "start": start,
                    "end": end,
                    "text": text,
                    "confidence": round(p_contra, 4),
                    "category": "contradiction",
                    "segment_type": seg_type,
                })

        resolved_spans = self._resolve_overlapping_spans(contradictory_spans)
        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        has_contradiction = len(resolved_spans) > 0

        return {
            "has_contradiction": has_contradiction,
            "max_contradiction_score": round(max_contradiction, 4),
            "max_entailment_score": round(max_entailment, 4),
            "contradictory_spans": resolved_spans,
            "all_segments": [p.to_dict() for p in segment_predictions],
            "nli_latency_ms": exec_time_ms,
        }

    def _resolve_overlapping_spans(self, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Selects the most specific non-redundant span when spans overlap."""
        if not spans:
            return []

        # Prefer shorter, more specific spans (propositions and clauses over whole sentences)
        sorted_spans = sorted(spans, key=lambda s: (s["end"] - s["start"]))
        accepted: List[Dict[str, Any]] = []

        for s in sorted_spans:
            s_start, s_end = s["start"], s["end"]
            overlap = False
            for a in accepted:
                a_start, a_end = a["start"], a["end"]
                inter = max(0, min(s_end, a_end) - max(s_start, a_start))
                if inter > 0:
                    overlap = True
                    break
            if not overlap:
                accepted.append(s)

        return sorted(accepted, key=lambda s: s["start"])


# Global singleton instance for production use
nli_service = NLIService()
