# HalluGuard — Evaluation Framework & Methodology

## 1. Overview and Objectives

This directory contains the independent evaluation framework for **HalluGuard**, an AI-powered hallucination detection system leveraging the pretrained LettuceDetect ModernBERT model (`KRLabsOrg/lettucedect-base-modernbert-en-v1`).

The evaluation framework is designed to provide:
1. **Objective Quality Assurance:** Rigorous, repeatable measurement of model accuracy and span localization capabilities without data leakage.
2. **Category-Specific Diagnostic Insight:** Fine-grained analysis across supported, contradictory, unsupported, and mixed claims.
3. **Dual-Level Metric Tracking:** Simultaneous assessment at both the coarse answer level (verdict classification) and the granular span level (token/character offset localization).
4. **Baseline Preservation:** Safe, decoupled evaluation that leaves production inference routines and model weights completely untouched.

---

## 2. Directory Architecture

```
evaluation/
├── dataset/
│   ├── ANNOTATION_GUIDE.md               # Rigorous guidelines for ground-truth annotation
│   └── evaluation_dataset_template.csv   # Labelled dataset template (10-column schema)
├── scripts/                              # (Phase 4, Step 3) Automated evaluation runners
├── results/                              # (Phase 4, Step 4) Raw JSON and CSV inference outputs
├── reports/                              # (Phase 4, Step 5) Final analytical evaluation reports
├── PHASE_4_STEP_1_REPORT.md             # Formal milestone report for Step 1
└── README.md                             # This documentation file
```

---

## 3. Dataset Composition and Domain Strategy

### 3.1 Domain: Physical and Human Geography
The initial benchmark focuses on **Geography**, chosen for several methodological advantages:
- **High Factual Stability:** Physical landforms, tectonic plates, coordinates, historical treaties, and municipal capitals do not fluctuate day-to-day.
- **Authoritative Ground Truth:** Backed by globally trusted institutions (NASA, USGS, UN Geospatial, UNESCO, National Geographic).
- **Reduced Ambiguity:** Geographical claims typically feature unambiguous entity relations and measurable quantities (elevation, area, length), allowing clear-cut human ground-truth annotation.

### 3.2 Category Distribution (Target: 60 Samples)
The benchmark is evenly balanced with **15 samples per quadrant** to prevent class imbalance biases:

```
Total Benchmark Size: 60 Samples
├── Supported Claims:      15 samples (25%) -> Ground Truth: CLEAN
├── Contradictory Claims:  15 samples (25%) -> Ground Truth: HALLUCINATED
├── Unsupported Claims:    15 samples (25%) -> Ground Truth: HALLUCINATED
└── Mixed Claims:          15 samples (25%) -> Ground Truth: HALLUCINATED
```

### 3.3 Category Descriptions
1. **`supported` (Clean):** The answer makes claims that are completely grounded in and entailed by the reference context.
2. **`contradictory` (Intrinsic Hallucination):** The answer makes assertions that directly conflict with facts provided in the reference context.
3. **`unsupported` (Extrinsic Hallucination):** The answer introduces claims absent from the reference context. (Even if true in the external physical world, the claim is ungrounded relative to the reference).
4. **`mixed` (Partial Hallucination):** The answer contains a mix of supported propositions and one or more hallucinated (contradictory or unsupported) propositions.

---

## 4. Evaluation Metrics Formulation

Evaluation operates at two distinct tiers: **Answer-Level Classification** and **Span-Level Localization**.

### 4.1 Answer-Level Classification Metrics
In safety-critical hallucination detection, **positive class = HALLUCINATED** (flagged as anomalous), and **negative class = CLEAN** (supported).

- **True Positive (TP):** Ground truth is `HALLUCINATED`, model predicts `HALLUCINATED` (`is_hallucinated=True`).
- **False Positive (FP):** Ground truth is `CLEAN`, model predicts `HALLUCINATED` (`is_hallucinated=True`) — *Type I error (False alarm)*.
- **True Negative (TN):** Ground truth is `CLEAN`, model predicts `CLEAN` (`is_hallucinated=False`).
- **False Negative (FN):** Ground truth is `HALLUCINATED`, model predicts `CLEAN` (`is_hallucinated=False`) — *Type II error (Missed hallucination; highest risk)*.

#### Formulas:
$$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$

$$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$$

$$\text{Recall (Sensitivity)} = \frac{\text{TP}}{\text{TP} + \text{FN}}$$

$$\text{Specificity} = \frac{\text{TN}}{\text{TN} + \text{FP}}$$

$$\text{F1-Score} = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

### 4.2 Span-Level Localization Metrics
Detecting that an answer is hallucinated is necessary, but pinpointing the exact hallucinated substring is crucial for interpretability and user trust.

1. **Exact Match (EM):**
   A predicted span $[s_{\text{pred}}, e_{\text{pred}}]$ is considered an Exact Match if and only if:
   $$s_{\text{pred}} = s_{\text{gold}} \quad \text{and} \quad e_{\text{pred}} = e_{\text{gold}}$$

2. **Partial Overlap / Intersection over Union (IoU):**
   For character-level spans:
   $$\text{IoU}(S_{\text{pred}}, S_{\text{gold}}) = \frac{|S_{\text{pred}} \cap S_{\text{gold}}|}{|S_{\text{pred}} \cup S_{\text{gold}}|}$$
   A predicted span is counted as a partial hit if $\text{IoU} \ge 0.5$.

3. **Span Token F1:**
   Token-level precision, recall, and F1 calculated over the set of character positions or word tokens flagged as hallucinated vs. gold ground truth.

### 4.3 Efficiency & Latency Metrics
- **Mean Inference Time (ms):** Average end-to-end latency per sample.
- **95th Percentile Latency (p95):** Latency threshold below which 95% of queries execute.
- **Min / Max Latency:** Range of CPU inference timings.

---

## 5. Methodological Safeguards & Limitations

### 5.1 Dataset Independence and Anti-Leakage Protocol
- The 60-sample evaluation dataset is strictly a **test-only benchmark**.
- **No Threshold Tuning on Test Data:** If threshold tuning (e.g. optimizing `min_confidence`) is performed in future experiments, a distinct validation split must be employed. The test set will remain frozen to prevent overfitted performance claims.

### 5.2 Technical & Conceptual Limitations
1. **Closed-Context Scope:** The evaluation tests grounding *strictly against the supplied context*. It does not evaluate open-domain general knowledge retrieval.
2. **Context Length Truncation:** LettuceDetect ModernBERT operates with a maximum token sequence length (typically 512 tokens). If context passages exceed this length without prior chunking, text may be truncated during token classification.
3. **Paraphrase Sensitivity:** Natural language variations where an answer is semantically equivalent to the reference context using different vocabulary may trigger subtle boundary shifts in token classification.

---

## 6. Execution Roadmap for Phase 4

| Phase 4 Step | Status | Key Deliverables |
| :--- | :--- | :--- |
| **Step 1: Framework Preparation** | **COMPLETED** | Directory structure, 10-column CSV template, annotation guide, README methodology, Step 1 report |
| **Step 2: Dataset Curation** | Next | Curate 60 validated geographic samples (15 per category) with verified source URLs |
| **Step 3: Evaluation Harness** | Pending | Automated Python runner script computing answer- and span-level metrics |
| **Step 4: Inference & Benchmark Execution** | Pending | Execute benchmark against live detector backend, generate raw JSON/CSV results |
| **Step 5: Quality Assurance Report** | Pending | Detailed performance analysis, confusion matrix visualization, error breakdown |

