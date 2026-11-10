"""Experimental DeBERTa-v3 NLI Hybrid Evaluation Runner for HalluGuard.

Evaluates an experimental hybrid system combining:
1. LettuceDetect ModernBERT token classification model (fine-grained span detection)
2. DeBERTa-v3 NLI model (cross-encoder/nli-deberta-v3-small) (relational & entity contradiction verifier)

Evaluates all 60 geography benchmark examples.
Preserves production code, baseline results, and production thresholds.
"""

import os
import sys
import time
import json
import csv
import math
from pathlib import Path

# Offline mode enforcement
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

EVAL_DIR = ROOT_DIR / "evaluation"
SCRIPTS_DIR = EVAL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DATASET_CSV = EVAL_DIR / "dataset" / "geography_evaluation_dataset.csv"
RESULTS_DIR = EVAL_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from app.services.detector_service import detector_service
from app.config import settings
from nli_service import nli_service


def calculate_iou(s1, e1, s2, e2):
    """Calculate Intersection over Union (IoU) of two 1D spans."""
    intersection = max(0, min(e1, e2) - max(s1, s2))
    union = (e1 - s1) + (e2 - s2) - intersection
    if union == 0:
        return 0.0
    return intersection / union


def match_spans(expected_spans, predicted_spans, iou_threshold=0.5):
    """Perform one-to-one greedy matching between expected and predicted spans."""
    if not expected_spans or not predicted_spans:
        return 0, 0

    matched_gold_exact = set()
    matched_pred_exact = set()
    exact_count = 0

    for p_idx, p in enumerate(predicted_spans):
        for g_idx, g in enumerate(expected_spans):
            if g_idx in matched_gold_exact or p_idx in matched_pred_exact:
                continue
            if p["start"] == g["start"] and p["end"] == g["end"]:
                exact_count += 1
                matched_gold_exact.add(g_idx)
                matched_pred_exact.add(p_idx)
                break

    partial_count = exact_count
    matched_gold_partial = set(matched_gold_exact)
    matched_pred_partial = set(matched_pred_exact)

    for p_idx, p in enumerate(predicted_spans):
        if p_idx in matched_pred_partial:
            continue
        best_iou = 0.0
        best_g_idx = -1
        for g_idx, g in enumerate(expected_spans):
            if g_idx in matched_gold_partial:
                continue
            iou = calculate_iou(p["start"], p["end"], g["start"], g["end"])
            if iou >= iou_threshold and iou > best_iou:
                best_iou = iou
                best_g_idx = g_idx

        if best_g_idx != -1:
            partial_count += 1
            matched_gold_partial.add(best_g_idx)
            matched_pred_partial.add(p_idx)

    return exact_count, partial_count


def calculate_char_overlap(expected_spans, predicted_spans, answer_len):
    """Compute character-level precision, recall, and F1."""
    gold_chars = set()
    for g in expected_spans:
        gold_chars.update(range(g["start"], g["end"]))

    pred_chars = set()
    for p in predicted_spans:
        pred_chars.update(range(p["start"], p["end"]))

    intersection = len(gold_chars.intersection(pred_chars))
    p_len = len(pred_chars)
    g_len = len(gold_chars)

    if p_len == 0 and g_len == 0:
        return 1.0, 1.0, 1.0, 0, 0, 0
    elif p_len == 0:
        return 1.0, 0.0, 0.0, 0, 0, g_len
    elif g_len == 0:
        return 0.0, 1.0, 0.0, 0, p_len, 0

    prec = intersection / p_len
    rec = intersection / g_len
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    return prec, rec, f1, intersection, p_len, g_len


