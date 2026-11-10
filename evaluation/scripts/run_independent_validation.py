"""Independent Validation Runner for HalluGuard (Phase 8 Step 3).

Evaluates BOTH:
1. Original LettuceDetect Baseline (ModernBERT token classifier)
2. Experimental NLI Hybrid (ModernBERT + DeBERTa-v3-small NLI verifier)

Over the NEW 100-sample independent geography evaluation dataset.
Configuration is completely frozen (no tuning on the test set).
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

DATASET_CSV = EVAL_DIR / "dataset" / "independent_geography_dataset.csv"
RESULTS_DIR = EVAL_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from app.services.detector_service import detector_service
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
def generate_svg_confusion_matrices(cm_b, cm_h, out_path):
    """Generate side-by-side SVG confusion matrices for baseline and hybrid."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 400" width="900" height="400" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <style>
    .title {{ font-size: 16px; font-weight: 700; fill: #1e293b; text-anchor: middle; }}
    .subtitle {{ font-size: 12px; fill: #64748b; text-anchor: middle; }}
    .panel-title {{ font-size: 14px; font-weight: 700; fill: #334155; text-anchor: middle; }}
    .axis-label {{ font-size: 11px; font-weight: 600; fill: #475569; text-anchor: middle; }}
    .cell-title {{ font-size: 11px; font-weight: 600; text-anchor: middle; }}
    .cell-val {{ font-size: 26px; font-weight: 800; text-anchor: middle; }}
    .cell-sub {{ font-size: 10px; text-anchor: middle; fill: #64748b; }}
  </style>

  <!-- Main Header -->
  <text x="450" y="30" class="title">Independent Benchmark Confusion Matrices (N = 100 Unseen Samples)</text>
  <text x="450" y="50" class="subtitle">LettuceDetect ModernBERT Baseline vs DeBERTa-v3 NLI Hybrid</text>

  <!-- PANEL 1: BASELINE -->
  <g transform="translate(30, 70)">
    <text x="180" y="15" class="panel-title">Baseline ModernBERT</text>
    <text x="180" y="32" class="axis-label">PREDICTED CLASS</text>
    <text x="110" y="50" class="axis-label" style="fill:#dc2626;">HALLUCINATED</text>
    <text x="250" y="50" class="axis-label" style="fill:#16a34a;">CLEAN</text>

    <text x="35" y="125" class="axis-label" style="fill:#dc2626; text-anchor:end;">ACTUAL HALL</text>
    <text x="35" y="215" class="axis-label" style="fill:#16a34a; text-anchor:end;">ACTUAL CLEAN</text>

    <!-- TP -->
    <rect x="50" y="65" width="120" height="80" rx="6" fill="#fef2f2" stroke="#fca5a5" stroke-width="1.5"/>
    <text x="110" y="87" class="cell-title" fill="#991b1b">TP</text>
    <text x="110" y="120" class="cell-val" fill="#b91c1c">{cm_b['tp']}</text>
    <text x="110" y="136" class="cell-sub">Correct Flag</text>

    <!-- FN -->
    <rect x="190" y="65" width="120" height="80" rx="6" fill="#fff7ed" stroke="#fdba74" stroke-width="1.5"/>
    <text x="250" y="87" class="cell-title" fill="#c2410c">FN (Missed)</text>
    <text x="250" y="120" class="cell-val" fill="#ea580c">{cm_b['fn']}</text>
    <text x="250" y="136" class="cell-sub">Type II Error</text>

    <!-- FP -->
    <rect x="50" y="155" width="120" height="80" rx="6" fill="#fefce8" stroke="#fde047" stroke-width="1.5"/>
    <text x="110" y="177" class="cell-title" fill="#a16207">FP</text>
    <text x="110" y="210" class="cell-val" fill="#ca8a04">{cm_b['fp']}</text>
    <text x="110" y="226" class="cell-sub">Type I Error</text>

    <!-- TN -->
    <rect x="190" y="155" width="120" height="80" rx="6" fill="#f0fdf4" stroke="#86efac" stroke-width="1.5"/>
    <text x="250" y="177" class="cell-title" fill="#15803d">TN</text>
    <text x="250" y="210" class="cell-val" fill="#16a34a">{cm_b['tn']}</text>
    <text x="250" y="226" class="cell-sub">Correct Clean</text>

    <text x="180" y="260" class="cell-sub">Accuracy: {cm_b['acc']:.1f}% | Recall: {cm_b['rec']:.1f}%</text>
  </g>

  <!-- PANEL 2: HYBRID -->
  <g transform="translate(480, 70)">
    <text x="180" y="15" class="panel-title" fill="#1e40af">Experimental NLI Hybrid (Ours)</text>
    <text x="180" y="32" class="axis-label">PREDICTED CLASS</text>
    <text x="110" y="50" class="axis-label" style="fill:#dc2626;">HALLUCINATED</text>
    <text x="250" y="50" class="axis-label" style="fill:#16a34a;">CLEAN</text>

    <text x="35" y="125" class="axis-label" style="fill:#dc2626; text-anchor:end;">ACTUAL HALL</text>
    <text x="35" y="215" class="axis-label" style="fill:#16a34a; text-anchor:end;">ACTUAL CLEAN</text>

    <!-- TP -->
    <rect x="50" y="65" width="120" height="80" rx="6" fill="#fef2f2" stroke="#fca5a5" stroke-width="2"/>
    <text x="110" y="87" class="cell-title" fill="#991b1b">TP</text>
    <text x="110" y="120" class="cell-val" fill="#b91c1c">{cm_h['tp']}</text>
    <text x="110" y="136" class="cell-sub">Correct Flag</text>

    <!-- FN -->
    <rect x="190" y="65" width="120" height="80" rx="6" fill="#fff7ed" stroke="#fdba74" stroke-width="2"/>
    <text x="250" y="87" class="cell-title" fill="#c2410c">FN (Missed)</text>
    <text x="250" y="120" class="cell-val" fill="#ea580c">{cm_h['fn']}</text>
    <text x="250" y="136" class="cell-sub">Type II Error</text>

    <!-- FP -->
    <rect x="50" y="155" width="120" height="80" rx="6" fill="#fefce8" stroke="#fde047" stroke-width="2"/>
    <text x="110" y="177" class="cell-title" fill="#a16207">FP</text>
    <text x="110" y="210" class="cell-val" fill="#ca8a04">{cm_h['fp']}</text>
    <text x="110" y="226" class="cell-sub">Type I Error</text>

    <!-- TN -->
    <rect x="190" y="155" width="120" height="80" rx="6" fill="#f0fdf4" stroke="#86efac" stroke-width="2"/>
    <text x="250" y="177" class="cell-title" fill="#15803d">TN</text>
    <text x="250" y="210" class="cell-val" fill="#16a34a">{cm_h['tn']}</text>
    <text x="250" y="226" class="cell-sub">Correct Clean</text>

    <text x="180" y="260" class="cell-sub">Accuracy: {cm_h['acc']:.1f}% | Recall: {cm_h['rec']:.1f}%</text>
  </g>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_svg_comparison_chart(m_b, m_h, out_path):
    """Generate SVG bar chart comparing Baseline vs Hybrid."""
    metrics = [
        ("Accuracy", m_b["accuracy"] * 100, m_h["accuracy"] * 100),
        ("Precision", m_b["precision"] * 100, m_h["precision"] * 100),
        ("Recall", m_b["recall"] * 100, m_h["recall"] * 100),
        ("Specificity", m_b["specificity"] * 100, m_h["specificity"] * 100),
        ("F1-Score", m_b["f1_score"] * 100, m_h["f1_score"] * 100),
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
    <text x="110" y="{y + 20}" font-size="12" font-weight="600" fill="#334155" text-anchor="end">{m_name}</text>
    <rect x="120" y="{y}" width="{b_w}" height="{bar_h}" rx="3" fill="#94a3b8"/>
    <text x="{120 + b_w + 6}" y="{y + 12}" font-size="11" font-weight="600" fill="#64748b">{b_val:.1f}%</text>
    <rect x="120" y="{y + bar_h + 3}" width="{h_w}" height="{bar_h}" rx="3" fill="#2563eb"/>
    <text x="{120 + h_w + 6}" y="{y + bar_h + 15}" font-size="11" font-weight="700" fill="#1e40af">{h_val:.1f}%</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 370" width="540" height="370" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="270" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">Independent Benchmark: Baseline vs Hybrid</text>
  <text x="270" y="52" font-size="12" fill="#64748b" text-anchor="middle">Out-of-Sample Performance on 100 Unseen Examples</text>

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


def generate_svg_category_accuracy(cat_b, cat_h, out_path):
    """Generate SVG bar chart for category-wise accuracy comparison."""
    categories = ["supported", "contradictory", "unsupported", "mixed"]
    bars_svg = ""
    start_y = 90
    group_gap = 52
    bar_h = 16
    max_w = 280

    for i, cat in enumerate(categories):
        y = start_y + (i * group_gap)
        b_acc = cat_b[cat]["accuracy_percent"]
        h_acc = cat_h[cat]["accuracy_percent"]
        b_corr = cat_b[cat]["correct"]
        h_corr = cat_h[cat]["correct"]
        tot = cat_h[cat]["total"]

        b_w = int((b_acc / 100.0) * max_w)
        h_w = int((h_acc / 100.0) * max_w)

        bars_svg += f"""
    <text x="120" y="{y + 20}" font-size="12" font-weight="600" fill="#334155" text-anchor="end">{cat.capitalize()}</text>
    <rect x="130" y="{y}" width="{b_w}" height="{bar_h}" rx="3" fill="#94a3b8"/>
    <text x="{130 + b_w + 6}" y="{y + 12}" font-size="11" fill="#64748b">{b_acc:.1f}% ({b_corr}/{tot})</text>
    <rect x="130" y="{y + bar_h + 3}" width="{h_w}" height="{bar_h}" rx="3" fill="#16a34a"/>
    <text x="{130 + h_w + 6}" y="{y + bar_h + 15}" font-size="11" font-weight="700" fill="#15803d">{h_acc:.1f}% ({h_corr}/{tot})</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 380" width="540" height="380" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="270" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">Category Accuracy: Independent Benchmark</text>
  <text x="270" y="52" font-size="12" fill="#64748b" text-anchor="middle">N = 25 examples per category (100 total)</text>

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
  <text x="270" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">CPU Inference Latency Breakdown (N = 100)</text>
  <text x="270" y="52" font-size="12" fill="#64748b" text-anchor="middle">Mean vs p95 Latency on Independent Benchmark</text>

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
  <rect x="180" y="260" width="14" height="14" rx="2" fill="#3b82f6"/>
  <text x="200" y="272" font-size="11" fill="#475569">Mean Latency</text>
  <rect x="300" y="260" width="14" height="14" rx="2" fill="#93c5fd"/>
  <text x="320" y="272" font-size="11" fill="#475569">p95 Latency</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    print("=" * 80)
    print("HALLUGUARD PHASE 8, STEP 3: INDEPENDENT HYBRID VALIDATION")
    print("=" * 80)
    print(f"Target Dataset:   {DATASET_CSV}")
    print(f"Results Directory: {RESULTS_DIR}\n")

    # 1. Load dataset rows
    dataset_rows = []
    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset_rows.append(row)

    if len(dataset_rows) != 100:
        print(f"[ERROR] Expected exactly 100 rows, found {len(dataset_rows)}.")
        sys.exit(1)
    print(f"[OK] Successfully verified dataset with {len(dataset_rows)} unseen rows.")

    # 2. Initialize Models (Offline CPU)
    print("[-] Initializing LettuceDetect ModernBERT model...")
    t0 = time.perf_counter()
    if not detector_service.is_loaded:
        detector_service.load_model()
    lettuce_load_sec = round(time.perf_counter() - t0, 2)
    print(f"[OK] LettuceDetect loaded in {lettuce_load_sec}s.")

    print("[-] Initializing DeBERTa-v3 NLI model (FROZEN configuration)...")
    t1 = time.perf_counter()
    if not nli_service.is_loaded:
        nli_service.load_model()
    nli_load_sec = round(time.perf_counter() - t1, 2)
    print(
        f"[OK] DeBERTa-v3 NLI loaded in {nli_load_sec}s "
        f"(Footprint: {nli_service.memory_footprint_mb} MB, Threshold: {nli_service.contradiction_threshold})."
    )

    # Tracking structures
    baseline_predictions = []
    hybrid_predictions = []

    latencies_lettuce = []
    latencies_nli = []
    latencies_total = []

    # Category tracking: Baseline
    cat_b = {
        c: {"total": 0, "correct": 0}
        for c in ["supported", "contradictory", "unsupported", "mixed"]
    }
    # Category tracking: Hybrid
    cat_h = {
        c: {"total": 0, "correct": 0}
        for c in ["supported", "contradictory", "unsupported", "mixed"]
    }

    # Confusion matrix counters: Baseline
    tp_b, fp_b, tn_b, fn_b = 0, 0, 0, 0
    fn_cases_b, fp_cases_b = [], []

    # Confusion matrix counters: Hybrid
    tp_h, fp_h, tn_h, fn_h = 0, 0, 0, 0
    fn_cases_h, fp_cases_h = [], []
    salvaged_fn_cases = []

    # Span counters: Baseline
    gold_spans_total = 0
    b_pred_spans_total = 0
    b_exact_matches = 0
    b_partial_matches = 0
    b_char_inter = 0
    b_char_pred = 0
    b_char_gold = 0

    # Span counters: Hybrid
    h_pred_spans_total = 0
    h_exact_matches = 0
    h_partial_matches = 0
    h_char_inter = 0
    h_char_pred = 0
    h_char_gold = 0

    # Neutral check tracking
    neutral_misclassified_cases = []

    print("\n[-] Running evaluation across all 100 unseen examples...")
    for idx, row in enumerate(dataset_rows, start=1):
        test_id = row["test_id"]
        cat = row["category"]
        expected_verdict = row["expected_verdict"]
        question = row["question"]
        context_str = row["reference_context"]
        answer = row["generated_answer"]
        expected_spans = json.loads(row["expected_unsupported_spans"])

        cat_b[cat]["total"] += 1
        cat_h[cat]["total"] += 1
        gold_spans_total += len(expected_spans)

        # -------------------------------------------------------------
        # 1. Run LettuceDetect Baseline Pass
        # -------------------------------------------------------------
        t_let_start = time.perf_counter()
        lettuce_spans_raw, lettuce_summary, _ = detector_service.predict(
            context=[context_str],
            answer=answer,
            question=question,
            min_confidence=0.0,
        )
        lettuce_lat = round((time.perf_counter() - t_let_start) * 1000, 2)
        latencies_lettuce.append(lettuce_lat)

        let_verdict = lettuce_summary.verdict
        let_spans = [
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

        # Evaluate Baseline
        b_correct = (let_verdict == expected_verdict)
        if b_correct:
            cat_b[cat]["correct"] += 1

        if expected_verdict == "HALLUCINATED" and let_verdict == "HALLUCINATED":
            tp_b += 1
        elif expected_verdict == "CLEAN" and let_verdict == "CLEAN":
            tn_b += 1
        elif expected_verdict == "CLEAN" and let_verdict == "HALLUCINATED":
            fp_b += 1
            fp_cases_b.append(test_id)
        elif expected_verdict == "HALLUCINATED" and let_verdict == "CLEAN":
            fn_b += 1
            fn_cases_b.append(test_id)

        # Baseline Span Metrics
        b_pred_spans_total += len(let_spans)
        ex_m_b, part_m_b = match_spans(expected_spans, let_spans, iou_threshold=0.5)
        b_exact_matches += ex_m_b
        b_partial_matches += part_m_b

        _, _, _, inter_c_b, p_len_c_b, g_len_c_b = calculate_char_overlap(
            expected_spans, let_spans, len(answer)
        )
        b_char_inter += inter_c_b
        b_char_pred += p_len_c_b
        b_char_gold += g_len_c_b

        baseline_record = {
            "test_id": test_id,
            "category": cat,
            "expected_verdict": expected_verdict,
            "predicted_verdict": let_verdict,
            "is_correct": b_correct,
            "expected_spans": expected_spans,
            "predicted_spans": let_spans,
            "span_count": len(let_spans),
            "inference_latency_ms": lettuce_lat,
        }
        baseline_predictions.append(baseline_record)

        # -------------------------------------------------------------
        # 2. Run NLI Verifier Pass
        # -------------------------------------------------------------
        t_nli_start = time.perf_counter()
        nli_res = nli_service.analyze_answer(
            context=context_str,
            answer=answer,
            question=question,
        )
        nli_lat = round((time.perf_counter() - t_nli_start) * 1000, 2)
        latencies_nli.append(nli_lat)

        tot_lat = round(lettuce_lat + nli_lat, 2)
        latencies_total.append(tot_lat)

        # Check for any incorrect neutral -> contradiction interpretations
        for seg in nli_res["all_segments"]:
            if seg["label"] == "neutral" and seg["is_contradiction"]:
                neutral_misclassified_cases.append({
                    "test_id": test_id,
                    "segment": seg["text"],
                    "scores": seg,
                })

        # -------------------------------------------------------------
        # 3. Apply Frozen Hybrid Decision Fusion Strategy
        # -------------------------------------------------------------
        fusion_source = "unanimous"
        if let_verdict == "HALLUCINATED":
            hybrid_verdict = "HALLUCINATED"
            hybrid_spans = let_spans
            fusion_source = "both_agree" if nli_res["has_contradiction"] else "lettucedetect_primary"
        elif nli_res["has_contradiction"]:
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
            hybrid_verdict = "CLEAN"
            hybrid_spans = []
            fusion_source = "unanimous_clean"

        h_correct = (hybrid_verdict == expected_verdict)
        if h_correct:
            cat_h[cat]["correct"] += 1

        if expected_verdict == "HALLUCINATED" and hybrid_verdict == "HALLUCINATED":
            tp_h += 1
        elif expected_verdict == "CLEAN" and hybrid_verdict == "CLEAN":
            tn_h += 1
        elif expected_verdict == "CLEAN" and hybrid_verdict == "HALLUCINATED":
            fp_h += 1
            fp_cases_h.append(test_id)
        elif expected_verdict == "HALLUCINATED" and hybrid_verdict == "CLEAN":
            fn_h += 1
            fn_cases_h.append(test_id)

        # Hybrid Span Metrics
        h_pred_spans_total += len(hybrid_spans)
        ex_m_h, part_m_h = match_spans(expected_spans, hybrid_spans, iou_threshold=0.5)
        h_exact_matches += ex_m_h
        h_partial_matches += part_m_h

        _, _, _, inter_c_h, p_len_c_h, g_len_c_h = calculate_char_overlap(
            expected_spans, hybrid_spans, len(answer)
        )
        h_char_inter += inter_c_h
        h_char_pred += p_len_c_h
        h_char_gold += g_len_c_h

        hybrid_record = {
            "test_id": test_id,
            "category": cat,
            "expected_verdict": expected_verdict,
            "baseline_verdict": let_verdict,
            "hybrid_verdict": hybrid_verdict,
            "is_correct": h_correct,
            "fusion_source": fusion_source,
            "question": question,
            "reference_context": context_str,
            "generated_answer": answer,
            "expected_unsupported_spans": expected_spans,
            "lettuce_spans": let_spans,
            "nli_contradictory_spans": nli_res["contradictory_spans"],
            "hybrid_spans": hybrid_spans,
            "span_count": len(hybrid_spans),
            "nli_max_contradiction": nli_res["max_contradiction_score"],
            "nli_segments": nli_res["all_segments"],
            "latency": {
                "lettucedetect_ms": lettuce_lat,
                "nli_ms": nli_lat,
                "total_ms": tot_lat,
            },
        }
        hybrid_predictions.append(hybrid_record)

        icon_b = "✓" if b_correct else "✗"
        icon_h = "✓" if h_correct else "✗"
        salvage_str = " [SALVAGED]" if fusion_source == "nli_salvaged" else ""
        print(
            f"[{idx:03d}/100] Base: {icon_b} | Hybrid: {icon_h} | {test_id} ({cat:13s}) | "
            f"Exp: {expected_verdict:12s} | Pred: {hybrid_verdict:12s} | Lat: {tot_lat:6.1f}ms{salvage_str}"
        )

    # 4. Compute Metrics
    total = len(dataset_rows)

    def calc_metrics(tp, tn, fp, fn):
        acc = (tp + tn) / total
        prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        spec = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        return {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "specificity": round(spec, 4),
            "f1_score": round(f1, 4),
        }

    m_b = calc_metrics(tp_b, tn_b, fp_b, fn_b)
    m_h = calc_metrics(tp_h, tn_h, fp_h, fn_h)

    for c in cat_b:
        cat_b[c]["accuracy_percent"] = round(cat_b[c]["correct"] / cat_b[c]["total"] * 100.0, 2)
    for c in cat_h:
        cat_h[c]["accuracy_percent"] = round(cat_h[c]["correct"] / cat_h[c]["total"] * 100.0, 2)

    # Span Metrics
    def calc_span_metrics(gold_tot, pred_tot, exact_cnt, partial_cnt, char_in, char_p, char_g):
        ex_p = (exact_cnt / pred_tot) if pred_tot > 0 else 0.0
        ex_r = (exact_cnt / gold_tot) if gold_tot > 0 else 0.0
        ex_f1 = (2 * ex_p * ex_r / (ex_p + ex_r)) if (ex_p + ex_r) > 0 else 0.0

        part_p = (partial_cnt / pred_tot) if pred_tot > 0 else 0.0
        part_r = (partial_cnt / gold_tot) if gold_tot > 0 else 0.0
        part_f1 = (2 * part_p * part_r / (part_p + part_r)) if (part_p + part_r) > 0 else 0.0

        ch_p = (char_in / char_p) if char_p > 0 else 0.0
        ch_r = (char_in / char_g) if char_g > 0 else 0.0
        ch_f1 = (2 * ch_p * ch_r / (ch_p + ch_r)) if (ch_p + ch_r) > 0 else 0.0

        return {
            "total_gold_spans": gold_tot,
            "total_predicted_spans": pred_tot,
            "exact_match": {
                "matched_count": exact_cnt,
                "precision": round(ex_p, 4),
                "recall": round(ex_r, 4),
                "f1_score": round(ex_f1, 4),
            },
            "partial_overlap_iou_0_5": {
                "matched_count": partial_cnt,
                "precision": round(part_p, 4),
                "recall": round(part_r, 4),
                "f1_score": round(part_f1, 4),
            },
            "character_overlap": {
                "precision": round(ch_p, 4),
                "recall": round(ch_r, 4),
                "f1_score": round(ch_f1, 4),
            },
        }

    span_b = calc_span_metrics(
        gold_spans_total, b_pred_spans_total, b_exact_matches, b_partial_matches,
        b_char_inter, b_char_pred, b_char_gold
    )
    span_h = calc_span_metrics(
        gold_spans_total, h_pred_spans_total, h_exact_matches, h_partial_matches,
        h_char_inter, h_char_pred, h_char_gold
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

    # Summary payload
    summary_data = {
        "experiment_name": "Independent Hybrid Validation (Phase 8 Step 3)",
        "dataset": {
            "path": str(DATASET_CSV),
            "total_samples": total,
            "categories": {c: cat_h[c]["total"] for c in cat_h},
        },
        "models": {
            "baseline": "KRLabsOrg/lettucedect-base-modernbert-en-v1",
            "nli_verifier": nli_service.model_name,
        },
        "device": "cpu",
        "contradiction_threshold": nli_service.contradiction_threshold,
        "baseline_metrics": {
            "answer_level": m_b,
            "confusion_matrix": {"tp": tp_b, "tn": tn_b, "fp": fp_b, "fn": fn_b},
            "category_metrics": cat_b,
            "span_level": span_b,
            "false_negative_cases": fn_cases_b,
            "false_positive_cases": fp_cases_b,
        },
        "hybrid_metrics": {
            "answer_level": m_h,
            "confusion_matrix": {"tp": tp_h, "tn": tn_h, "fp": fp_h, "fn": fn_h},
            "category_metrics": cat_h,
            "span_level": span_h,
            "false_negative_cases": fn_cases_h,
            "false_positive_cases": fp_cases_h,
            "salvaged_fn_cases": salvaged_fn_cases,
        },
        "comparison_deltas": {
            "accuracy_delta": round(m_h["accuracy"] - m_b["accuracy"], 4),
            "recall_delta": round(m_h["recall"] - m_b["recall"], 4),
            "precision_delta": round(m_h["precision"] - m_b["precision"], 4),
            "f1_delta": round(m_h["f1_score"] - m_b["f1_score"], 4),
            "fn_reduction": fn_b - fn_h,
            "fp_increase": fp_h - fp_b,
        },
        "latency_metrics_ms": {
            "lettucedetect": stats_lettuce,
            "nli_verifier": stats_nli,
            "hybrid_total": stats_total,
        },
        "neutral_misclassified_cases": neutral_misclassified_cases,
    }

    # Save predictions JSONs
    out_b_json = RESULTS_DIR / "independent_baseline_predictions.json"
    with open(out_b_json, "w", encoding="utf-8") as f:
        json.dump(baseline_predictions, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {out_b_json}")

    out_h_json = RESULTS_DIR / "independent_hybrid_predictions.json"
    with open(out_h_json, "w", encoding="utf-8") as f:
        json.dump(hybrid_predictions, f, indent=2, ensure_ascii=False)
    print(f"[SAVED] {out_h_json}")

    out_sum_json = RESULTS_DIR / "independent_validation_summary.json"
    with open(out_sum_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"[SAVED] {out_sum_json}")

    # Generate SVGs
    cm_b_plot = {"tp": tp_b, "tn": tn_b, "fp": fp_b, "fn": fn_b, "acc": m_b["accuracy"] * 100, "rec": m_b["recall"] * 100}
    cm_h_plot = {"tp": tp_h, "tn": tn_h, "fp": fp_h, "fn": fn_h, "acc": m_h["accuracy"] * 100, "rec": m_h["recall"] * 100}
    cm_svg = RESULTS_DIR / "independent_validation_confusion_matrix.svg"
    generate_svg_confusion_matrices(cm_b_plot, cm_h_plot, cm_svg)
    print(f"[SAVED] {cm_svg}")

    comp_svg = RESULTS_DIR / "independent_validation_comparison.svg"
    generate_svg_comparison_chart(m_b, m_h, comp_svg)
    print(f"[SAVED] {comp_svg}")

    cat_svg = RESULTS_DIR / "independent_validation_category_accuracy.svg"
    generate_svg_category_accuracy(cat_b, cat_h, cat_svg)
    print(f"[SAVED] {cat_svg}")

    lat_svg = RESULTS_DIR / "independent_validation_latency.svg"
    generate_svg_latency_breakdown(latencies_lettuce, latencies_nli, latencies_total, lat_svg)
    print(f"[SAVED] {lat_svg}")

    print("\n" + "=" * 80)
    print("INDEPENDENT VALIDATION COMPLETE")
    print(f"Baseline Accuracy: {m_b['accuracy']*100:.1f}% -> Hybrid Accuracy: {m_h['accuracy']*100:.1f}% (Delta: +{(m_h['accuracy']-m_b['accuracy'])*100:.1f}%)")
    print(f"Baseline Recall:   {m_b['recall']*100:.1f}% -> Hybrid Recall:   {m_h['recall']*100:.1f}% (Delta: +{(m_h['recall']-m_b['recall'])*100:.1f}%)")
    print(f"Baseline F1:       {m_b['f1_score']*100:.1f}% -> Hybrid F1:       {m_h['f1_score']*100:.1f}% (Delta: +{(m_h['f1_score']-m_b['f1_score'])*100:.1f}%)")
    print(f"Baseline FN: {fn_b} -> Hybrid FN: {fn_h} (Salvaged: {len(salvaged_fn_cases)})")
    print(f"Baseline FP: {fp_b} -> Hybrid FP: {fp_h}")
    print("=" * 80)


if __name__ == "__main__":
    main()

