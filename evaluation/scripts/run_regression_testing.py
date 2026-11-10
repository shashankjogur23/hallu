"""Regression Testing Suite for HalluGuard Phase 8 Step 4.

Executes regression evaluation using the refined NLI hybrid system across:
1. Original 60-example benchmark (geography_evaluation_dataset.csv)
2. 100-example benchmark (independent_geography_dataset.csv) [labeled as post-fix regression]

Outputs comprehensive metrics, confusion matrices, span metrics, latencies,
memory footprint, and visual comparison charts.
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

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

EVAL_DIR = ROOT_DIR / "evaluation"
SCRIPTS_DIR = EVAL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

DATASET_60 = EVAL_DIR / "dataset" / "geography_evaluation_dataset.csv"
DATASET_100 = EVAL_DIR / "dataset" / "independent_geography_dataset.csv"
RESULTS_DIR = EVAL_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

from app.services.detector_service import detector_service
from nli_service import nli_service

try:
    import psutil
except ImportError:
    psutil = None


def calculate_iou(s1, e1, s2, e2):
    intersection = max(0, min(e1, e2) - max(s1, s2))
    union = (e1 - s1) + (e2 - s2) - intersection
    return (intersection / union) if union > 0 else 0.0


def match_spans(expected_spans, predicted_spans, iou_threshold=0.5):
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


def evaluate_dataset(dataset_path: Path, label: str):
    """Evaluates the hybrid pipeline over a specified dataset."""
    print(f"\n[-] Running Regression Evaluation on {label}: {dataset_path} ...")
    
    rows = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    predictions = []
    latencies_lettuce = []
    latencies_nli = []
    latencies_total = []

    cat_stats = {
        c: {"total": 0, "correct": 0}
        for c in ["supported", "contradictory", "unsupported", "mixed"]
    }

    tp, fp, tn, fn = 0, 0, 0, 0
    fp_cases, fn_cases, salvaged_cases = [], [], []

    gold_spans_total = 0
    pred_spans_total = 0
    exact_matches = 0
    partial_matches = 0
    char_inter = 0
    char_pred = 0
    char_gold = 0

    for idx, row in enumerate(rows, start=1):
        test_id = row["test_id"]
        cat = row["category"]
        expected_verdict = row["expected_verdict"]
        question = row["question"]
        context_str = row["reference_context"]
        answer = row["generated_answer"]
        expected_spans = json.loads(row["expected_unsupported_spans"])

        cat_stats[cat]["total"] += 1
        gold_spans_total += len(expected_spans)

        # 1. LettuceDetect Pass
        t_let = time.perf_counter()
        let_spans_raw, let_summary, _ = detector_service.predict(
            context=[context_str],
            answer=answer,
            question=question,
            min_confidence=0.0,
        )
        let_latency = round((time.perf_counter() - t_let) * 1000, 2)
        latencies_lettuce.append(let_latency)

        let_verdict = let_summary.verdict
        let_spans = [
            {
                "start": s.start,
                "end": s.end,
                "text": s.text,
                "confidence": s.confidence,
                "category": s.category,
                "source": "lettucedetect",
            }
            for s in let_spans_raw
        ]

        # 2. Refined NLI Pass
        t_nli = time.perf_counter()
        nli_res = nli_service.analyze_answer(
            context=context_str,
            answer=answer,
            question=question,
        )
        nli_latency = round((time.perf_counter() - t_nli) * 1000, 2)
        latencies_nli.append(nli_latency)

        tot_lat = round(let_latency + nli_latency, 2)
        latencies_total.append(tot_lat)

        # 3. Decision Fusion
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
            salvaged_cases.append(test_id)
        else:
            hybrid_verdict = "CLEAN"
            hybrid_spans = []
            fusion_source = "unanimous_clean"

        is_correct = (hybrid_verdict == expected_verdict)
        if is_correct:
            cat_stats[cat]["correct"] += 1

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

        # Span Metrics
        pred_spans_total += len(hybrid_spans)
        ex_m, part_m = match_spans(expected_spans, hybrid_spans, iou_threshold=0.5)
        exact_matches += ex_m
        partial_matches += part_m

        _, _, _, inter_c, p_len_c, g_len_c = calculate_char_overlap(
            expected_spans, hybrid_spans, len(answer)
        )
        char_inter += inter_c
        char_pred += p_len_c
        char_gold += g_len_c

        record = {
            "test_id": test_id,
            "category": cat,
            "expected_verdict": expected_verdict,
            "baseline_verdict": let_verdict,
            "hybrid_verdict": hybrid_verdict,
            "is_correct": is_correct,
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
                "lettucedetect_ms": let_latency,
                "nli_ms": nli_latency,
                "total_ms": tot_lat,
            },
        }
        predictions.append(record)

    total = len(rows)
    acc = (tp + tn) / total
    prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
    spec = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

    for c in cat_stats:
        tot_c = cat_stats[c]["total"]
        cat_stats[c]["accuracy_percent"] = round(cat_stats[c]["correct"] / tot_c * 100.0, 2) if tot_c > 0 else 0.0

    ex_p = (exact_matches / pred_spans_total) if pred_spans_total > 0 else 0.0
    ex_r = (exact_matches / gold_spans_total) if gold_spans_total > 0 else 0.0
    ex_f1 = (2 * ex_p * ex_r / (ex_p + ex_r)) if (ex_p + ex_r) > 0 else 0.0

    part_p = (partial_matches / pred_spans_total) if pred_spans_total > 0 else 0.0
    part_r = (partial_matches / gold_spans_total) if gold_spans_total > 0 else 0.0
    part_f1 = (2 * part_p * part_r / (part_p + part_r)) if (part_p + part_r) > 0 else 0.0

    ch_p = (char_inter / char_pred) if char_pred > 0 else 0.0
    ch_r = (char_inter / char_gold) if char_gold > 0 else 0.0
    ch_f1 = (2 * ch_p * ch_r / (ch_p + ch_r)) if (ch_p + ch_r) > 0 else 0.0

    def get_lat_stats(lats):
        sl = sorted(lats)
        return {
            "mean": round(sum(sl) / len(sl), 2),
            "median": round(sl[len(sl) // 2], 2),
            "min": round(sl[0], 2),
            "max": round(sl[-1], 2),
            "p95": round(sl[int(math.ceil(0.95 * len(sl))) - 1], 2),
        }

    process = psutil.Process() if psutil else None
    mem_mb = round(process.memory_info().rss / (1024 * 1024), 2) if process else 0.0

    summary = {
        "dataset_label": label,
        "dataset_path": str(dataset_path),
        "total_samples": total,
        "answer_level_metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "specificity": round(spec, 4),
            "f1_score": round(f1, 4),
        },
        "confusion_matrix": {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
        },
        "category_metrics": cat_stats,
        "span_level_metrics": {
            "total_gold_spans": gold_spans_total,
            "total_predicted_spans": pred_spans_total,
            "exact_match": {
                "matched_count": exact_matches,
                "precision": round(ex_p, 4),
                "recall": round(ex_r, 4),
                "f1_score": round(ex_f1, 4),
            },
            "partial_overlap_iou_0_5": {
                "matched_count": partial_matches,
                "precision": round(part_p, 4),
                "recall": round(part_r, 4),
                "f1_score": round(part_f1, 4),
            },
            "character_overlap": {
                "precision": round(ch_p, 4),
                "recall": round(ch_r, 4),
                "f1_score": round(ch_f1, 4),
            },
        },
        "latency_metrics_ms": {
            "lettucedetect": get_lat_stats(latencies_lettuce),
            "nli_verifier": get_lat_stats(latencies_nli),
            "hybrid_total": get_lat_stats(latencies_total),
        },
        "memory_rss_mb": mem_mb,
        "salvaged_cases": salvaged_cases,
        "false_positive_cases": fp_cases,
        "false_negative_cases": fn_cases,
    }

    print(f"[{label} Results] Accuracy: {acc*100:.2f}%, Recall: {rec*100:.2f}%, Precision: {prec*100:.2f}%, F1: {f1*100:.2f}%")
    print(f"  TP: {tp}, TN: {tn}, FP: {fp}, FN: {fn}")
    print(f"  FP Cases: {fp_cases}")
    print(f"  FN Cases: {fn_cases}")

    return predictions, summary


def generate_svg_regression_comparison(s60, s100, out_path):
    """Generate SVG comparison chart for regression testing."""
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 360" width="600" height="360" style="background:#ffffff; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <text x="300" y="32" font-size="16" font-weight="700" fill="#1e293b" text-anchor="middle">Phase 8 Step 4: Regression Test Performance</text>
  <text x="300" y="52" font-size="12" fill="#64748b" text-anchor="middle">Refined NLI Hybrid on Baseline 60 &amp; Independent 100 Datasets</text>

  <!-- Legend -->
  <rect x="180" y="70" width="14" height="14" rx="2" fill="#3b82f6"/>
  <text x="200" y="82" font-size="11" fill="#1e40af">Original 60 Benchmark</text>
  <rect x="330" y="70" width="14" height="14" rx="2" fill="#10b981"/>
  <text x="350" y="82" font-size="11" fill="#065f46">100 Independent Benchmark (Post-Fix)</text>

  <!-- Bars for Accuracy, Precision, Recall, Specificity, F1 -->
  <!-- Accuracy -->
  <text x="120" y="125" font-size="12" font-weight="600" fill="#334155" text-anchor="end">Accuracy</text>
  <rect x="130" y="110" width="{int(s60['answer_level_metrics']['accuracy']*300)}" height="15" rx="3" fill="#3b82f6"/>
  <text x="{130 + int(s60['answer_level_metrics']['accuracy']*300) + 6}" y="122" font-size="11" fill="#1e40af">{s60['answer_level_metrics']['accuracy']*100:.1f}%</text>
  <rect x="130" y="128" width="{int(s100['answer_level_metrics']['accuracy']*300)}" height="15" rx="3" fill="#10b981"/>
  <text x="{130 + int(s100['answer_level_metrics']['accuracy']*300) + 6}" y="140" font-size="11" fill="#065f46">{s100['answer_level_metrics']['accuracy']*100:.1f}%</text>

  <!-- Precision -->
  <text x="120" y="175" font-size="12" font-weight="600" fill="#334155" text-anchor="end">Precision</text>
  <rect x="130" y="160" width="{int(s60['answer_level_metrics']['precision']*300)}" height="15" rx="3" fill="#3b82f6"/>
  <text x="{130 + int(s60['answer_level_metrics']['precision']*300) + 6}" y="172" font-size="11" fill="#1e40af">{s60['answer_level_metrics']['precision']*100:.1f}%</text>
  <rect x="130" y="178" width="{int(s100['answer_level_metrics']['precision']*300)}" height="15" rx="3" fill="#10b981"/>
  <text x="{130 + int(s100['answer_level_metrics']['precision']*300) + 6}" y="190" font-size="11" fill="#065f46">{s100['answer_level_metrics']['precision']*100:.1f}%</text>

  <!-- Recall -->
  <text x="120" y="225" font-size="12" font-weight="600" fill="#334155" text-anchor="end">Recall</text>
  <rect x="130" y="210" width="{int(s60['answer_level_metrics']['recall']*300)}" height="15" rx="3" fill="#3b82f6"/>
  <text x="{130 + int(s60['answer_level_metrics']['recall']*300) + 6}" y="222" font-size="11" fill="#1e40af">{s60['answer_level_metrics']['recall']*100:.1f}%</text>
  <rect x="130" y="228" width="{int(s100['answer_level_metrics']['recall']*300)}" height="15" rx="3" fill="#10b981"/>
  <text x="{130 + int(s100['answer_level_metrics']['recall']*300) + 6}" y="240" font-size="11" fill="#065f46">{s100['answer_level_metrics']['recall']*100:.1f}%</text>

  <!-- F1-Score -->
  <text x="120" y="275" font-size="12" font-weight="600" fill="#334155" text-anchor="end">F1-Score</text>
  <rect x="130" y="260" width="{int(s60['answer_level_metrics']['f1_score']*300)}" height="15" rx="3" fill="#3b82f6"/>
  <text x="{130 + int(s60['answer_level_metrics']['f1_score']*300) + 6}" y="272" font-size="11" fill="#1e40af">{s60['answer_level_metrics']['f1_score']*100:.1f}%</text>
  <rect x="130" y="278" width="{int(s100['answer_level_metrics']['f1_score']*300)}" height="15" rx="3" fill="#10b981"/>
  <text x="{130 + int(s100['answer_level_metrics']['f1_score']*300) + 6}" y="290" font-size="11" fill="#065f46">{s100['answer_level_metrics']['f1_score']*100:.1f}%</text>

  <line x1="130" y1="310" x2="430" y2="310" stroke="#cbd5e1" stroke-width="1"/>
  <text x="130" y="325" font-size="10" fill="#94a3b8" text-anchor="middle">0%</text>
  <text x="280" y="325" font-size="10" fill="#94a3b8" text-anchor="middle">50%</text>
  <text x="430" y="325" font-size="10" fill="#94a3b8" text-anchor="middle">100%</text>
</svg>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    print("=" * 80)
    print("HALLUGUARD PHASE 8, STEP 4: REGRESSION TESTING SUITE")
    print("=" * 80)

    # Ensure models loaded
    if not detector_service.is_loaded:
        detector_service.load_model()
    if not nli_service.is_loaded:
        nli_service.load_model()

    # 1. Evaluate 60 Benchmark
    preds_60, sum_60 = evaluate_dataset(DATASET_60, "Original 60 Benchmark")
    out_p60 = RESULTS_DIR / "regression_baseline60_predictions.json"
    with open(out_p60, "w", encoding="utf-8") as f:
        json.dump(preds_60, f, indent=2, ensure_ascii=False)
    out_s60 = RESULTS_DIR / "regression_baseline60_summary.json"
    with open(out_s60, "w", encoding="utf-8") as f:
        json.dump(sum_60, f, indent=2)

    # 2. Evaluate 100 Benchmark (Post-Fix Regression)
    preds_100, sum_100 = evaluate_dataset(DATASET_100, "100 Independent Benchmark (Post-Fix Regression)")
    out_p100 = RESULTS_DIR / "regression_100_predictions.json"
    with open(out_p100, "w", encoding="utf-8") as f:
        json.dump(preds_100, f, indent=2, ensure_ascii=False)
    out_s100 = RESULTS_DIR / "regression_100_summary.json"
    with open(out_s100, "w", encoding="utf-8") as f:
        json.dump(sum_100, f, indent=2)

    # 3. Generate Comparison Chart
    svg_comp = RESULTS_DIR / "regression_comparison.svg"
    generate_svg_regression_comparison(sum_60, sum_100, svg_comp)
    print(f"\n[SAVED] {svg_comp}")

    print("\n" + "=" * 80)
    print("REGRESSION TESTING COMPLETED SUCCESSFULLY")
    print("=" * 80)


if __name__ == "__main__":
    main()

