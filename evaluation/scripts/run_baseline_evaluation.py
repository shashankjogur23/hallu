"""Baseline Model Evaluation Runner for HalluGuard.

Executes the official pretrained LettuceDetect ModernBERT model
('KRLabsOrg/lettucedect-base-modernbert-en-v1') over the 60-example
geography evaluation dataset.

Preserves the existing production system:
- Loads production detector_service once on CPU.
- Uses the unchanged production confidence threshold (min_confidence=0.0).
- Records per-sample inference latency.
- Computes comprehensive answer-level, category-wise, and span-level metrics.
- Serializes complete results to evaluation/results/.
"""

import os
import sys
import time
import json
import csv
import math
from pathlib import Path

# Ensure local offline mode for cached HF weights
os.environ["HF_HUB_OFFLINE"] = "1"

# Setup sys.path to access production backend
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

EVAL_DIR = ROOT_DIR / "evaluation"
DATASET_CSV = EVAL_DIR / "dataset" / "geography_evaluation_dataset.csv"
RESULTS_DIR = EVAL_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def calculate_iou(s1, e1, s2, e2):
    """Calculate Intersection over Union (IoU) of two 1D spans."""
    intersection = max(0, min(e1, e2) - max(s1, s2))
    union = (e1 - s1) + (e2 - s2) - intersection
    if union == 0:
        return 0.0
    return intersection / union


def match_spans(expected_spans, predicted_spans, iou_threshold=0.5):
    """Perform one-to-one greedy matching between expected and predicted spans.

    Returns:
        matched_exact: count of exact matches
        matched_partial: count of matches with IoU >= iou_threshold
    """
    if not expected_spans or not predicted_spans:
        return 0, 0

    # 1. Exact matches (start == start and end == end)
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

    # 2. Partial matches (IoU >= threshold) among remaining spans
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


