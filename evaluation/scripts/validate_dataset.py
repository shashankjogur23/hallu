"""Comprehensive Validation Script for HalluGuard Geography Evaluation Dataset.

Performs stringent verification of both the CSV and JSON evaluation datasets:
1. File existence and schema conformity (10 columns).
2. Exactly 60 total examples.
3. Category balance: exactly 15 per category (supported, contradictory, unsupported, mixed).
4. Uniqueness of test IDs and absence of duplicate examples.
5. Non-empty string fields (question, answer, reference_context, source_name, source_url, notes).
6. Expected verdict validity:
   - 'supported' -> 'CLEAN'
   - 'contradictory', 'unsupported', 'mixed' -> 'HALLUCINATED'
7. Span integrity and mathematical offset verification:
   - Valid JSON array of span objects with 'start', 'end', 'text'.
   - answer[start:end] == text (exact Python slicing check).
   - Zero-based indexing, start >= 0, end > start, end <= len(answer).
   - Spans are non-overlapping.
   - 'supported' examples MUST have exactly 0 spans ([]).
   - 'contradictory' and 'unsupported' MUST have at least 1 span.
   - 'mixed' MUST have at least 1 span, AND must leave supported content (spans cannot cover entire answer).
8. Source credibility and URL presence check.
9. Cross-file consistency: identical records between CSV and JSON.
"""

import sys
import json
import csv
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
CSV_PATH = DATASET_DIR / "geography_evaluation_dataset.csv"
JSON_PATH = DATASET_DIR / "geography_evaluation_dataset.json"

REQUIRED_COLUMNS = [
    "test_id",
    "category",
    "question",
    "reference_context",
    "generated_answer",
    "expected_verdict",
    "expected_unsupported_spans",
    "source_name",
    "source_url",
    "annotation_notes",
]

VALID_CATEGORIES = {"supported", "contradictory", "unsupported", "mixed"}
VALID_VERDICTS = {"CLEAN", "HALLUCINATED"}

