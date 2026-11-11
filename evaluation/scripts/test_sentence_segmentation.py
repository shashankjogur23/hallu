"""Unit tests and benchmarks for robust sentence and clause segmentation.

Tests:
1. Decimal numbers (e.g. 8,848.86 meters)
2. Honorifics and titles (Dr. Smith, Mr. Brown, Ms. Davis)
3. Acronyms and countries (U.S. State, U.K., E.U.)
4. Scholarly abbreviations (e.g., i.e., etc.)
5. Multiple sentences and diverse punctuation (. ! ?)
6. Exact character offset validation
"""

import re
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
from app.services.nli_service import nli_service

print("=" * 70)
print("SENTENCE SEGMENTATION & ABBREVIATION BENCHMARK (TASK 3)")
print("=" * 70)

test_suite = [
    {
        "id": "SEG-001",
        "name": "Decimal Number Preservation (8,848.86)",
        "text": "Mount Everest elevation is 8,848.86 meters. It is tall.",
        "expected_sentences": [
            "Mount Everest elevation is 8,848.86 meters.",
            "It is tall.",
        ],
    },
    {
        "id": "SEG-002",
        "name": "Honorific Title (Dr. Smith)",
        "text": "Dr. Smith visited the clinic yesterday. He was on time.",
        "expected_sentences": [
            "Dr. Smith visited the clinic yesterday.",
            "He was on time.",
        ],
    },
    {
        "id": "SEG-003",
        "name": "Acronym Entity (U.S. State)",
        "text": "Denali is in the U.S. State of Alaska. Its peak is high.",
        "expected_sentences": [
            "Denali is in the U.S. State of Alaska.",
            "Its peak is high.",
        ],
    },
    {
        "id": "SEG-004",
        "name": "Latin Abbreviations (e.g. and i.e.)",
        "text": "Some countries (e.g. France, Germany) are in Europe. That is, i.e. the EU.",
        "expected_sentences": [
            "Some countries (e.g. France, Germany) are in Europe.",
            "That is, i.e. the EU.",
        ],
    },
    {
        "id": "SEG-005",
        "name": "Multiple Punctuation Marks (! ? .)",
        "text": "Hello! How are you? I am fine. Great.",
        "expected_sentences": [
            "Hello!",
            "How are you?",
            "I am fine.",
            "Great.",
        ],
    },
    {
        "id": "SEG-006",
        "name": "Multi-Clause Compound Complex Sentence",
        "text": "The summit reaches 6,190 metres above sea level, making it the highest mountain peak in North America, followed by Mount Logan in Canada.",
        "expected_sentences": [
            "The summit reaches 6,190 metres above sea level, making it the highest mountain peak in North America, followed by Mount Logan in Canada."
        ],
    },
]

passed_count = 0

for item in test_suite:
    text = item["text"]
    expected = item["expected_sentences"]
    segments = nli_service.segment_answer(text)
    
    # Extract only sentence-level segments
    actual_sentences = []
    offset_valid = True
    for s_start, s_end, s_text, s_type, _ in segments:
        if s_type == "sentence":
            actual_sentences.append(s_text)
            # Verify exact offset parity against original text
            if text[s_start:s_end] != s_text:
                offset_valid = False
                print(f"  [ERROR] Offset mismatch: slice '{text[s_start:s_end]}' != '{s_text}'")

    # If full answer is 1 sentence, segment_answer stores it as full_answer
    if len(expected) == 1 and not actual_sentences:
        actual_sentences = [segments[0][2]]

    is_pass = (actual_sentences == expected) and offset_valid
    if is_pass:
        passed_count += 1
        print(f"✓ [{item['id']}] {item['name']}: PASS ({len(actual_sentences)} sentences)")
    else:
        print(f"✗ [{item['id']}] {item['name']}: FAIL")
        print(f"    Expected: {expected}")
        print(f"    Actual:   {actual_sentences}")

print(f"\nTotal: {len(test_suite)}, Passed: {passed_count}, Failed: {len(test_suite) - passed_count}")
print("=" * 70)