def generate_svg_confusion_matrix(tp, fp, fn, tn, out_path):
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

  <!-- Title -->
  <text x="270" y="32" class="title">HalluGuard Baseline Confusion Matrix</text>
  <text x="270" y="52" class="subtitle">Model: KRLabsOrg/lettucedect-base-modernbert-en-v1 (N = 60)</text>

  <!-- Axis Headers -->
  <text x="270" y="90" class="axis-label">PREDICTED CLASS</text>
  <text x="180" y="112" class="axis-label" style="fill:#dc2626;">HALLUCINATED</text>
  <text x="360" y="112" class="axis-label" style="fill:#16a34a;">CLEAN</text>

  <!-- Row Labels -->
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

  <!-- Bottom Legend -->
  <text x="270" y="360" class="subtitle">Total Actual Hallucinated: {tp + fn} | Total Actual Clean: {fp + tn}</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_svg_category_accuracy(cat_stats, out_path):
    """Generate SVG bar chart for category-wise accuracy."""
    categories = ["supported", "contradictory", "unsupported", "mixed"]
    colors = {
        "supported": "#16a34a",
        "contradictory": "#dc2626",
        "unsupported": "#ea580c",
        "mixed": "#2563eb",
    }

    bars_svg = ""
    start_y = 90
    bar_height = 36
    gap = 48
    max_w = 320

    for i, cat in enumerate(categories):
        stats = cat_stats.get(cat, {"correct": 0, "total": 15, "acc": 0.0})
        acc = stats["acc"]
        correct = stats["correct"]
        total = stats["total"]
        width = int((acc / 100.0) * max_w)
        y = start_y + (i * gap)
        color = colors[cat]

        bars_svg += f"""
    <!-- Category {cat} -->
    <text x="140" y="{y + 22}" font-size="13" font-weight="600" fill="#334155" text-anchor="end">{cat.capitalize()}</text>
    <rect x="150" y="{y}" width="{max_w}" height="{bar_height}" rx="6" fill="#f1f5f9"/>
    <rect x="150" y="{y}" width="{width}" height="{bar_height}" rx="6" fill="{color}"/>
    <text x="{150 + width + 10}" y="{y + 23}" font-size="13" font-weight="700" fill="#1e293b">{acc:.1f}% ({correct}/{total})</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 580 320" width="580" height="320" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="290" y="35" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">Category-Wise Accuracy (N = 15 per category)</text>
  <text x="290" y="55" font-size="12" fill="#64748b" text-anchor="middle">Baseline ModernBERT Evaluation on Geography Benchmark</text>
  {bars_svg}
  <line x1="150" y1="{start_y + 4 * gap}" x2="470" y2="{start_y + 4 * gap}" stroke="#cbd5e1" stroke-width="1"/>
  <text x="150" y="{start_y + 4 * gap + 18}" font-size="11" fill="#94a3b8" text-anchor="middle">0%</text>
  <text x="310" y="{start_y + 4 * gap + 18}" font-size="11" fill="#94a3b8" text-anchor="middle">50%</text>
  <text x="470" y="{start_y + 4 * gap + 18}" font-size="11" fill="#94a3b8" text-anchor="middle">100%</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def generate_svg_latency(latencies, out_path):
    """Generate SVG chart for inference latency distribution."""
    sorted_lats = sorted(latencies)
    mean_lat = sum(sorted_lats) / len(sorted_lats)
    median_lat = sorted_lats[len(sorted_lats) // 2]
    min_lat = sorted_lats[0]
    max_lat = sorted_lats[-1]
    p95_idx = int(0.95 * len(sorted_lats))
    p95_lat = sorted_lats[p95_idx]

    # Histogram bins (5 bins)
    bin_width = (max_lat - min_lat) / 5 if max_lat > min_lat else 1.0
    bins = [0] * 5
    for l in sorted_lats:
        idx = min(4, int((l - min_lat) / bin_width))
        bins[idx] += 1

    max_bin = max(bins) if bins else 1
    bars_svg = ""
    for i, b_count in enumerate(bins):
        b_low = min_lat + i * bin_width
        b_high = b_low + bin_width
        h = int((b_count / max_bin) * 120)
        x = 90 + (i * 75)
        y = 220 - h
        bars_svg += f"""
    <rect x="{x}" y="{y}" width="60" height="{h}" rx="4" fill="#3b82f6"/>
    <text x="{x + 30}" y="{y - 6}" font-size="12" font-weight="700" fill="#1e293b" text-anchor="middle">{b_count}</text>
    <text x="{x + 30}" y="240" font-size="10" fill="#64748b" text-anchor="middle">{int(b_low)}-{int(b_high)}ms</text>
