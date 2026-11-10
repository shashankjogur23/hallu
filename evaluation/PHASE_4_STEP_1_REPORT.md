# HalluGuard — Phase 4, Step 1: Evaluation Framework Preparation Report

**Date:** 2026-11-10  
**Phase:** Phase 4 — Evaluation and Quality Assurance (Step 1: Framework Preparation)  
**Status:** Successfully Completed  
**Model Under Evaluation:** `KRLabsOrg/lettucedect-base-modernbert-en-v1` (CPU inference)

---

## 1. Executive Summary

Phase 4, Step 1 of the **HalluGuard** project has been successfully executed. An independent, scientifically rigorous evaluation framework has been designed and set up in `F:\final project\HalluGuard\evaluation`. 

All production components—including the backend API, detector service, inference configuration, thresholds, and model weights—have been inspected in full and remain **strictly unaltered**. The evaluation benchmark is fully decoupled from production serving logic to prevent evaluation contamination and test set leakage.

---

## 2. Comprehensive Codebase & Interface Inspection

Prior to establishing the evaluation assets, the production backend was inspected directly to verify interface contracts:

### 2.1 Backend Verification Endpoint
- **Source File:** [`backend/app/api/verification.py`](file:///f:/final%20project/HalluGuard/backend/app/api/verification.py#L30-L85)
- **Endpoint:** `POST /verify` (Status: `200 OK`)
- **Lifecycle & Model Verification:** Confirmed that `detector_service.is_loaded` is checked before processing; returns `503 Service Unavailable` if the model has not completed its startup loading sequence.
- **Payload Handling:** Transparently converts single-string contexts or arrays into a clean `list[str]`. Captures end-to-end execution time in milliseconds and persists session history.

### 2.2 Detector Service
- **Source File:** [`backend/app/services/detector_service.py`](file:///f:/final%20project/HalluGuard/backend/app/services/detector_service.py#L19-L182)
- **Model Loading:** `DetectorService.load_model()` loads `KRLabsOrg/lettucedect-base-modernbert-en-v1` once via `app/main.py` lifespan events on device `cpu`.
- **Inference Invocation:**
  ```python
  raw_predictions = self._detector.predict(
      context=context,
      question=question,
      answer=answer,
      output_format="spans",
      min_confidence=min_confidence,
  )
  ```
- **Span Extraction:** Each item in `raw_predictions` is converted into a `HallucinationSpan(start=..., end=..., text=..., confidence=..., category=...)`.
- **Summary Verdict:** 
  - If `span_count > 0` $\rightarrow$ `verdict = "HALLUCINATED"`, `is_hallucinated = True`.
  - If `span_count == 0` $\rightarrow$ `verdict = "CLEAN"`, `is_hallucinated = False`.

### 2.3 Pydantic Data Contracts
- **Source File:** [`backend/app/schemas/verification.py`](file:///f:/final%20project/HalluGuard/backend/app/schemas/verification.py#L7-L102)
- **Request (`VerificationRequest`):**
  - `question: str | None = None`
  - `answer: str` (min length 1, whitespace-checked)
  - `context: list[str] | str` (validated to at least one non-empty string)
  - `min_confidence: float = 0.0` ($0.0 \le c \le 1.0$)
- **Span (`HallucinationSpan`):**
  - `start: int`: 0-indexed character offset matching `answer[start:end]`
  - `end: int`: exclusive character end offset
  - `text: str`: substring `answer[start:end]`
  - `confidence: float | None`: aggregated token probability ($0.0$ to $1.0$)
  - `category: str | None`: taxonomy category if assigned
- **Summary (`VerificationSummary`):**
  - `is_hallucinated: bool`
  - `span_count: int`
  - `max_confidence: float | None`
  - `verdict: str` (`"CLEAN"` or `"HALLUCINATED"`)
  - `message: str`

### 2.4 Document and Retrieval Services
- **Document Ingestion:** [`backend/app/services/document_service.py`](file:///f:/final%20project/HalluGuard/backend/app/services/document_service.py) provides PyMuPDF-based text extraction from PDF and plain TXT, with chunking supporting sentence-boundary-preserving overlap.
- **Context Retrieval:** [`backend/app/services/retrieval_service.py`](file:///f:/final%20project/HalluGuard/backend/app/services/retrieval_service.py) utilizes scikit-learn TF-IDF vectorization with cosine similarity scoring for query-focused passage extraction.

---

## 3. Evaluation Directory Structure

The evaluation workspace has been structured at `F:\final project\HalluGuard\evaluation`:

```
evaluation/
├── dataset/
│   ├── ANNOTATION_GUIDE.md               # Human ground-truth labelling guidelines
│   └── evaluation_dataset_template.csv   # 10-column RFC 4180 CSV dataset template
├── scripts/                              # Directory for automated evaluation runner scripts
├── results/                              # Directory for raw JSON/CSV inference run logs
├── reports/                              # Directory for analytical performance reports
├── PHASE_4_STEP_1_REPORT.md             # This milestone preparation report
└── README.md                             # Comprehensive evaluation methodology and metrics
```

---

## 4. Evaluation Dataset Template & Schema

The dataset template has been created at:  
[`evaluation/dataset/evaluation_dataset_template.csv`](file:///f:/final%20project/HalluGuard/evaluation/dataset/evaluation_dataset_template.csv)

### 4.1 Schema Definition (10 Columns)
1. `test_id`: Unique identifier formatted as `GEO-[SUP|CON|UNS|MIX]-XXX`
2. `category`: Ground-truth category (`supported`, `contradictory`, `unsupported`, `mixed`)
3. `question`: Query or contextual prompt
4. `reference_context`: Verifiable reference context text
5. `generated_answer`: Synthetic or model-generated candidate response
6. `expected_verdict`: Target verdict (`CLEAN` or `HALLUCINATED`)
7. `expected_unsupported_spans`: JSON string array of ground-truth spans (`[{"start": int, "end": int, "text": str}]`)
8. `source_name`: Reputable geographical authority (e.g., NASA Earth Observatory, USGS)
9. `source_url`: Verifiable authoritative URL
10. `annotation_notes`: Methodological notes and rationale for ground-truth classification

### 4.2 Representative Template Rows
The template includes four canonical, verified reference rows illustrating exact syntax and mathematically verified character offsets:

| test_id | category | expected_verdict | expected_unsupported_spans | source_name |
| :--- | :--- | :--- | :--- | :--- |
| `GEO-SUP-001` | `supported` | `CLEAN` | `[]` | NASA Earth Observatory |
| `GEO-CON-001` | `contradictory` | `HALLUCINATED` | `[{"start": 28, "end": 44, "text": "the Amazon River"}]` | USGS Water Science School |
| `GEO-UNS-001` | `unsupported` | `HALLUCINATED` | `[{"start": 52, "end": 105, "text": "and was declared a UNESCO World Heritage Site in 1996"}]` | UNESCO World Heritage Centre |
| `GEO-MIX-001` | `mixed` | `HALLUCINATED` | `[{"start": 44, "end": 89, "text": "Melbourne is the country's most populous city"}]` | Geoscience Australia |

---

## 5. Annotation Protocol & Ground-Truth Rules

The annotation guide has been created at:  
[`evaluation/dataset/ANNOTATION_GUIDE.md`](file:///f:/final%20project/HalluGuard/evaluation/dataset/ANNOTATION_GUIDE.md)

### Key Methodological Safeguards:
1. **Model Independence:** Human ground-truth must be annotated strictly by comparing the answer against the reference context, without consulting the detector or viewing model predictions.
2. **Closed-Context Truth:** An answer statement absent from the reference context must be classified as `unsupported` (extrinsic hallucination), regardless of whether it is true in the external physical world.
3. **Contradiction vs. Unsupported:** Contradictions explicitly conflict with facts stated in the context; unsupported claims introduce facts not mentioned in the context.
4. **Minimal Span Principle:** Spans must isolate the minimal semantic unit causing the invalidity, excluding surrounding valid text and trailing punctuation.
5. **Programmatic Offset Verification:** All ground-truth span indices must satisfy `answer[start:end] == text`.

---

## 6. Evaluation Methodology and Metrics Plan

Documented in detail in [`evaluation/README.md`](file:///f:/final%20project/HalluGuard/evaluation/README.md):

### 6.1 Answer-Level Classification
- **Positive Class:** `HALLUCINATED` (flagged)
- **Negative Class:** `CLEAN` (supported)
- **Metrics:** Accuracy, Precision, Recall (Sensitivity), Specificity, F1-Score, Confusion Matrix ($TP, FP, TN, FN$).

### 6.2 Span-Level Localization
- **Exact Match (EM) F1:** Precision and recall where $s_{\text{pred}} = s_{\text{gold}}$ and $e_{\text{pred}} = e_{\text{gold}}$.
- **Partial Overlap (IoU $\ge 0.5$):** Precision and recall for intersecting character spans.
- **Character/Token Overlap F1:** Granular token-level coverage.

### 6.3 Anti-Leakage Assurance
The 60-example evaluation benchmark is strictly designated as a test set. No model threshold tuning or prompt engineering will be performed on this benchmark.

---

## 7. Baseline Preservation Confirmation

- **LettuceDetect Package:** Untouched at `f:\final project\LettuceDetect` (version `0.2.3`).
- **Model Checkpoint:** Untouched at HuggingFace hub cache (`KRLabsOrg/lettucedect-base-modernbert-en-v1`).
- **Backend Code:** No changes to `backend/app/services/detector_service.py`, `backend/app/api/verification.py`, or threshold settings (`min_confidence=0.0`).
- **Test Integrity:** All 24 backend test suites pass with identical baseline behavior.

---

## 8. Next Steps (Phase 4, Step 2)

With the evaluation framework, template, and annotation guide in place, the project is ready for **Phase 4, Step 2: Benchmark Dataset Collection & Curation**, which will populate the 60 balanced geography samples across all four categories following the established annotation guide.

