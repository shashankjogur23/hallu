# HalluGuard Evaluation Dataset — Annotation Guide

## 1. Overview and Purpose

This document provides standardized instructions and criteria for annotating the ground-truth benchmark dataset for **HalluGuard** (`KRLabsOrg/lettucedect-base-modernbert-en-v1` evaluation).

The objective is to establish an objective, high-quality, independent ground-truth evaluation set for hallucination detection across closed-context Question Answering and Document Verification tasks.

---

## 2. Fundamental Annotation Principles

### 2.1 Complete Detector Independence
- **Rule:** Ground-truth labels and span boundaries **must be created without running the detector or consulting model outputs**.
- The human annotator acts as an impartial auditor assessing the fidelity of the `generated_answer` solely against the provided `reference_context`.

### 2.2 Closed-Context Truth vs. Real-World Knowledge
- **Closed-Context Paradigm:** The reference context is the **sole source of truth**.
- Even if a statement is universally true in the real world (e.g., *"Mount Everest is 8,848.86 metres high"*), if it is not stated or directly entailed by the provided `reference_context`, it is classified as **`unsupported`** (extrinsic hallucination).
- Conversely, if the reference context contains a deliberate counterfactual premise (e.g., in controlled synthetic testing), an answer reflecting that context is **`supported`**, whereas an answer reflecting real-world truth contradicting that context is **`contradictory`**.

### 2.3 Stable Domain Focus: Geography
- **Domain:** Physical and political geography (mountains, rivers, capitals, oceans, landforms, geographic treaties).
- **Rationale:** Geography offers well-documented, verifiable, and enduring factual relationships that do not fluctuate rapidly (unlike dynamic economic statistics, political polling, or live sports scores).
- **Approved Source Authorities:**
  - NASA Earth Observatory (`https://earthobservatory.nasa.gov`)
  - United States Geological Survey (USGS) (`https://www.usgs.gov`)
  - United Nations Geospatial / UNESCO (`https://whc.unesco.org`)
  - National Geographic Society
  - Geoscience Australia (`https://www.ga.gov.au`)
  - Official national cartographic / geographical surveys

---

## 3. Dataset Taxonomy and Categories

The benchmark is partitioned evenly across **four distinct categories** (target: 15 per category, 60 total):

| Category | Definition | Ground-Truth Verdict | Expected Spans |
| :--- | :--- | :--- | :--- |
| **`supported`** | All factual statements and claims in the answer are strictly entailed by the reference context. | `CLEAN` | `[]` (Empty list) |
| **`contradictory`** | At least one statement in the answer directly conflicts with or negates explicit statements in the reference context (intrinsic contradiction). | `HALLUCINATED` | 1 or more conflicting spans |
| **`unsupported`** | At least one claim introduces new entities, figures, dates, or relations entirely absent from the reference context, with no direct conflict (extrinsic hallucination). | `HALLUCINATED` | 1 or more unmentioned claim spans |
| **`mixed`** | The answer contains a combination of genuinely supported claims AND one or more unsupported or contradictory claims. | `HALLUCINATED` | Spans covering only the invalid portions |

### Category 1: `supported`
- **Definition:** Every predicate, entity, attribute, and relation asserted in `generated_answer` is explicitly supported or logically entailed by `reference_context`.
- **Verdict:** `CLEAN`
- **Expected Spans:** `[]`
- **Example:**
  - *Context:* "Lake Victoria has a surface area of approximately 59,947 square kilometres, making it Africa's largest lake by area."
  - *Answer:* "Africa's largest lake by surface area is Lake Victoria, covering around 59,947 square kilometres."
  - *Annotation:* Valid paraphrase. Both the entity, relation, and metric are verified.

### Category 2: `contradictory`
- **Definition:** The answer makes a claim that directly inverts, changes, or contradicts a fact stated in the context.
- **Verdict:** `HALLUCINATED`
- **Expected Spans:** The minimal substring containing the contradictory claim.
- **Example:**
  - *Context:* "K2 is the second-highest mountain on Earth at 8,611 metres above sea level."
  - *Answer:* "K2 is the third-highest mountain on Earth at 8,611 metres."
  - *Contradictory Span:* `"third-highest"` (conflicts with "second-highest").

### Category 3: `unsupported`
- **Definition:** The answer asserts claims that do not exist anywhere in the reference context. The claim is ungrounded.
- **Important Note:** A claim that is absent from the reference should be labelled `unsupported`, **not automatically false in real life**.
- **Verdict:** `HALLUCINATED`
- **Expected Spans:** The substring asserting the ungrounded information.
- **Example:**
  - *Context:* "The Mariana Trench is located in the western Pacific Ocean and reaches a maximum known depth of nearly 11,000 metres."
  - *Answer:* "The Mariana Trench is in the western Pacific Ocean and was first explored by Jacques Piccard and Don Walsh in the bathyscaphe Trieste in 1960."
  - *Unsupported Span:* `"and was first explored by Jacques Piccard and Don Walsh in the bathyscaphe Trieste in 1960"` (Historically true in the real world, but absent from the reference context).