"""

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 540 320" width="540" height="320" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="270" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">CPU Inference Latency Distribution (N = 60)</text>
  <text x="270" y="52" font-size="12" fill="#64748b" text-anchor="middle">Mean: {mean_lat:.1f}ms | Median: {median_lat:.1f}ms | p95: {p95_lat:.1f}ms | Min: {min_lat:.1f}ms | Max: {max_lat:.1f}ms</text>
  {bars_svg}
  <line x1="70" y1="220" x2="480" y2="220" stroke="#cbd5e1" stroke-width="1"/>
  <text x="270" y="270" font-size="11" fill="#64748b" text-anchor="middle">Latency Bins (Milliseconds per inference on local CPU)</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    print("=" * 80)
    print("HALLUGUARD BASELINE EVALUATION EXPERIMENT — PHASE 4, STEP 3")
    print("=" * 80)
    print(f"Target Dataset:  {DATASET_CSV}")
    print(f"Results Directory:{RESULTS_DIR}\n")

    # 1. Inspect and verify dataset
    if not DATASET_CSV.exists():
        print(f"[ERROR] Dataset CSV not found: {DATASET_CSV}")
        sys.exit(1)

    dataset_rows = []
    with open(DATASET_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset_rows.append(row)

    if len(dataset_rows) != 60:
        print(f"[ERROR] Expected exactly 60 rows, found {len(dataset_rows)}.")
        sys.exit(1)

    print(f"[OK] Successfully verified dataset with {len(dataset_rows)} rows.")

    # 2. Inspect production backend service and load detector
    print("[-] Initializing production DetectorService...")
    from app.services.detector_service import detector_service
    from app.config import settings

    model_path = settings.model_path
    device = settings.device
    production_threshold = 0.0  # Production default min_confidence

    print(f"  * Model Identifier:     {model_path}")
    print(f"  * Device:               {device}")
    print(f"  * Production Threshold: min_confidence = {production_threshold}")

    t_load_start = time.perf_counter()
    if not detector_service.is_loaded:
        print("[-] Loading LettuceDetect model into memory once...")
        detector_service.load_model()
    t_load_elapsed = time.perf_counter() - t_load_start
    print(f"[OK] Model loaded and ready in {t_load_elapsed:.2f} seconds.\n")

    # 3. Execute evaluation across all 60 examples
    print(f"[-] Running baseline inference on all 60 test examples...")
    predictions = []
    latencies = []
    errors = []

    # Category tracking
    cat_correct = {"supported": 0, "contradictory": 0, "unsupported": 0, "mixed": 0}
    cat_totals = {"supported": 0, "contradictory": 0, "unsupported": 0, "mixed": 0}

    # Answer-level confusion matrix counters
    # Positive class = HALLUCINATED, Negative class = CLEAN
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    fp_cases = []
    fn_cases = []

    # Span-level counters
    total_gold_spans = 0
    total_pred_spans = 0
    total_exact_matches = 0
    total_partial_matches = 0
    total_char_intersection = 0
    total_char_pred = 0
    total_char_gold = 0

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

        pred_record = {
            "test_id": test_id,
            "category": cat,
            "expected_verdict": expected_verdict,
            "predicted_verdict": None,
            "is_correct": False,
            "question": question,
            "reference_context": context_str,
            "generated_answer": answer,
            "expected_unsupported_spans": expected_spans,
            "predicted_spans": [],
            "span_count": 0,
            "confidence_scores": [],
            "max_confidence": None,
            "prediction_message": "",
            "inference_latency_ms": 0.0,
            "error": None,
        }

        t0 = time.perf_counter()
        try:
            spans, summary, exec_time_ms = detector_service.predict(
                context=[context_str],
                answer=answer,
                question=question,
                min_confidence=production_threshold,
            )
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            latencies.append(latency_ms)

            # Extract predicted spans
            pred_spans = [
                {
                    "start": s.start,
                    "end": s.end,
                    "text": s.text,
                    "confidence": s.confidence,
                    "category": s.category,
                }
                for s in spans
            ]

            predicted_verdict = summary.verdict
            is_correct = (predicted_verdict == expected_verdict)

            pred_record["predicted_verdict"] = predicted_verdict
            pred_record["is_correct"] = is_correct
            pred_record["predicted_spans"] = pred_spans
            pred_record["span_count"] = summary.span_count
            pred_record["confidence_scores"] = [s.confidence for s in spans if s.confidence is not None]
            pred_record["max_confidence"] = summary.max_confidence
            pred_record["prediction_message"] = summary.message
            pred_record["inference_latency_ms"] = latency_ms

            if is_correct:
                cat_correct[cat] += 1

            # Update answer-level confusion matrix
            if expected_verdict == "HALLUCINATED" and predicted_verdict == "HALLUCINATED":
                tp += 1
            elif expected_verdict == "CLEAN" and predicted_verdict == "CLEAN":
                tn += 1
            elif expected_verdict == "CLEAN" and predicted_verdict == "HALLUCINATED":
                fp += 1
                fp_cases.append(test_id)
            elif expected_verdict == "HALLUCINATED" and predicted_verdict == "CLEAN":
                fn += 1
                fn_cases.append(test_id)

            # Update span-level metrics
            total_pred_spans += len(pred_spans)
            exact_m, partial_m = match_spans(expected_spans, pred_spans, iou_threshold=0.5)
            total_exact_matches += exact_m
            total_partial_matches += partial_m

            _, _, _, inter_c, p_len_c, g_len_c = calculate_char_overlap(
                expected_spans, pred_spans, len(answer)
            )
            total_char_intersection += inter_c
            total_char_pred += p_len_c
            total_char_gold += g_len_c

            status_icon = "✓" if is_correct else "✗"
            print(
                f"[{idx:02d}/60] {status_icon} {test_id} ({cat:13s}) | "
                f"Exp: {expected_verdict:12s} | Pred: {predicted_verdict:12s} | "
                f"Spans: {summary.span_count} | Latency: {latency_ms:6.1f}ms"
            )

        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            pred_record["error"] = str(e)
            pred_record["inference_latency_ms"] = latency_ms
            errors.append({"test_id": test_id, "error": str(e)})
            print(f"[{idx:02d}/60] [ERROR] {test_id}: {e}")

        predictions.append(pred_record)

    # 4. Compute metrics
    total_evaluated = len(predictions)
    successful_evaluated = total_evaluated - len(errors)
    total_correct = tp + tn

    accuracy = (total_correct / successful_evaluated) if successful_evaluated > 0 else 0.0
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    specificity = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    # Category accuracies
    category_metrics = {}
    for cat in cat_totals:
        tot = cat_totals[cat]
        corr = cat_correct[cat]
        acc = (corr / tot * 100.0) if tot > 0 else 0.0
        category_metrics[cat] = {
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

    # Latency statistics
    sorted_latencies = sorted(latencies)
    mean_lat = sum(sorted_latencies) / len(sorted_latencies) if sorted_latencies else 0.0
    median_lat = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0.0
    min_lat = sorted_latencies[0] if sorted_latencies else 0.0
    max_lat = sorted_latencies[-1] if sorted_latencies else 0.0
    p95_idx = int(math.ceil(0.95 * len(sorted_latencies))) - 1
    p95_lat = sorted_latencies[max(0, p95_idx)] if sorted_latencies else 0.0

    # 5. Save output artifacts
    # A. baseline_predictions.json
    out_json = RESULTS_DIR / "baseline_predictions.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2, ensure_ascii=False)
    print(f"\n[SAVED] {out_json}")

    # B. baseline_predictions.csv
    out_csv = RESULTS_DIR / "baseline_predictions.csv"
    csv_fields = [
        "test_id",
        "category",
        "expected_verdict",
        "predicted_verdict",
        "is_correct",
        "span_count",
        "max_confidence",
        "inference_latency_ms",
        "expected_unsupported_spans",
        "predicted_spans",
        "question",
        "reference_context",
        "generated_answer",
        "error",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for p in predictions:
            writer.writerow({
                "test_id": p["test_id"],
                "category": p["category"],
                "expected_verdict": p["expected_verdict"],
                "predicted_verdict": p["predicted_verdict"],
                "is_correct": p["is_correct"],
                "span_count": p["span_count"],
                "max_confidence": p["max_confidence"],
                "inference_latency_ms": p["inference_latency_ms"],
                "expected_unsupported_spans": json.dumps(p["expected_unsupported_spans"], ensure_ascii=False),
                "predicted_spans": json.dumps(p["predicted_spans"], ensure_ascii=False),
                "question": p["question"],
                "reference_context": p["reference_context"],
                "generated_answer": p["generated_answer"],
                "error": p["error"] or "",
            })
    print(f"[SAVED] {out_csv}")

    # C. baseline_confusion_matrix.json
    out_cm = RESULTS_DIR / "baseline_confusion_matrix.json"
    cm_data = {
        "true_positives": tp,
        "true_negatives": tn,
        "false_positives": fp,
        "false_negatives": fn,
        "positive_class": "HALLUCINATED",
        "negative_class": "CLEAN",
        "total_samples": total_evaluated,
        "false_positive_ids": fp_cases,
        "false_negative_ids": fn_cases,
    }
    with open(out_cm, "w", encoding="utf-8") as f:
        json.dump(cm_data, f, indent=2)
    print(f"[SAVED] {out_cm}")

    # D. baseline_run_summary.json
    out_summary = RESULTS_DIR / "baseline_run_summary.json"
    summary_data = {
        "model_path": model_path,
        "device": device,
        "production_threshold": production_threshold,
        "total_attempted": total_evaluated,
        "successful_predictions": successful_evaluated,
        "error_count": len(errors),
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
        "category_metrics": category_metrics,
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
            "mean": round(mean_lat, 2),
            "median": round(median_lat, 2),
            "min": round(min_lat, 2),
            "max": round(max_lat, 2),
            "p95": round(p95_lat, 2),
        },
        "false_positive_cases": fp_cases,
        "false_negative_cases": fn_cases,
    }
    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"[SAVED] {out_summary}")

    # E. Visualizations
    cm_svg_path = RESULTS_DIR / "confusion_matrix.svg"
    generate_svg_confusion_matrix(tp, fp, fn, tn, cm_svg_path)
    print(f"[SAVED] {cm_svg_path}")

    cat_svg_path = RESULTS_DIR / "category_accuracy.svg"
    cat_plot_stats = {
        cat: {
            "correct": category_metrics[cat]["correct"],
            "total": category_metrics[cat]["total"],
            "acc": category_metrics[cat]["accuracy_percent"],
        }
        for cat in category_metrics
    }
    generate_svg_category_accuracy(cat_plot_stats, cat_svg_path)
    print(f"[SAVED] {cat_svg_path}")

    lat_svg_path = RESULTS_DIR / "latency_distribution.svg"
    generate_svg_latency(latencies, lat_svg_path)
    print(f"[SAVED] {lat_svg_path}")

    # Print summary report to stdout
    print("\n" + "=" * 80)
    print("BASELINE EVALUATION RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Examples Attempted:  {total_evaluated} / 60 (Coverage: 100.0%)")
    print(f"Inference Errors:          {len(errors)}")
    print(f"Overall Accuracy:          {accuracy * 100:.2f}% ({total_correct}/{successful_evaluated})")
    print(f"Precision (Positive=HALL): {precision * 100:.2f}%")
    print(f"Recall (Sensitivity):      {recall * 100:.2f}%")
    print(f"Specificity:               {specificity * 100:.2f}%")
    print(f"F1-Score:                  {f1 * 100:.2f}%\n")

    print(f"Confusion Matrix:")
    print(f"  TP: {tp:2d} (Hallucinations correctly flagged)")
    print(f"  TN: {tn:2d} (Clean answers correctly verified)")
    print(f"  FP: {fp:2d} (Clean answers incorrectly flagged as hallucinated)")
    print(f"  FN: {fn:2d} (Hallucinations missed as clean)\n")

    print(f"Category Breakdown:")
    for cat, m in category_metrics.items():
        print(f"  - {cat.capitalize():14s}: {m['correct']:2d} / {m['total']:2d} ({m['accuracy_percent']:.1f}%)")

    print(f"\nSpan-Level Localization:")
    print(f"  - Total Gold Spans:      {total_gold_spans}")
    print(f"  - Total Predicted Spans: {total_pred_spans}")
    print(f"  - Exact Match F1:        {span_exact_f1 * 100:.2f}% (P: {span_exact_precision*100:.1f}%, R: {span_exact_recall*100:.1f}%)")
    print(f"  - Partial IoU>=0.5 F1:   {span_partial_f1 * 100:.2f}% (P: {span_partial_precision*100:.1f}%, R: {span_partial_recall*100:.1f}%)")
    print(f"  - Character Overlap F1:  {char_f1 * 100:.2f}% (P: {char_precision*100:.1f}%, R: {char_recall*100:.1f}%)")

    print(f"\nLatency Performance (CPU):")
    print(f"  - Mean:   {mean_lat:.1f} ms")
    print(f"  - Median: {median_lat:.1f} ms")
    print(f"  - p95:    {p95_lat:.1f} ms")
    print(f"  - Min:    {min_lat:.1f} ms")
    print(f"  - Max:    {max_lat:.1f} ms")

    if fp_cases:
        print(f"\nFalse Positive IDs (Type I error): {', '.join(fp_cases)}")
    if fn_cases:
        print(f"False Negative IDs (Type II error): {', '.join(fn_cases)}")
    print("=" * 80)


if __name__ == "__main__":
    main()

