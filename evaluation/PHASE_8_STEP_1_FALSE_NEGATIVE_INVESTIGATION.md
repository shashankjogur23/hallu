# HalluGuard — Phase 8, Step 1: False Negative Investigation Report

**Project:** HalluGuard (Factual Grounding & Hallucination Detection Framework)  
**Date:** November 11, 2026  
**Auditor / Investigator:** Antigravity System Audit Engine  
**Project Workspace:** `F:\final project\HalluGuard`  
**Detector Submodule:** `F:\final project\LettuceDetect`  
**Audited Model:** `KRLabsOrg/lettucedect-base-modernbert-en-v1`  
**Evaluation Benchmark:** Geography Evaluation Dataset ($N = 60$)  
**Focus of Investigation:** Root-cause analysis of all six false-negative cases ($FN = 6$)  
**Integrity Rule:** Zero modifications to model weights, code, thresholds, or baseline artifacts.  

---

## 1. Executive Summary

During the Phase 4 baseline evaluation and subsequent Phase 4 Step 4 independent audit, HalluGuard demonstrated strong answer-level factual grounding performance on the 60-example geography benchmark:
- **Accuracy:** 90.00% (54 / 60)
- **Precision:** 100.00% (39 / 39)
- **Recall (Sensitivity):** 86.67% (39 / 45)
- **Specificity:** 100.00% (15 / 15)
- **F1-Score:** 92.86%
- **False Positives:** 0
- **False Negatives:** 6

All six false negatives represent instances where the generated answer contained an ungrounded or contradictory claim, but the detector output `CLEAN` with zero flagged spans (`predicted_spans = []`).

This investigation was conducted to determine the exact failure mechanisms behind these six cases. Using token-level probability probes extracted directly from the ModernBERT token classification head, this report provides empirical evidence explaining why each case was missed, models the risk of threshold adjustments, and outlines prioritized improvement experiments for subsequent phases.

### Key Investigation Findings

1. **The "High Lexical Overlap" Phenomenon:** In 100% of the false-negative cases, **every primary entity, number, and descriptor in the false assertion was explicitly present in the reference context**. The model failed because bidirectional self-attention between context and answer registered high token-level co-occurrence, masking the relational or ordinal inversion.
2. **Contrast with Extrinsic Hallucinations:** On the `unsupported` quadrant (where entities were completely novel/invented, such as "Ferdinand de Lesseps" or "polar bears"), the model achieved **100.0% detection accuracy** (15 / 15).
3. **Threshold Lowering is Counter-Productive:** Diagnostic token inspection revealed that 5 of the 6 false negatives had peak hallucination probabilities below **0.011** (1.1%). Meanwhile, clean benchmark samples reached hallucination probabilities as high as **0.2100** (21.0% on `GEO-SUP-010`). Consequently, lowering the token classification threshold cannot resolve these false negatives and would immediately introduce catastrophic False Positives.
4. **Primary Failure Class:** The failures are driven by **entity-relation binding and syntactic directionality limitations** in token classification encoders rather than retrieval failure, context truncation, or threshold miscalibration.

---

## 2. Files Inspected & Audit Trail

The investigation was performed by directly inspecting the following configuration files, benchmark datasets, and serialized inference outputs:

| File Path | Description | Verified Status |
| :--- | :--- | :--- |
| [`evaluation/dataset/geography_evaluation_dataset.json`](file:///f:/final%20project/HalluGuard/evaluation/dataset/geography_evaluation_dataset.json) | Full 60-sample benchmark dataset with gold character spans. | Inspected & Verified |
| [`evaluation/dataset/geography_evaluation_dataset.csv`](file:///f:/final%20project/HalluGuard/evaluation/dataset/geography_evaluation_dataset.csv) | Tabular representation of benchmark dataset. | Inspected & Verified |
| [`evaluation/results/baseline_predictions.json`](file:///f:/final%20project/HalluGuard/evaluation/results/baseline_predictions.json) | Complete baseline inference predictions for all 60 samples. | Inspected & Verified |
| [`evaluation/results/baseline_run_summary.json`](file:///f:/final%20project/HalluGuard/evaluation/results/baseline_run_summary.json) | High-level baseline metrics and confusion matrix. | Inspected & Verified |
| [`backend/app/services/detector_service.py`](file:///f:/final%20project/HalluGuard/backend/app/services/detector_service.py) | Application service wrapper for LettuceDetect inference. | Inspected & Verified |
| [`backend/app/config.py`](file:///f:/final%20project/HalluGuard/backend/app/config.py) | Application configuration and model hyperparameters. | Inspected & Verified |
| [`LettuceDetect/lettucedetect/detectors/transformer.py`](file:///f:/final%20project/LettuceDetect/lettucedetect/detectors/transformer.py) | Token classifier, chunking, and span grouping implementation. | Inspected & Verified |
| [`LettuceDetect/lettucedetect/detectors/prompt_utils.py`](file:///f:/final%20project/LettuceDetect/lettucedetect/detectors/prompt_utils.py) | Prompt assembly and instruction formatting templates. | Inspected & Verified |
| [`LettuceDetect/lettucedetect/prompts/qa_prompt_en.txt`](file:///f:/final%20project/LettuceDetect/lettucedetect/prompts/qa_prompt_en.txt) | Instruction prompt template used during QA verification. | Inspected & Verified |

---

## 3. Detailed Case-by-Case Deep Dive

For each of the six false negatives, the exact question, reference context, generated answer, gold annotation, model prediction, and diagnostic token-level probabilities were analyzed:

```
False Negative Catalog:
├── Contradictory Quadrant (Intrinsic Hallucinations):
│   ├── Case 1: GEO-CON-001 (Amazon vs. Nile River Length)
│   ├── Case 2: GEO-CON-002 (K2 Second vs. Third-Highest Mountain)
│   ├── Case 3: GEO-CON-005 (Sahara Desert Area Ranking vs. Polar Deserts)
│   └── Case 4: GEO-CON-011 (Mauna Kea vs. Mount Everest Base-to-Peak Height)
└── Mixed Quadrant (Partial Hallucinations):
    ├── Case 5: GEO-MIX-001 (Melbourne vs. Sydney Most Populous City)
    └── Case 6: GEO-MIX-005 (Vancouver vs. Victoria Provincial Capital)
```

---

### Case 1: `GEO-CON-001` — Relational Inversion of River Lengths

#### 1. Extracted Data
- **Test ID:** `GEO-CON-001`
- **Category:** `contradictory`
- **Source Authority:** USGS Water Science School
- **Question:**  
  *"Which river is the longest in the world according to the reference?"*
- **Reference Context:**  
  > *"The Nile River in northeastern Africa is traditionally considered the longest river in the world, with a measured length of approximately 6,650 kilometres (4,132 miles). The Amazon River in South America is the second longest at roughly 6,400 kilometres."*
- **Generated Answer:**  
  > *"According to the reference, the Amazon River is the longest river in the world at 6,650 kilometres."*
- **Ground-Truth Hallucinated Span:**  
  - Start Offset: `28`
  - End Offset: `44`
  - Substring: `"the Amazon River"`
  - Annotation Note: *Direct contradiction: Reference explicitly identifies Nile as longest and Amazon as second longest.*
- **Actual Model Prediction:**  
  - Predicted Verdict: `CLEAN`
  - Predicted Spans: `[]`
  - Max Confidence: `None`
  - Latency: `449.16 ms`

#### 2. Diagnostic Token Probability Profile
Probing the raw logits of the ModernBERT token classification head reveals:

| Subword Token | Raw Character Slice | Hallucination Probability $P(\text{hall})$ | Classification Verdict ($\theta = 0.50$) |
| :--- | :--- | :---: | :---: |
| `'650'` | `"6,650"` | **0.3490 (34.90%)** | Clean (Sub-threshold) |
| `','` | `","` | **0.3261 (32.61%)** | Clean (Sub-threshold) |
| `' 6'` | `"6"` | **0.2097 (20.97%)** | Clean (Sub-threshold) |
| `' kilometres'` | `" kilometres"` | **0.1804 (18.04%)** | Clean (Sub-threshold) |
| `' longest'` | `" longest"` | **0.1340 (13.40%)** | Clean (Sub-threshold) |
| `' world'` | `" world"` | **0.1250 (12.50%)** | Clean (Sub-threshold) |
| `'.'` | `"."` | **0.1196 (11.96%)** | Clean (Sub-threshold) |
| `' at'` | `" at"` | **0.1039 (10.39%)** | Clean (Sub-threshold) |
| `' Amazon'` | `" Amazon"` | **0.0550 (5.50%)** | Clean (Sub-threshold) |
| `' River'` | `" River"` | **0.0220 (2.20%)** | Clean (Sub-threshold) |

#### 3. Root Cause Diagnosis
- **Failure Classification:** **Entity-Attribute Binding Inversion with High Lexical Overlap**.
- **Mechanistic Evidence:** The context mentions both `"Nile River"`, `"Amazon River"`, `"longest river"`, and `"6,650 kilometres"`. The generated answer cross-wires the attribute `"6,650 kilometres"` with `"Amazon River"`. ModernBERT registered elevated uncertainty on the number token (`P = 0.3490`), but because all four constituent phrases are individually present in the context, attention weights to the context passages remained high, dampening the hallucination logit below the default 0.50 threshold.

---

### Case 2: `GEO-CON-002` — Fine-Grained Ordinal Substitution

#### 1. Extracted Data
- **Test ID:** `GEO-CON-002`
- **Category:** `contradictory`
- **Source Authority:** NASA Earth Observatory
- **Question:**  
  *"What is the elevation ranking of K2?"*
- **Reference Context:**  
  > *"K2, situated on the China-Pakistan border in the Karakoram range, is the second-highest mountain on Earth at 8,611 metres above sea level, surpassed only by Mount Everest at 8,848 metres."*
- **Generated Answer:**  
  > *"K2 is the third-highest mountain on Earth at 8,611 metres above sea level."*
- **Ground-Truth Hallucinated Span:**  
  - Start Offset: `10`
  - End Offset: `23`
  - Substring: `"third-highest"`
  - Annotation Note: *Contradiction: Answer asserts 'third-highest', conflicting with 'second-highest' in reference.*
- **Actual Model Prediction:**  
  - Predicted Verdict: `CLEAN`
  - Predicted Spans: `[]`
  - Max Confidence: `None`
  - Latency: `387.16 ms`

#### 2. Diagnostic Token Probability Profile

| Subword Token | Raw Character Slice | Hallucination Probability $P(\text{hall})$ | Classification Verdict ($\theta = 0.50$) |
| :--- | :--- | :---: | :---: |
| `'2'` | `"K2"` | **0.0068 (0.68%)** | Clean |
| `'K'` | `"K2"` | **0.0005 (0.05%)** | Clean |
| `'611'` | `"8,611"` | **0.0002 (0.02%)** | Clean |
| `' third'` | `" third"` | **0.0000 (0.00%)** | Clean |
| `' highest'` | `"-highest"` | **0.0000 (0.00%)** | Clean |
| `' mountain'` | `" mountain"` | **0.0000 (0.00%)** | Clean |

#### 3. Root Cause Diagnosis
- **Failure Classification:** **Fine-Grained Ordinal Substitution Blind Spot**.
- **Mechanistic Evidence:** The contradiction hinges entirely on substituting the ordinal token `"third"` for `"second"`. Syntactically and semantically, `"third-highest mountain on Earth at 8,611 metres above sea level"` has near-identical semantic embedding similarity to `"second-highest mountain on Earth at 8,611 metres above sea level"`. The token `' third'` produced $P(\text{hall}) = 0.0000$. The token classification head treated the phrase as fully supported because all surrounding tokens (95% of the sentence) match the context verbatim.

---

### Case 3: `GEO-CON-005` — Subordinate Clause Negation & Area Ranking

#### 1. Extracted Data
- **Test ID:** `GEO-CON-005`
- **Category:** `contradictory`
- **Source Authority:** National Geographic Society
- **Question:**  
  *"How large is the Sahara Desert and what type of desert is it?"*
- **Reference Context:**  
  > *"The Sahara is the largest hot desert in the world, covering an area of approximately 9.2 million square kilometres across North Africa. By total area, it ranks third behind the cold polar deserts of Antarctica and the Arctic."*
- **Generated Answer:**  
  > *"The Sahara is the world's largest desert overall, surpassing both Antarctica and the Arctic in total area."*
- **Ground-Truth Hallucinated Span:**  
  - Start Offset: `14`
  - End Offset: `105`
  - Substring: `"the world's largest desert overall, surpassing both Antarctica and the Arctic in total area"`
  - Annotation Note: *Contradiction: Reference explicitly states Sahara ranks third behind Antarctica and the Arctic.*
- **Actual Model Prediction:**  
  - Predicted Verdict: `CLEAN`
  - Predicted Spans: `[]`
  - Max Confidence: `None`
  - Latency: `474.71 ms`

#### 2. Diagnostic Token Probability Profile

| Subword Token | Raw Character Slice | Hallucination Probability $P(\text{hall})$ | Classification Verdict ($\theta = 0.50$) |
| :--- | :--- | :---: | :---: |
| `' Sah'` | `"Sahara"` | **0.0003 (0.03%)** | Clean |
| `' overall'` | `" overall"` | **0.0002 (0.02%)** | Clean |
| `' surpass'` | `" surpassing"` | **0.0002 (0.02%)** | Clean |
| `' Antarctica'` | `" Antarctica"` | **0.0001 (0.01%)** | Clean |
| `' Arctic'` | `" Arctic"` | **0.0001 (0.01%)** | Clean |

#### 3. Root Cause Diagnosis
- **Failure Classification:** **Semantic Relation Inversion with Total Vocabulary Overlap**.
- **Mechanistic Evidence:** The context contains `"Sahara"`, `"largest"`, `"world"`, `"total area"`, `"third behind"`, `"Antarctica"`, and `"Arctic"`. The generated answer asserts that the Sahara is the largest *"overall, surpassing both Antarctica and the Arctic"*. Despite directly reversing the ranking relation ("ranks third behind" $\to$ "surpassing"), every named entity and noun phrase is present in the context. The model failed to compute the logical negation implied by "surpassing" versus "ranks third behind", producing a maximum probability of only $0.0003$.

---

### Case 4: `GEO-CON-011` — Subject-Object Inversion on Comparative Adjectives

#### 1. Extracted Data
- **Test ID:** `GEO-CON-011`
- **Category:** `contradictory`
- **Source Authority:** USGS Hawaiian Volcano Observatory
- **Question:**  
  *"How does Mauna Kea compare to Mount Everest from base to peak?"*
- **Reference Context:**  
  > *"Mount Everest is the highest mountain above sea level at 8,848 metres. However, Mauna Kea in Hawaii is taller when measured from its underwater base on the oceanic floor to its summit, totaling over 10,200 metres, though only 4,207 metres rise above sea level."*
- **Generated Answer:**  
  > *"Measured from its underwater base to its summit, Mount Everest is taller than Mauna Kea, reaching over 10,200 metres."*
- **Ground-Truth Hallucinated Span:**  
  - Start Offset: `49`
  - End Offset: `87`
  - Substring: `"Mount Everest is taller than Mauna Kea"`
  - Annotation Note: *Contradiction: Context specifies Mauna Kea is taller base-to-peak; answer inverts the subject to Everest.*
- **Actual Model Prediction:**  
  - Predicted Verdict: `CLEAN`
  - Predicted Spans: `[]`
  - Max Confidence: `None`
  - Latency: `483.73 ms`

#### 2. Diagnostic Token Probability Profile

| Subword Token | Raw Character Slice | Hallucination Probability $P(\text{hall})$ | Classification Verdict ($\theta = 0.50$) |
| :--- | :--- | :---: | :---: |
| `' Eve'` | `"Everest"` | **0.0107 (1.07%)** | Clean |
| `' Mount'` | `"Mount"` | **0.0066 (0.66%)** | Clean |
| `'200'` | `"10,200"` | **0.0056 (0.56%)** | Clean |
| `' metres'` | `" metres"` | **0.0039 (0.39%)** | Clean |
| `' taller'` | `" taller"` | **0.0018 (0.18%)** | Clean |
| `' Mauna'` | `" Mauna"` | **0.0012 (0.12%)** | Clean |

#### 3. Root Cause Diagnosis
- **Failure Classification:** **Syntactic Subject-Object Directionality Failure**.
- **Mechanistic Evidence:** The context asserts: $\text{Mauna Kea} > \text{Mount Everest}$ (base-to-summit). The answer asserts: $\text{Mount Everest} > \text{Mauna Kea}$ (base-to-summit). Because the context contains both mountains, the comparative adjective "taller", and the quantity "10,200 metres", ModernBERT's bidirectional attention tokens attend strongly to all matching lexical anchors. The token classifier lacks the structural syntactic dependency resolution required to enforce directionality across $X \text{ is taller than } Y$.

---

### Case 5: `GEO-MIX-001` — Multi-Entity Co-Occurrence Distractor

#### 1. Extracted Data
- **Test ID:** `GEO-MIX-001`
- **Category:** `mixed`
- **Source Authority:** Geoscience Australia
- **Question:**  
  *"What is the capital of Australia and what is its largest city?"*
- **Reference Context:**  
  > *"Canberra is the federal capital of Australia, selected as a compromise between Sydney and Melbourne in 1908. Sydney is Australia's most populous city."*
- **Generated Answer:**  
  > *"Canberra is the capital of Australia, while Melbourne is the country's most populous city."*
- **Ground-Truth Hallucinated Span:**  
  - Start Offset: `44`
  - End Offset: `89`
  - Substring: `"Melbourne is the country's most populous city"`
  - Annotation Note: *Mixed: Capital claim (Canberra) is supported; most populous claim (Melbourne) contradicts Sydney.*
- **Actual Model Prediction:**  
  - Predicted Verdict: `CLEAN`
  - Predicted Spans: `[]`
  - Max Confidence: `None`
  - Latency: `390.18 ms`

#### 2. Diagnostic Token Probability Profile

| Subword Token | Raw Character Slice | Hallucination Probability $P(\text{hall})$ | Classification Verdict ($\theta = 0.50$) |
| :--- | :--- | :---: | :---: |
| `' Melbourne'` | `" Melbourne"` | **0.0106 (1.06%)** | Clean |
| `' country'` | `" country"` | **0.0098 (0.98%)** | Clean |
| `'.'` | `"."` | **0.0054 (0.54%)** | Clean |
| `' most'` | `" most"` | **0.0052 (0.52%)** | Clean |
| `' pop'` | `" populous"` | **0.0044 (0.44%)** | Clean |
| `' Canberra'` | `"Canberra"` | **0.0001 (0.01%)** | Clean |

#### 3. Root Cause Diagnosis
- **Failure Classification:** **Entity Distractor Substitution within Mixed Compound Sentences**.
- **Mechanistic Evidence:** The sentence structure consists of two clauses:
  1. Clause 1: *"Canberra is the capital of Australia"* $\to$ Strictly Supported (Clean).
  2. Clause 2: *"while Melbourne is the country's most populous city"* $\to$ Contradicts context (Sydney is most populous).
  Because "Melbourne", "Sydney", and "Australia's most populous city" are all present in the reference context, the token `' Melbourne'` registered only $P(\text{hall}) = 0.0106$. The strong grounding of the first clause ("Canberra") combined with the contextual presence of "Melbourne" caused the model to overlook the false entity-attribute binding.

---

### Case 6: `GEO-MIX-005` — Metropolitan Area vs. Capital Confusion

#### 1. Extracted Data
- **Test ID:** `GEO-MIX-005`
- **Category:** `mixed`
- **Source Authority:** Natural Resources Canada
- **Question:**  
  *"Where is Vancouver located and is it the capital of British Columbia?"*
- **Reference Context:**  
  > *"British Columbia is the westernmost province of Canada, bordered by the Pacific Ocean. Its provincial capital is Victoria, located on Vancouver Island, whereas Vancouver is its largest metropolitan area on the mainland."*
- **Generated Answer:**  
  > *"British Columbia is Canada's westernmost province bordering the Pacific, and its provincial capital is Vancouver."*
- **Ground-Truth Hallucinated Span:**  
  - Start Offset: `73`
  - End Offset: `112`
  - Substring: `"and its provincial capital is Vancouver"`
  - Annotation Note: *Mixed: Geography and ocean border supported; Vancouver capital claim contradicts Victoria.*
- **Actual Model Prediction:**  
  - Predicted Verdict: `CLEAN`
  - Predicted Spans: `[]`
  - Max Confidence: `None`
  - Latency: `367.67 ms`

#### 2. Diagnostic Token Probability Profile

| Subword Token | Raw Character Slice | Hallucination Probability $P(\text{hall})$ | Classification Verdict ($\theta = 0.50$) |
| :--- | :--- | :---: | :---: |
| `' Vancouver'` | `" Vancouver"` | **0.0105 (1.05%)** | Clean |
| `'.'` | `"."` | **0.0059 (0.59%)** | Clean |
| `' is'` | `" is"` | **0.0056 (0.56%)** | Clean |
| `' provincial'` | `" provincial"` | **0.0039 (0.39%)** | Clean |
| `' capital'` | `" capital"` | **0.0027 (0.27%)** | Clean |

#### 3. Root Cause Diagnosis
- **Failure Classification:** **Geographic Colocation Distractor with Multiple Entity Mentions**.
- **Mechanistic Evidence:** The context mentions "British Columbia", "provincial capital", "Victoria", "Vancouver Island", and "Vancouver". The answer incorrectly claims that the provincial capital is Vancouver. Because "Vancouver" appears twice in the reference context (once as "Vancouver Island" and once as "Vancouver"), the word is heavily anchored. ModernBERT's token classifier attends to the repeated occurrences of "Vancouver" and "provincial capital", failing to recognize that "Victoria" was the true capital.

---

## 4. Failure Taxonomy & Root Cause Synthesis

Comparing all 6 false negatives against the 39 true positives reveals a clear structural dichotomy:

### 4.1 Comparative Failure Analysis

| Failure Dimension | Extrinsic Hallucinations (`unsupported`) | Intrinsic Hallucinations (`contradictory` & `mixed` FN) |
| :--- | :--- | :--- |
| **Benchmark Result** | **15 / 15 Detected (100.0% Recall)** | **6 Missed (73.3% Contradictory, 86.7% Mixed)** |
| **Lexical Context Overlap** | Low to Zero (Novel entity or fact introduced) | Near 100% (All words already present in context) |
| **Attention Behavior** | Softmax attention finds zero matching context tokens $\to$ cross-attention fails to ground $\to$ high hallucination logit ($P \ge 0.90$). | Softmax attention finds strong matching tokens across context $\to$ cross-attention grounds heavily $\to$ low hallucination logit ($P < 0.05$). |
| **Cognitive Requirement** | Simple lexical/semantic entity absence detection. | Relational dependency resolution, syntactic directionality, and ordinal reasoning. |

### 4.2 Failure Mechanism Classification Matrix

```
Total False Negatives (FN = 6)
├── Relational Attribute Binding Inversion (1 case):
│   └── GEO-CON-001: 6,650 km incorrectly bound to Amazon River
├── Ordinal / Quantitative Substitution (1 case):
│   └── GEO-CON-002: "third-highest" substituted for "second-highest"
├── Logical Negation / Comparative Reversal (2 cases):
│   ├── GEO-CON-005: "surpassing both" reversed from "ranks third behind"
│   └── GEO-CON-011: Subject-object inversion on "is taller than"
└── Entity Distractor Substitution in Compound Sentences (2 cases):
    ├── GEO-MIX-001: Melbourne substituted for Sydney as most populous
    └── GEO-MIX-005: Vancouver substituted for Victoria as capital
```

---

## 5. Confidence Threshold & Calibration Analysis

A common assumption in binary classification errors is that the decision boundary is simply set too high. This hypothesis was rigorously tested.

### 5.1 Token Probability Landscape

In LettuceDetect, a token is predicted as hallucinated when:
$$\text{pred} = 1 \quad \iff \quad P(\text{hallucinated}) \ge \theta_{\text{token}} = 0.50$$

Let us review the peak hallucination probability $\max(P_{\text{hall}})$ across all six false negatives:

```
False Negative Peak Probabilities:
├── GEO-CON-001:  0.3490 (34.90%)  ── Has moderate hallucination signal
├── GEO-CON-002:  0.0068 (0.68%)   ── Zero signal
├── GEO-CON-005:  0.0003 (0.03%)   ── Zero signal
├── GEO-CON-011:  0.0107 (1.07%)   ── Zero signal
├── GEO-MIX-001:  0.0106 (1.06%)   ── Zero signal
└── GEO-MIX-005:  0.0105 (1.05%)   ── Zero signal
```

### 5.2 Clean Sample Peak Probabilities (The False Positive Ceiling)

To determine the risk of lowering $\theta_{\text{token}}$, the maximum hallucination probabilities across all 15 clean (`supported`) benchmark samples were measured:

```
Clean Samples Peak Probabilities:
├── GEO-SUP-010:  0.2100 (21.00%)  ── Token ' Europe'
├── GEO-SUP-012:  0.1219 (12.19%)  ── Token ' 20'
├── GEO-SUP-005:  0.0148 (1.48%)   ── Token ','
├── GEO-SUP-007:  0.0116 (1.16%)   ── Token ' approximately'
├── GEO-SUP-003:  0.0103 (1.03%)   ── Token '100'
├── GEO-SUP-013:  0.0102 (1.02%)   ── Token ' peak'
└── Remaining 9:  < 0.0040 (< 0.40%)
```

### 5.3 Mathematical Proof: Why Threshold Tuning Fails

1. **If $\theta_{\text{token}}$ is lowered from $0.50$ to $0.30$:**
   - `GEO-CON-001` ($0.3490$) is successfully detected ($\text{TP} \to 40$, $\text{FN} \to 5$).
   - False Positives remain $0$ (since max clean is $0.2100$).
   - **However, the remaining 5 false negatives are completely unaffected** (their peak probabilities are $0.0003$ to $0.0107$).
2. **If $\theta_{\text{token}}$ is lowered below $0.2100$:**
   - Sample `GEO-SUP-010` is immediately misclassified as `HALLUCINATED`.
   - **Precision drops from 100.0% to 97.5%**, introducing the first False Positive.
3. **If $\theta_{\text{token}}$ is lowered below $0.0100$ (to catch the remaining 5 FN):**
   - At least 6 clean samples (`GEO-SUP-010`, `012`, `005`, `007`, `003`, `013`) will be falsely flagged.
   - **Specificity collapses from 100.0% to 60.0%**, destroying the reliability of the system.

> **Investigation Verdict on Thresholding:**  
> Lowering the classification threshold is mathematically unviable as a general solution. Aside from `GEO-CON-001`, the failures are not border-line threshold misses; they are deep representation blind spots where the model is 99% confident that the answer is supported.

---

## 6. Recommended Improvement Experiments (Ranked by Priority)

To address these relational blind spots without retraining the base ModernBERT foundation model or compromising specificity, five distinct improvement experiments are proposed and ranked by feasibility and expected impact:

```
Improvement Roadmap:
├── Priority 1: Multi-Perspective NLI Verification Cascade (High Impact / Low Risk)
├── Priority 2: Structured Entity-Relation Contrast Extractor (High Impact / Medium Effort)
├── Priority 3: Prompt Instruction Reformulation with Relational Constraints (Quick Win)
├── Priority 4: Bidirectional Verification (Context-to-Answer & Answer-to-Context)
└── Priority 5: Specialized Fine-Tuning on Relational Inversion Benchmarks (Long-Term)
```

---

### Priority 1: Multi-Perspective Natural Language Inference (NLI) Verification Cascade

- **Concept:** Pair ModernBERT token classification with a sequence-level DeBERTa-v3 NLI model (e.g. `cross-encoder/nli-deberta-v3-base` or `FacebookAI/roberta-large-mnli`).
- **Mechanism:**
  - ModernBERT runs first to identify fine-grained token spans.
  - If ModernBERT outputs `CLEAN`, but the context contains high lexical overlap with the answer, an NLI check evaluates whether $\text{Context} \models \text{Answer}$ (Premise $\to$ Hypothesis).
  - If NLI predicts `CONTRADICTION` with high probability, the answer is flagged, prompting a targeted span localization pass.
- **Expected Benefit:** DeBERTa-v3 is known to excel at syntactic directionality and ordinal contradictions ($X > Y$ vs $Y > X$).
- **Risk Assessment:** Low risk to latency if executed only on candidate clean cases with high entity density.

---

### Priority 2: Structured Entity-Relation Contrast Extractor

- **Concept:** Implement a lightweight entity-attribute extraction pre-check in [`retrieval_service.py`](file:///f:/final%20project/HalluGuard/backend/app/services/retrieval_service.py).
- **Mechanism:**
  - Extract named entities (locations, organizations) and numerical attributes (lengths, populations, rankings) from both the context and answer using rule-based patterns or spaCy.
  - Verify that attribute bindings match (e.g., verifying that "6,650 km" is bound to "Nile" in both texts, not "Amazon").
  - If an attribute re-binding is detected, pass an augmented warning prompt into the detector.
- **Expected Benefit:** Directly addresses `GEO-CON-001`, `GEO-MIX-001`, and `GEO-MIX-005`.

---

### Priority 3: Prompt Instruction Reformulation with Explicit Relational Warnings

- **Concept:** Modify [`qa_prompt_en.txt`](file:///f:/final%20project/LettuceDetect/lettucedetect/prompts/qa_prompt_en.txt) to explicitly instruct the model to verify entity-attribute pairings and comparative rankings.
- **Mechanism:**
  - Add explicit instructions such as:  
    *"Pay special attention to numbers, rankings, comparative relations (such as tallest, longest, capital), and verify that each entity is paired with its exact correct attribute."*
- **Expected Benefit:** Minimal engineering overhead; tests whether ModernBERT's cross-attention can be steered by stronger instruction prompting.
- **Risk Assessment:** Zero risk to codebase; easily evaluated across the 60 benchmark samples.

---

### Priority 4: Bidirectional Consistency Checking (Cycle-Consistency)

- **Concept:** Run verification in both directions:
  1. Direction A: Does the Context support the Answer? (Current)
  2. Direction B: Does the Answer contradict any explicit claim in the Context?
- **Mechanism:** Generate counter-hypotheses from the reference context and score them against the answer.
- **Expected Benefit:** Captures contradictions like `GEO-CON-005` ("ranks third behind" vs "surpassing").

---

### Priority 5: Specialized Contrastive Fine-Tuning on Relational Swaps (Long-Term)

- **Concept:** Fine-tune the ModernBERT token classification head on a synthetic dataset specifically generated to teach entity-attribute swaps (e.g. perturbing clean RAG QA pairs by swapping subjects, numbers, and ordinals).
- **Mechanism:** Use data augmentation scripts (such as `LettuceDetect/scripts/convert_clean_samples_to_hallucinated.py`) with explicit entity-swap mutations.
- **Expected Benefit:** Fundamentally cures the representation blind spot at the model weight level.
- **Cost / Effort:** Requires GPU compute, hyperparameter sweeps, and extensive regression testing to preserve 100% specificity.

---

## 7. False Positive Risk Analysis & Guardrails

Any modification intended to increase Recall ($86.67\% \to 100\%$) carries the severe hazard of degrading Precision ($100\% \to <90\%$).

### 7.1 The Cost of False Positives in Factual Grounding
In enterprise and academic RAG applications, **False Positives (Type I errors) erode user trust faster than False Negatives**. If clean, well-grounded answers generated by LLMs are repeatedly flagged with alarming red banners and false confidence scores, users quickly disregard the verification tool entirely.

### 7.2 Strict Guardrail Criteria for Future Improvement Phases
Before any improvement experiment is merged into production:
1. **The Specificity Guardrail:** The system **must maintain 100.0% Specificity** ($TN = 15 / 15$, $FP = 0$) on the verified clean quadrant.
2. **The Precision Guardrail:** Overall Precision must remain $\ge 95.0\%$.
3. **The Latency Budget:** End-to-end CPU verification latency must remain under **1,000 ms** (1.0 second).
4. **Decoupled Verification:** Any new model or rule must be evaluated through the decoupled evaluation suite (`evaluation/scripts/run_baseline_evaluation.py`) before touching production backend code.

---

## 8. Summary Comparison Table of the Six False Negatives

| Test ID | Ground Truth Substring | Expected Category | Diagnostic Peak $P(\text{hall})$ | Primary Failure Mechanism | Recommended Solution |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **`GEO-CON-001`** | `"the Amazon River"` | `contradictory` | **0.3490** | Relational Inversion (Length attribute swap) | Entity-attribute binding pre-check or DeBERTa NLI |
| **`GEO-CON-002`** | `"third-highest"` | `contradictory` | **0.0068** | Ordinal Substitution ("second" $\to$ "third") | DeBERTa-v3 NLI comparative reasoning |
| **`GEO-CON-005`** | `"the world's largest... in total area"` | `contradictory` | **0.0003** | Semantic Negation ("surpassing" vs "ranks third") | Cycle-consistency contradiction check |
| **`GEO-CON-011`** | `"Mount Everest is taller than Mauna Kea"` | `contradictory` | **0.0107** | Comparative Directionality ($X > Y$ inverted) | Dependency-based syntactic directionality check |
| **`GEO-MIX-001`** | `"Melbourne is the country's most populous..."` | `mixed` | **0.0106** | Entity Distractor (Sydney vs Melbourne) | Entity-attribute binding extraction |
| **`GEO-MIX-005`** | `"and its provincial capital is Vancouver"` | `mixed` | **0.0105** | Colocation Distractor (Vancouver vs Victoria) | Named entity relation verification |

---

## 9. Conclusion & Next Steps

This investigation successfully diagnoses why the six false negatives occurred:
- The failures are **not** caused by document ingestion bugs, text truncation, or threshold miscalibration.
- They are caused by an intrinsic limitation of token-level self-attention models when confronted with **contradictions that possess 100% lexical overlap with the reference context**.
- Lowering the classification threshold was empirically proven to be an invalid solution that introduces immediate false positives.
- The path forward involves **hybrid multi-perspective verification** (combining token classification with relational NLI or entity-relation binding checks).

**Status:** **INVESTIGATION COMPLETE — AWAITING USER APPROVAL TO PROCEED TO STEP 2**

