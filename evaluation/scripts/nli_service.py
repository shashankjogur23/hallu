"""Experimental DeBERTa-v3 NLI Service for HalluGuard.

Provides sentence- and clause-level Natural Language Inference (NLI) to complement
the production LettuceDetect ModernBERT token classification model.

Target Model: cross-encoder/nli-deberta-v3-small
Model Card & Weights: Cached locally in Hugging Face hub cache.
Label Mapping Verified from config.json:
    0: contradiction
    1: entailment
    2: neutral
"""

import os
import re
import sys
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Offline mode enforcement
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

try:
    import psutil
except ImportError:
    psutil = None


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
    """Experimental Natural Language Inference service."""

    DEFAULT_MODEL = "cross-encoder/nli-deberta-v3-small"

    # Known conversational prefixes that obscure NLI hypothesis semantics
    LEAD_IN_PREFIXES = [
        r"^according to the (?:reference|context|text|passage|provided text)[,\s:]*",
        r"^based on the (?:reference|context|text|passage|provided text)[,\s:]*",
        r"^the reference states that\s*",
        r"^the context indicates that\s*",
        r"^the provided text mentions that\s*",
    ]

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str = "cpu",
        contradiction_threshold: float = 0.60,
    ):
        self.model_name = model_name
        self.device = device
        self.contradiction_threshold = contradiction_threshold
        self.tokenizer = None
        self.model = None
        self.id2label: Dict[int, str] = {}
        self.label2id: Dict[str, int] = {}
        self.is_loaded = False
        self.load_time_seconds = 0.0
        self.memory_footprint_mb = 0.0

    def load_model(self):
        """Loads tokenizer and model weights on CPU and verifies label mapping."""
        if self.is_loaded:
            return

        t0 = time.perf_counter()
        process = psutil.Process() if psutil else None
        mem_before = process.memory_info().rss / (1024 * 1024) if process else 0.0

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.to(self.device)
        self.model.eval()

        self.id2label = {int(k): v for k, v in self.model.config.id2label.items()}
        self.label2id = {v: int(k) for k, v in self.id2label.items()}

        # Verify required label names
        expected_labels = {"contradiction", "entailment", "neutral"}
        actual_labels = set(self.id2label.values())
        if not expected_labels.issubset(actual_labels):
            raise ValueError(
                f"Model config labels {actual_labels} do not match expected NLI labels {expected_labels}"
            )

        self.load_time_seconds = round(time.perf_counter() - t0, 3)
        mem_after = process.memory_info().rss / (1024 * 1024) if process else 0.0
        self.memory_footprint_mb = round(mem_after - mem_before, 2)
        self.is_loaded = True

    def clean_hypothesis_text(self, text: str) -> str:
        """Strips conversational lead-in phrases while retaining core proposition."""
        cleaned = text.strip()
        for pat in self.LEAD_IN_PREFIXES:
            cleaned = re.sub(pat, "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned

    def _has_finite_verb(self, text: str) -> bool:
        """Determine whether a string fragment contains at least one likely finite verb."""
        common_verbs = {
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
        tokens = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        for t in tokens:
            if t in common_verbs:
                return True
            # Regular verbs ending in -ed, -izes, -ises with minimum root length
            if len(t) > 4 and (t.endswith("ed") or t.endswith("izes") or t.endswith("ises")):
                return True
        return False

    def segment_answer(self, answer_text: str) -> List[Tuple[int, int, str, str]]:
        """Segments answer into sentences and independent clauses with start/end offsets.

        Preserves coordinated noun lists (with or without Oxford commas) and avoids
        fragmenting lists into incomplete propositions.

        Returns list of (start_char, end_char, text, segment_type).
        """
        segments = []
        # 1. Full answer level
        clean_ans = answer_text.strip()
        segments.append((0, len(answer_text), clean_ans, "full_answer"))

        # 2. Sentence boundary splitting
        sentence_pattern = re.compile(r'([^.!?]+[.!?]?)')
        for m in sentence_pattern.finditer(answer_text):
            s_raw = m.group()
            s_text = s_raw.strip()
            if not s_text or len(s_text) < 4:
                continue
            start = m.start() + s_raw.find(s_text)
            end = start + len(s_text)

            # Avoid duplicating full answer if answer is a single sentence
            if s_text != clean_ans:
                segments.append((start, end, s_text, "sentence"))

            # 3. Robust Clause Boundary Splitting
            # Candidate delimiters:
            # - Semicolons: ';'
            # - Subordinating/contrasting conjunctions: ', while ', ', whereas ', ', although ', ', though ', ', but '
            # - Coordinating conjunction: ', and ' (conditional on being a genuine clause boundary, not an Oxford comma list)
            clause_delim_pattern = re.compile(
                r'(;\s*|,\s*(?:while|whereas|although|though|but)\s+|,\s*and\s+)',
                re.IGNORECASE
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

                # Must have non-trivial text on both sides
                if len(pre_str) < 5 or len(post_str) < 5:
                    continue

                # What follows MUST have a finite verb to constitute a clause
                if not self._has_finite_verb(post_str):
                    # E.g. ', and Brunei.' -> 'Brunei.' has no verb, so this is a list item, NOT a clause
                    continue

                # If the delimiter is ', and ':
                if re.search(r'\band\b', d_str, re.IGNORECASE):
                    # Check for Oxford comma enumeration:
                    # E.g., '... shared among Indonesia, Malaysia'
                    # If pre_str ends with an enumeration (a comma followed by a noun phrase with no verb)
                    last_comma = pre_str.rfind(',')
                    if last_comma != -1:
                        item_before_and = pre_str[last_comma + 1:].strip()
                        # If item_before_and is a short phrase without a verb (e.g. 'Malaysia')
                        if not self._has_finite_verb(item_before_and) and len(item_before_and.split()) <= 4:
                            # This is an Oxford comma in a list: 'Item1, Item2, and Item3'
                            continue

                # What precedes must also contain a finite verb
                if not self._has_finite_verb(pre_str):
                    continue

                valid_split_indices.append((d_start, d_end))

            if not valid_split_indices:
                continue

            curr_pos = 0
            for d_start, d_end in valid_split_indices:
                c_text = s_text[curr_pos:d_start].strip()
                if len(c_text) >= 4 and self._has_finite_verb(c_text):
                    abs_start = start + s_text.find(c_text, curr_pos)
                    abs_end = abs_start + len(c_text)
                    if c_text != s_text:
                        segments.append((abs_start, abs_end, c_text, "clause"))
                curr_pos = d_end

            # Trailing clause
            c_text = s_text[curr_pos:].strip()
            if len(c_text) >= 4 and self._has_finite_verb(c_text):
                abs_start = start + s_text.find(c_text, curr_pos)
                abs_end = abs_start + len(c_text)
                if c_text != s_text:
                    segments.append((abs_start, abs_end, c_text, "clause"))

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
        """Performs multi-granularity NLI analysis over an answer given reference context."""
        t0 = time.perf_counter()

        segments_raw = self.segment_answer(answer)
        segment_predictions: List[NLISegmentPrediction] = []

        max_contradiction = 0.0
        contradictory_spans: List[Dict[str, Any]] = []

        # Evaluate each segment
        for start, end, text, seg_type in segments_raw:
            clean_hypo = self.clean_hypothesis_text(text)
            scores = self.predict_pair(premise=context, hypothesis=clean_hypo)

            p_contra = scores["contradiction"]
            p_entail = scores["entailment"]
            p_neutral = scores["neutral"]

            # Determine dominant label
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

            # If contradiction flagged, collect span (prefer finer-grained clause/sentence over full answer if available)
            if is_contra:
                contradictory_spans.append({
                    "start": start,
                    "end": end,
                    "text": text,
                    "confidence": round(p_contra, 4),
                    "category": "contradiction",
                    "segment_type": seg_type,
                })

        # Span deduplication / resolution:
        # If both a sentence and a sub-clause inside it are flagged as contradiction, prefer the more specific sub-clause
        resolved_spans = self._resolve_overlapping_spans(contradictory_spans)

        exec_time_ms = round((time.perf_counter() - t0) * 1000, 2)

        has_contradiction = len(resolved_spans) > 0

        return {
            "has_contradiction": has_contradiction,
            "max_contradiction_score": round(max_contradiction, 4),
            "contradictory_spans": resolved_spans,
            "all_segments": [p.to_dict() for p in segment_predictions],
            "nli_latency_ms": exec_time_ms,
        }

    def _resolve_overlapping_spans(self, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Selects the most specific non-redundant span when spans overlap."""
        if not spans:
            return []

        # Sort by length ascending (prefer shorter, more precise spans)
        sorted_spans = sorted(spans, key=lambda s: (s["end"] - s["start"]))
        accepted: List[Dict[str, Any]] = []

        for s in sorted_spans:
            s_start, s_end = s["start"], s["end"]
            # Check if this span is already subsumed or subsumes an accepted span
            overlap = False
            for a in accepted:
                a_start, a_end = a["start"], a["end"]
                # If they overlap significantly
                inter = max(0, min(s_end, a_end) - max(s_start, a_start))
                if inter > 0:
                    overlap = True
                    break
            if not overlap:
                accepted.append(s)

        # Sort accepted spans by start offset for readability
        return sorted(accepted, key=lambda s: s["start"])


# Global singleton for experiment runner
nli_service = NLIService()