# SVG Chart Generators
def generate_svg_confusion_matrix(tp, fp, fn, tn, out_path, title="NLI Hybrid Confusion Matrix"):
    """Generate SVG visualization of the 2x2 confusion matrix."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 380" width="540" height="380" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <style>
    .title {{ font-size: 16px; font-weight: 700; fill: #1e293b; text-anchor: middle; }}
    .subtitle {{ font-size: 12px; fill: #64748b; text-anchor: middle; }}
    .axis-label {{ font-size: 13px; font-weight: 600; fill: #334155; text-anchor: middle; }}
    .cell-title {{ font-size: 12px; font-weight: 600; text-anchor: middle; }}
    .cell-val {{ font-size: 32px; font-weight: 800; text-anchor: middle; }}
    .cell-sub {{ font-size: 11px; text-anchor: middle; fill: #64748b; }}
  </style>

  <text x="270" y="32" class="title">{title}</text>
  <text x="270" y="52" class="subtitle">LettuceDetect ModernBERT + DeBERTa-v3-small NLI (N = 60)</text>

  <text x="270" y="90" class="axis-label">PREDICTED CLASS</text>
  <text x="180" y="112" class="axis-label" style="fill:#dc2626;">HALLUCINATED</text>
  <text x="360" y="112" class="axis-label" style="fill:#16a34a;">CLEAN</text>

  <text x="45" y="180" class="axis-label" transform="rotate(-90 45,180)">ACTUAL CLASS</text>
  <text x="80" y="180" class="axis-label" style="fill:#dc2626; text-anchor:end;">HALLUCINATED</text>
  <text x="80" y="280" class="axis-label" style="fill:#16a34a; text-anchor:end;">CLEAN</text>

  <!-- Cell 1: TP -->
  <rect x="100" y="125" width="160" height="100" rx="8" fill="#fef2f2" stroke="#fca5a5" stroke-width="2"/>
  <text x="180" y="150" class="cell-title" fill="#991b1b">TRUE POSITIVE (TP)</text>
  <text x="180" y="195" class="cell-val" fill="#b91c1c">{tp}</text>
  <text x="180" y="215" class="cell-sub">Hallucinated correctly flagged</text>

  <!-- Cell 2: FN -->
  <rect x="280" y="125" width="160" height="100" rx="8" fill="#fff7ed" stroke="#fdba74" stroke-width="2"/>
  <text x="360" y="150" class="cell-title" fill="#c2410c">FALSE NEGATIVE (FN)</text>
  <text x="360" y="195" class="cell-val" fill="#ea580c">{fn}</text>
  <text x="360" y="215" class="cell-sub">Hallucination missed (Type II)</text>

  <!-- Cell 3: FP -->
  <rect x="100" y="235" width="160" height="100" rx="8" fill="#fefce8" stroke="#fde047" stroke-width="2"/>
  <text x="180" y="260" class="cell-title" fill="#a16207">FALSE POSITIVE (FP)</text>
  <text x="180" y="305" class="cell-val" fill="#ca8a04">{fp}</text>
  <text x="180" y="325" class="cell-sub">Clean answer falsely flagged (Type I)</text>

  <!-- Cell 4: TN -->
  <rect x="280" y="235" width="160" height="100" rx="8" fill="#f0fdf4" stroke="#86efac" stroke-width="2"/>
  <text x="360" y="260" class="cell-title" fill="#15803d">TRUE NEGATIVE (TN)</text>
  <text x="360" y="305" class="cell-val" fill="#16a34a">{tn}</text>
  <text x="360" y="325" class="cell-sub">Clean answer verified</text>

  <text x="270" y="360" class="subtitle">Total Actual Hallucinated: {tp + fn} | Total Actual Clean: {fp + tn}</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_svg_comparison_chart(baseline_metrics, hybrid_metrics, out_path):
    """Generate SVG bar chart comparing Baseline ModernBERT vs NLI Hybrid."""
    metrics = [
        ("Accuracy", baseline_metrics["accuracy"] * 100, hybrid_metrics["accuracy"] * 100),
        ("Precision", baseline_metrics["precision"] * 100, hybrid_metrics["precision"] * 100),
        ("Recall", baseline_metrics["recall"] * 100, hybrid_metrics["recall"] * 100),
        ("Specificity", baseline_metrics["specificity"] * 100, hybrid_metrics["specificity"] * 100),
        ("F1-Score", baseline_metrics["f1_score"] * 100, hybrid_metrics["f1_score"] * 100),
    ]

    bars_svg = ""
    start_y = 90
    group_gap = 48
    bar_h = 16
    max_w = 300

    for i, (m_name, b_val, h_val) in enumerate(metrics):
        y = start_y + (i * group_gap)
        b_w = int((b_val / 100.0) * max_w)
        h_w = int((h_val / 100.0) * max_w)

        bars_svg += f"""
    <!-- {m_name} -->
    <text x="110" y="{y + 20}" font-size="12" font-weight="600" fill="#334155" text-anchor="end">{m_name}</text>
    
    <!-- Baseline bar -->
    <rect x="120" y="{y}" width="{b_w}" height="{bar_h}" rx="3" fill="#94a3b8"/>
    <text x="{120 + b_w + 6}" y="{y + 12}" font-size="11" font-weight="600" fill="#64748b">{b_val:.1f}%</text>
    
    <!-- Hybrid bar -->
    <rect x="120" y="{y + bar_h + 3}" width="{h_w}" height="{bar_h}" rx="3" fill="#2563eb"/>
    <text x="{120 + h_w + 6}" y="{y + bar_h + 15}" font-size="11" font-weight="700" fill="#1e40af">{h_val:.1f}%</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 370" width="540" height="370" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="270" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">Baseline ModernBERT vs NLI Hybrid Performance</text>
  <text x="270" y="52" font-size="12" fill="#64748b" text-anchor="middle">Answer-Level Benchmark Comparison (N = 60)</text>

  <!-- Legend -->
  <rect x="180" y="65" width="14" height="14" rx="2" fill="#94a3b8"/>
  <text x="200" y="77" font-size="11" fill="#475569">Baseline ModernBERT</text>
  <rect x="320" y="65" width="14" height="14" rx="2" fill="#2563eb"/>
  <text x="340" y="77" font-size="11" font-weight="600" fill="#1e40af">NLI Hybrid (Ours)</text>

  {bars_svg}
  <line x1="120" y1="{start_y + 5 * group_gap}" x2="420" y2="{start_y + 5 * group_gap}" stroke="#cbd5e1" stroke-width="1"/>
  <text x="120" y="{start_y + 5 * group_gap + 16}" font-size="10" fill="#94a3b8" text-anchor="middle">0%</text>
  <text x="270" y="{start_y + 5 * group_gap + 16}" font-size="10" fill="#94a3b8" text-anchor="middle">50%</text>
  <text x="420" y="{start_y + 5 * group_gap + 16}" font-size="10" fill="#94a3b8" text-anchor="middle">100%</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_svg_category_accuracy(cat_stats_b, cat_stats_h, out_path):
    """Generate SVG bar chart for category-wise accuracy comparison."""
    categories = ["supported", "contradictory", "unsupported", "mixed"]
    bars_svg = ""
    start_y = 90
    group_gap = 52
    bar_h = 16
    max_w = 280

    for i, cat in enumerate(categories):
        y = start_y + (i * group_gap)
        b_acc = cat_stats_b[cat]["accuracy_percent"]
        h_acc = cat_stats_h[cat]["accuracy_percent"]
        b_corr = cat_stats_b[cat]["correct"]
        h_corr = cat_stats_h[cat]["correct"]
        tot = cat_stats_h[cat]["total"]

        b_w = int((b_acc / 100.0) * max_w)
        h_w = int((h_acc / 100.0) * max_w)

        bars_svg += f"""
    <!-- Category {cat} -->
    <text x="120" y="{y + 20}" font-size="12" font-weight="600" fill="#334155" text-anchor="end">{cat.capitalize()}</text>
    
    <rect x="130" y="{y}" width="{b_w}" height="{bar_h}" rx="3" fill="#94a3b8"/>
    <text x="{130 + b_w + 6}" y="{y + 12}" font-size="11" fill="#64748b">{b_acc:.1f}% ({b_corr}/{tot})</text>
    
    <rect x="130" y="{y + bar_h + 3}" width="{h_w}" height="{bar_h}" rx="3" fill="#16a34a"/>
    <text x="{130 + h_w + 6}" y="{y + bar_h + 15}" font-size="11" font-weight="700" fill="#15803d">{h_acc:.1f}% ({h_corr}/{tot})</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 380" width="540" height="380" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="270" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">Category Accuracy: Baseline vs Hybrid</text>
  <text x="270" y="52" font-size="12" fill="#64748b" text-anchor="middle">N = 15 examples per category</text>

  <!-- Legend -->
  <rect x="170" y="65" width="14" height="14" rx="2" fill="#94a3b8"/>
  <text x="190" y="77" font-size="11" fill="#475569">Baseline ModernBERT</text>
  <rect x="310" y="65" width="14" height="14" rx="2" fill="#16a34a"/>
  <text x="330" y="77" font-size="11" font-weight="600" fill="#15803d">NLI Hybrid (Ours)</text>

  {bars_svg}
  <line x1="130" y1="{start_y + 4 * group_gap}" x2="410" y2="{start_y + 4 * group_gap}" stroke="#cbd5e1" stroke-width="1"/>
  <text x="130" y="{start_y + 4 * group_gap + 16}" font-size="10" fill="#94a3b8" text-anchor="middle">0%</text>
  <text x="270" y="{start_y + 4 * group_gap + 16}" font-size="10" fill="#94a3b8" text-anchor="middle">50%</text>
  <text x="410" y="{start_y + 4 * group_gap + 16}" font-size="10" fill="#94a3b8" text-anchor="middle">100%</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_svg_latency_breakdown(lats_lettuce, lats_nli, lats_total, out_path):
    """Generate SVG chart comparing latency components."""
    mean_let = sum(lats_lettuce) / len(lats_lettuce)
    mean_nli = sum(lats_nli) / len(lats_nli)
    mean_tot = sum(lats_total) / len(lats_total)

    p95_let = sorted(lats_lettuce)[int(0.95 * len(lats_lettuce))]
    p95_nli = sorted(lats_nli)[int(0.95 * len(lats_nli))]
    p95_tot = sorted(lats_total)[int(0.95 * len(lats_total))]

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 320" width="540" height="320" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="270" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">CPU Inference Latency Breakdown (N = 60)</text>
  <text x="270" y="52" font-size="12" fill="#64748b" text-anchor="middle">Mean vs p95 Latency Across Evaluation Components</text>

  <!-- Group 1: LettuceDetect -->
  <text x="110" y="90" font-size="13" font-weight="600" fill="#334155" text-anchor="middle">LettuceDetect</text>
  <rect x="70" y="{220 - int(mean_let * 0.15)}" width="35" height="{int(mean_let * 0.15)}" rx="4" fill="#3b82f6"/>
  <text x="87" y="{220 - int(mean_let * 0.15) - 6}" font-size="11" font-weight="700" fill="#1e40af" text-anchor="middle">{mean_let:.0f}ms</text>
  <rect x="115" y="{220 - int(p95_let * 0.15)}" width="35" height="{int(p95_let * 0.15)}" rx="4" fill="#93c5fd"/>
  <text x="132" y="{220 - int(p95_let * 0.15) - 6}" font-size="11" fill="#475569" text-anchor="middle">{p95_let:.0f}ms</text>

  <!-- Group 2: NLI Verifier -->
  <text x="270" y="90" font-size="13" font-weight="600" fill="#334155" text-anchor="middle">DeBERTa-v3 NLI</text>
  <rect x="230" y="{220 - int(mean_nli * 0.15)}" width="35" height="{int(mean_nli * 0.15)}" rx="4" fill="#8b5cf6"/>
  <text x="247" y="{220 - int(mean_nli * 0.15) - 6}" font-size="11" font-weight="700" fill="#6d28d9" text-anchor="middle">{mean_nli:.0f}ms</text>
  <rect x="275" y="{220 - int(p95_nli * 0.15)}" width="35" height="{int(p95_nli * 0.15)}" rx="4" fill="#c4b5fd"/>
  <text x="292" y="{220 - int(p95_nli * 0.15) - 6}" font-size="11" fill="#475569" text-anchor="middle">{p95_nli:.0f}ms</text>

  <!-- Group 3: Total Pipeline -->
  <text x="430" y="90" font-size="13" font-weight="600" fill="#334155" text-anchor="middle">Total Hybrid</text>
  <rect x="390" y="{220 - int(mean_tot * 0.15)}" width="35" height="{int(mean_tot * 0.15)}" rx="4" fill="#059669"/>
  <text x="407" y="{220 - int(mean_tot * 0.15) - 6}" font-size="11" font-weight="700" fill="#065f46" text-anchor="middle">{mean_tot:.0f}ms</text>
  <rect x="435" y="{220 - int(p95_tot * 0.15)}" width="35" height="{int(p95_tot * 0.15)}" rx="4" fill="#6ee7b7"/>
  <text x="452" y="{220 - int(p95_tot * 0.15) - 6}" font-size="11" fill="#475569" text-anchor="middle">{p95_tot:.0f}ms</text>

  <line x1="50" y1="220" x2="490" y2="220" stroke="#cbd5e1" stroke-width="1"/>
  <!-- Legend -->
  <rect x="180" y="260" width="14" height="14" rx="2" fill="#3b82f6"/>
  <text x="200" y="272" font-size="11" fill="#475569">Mean Latency</text>
  <rect x="300" y="260" width="14" height="14" rx="2" fill="#93c5fd"/>
  <text x="320" y="272" font-size="11" fill="#475569">p95 Latency</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    print("=" * 80)
    print("HALLUGUARD PHASE 8, STEP 2: EXPERIMENTAL NLI HYBRID EVALUATION")
    print("=" * 80)
    print(f"Target Dataset:   {DATASET_CSV}")
    print(f"Results Directory: {RESULTS_DIR}\n")

    # Load baseline summary to verify baseline figures
    baseline_summary_file = RESULTS_DIR / "baseline_run_summary.json"
    with open(baseline_summary_file, "r", encoding="utf-8") as f:
        baseline_summary = json.load(f)

    # 1. Load dataset rows
    dataset_rows = []
    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset_rows.append(row)
    print(f"[OK] Loaded {len(dataset_rows)} benchmark rows.")

    # 2. Load Models
    print("[-] Initializing LettuceDetect ModernBERT model...")
    t0 = time.perf_counter()
    if not detector_service.is_loaded:
        detector_service.load_model()
    lettuce_load_sec = round(time.perf_counter() - t0, 2)
    print(f"[OK] LettuceDetect loaded in {lettuce_load_sec}s.")

    print("[-] Initializing DeBERTa-v3 NLI model...")
    t1 = time.perf_counter()
    if not nli_service.is_loaded:
        nli_service.load_model()
    nli_load_sec = round(time.perf_counter() - t1, 2)
    print(
        f"[OK] DeBERTa-v3 NLI loaded in {nli_load_sec}s "
        f"(Footprint: {nli_service.memory_footprint_mb} MB, Threshold: {nli_service.contradiction_threshold})."
    )
    print(f"  * Verified id2label: {nli_service.id2label}\n")

    # Tracking structures
    predictions = []
    latencies_lettuce = []
    latencies_nli = []
    latencies_total = []

    cat_correct_hybrid = {"supported": 0, "contradictory": 0, "unsupported": 0, "mixed": 0}
    cat_totals = {"supported": 0, "contradictory": 0, "unsupported": 0, "mixed": 0}

    # Confusion matrix counters
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    fp_cases = []
    fn_cases = []
    salvaged_fn_cases = []

    # Span counters
    total_gold_spans = 0
    total_pred_spans = 0
    total_exact_matches = 0
    total_partial_matches = 0
    total_char_intersection = 0
    total_char_pred = 0
    total_char_gold = 0

    print("[-] Running hybrid evaluation on all 60 examples...")
    for idx, row in enumerate(dataset_rows, start=1):
        test_id = row["test_id"]
        cat = row["category"]
        expected_verdict = row["expected_verdict"]
        question = row["question"]
        context_str = row["reference_context"]
        answer = row["generated_answer"]
        expected_spans = json.loads(row["expected_unsupported_spans"])

        cat_totals[cat] += 1
        total_gold_spans += len(expected_spans)

        # 1. Run LettuceDetect Pass
        t_let_start = time.perf_counter()
        lettuce_spans_raw, lettuce_summary, _ = detector_service.predict(
            context=[context_str],
            answer=answer,
            question=question,
            min_confidence=0.0,
        )
        lettuce_latency_ms = round((time.perf_counter() - t_let_start) * 1000, 2)
        latencies_lettuce.append(lettuce_latency_ms)

        lettuce_verdict = lettuce_summary.verdict
        lettuce_spans = [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text,
                "confidence": s.confidence,
                "category": s.category,
                "source": "lettucedetect",
            }
            for s in lettuce_spans_raw
        ]

        # 2. Run NLI Pass
        t_nli_start = time.perf_counter()
        nli_res = nli_service.analyze_answer(
            context=context_str,
            answer=answer,
            question=question,
        )
        nli_latency_ms = round((time.perf_counter() - t_nli_start) * 1000, 2)
        latencies_nli.append(nli_latency_ms)

        total_sample_latency = round(lettuce_latency_ms + nli_latency_ms, 2)
        latencies_total.append(total_sample_latency)

        # 3. Hybrid Decision Fusion
        fusion_source = "unanimous"
        if lettuce_verdict == "HALLUCINATED":
            hybrid_verdict = "HALLUCINATED"
            hybrid_spans = lettuce_spans
            fusion_source = "both_agree" if nli_res["has_contradiction"] else "lettucedetect_primary"
        elif nli_res["has_contradiction"]:
            # LettuceDetect missed it (False Negative), but NLI caught contradiction
            hybrid_verdict = "HALLUCINATED"
            hybrid_spans = [
                {
                    "start": cs["start"],
                    "end": cs["end"],
                    "text": cs["text"],
                    "confidence": cs["confidence"],
                    "category": "contradiction",
                    "source": "nli_salvaged",
                }
                for cs in nli_res["contradictory_spans"]
            ]
            fusion_source = "nli_salvaged"
            salvaged_fn_cases.append(test_id)
        else:
            # Neither detector flagged any issue
            hybrid_verdict = "CLEAN"
            hybrid_spans = []
            fusion_source = "unanimous_clean"

        is_correct = (hybrid_verdict == expected_verdict)
        if is_correct:
            cat_correct_hybrid[cat] += 1

        # Update confusion matrix
        if expected_verdict == "HALLUCINATED" and hybrid_verdict == "HALLUCINATED":
            tp += 1
        elif expected_verdict == "CLEAN" and hybrid_verdict == "CLEAN":
            tn += 1
        elif expected_verdict == "CLEAN" and hybrid_verdict == "HALLUCINATED":
            fp += 1
            fp_cases.append(test_id)
        elif expected_verdict == "HALLUCINATED" and hybrid_verdict == "CLEAN":
            fn += 1
            fn_cases.append(test_id)

        # Span metrics
        total_pred_spans += len(hybrid_spans)
        exact_m, partial_m = match_spans(expected_spans, hybrid_spans, iou_threshold=0.5)
        total_exact_matches += exact_m
        total_partial_matches += partial_m

        _, _, _, inter_c, p_len_c, g_len_c = calculate_char_overlap(
            expected_spans, hybrid_spans, len(answer)
        )
        total_char_intersection += inter_c
        total_char_pred += p_len_c
        total_char_gold += g_len_c

        # Record prediction details
        record = {
            "test_id": test_id,
            "category": cat,
            "expected_verdict": expected_verdict,
            "baseline_verdict": lettuce_verdict,
            "hybrid_verdict": hybrid_verdict,
            "is_correct": is_correct,
            "fusion_source": fusion_source,
            "question": question,
            "reference_context": context_str,
            "generated_answer": answer,
            "expected_unsupported_spans": expected_spans,
            "lettuce_spans": lettuce_spans,
            "nli_contradictory_spans": nli_res["contradictory_spans"],
            "hybrid_spans": hybrid_spans,
            "span_count": len(hybrid_spans),
            "nli_max_contradiction": nli_res["max_contradiction_score"],
            "nli_segments": nli_res["all_segments"],
            "latency": {
                "lettucedetect_ms": lettuce_latency_ms,
                "nli_ms": nli_latency_ms,
                "total_ms": total_sample_latency,
            },
        }
        predictions.append(record)

        status_icon = "✓" if is_correct else "✗"
        salvage_marker = " [NLI SALVAGED]" if fusion_source == "nli_salvaged" else ""
        print(
            f"[{idx:02d}/60] {status_icon} {test_id} ({cat:13s}) | "
            f"Exp: {expected_verdict:12s} | Base: {lettuce_verdict:12s} | "
            f"Hybrid: {hybrid_verdict:12s} | Lat: {total_sample_latency:6.1f}ms{salvage_marker}"
        )

    # 4. Compute Summary Metrics
    total_samples = len(predictions)
    accuracy = (tp + tn) / total_samples
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    specificity = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    category_metrics_hybrid = {}
    for cat in cat_totals:
        tot = cat_totals[cat]
        corr = cat_correct_hybrid[cat]
        acc = (corr / tot * 100.0) if tot > 0 else 0.0
        category_metrics_hybrid[cat] = {
            "total": tot,
            "correct": corr,
            "accuracy_percent": round(acc, 2),
        }

    # Span metrics
    span_exact_precision = (total_exact_matches / total_pred_spans) if total_pred_spans > 0 else 0.0
    span_exact_recall = (total_exact_matches / total_gold_spans) if total_gold_spans > 0 else 0.0
    span_exact_f1 = (
        (2 * span_exact_precision * span_exact_recall / (span_exact_precision + span_exact_recall))
        if (span_exact_precision + span_exact_recall) > 0
        else 0.0
    )

    span_partial_precision = (total_partial_matches / total_pred_spans) if total_pred_spans > 0 else 0.0
    span_partial_recall = (total_partial_matches / total_gold_spans) if total_gold_spans > 0 else 0.0
    span_partial_f1 = (
        (2 * span_partial_precision * span_partial_recall / (span_partial_precision + span_partial_recall))
        if (span_partial_precision + span_partial_recall) > 0
        else 0.0
    )

    char_precision = (total_char_intersection / total_char_pred) if total_char_pred > 0 else 0.0
    char_recall = (total_char_intersection / total_char_gold) if total_char_gold > 0 else 0.0
    char_f1 = (
        (2 * char_precision * char_recall / (char_precision + char_recall))
        if (char_precision + char_recall) > 0
        else 0.0
    )

    # Latencies
    def get_lat_stats(lats):
        sl = sorted(lats)
        return {
            "mean": round(sum(sl) / len(sl), 2),
            "median": round(sl[len(sl) // 2], 2),
            "min": round(sl[0], 2),
            "max": round(sl[-1], 2),
            "p95": round(sl[int(math.ceil(0.95 * len(sl))) - 1], 2),
        }

    stats_lettuce = get_lat_stats(latencies_lettuce)
    stats_nli = get_lat_stats(latencies_nli)
    stats_total = get_lat_stats(latencies_total)

    # Serialize Predictions JSON
    out_pred_json = RESULTS_DIR / "nli_hybrid_predictions.json"
    with open(out_pred_json, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {out_pred_json}")

    # Serialize Summary JSON
    summary_data = {
        "experiment_name": "DeBERTa-v3 NLI Hybrid Evaluation (Phase 8 Step 2)",
        "models": {
            "span_detector": "KRLabsOrg/lettucedect-base-modernbert-en-v1",
            "nli_verifier": nli_service.model_name,
        },
        "device": "cpu",
        "contradiction_threshold": nli_service.contradiction_threshold,
        "total_samples": total_samples,
        "answer_level_metrics": {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "specificity": round(specificity, 4),
            "f1_score": round(f1, 4),
        },
        "confusion_matrix": {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        },
        "category_metrics": category_metrics_hybrid,
        "span_level_metrics": {
            "total_gold_spans": total_gold_spans,
            "total_predicted_spans": total_pred_spans,
            "exact_match": {
                "matched_count": total_exact_matches,
                "precision": round(span_exact_precision, 4),
                "recall": round(span_exact_recall, 4),
                "f1_score": round(span_exact_f1, 4),
            },
            "partial_overlap_iou_0_5": {
                "matched_count": total_partial_matches,
                "precision": round(span_partial_precision, 4),
                "recall": round(span_partial_recall, 4),
                "f1_score": round(span_partial_f1, 4),
            },
            "character_overlap": {
                "precision": round(char_precision, 4),
                "recall": round(char_recall, 4),
                "f1_score": round(char_f1, 4),
            },
        },
        "latency_metrics_ms": {
            "lettucedetect": stats_lettuce,
            "nli_verifier": stats_nli,
            "hybrid_total": stats_total,
        },
        "salvaged_fn_cases": salvaged_fn_cases,
        "false_positive_cases": fp_cases,
        "remaining_false_negative_cases": fn_cases,
        "baseline_comparison": {
            "baseline_accuracy": baseline_summary["answer_level_metrics"]["accuracy"],
            "hybrid_accuracy": round(accuracy, 4),
            "accuracy_delta": round(accuracy - baseline_summary["answer_level_metrics"]["accuracy"], 4),
            "baseline_recall": baseline_summary["answer_level_metrics"]["recall"],
            "hybrid_recall": round(recall, 4),
            "recall_delta": round(recall - baseline_summary["answer_level_metrics"]["recall"], 4),
            "baseline_f1": baseline_summary["answer_level_metrics"]["f1_score"],
            "hybrid_f1": round(f1, 4),
            "f1_delta": round(f1 - baseline_summary["answer_level_metrics"]["f1_score"], 4),
            "baseline_fn_count": len(baseline_summary["false_negative_cases"]),
            "hybrid_fn_count": fn,
            "baseline_fp_count": len(baseline_summary["false_positive_cases"]),
            "hybrid_fp_count": fp,
        },
    }

    out_summary_json = RESULTS_DIR / "nli_hybrid_run_summary.json"
    with open(out_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"[SAVED] {out_summary_json}")

    # Generate SVGs
    cm_svg = RESULTS_DIR / "nli_hybrid_confusion_matrix.svg"
    generate_svg_confusion_matrix(tp, fp, fn, tn, cm_svg)
    print(f"[SAVED] {cm_svg}")

    comp_svg = RESULTS_DIR / "nli_hybrid_comparison.svg"
    generate_svg_comparison_chart(
        baseline_summary["answer_level_metrics"],
        summary_data["answer_level_metrics"],
        comp_svg,
    )
    print(f"[SAVED] {comp_svg}")

    cat_svg = RESULTS_DIR / "nli_hybrid_category_accuracy.svg"
    generate_svg_category_accuracy(
        baseline_summary["category_metrics"],
        category_metrics_hybrid,
        cat_svg,
    )
    print(f"[SAVED] {cat_svg}")

    lat_svg = RESULTS_DIR / "nli_hybrid_latency.svg"
    generate_svg_latency_breakdown(latencies_lettuce, latencies_nli, latencies_total, lat_svg)
    print(f"[SAVED] {lat_svg}")

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETE")
    print(f"Baseline Accuracy: {baseline_summary['answer_level_metrics']['accuracy']*100:.1f}% -> Hybrid Accuracy: {accuracy*100:.1f}%")
    print(f"Baseline Recall:   {baseline_summary['answer_level_metrics']['recall']*100:.1f}% -> Hybrid Recall:   {recall*100:.1f}%")
    print(f"Baseline F1:       {baseline_summary['answer_level_metrics']['f1_score']*100:.1f}% -> Hybrid F1:       {f1*100:.1f}%")
    print(f"Salvaged FN Cases: {salvaged_fn_cases}")
    print("=" * 80)


if __name__ == "__main__":
    main()