### Category 4: `mixed`
- **Definition:** The answer includes both completely supported clauses and hallucinated (unsupported or contradictory) clauses.
- **Verdict:** `HALLUCINATED` (at the answer level)
- **Expected Spans:** Only the erroneous or ungrounded span(s) must be annotated. Supported portions must remain unflagged.
- **Example:**
  - *Context:* "Madrid is the capital and most populous city of Spain, situated on the Manzanares River."
  - *Answer:* "Madrid is the capital of Spain and is located along the Danube River."
  - *Supported portion:* "Madrid is the capital of Spain"
  - *Hallucinated Span:* `"the Danube River"` (contradicts Manzanares River).

---

## 4. Span Annotation Guidelines

### 4.1 Minimal Span Principle
Annotators must select the **minimal contiguous span of text** that causes the claim to be invalid:
- **Good:** Span = `"third-highest"`
- **Too Broad:** Span = `"K2 is the third-highest mountain on Earth at 8,611 metres."` (Includes correct information)
- **Too Narrow:** Span = `"third"` (Missing context of what is third)

### 4.2 Exact Character Offsets
Span offsets are 0-indexed character offsets within the `generated_answer` string:
- `start`: Index of the first character of the span (inclusive).
- `end`: Index immediately following the last character of the span (exclusive, Python slice notation `answer[start:end]`).
- `text`: Exact substring identical to `answer[start:end]`.

### 4.3 Punctuation and Boundary Rules
1. **Punctuation:** Do not include sentence-ending periods, commas, or semicolons unless they are an integral part of a numerical expression (e.g., `5,895` or `3.14`) or abbreviation (e.g., `U.S.`).
2. **Articles & Prepositions:** Include determiners (`the`, `a`) only if removing them distorts the semantic unit (e.g., `"the Amazon River"` vs `"Amazon River"`). Consistency is maintained by preferring the full noun phrase.
3. **Whitespace:** Never include leading or trailing whitespace in the span.
4. **Multiple Spans:** If an answer contains multiple disjoint hallucinated statements, annotate each as a separate item in the JSON array:
   ```json
   [
     {"start": 12, "end": 28, "text": "invalid claim 1"},
     {"start": 45, "end": 62, "text": "invalid claim 2"}
   ]
   ```

---

## 5. CSV Schema Specification

The dataset file `evaluation_dataset_template.csv` adheres to the following 10-column specification:

| # | Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `test_id` | String | Unique sample ID: `GEO-[SUP\|CON\|UNS\|MIX]-XXX` | `GEO-SUP-001` |
| 2 | `category` | Enum | One of: `supported`, `contradictory`, `unsupported`, `mixed` | `supported` |
| 3 | `question` | String | User query or prompt | `What is the capital of France?` |
| 4 | `reference_context` | String | Ground-truth reference passage(s) | `Paris is the capital of France...` |
| 5 | `generated_answer` | String | Candidate answer to evaluate | `The capital of France is Paris.` |
| 6 | `expected_verdict` | Enum | `CLEAN` (for supported) or `HALLUCINATED` (all others) | `CLEAN` |
| 7 | `expected_unsupported_spans` | JSON Array | Array of objects: `[{"start": int, "end": int, "text": str}]` | `[]` |
| 8 | `source_name` | String | Name of reputable reference organization | `NASA Earth Observatory` |
| 9 | `source_url` | String | URL of the reference source authority | `https://earthobservatory.nasa.gov` |
| 10 | `annotation_notes` | String | Rationale explaining category, facts, and span choice | `Verified against section 2.1...` |

---

## 6. Annotation Workflow & Quality Checklist

Before submitting an annotated row to the benchmark dataset:
- [ ] Has the reference text been copied verbatim from a credible geographic source?
- [ ] Is the source URL valid and functional?
- [ ] Has the label been chosen solely based on the text in `reference_context`?
- [ ] If `expected_verdict` is `CLEAN`, is `expected_unsupported_spans` strictly `[]`?
- [ ] If `expected_verdict` is `HALLUCINATED`, does `expected_unsupported_spans` contain at least one valid span?
- [ ] Has `answer[start:end] == text` been verified with programmatic indexing?
- [ ] Is the span minimal and free of accidental whitespace or punctuation?