def run_validation():
    print("=" * 80)
    print("HALLUGUARD DATASET VALIDATION HARNESS — PHASE 4, STEP 2")
    print("=" * 80)
    print(f"Target CSV:  {CSV_PATH}")
    print(f"Target JSON: {JSON_PATH}\n")

    errors = []
    warnings = []

    # 1. File existence
    if not CSV_PATH.exists():
        errors.append(f"Missing CSV file: {CSV_PATH}")
    if not JSON_PATH.exists():
        errors.append(f"Missing JSON file: {JSON_PATH}")

    if errors:
        for err in errors:
            print(f"[FAIL] {err}")
        return False

    # 2. Load CSV records
    csv_records = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != REQUIRED_COLUMNS:
            errors.append(f"CSV header mismatch. Expected {REQUIRED_COLUMNS}, got {reader.fieldnames}")
        for idx, row in enumerate(reader, start=2): # 1-based, line 1 is header
            csv_records.append((idx, row))

    # 3. Load JSON records
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        try:
            json_records = json.load(f)
        except Exception as e:
            errors.append(f"Failed to parse JSON file: {e}")
            json_records = []

    # 4. Check row counts
    print(f"[-] Checking row counts...")
    if len(csv_records) != 60:
        errors.append(f"CSV row count is {len(csv_records)}, expected exactly 60.")
    else:
        print(f"  [PASS] CSV contains exactly 60 examples.")

    if len(json_records) != 60:
        errors.append(f"JSON record count is {len(json_records)}, expected exactly 60.")
    else:
        print(f"  [PASS] JSON contains exactly 60 examples.")

    # 5. Check cross-file equivalence
    print(f"[-] Checking CSV vs JSON data parity...")
    if len(csv_records) == len(json_records) == 60:
        parity_mismatches = 0
        for (_, c_row), j_row in zip(csv_records, json_records):
            for col in ["test_id", "category", "question", "reference_context", "generated_answer", "expected_verdict", "source_name", "source_url", "annotation_notes"]:
                if c_row[col].strip() != j_row[col].strip():
                    errors.append(f"Mismatch in {c_row['test_id']} field '{col}': CSV='{c_row[col]}' vs JSON='{j_row[col]}'")
                    parity_mismatches += 1
            # Check parsed spans
            try:
                c_spans = json.loads(c_row["expected_unsupported_spans"])
                j_spans = j_row["expected_unsupported_spans"]
                if c_spans != j_spans:
                    errors.append(f"Span mismatch in {c_row['test_id']}: CSV spans != JSON spans")
                    parity_mismatches += 1
            except Exception as e:
                errors.append(f"Failed to compare spans for {c_row['test_id']}: {e}")
        if parity_mismatches == 0:
            print("  [PASS] 100% data parity between CSV and JSON files.")

    # 6. Detailed per-record validation (using CSV rows as baseline)
    print(f"[-] Validating individual records and ground-truth spans...")
    seen_ids = set()
    seen_answers = set()
    category_counts = {c: 0 for c in VALID_CATEGORIES}
    source_distribution = {}

    for line_num, row in csv_records:
        test_id = row.get("test_id", "").strip()
        cat = row.get("category", "").strip()
        question = row.get("question", "").strip()
        context = row.get("reference_context", "").strip()
        answer = row.get("generated_answer", "").strip()
        verdict = row.get("expected_verdict", "").strip()
        raw_spans = row.get("expected_unsupported_spans", "").strip()
        source_name = row.get("source_name", "").strip()
        source_url = row.get("source_url", "").strip()
        notes = row.get("annotation_notes", "").strip()

        # Check for empty essential fields
        for field_name, val in [
            ("test_id", test_id),
            ("category", cat),
            ("question", question),
            ("reference_context", context),
            ("generated_answer", answer),
            ("expected_verdict", verdict),
            ("source_name", source_name),
            ("source_url", source_url),
            ("annotation_notes", notes),
        ]:
            if not val:
                errors.append(f"Line {line_num} ({test_id}): Field '{field_name}' is empty.")

        # ID uniqueness
        if test_id in seen_ids:
            errors.append(f"Line {line_num}: Duplicate test_id '{test_id}'.")
        seen_ids.add(test_id)

        # Answer uniqueness
        if answer in seen_answers:
            errors.append(f"Line {line_num} ({test_id}): Duplicate answer text detected.")
        seen_answers.add(answer)

        # Category validity
        if cat not in VALID_CATEGORIES:
            errors.append(f"Line {line_num} ({test_id}): Invalid category '{cat}'.")
        else:
            category_counts[cat] += 1

        # Verdict validity and mapping rules
        if verdict not in VALID_VERDICTS:
            errors.append(f"Line {line_num} ({test_id}): Invalid verdict '{verdict}'.")
        elif cat == "supported" and verdict != "CLEAN":
            errors.append(f"Line {line_num} ({test_id}): Supported examples must have expected_verdict='CLEAN', got '{verdict}'.")
        elif cat in {"contradictory", "unsupported", "mixed"} and verdict != "HALLUCINATED":
            errors.append(f"Line {line_num} ({test_id}): Category '{cat}' must have expected_verdict='HALLUCINATED', got '{verdict}'.")

        # Source URL validity
        if source_url:
            parsed = urlparse(source_url)
            if not (parsed.scheme in ("http", "https") and parsed.netloc):
                errors.append(f"Line {line_num} ({test_id}): Invalid source URL '{source_url}'.")
            domain = parsed.netloc
            source_distribution[domain] = source_distribution.get(domain, 0) + 1

        # Span parsing and offset validation
        try:
            spans = json.loads(raw_spans)
            if not isinstance(spans, list):
                errors.append(f"Line {line_num} ({test_id}): expected_unsupported_spans must be a JSON list.")
                continue

            # Category-specific span constraints
            if cat == "supported" and len(spans) != 0:
                errors.append(f"Line {line_num} ({test_id}): Supported category must have empty spans list [], found {len(spans)}.")
            elif cat in {"contradictory", "unsupported", "mixed"} and len(spans) == 0:
                errors.append(f"Line {line_num} ({test_id}): Category '{cat}' must have at least 1 expected span, found 0.")

            # Validate each span
            prev_end = -1
            total_span_len = 0
            for s_idx, span in enumerate(spans):
                if not isinstance(span, dict):
                    errors.append(f"Line {line_num} ({test_id}) span #{s_idx}: Span must be a dict.")
                    continue
                start = span.get("start")
                end = span.get("end")
                text = span.get("text")

                if not (isinstance(start, int) and isinstance(end, int) and isinstance(text, str)):
                    errors.append(f"Line {line_num} ({test_id}) span #{s_idx}: Invalid types in span {span}.")
                    continue

                if start < 0 or end > len(answer) or start >= end:
                    errors.append(f"Line {line_num} ({test_id}) span #{s_idx}: Out of bounds offsets [start={start}, end={end}] for answer len={len(answer)}.")
                    continue

                if start < prev_end:
                    errors.append(f"Line {line_num} ({test_id}) span #{s_idx}: Overlapping span detected [start={start} < prev_end={prev_end}].")
                prev_end = end

                # Verify exact character slice equality
                actual_slice = answer[start:end]
                if actual_slice != text:
                    errors.append(
                        f"Line {line_num} ({test_id}) span #{s_idx} OFFSET MISMATCH!\n"
                        f"  Expected text:  '{text}'\n"
                        f"  Actual slice:   '{actual_slice}' [start={start}, end={end}]"
                    )

                total_span_len += (end - start)

            # Mixed category check: spans cannot cover 100% of the answer
            if cat == "mixed":
                if total_span_len >= len(answer.strip()):
                    errors.append(f"Line {line_num} ({test_id}): Mixed example spans cover the entire answer. Must retain supported content.")

        except Exception as e:
            errors.append(f"Line {line_num} ({test_id}): Failed to parse JSON in expected_unsupported_spans: {e}")

    # 7. Category distribution check
    print(f"[-] Checking category distribution...")
    for cat in sorted(VALID_CATEGORIES):
        count = category_counts[cat]
        status = "PASS" if count == 15 else "FAIL"
        print(f"  [{status}] Category '{cat}': {count} examples (Target: 15)")
        if count != 15:
            errors.append(f"Category '{cat}' has {count} examples, expected exactly 15.")

    # 8. Report source domain distribution
    print(f"\n[-] Source Authority Domain Distribution:")
    for domain, count in sorted(source_distribution.items(), key=lambda x: -x[1]):
        print(f"  - {domain:35s}: {count:2d} references")

    # Final summary
    print("\n" + "=" * 80)
    if errors:
        print(f"[FAIL] VALIDATION FAILED WITH {len(errors)} ERROR(S):")
        for err in errors:
            print(f"  * {err}")
        print("=" * 80)
        return False
    else:
        print("[SUCCESS] ALL 60 EXAMPLES PASSED 100% OF VALIDATION CHECKS!")
        print("  - Total Examples:             60")
        print("  - Supported (CLEAN):          15 (spans = [])")
        print("  - Contradictory (HALLUCINATED):15 (spans >= 1, minimal conflicts)")
        print("  - Unsupported (HALLUCINATED):  15 (spans >= 1, extrinsic ungrounded claims)")
        print("  - Mixed (HALLUCINATED):        15 (spans >= 1, supported portions preserved)")
        print("  - Exact Slice Offsets:        100% verified (answer[start:end] == text)")
        print("  - Parity:                     CSV and JSON datasets identical")
        print("=" * 80)
        return True

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)

