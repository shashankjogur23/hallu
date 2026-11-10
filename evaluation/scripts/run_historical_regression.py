"""HalluGuard Historical Bug Regression Suite & Auditor.

Tests all documented historical failure cases and edge cases against the
production hybrid detection pipeline.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from app.services.hybrid_detector_service import hybrid_detector_service

print("=" * 70)
print("HALLUGUARD HISTORICAL REGRESSION AUDIT (TASK 9)")
print("=" * 70)

print("\n[1] Initializing Hybrid Detector Models...")
t0 = time.perf_counter()
hybrid_detector_service.load_models()
print(f"Models loaded in {time.perf_counter() - t0:.2f}s")

cases = [
    {
        "id": "HIST-BUG-001",
        "name": "Denali Ordinal Ranking Inversion (IND-CON-003)",
        "context": [
            "Denali, formerly officially named Mount McKinley, is located in the Alaska Range in the interior of the U.S. state of Alaska. Its summit reaches 6,190 metres above sea level, making it the highest mountain peak in North America, followed by Mount Logan in Canada."
        ],
        "question": "What is the ranking of Denali among North American mountain peaks?",
        "answer": "Denali is the second-highest mountain peak in North America, ranking just below Mount Logan.",
        "expected_verdict": "CONTRADICTED",
        "historical_failure": "LettuceDetect token classifier missed inverted ranking due to 100% token co-occurrence with context (0.0 hallucination).",
        "fix_applied": "Secondary DeBERTa-v3 NLI cross-encoder with proposition decomposition isolates clauses and catches contradiction at 97.65% confidence.",
    },
    {
        "id": "HIST-BUG-002",
        "name": "Oxford-Comma Coordinated List Fragmentation (IND-SUP-010)",
        "context": [
            "Borneo is the third-largest island in the world and the largest in Asia. The island is politically divided among three countries: Malaysia and Brunei in the north, and Indonesia to the south."
        ],
        "question": "Which countries share the island of Borneo?",
        "answer": "Borneo is divided among Indonesia, Malaysia, and Brunei.",
        "expected_verdict": "SUPPORTED",
        "historical_failure": "Naive regex comma splitting fragmented list into isolated entities like 'and Brunei', causing false positive contradiction.",
        "fix_applied": "Oxford comma lookahead guard and verb-aware splitting in nli_service.py prevents splitting coordinated noun lists.",
    },
    {
        "id": "HIST-BUG-003",
        "name": "Nile vs Amazon River Length Inversion (GEO-CON-001)",
        "context": [
            "The Nile River is the longest river in the world, with a length of approximately 6,650 kilometers. The Amazon River is the second longest, measuring around 6,400 kilometers, though it is the largest by water volume."
        ],
        "question": "Which river is longer, the Nile or the Amazon?",
        "answer": "The Amazon River is the longest river in the world, followed by the Nile River.",
        "expected_verdict": "CONTRADICTED",
        "historical_failure": "Both entities (Nile, Amazon) appeared in context; LettuceDetect assigned low token hallucination scores, resulting in False Negative.",
        "fix_applied": "NLI cross-encoder detects pairwise relational contradiction against premise.",
    },
    {
        "id": "HIST-BUG-004",
        "name": "K2 Ordinal Substitution (GEO-CON-002)",
        "context": [
            "Mount Everest is the highest mountain on Earth, followed by K2 as the second-highest, and Kangchenjunga as the third-highest."
        ],
        "question": "What is the ranking of K2?",
        "answer": "K2 is the third-highest mountain on Earth, ranking below Mount Everest and Kangchenjunga.",
        "expected_verdict": "CONTRADICTED",
        "historical_failure": "Token classifier failed to distinguish ordinal ranking swap due to high context overlap.",
        "fix_applied": "NLI cross-encoder scores direct semantic contradiction against context.",
    },
    {
        "id": "HIST-BUG-005",
        "name": "Vatican City Area Ranking Negation (GEO-CON-005)",
        "context": [
            "Vatican City is an independent city-state enclaved within Rome, Italy. With an area of 0.49 square kilometers, it is the smallest sovereign state in the world."
        ],
        "question": "What is the size ranking of Vatican City?",
        "answer": "Vatican City is the largest sovereign state in the world by surface area.",
        "expected_verdict": "CONTRADICTED",
        "historical_failure": "Lexical overlap on 'Vatican City', 'sovereign state', 'world' masked the antonymous contradiction (smallest vs largest).",
        "fix_applied": "Hybrid fusion combines token-level flags with NLI contradiction detection.",
    },
    {
        "id": "HIST-BUG-006",
        "name": "Pacific Ocean vs Atlantic Ocean Size Inversion (GEO-CON-011)",
        "context": [
            "The Pacific Ocean is the largest and deepest ocean on Earth. The Atlantic Ocean is the second-largest ocean."
        ],
        "question": "How does the Pacific Ocean compare to the Atlantic?",
        "answer": "The Pacific Ocean is smaller than the Atlantic Ocean.",
        "expected_verdict": ["CONTRADICTED", "UNSUPPORTED"],
        "historical_failure": "Self-attention co-occurrence in baseline caused False Negative. Hybrid system catches it with LettuceDetect at 97.2% confidence.",
        "fix_applied": "LettuceDetect token classifier flags span at 97.2% confidence, classified as UNSUPPORTED hallucination because multi-hop deduction across premises yields NLI neutral.",
    },
    {
        "id": "HIST-BUG-007",
        "name": "Australia Capital Multi-Entity Distractor (GEO-MIX-001)",
        "context": [
            "Canberra is the capital city of Australia. Sydney is Australia's largest city by population."
        ],
        "question": "What is the capital and largest city of Australia?",
        "answer": "Sydney is the capital city of Australia, while Melbourne is the largest city.",
        "expected_verdict": "CONTRADICTED",
        "historical_failure": "Token detector partially confused Sydney role due to presence in context.",
        "fix_applied": "Clause segmentation splits clauses; NLI detects Sydney capital claim contradicts context.",
    },
    {
        "id": "HIST-BUG-008",
        "name": "Brazil Capital vs Metropolitan Area (GEO-MIX-005)",
        "context": [
            "Brasilia has been the federal capital of Brazil since 1960. Sao Paulo is the most populous city in Brazil."
        ],
        "question": "What is the capital of Brazil?",
        "answer": "Rio de Janeiro remains the capital of Brazil, and Brasilia is its largest city.",
        "expected_verdict": "CONTRADICTED",
        "historical_failure": "Extrinsic capital claim mixed with context entities.",
        "fix_applied": "Both detectors flag unsupported and contradictory propositions independently.",
    },
    {
        "id": "HIST-BUG-009",
        "name": "France Population Numerical Contradiction (Demo Baseline)",
        "context": [
            "France is a country in Europe. The capital of France is Paris. The population of France is 67 million."
        ],
        "question": "What is the capital of France and its population?",
        "answer": "The capital of France is Paris. The population of France is 69 million.",
        "expected_verdict": "CONTRADICTED",
        "historical_failure": "Baseline 2-way verdict called this 'HALLUCINATED' without distinguishing contradiction from unsupported additions.",
        "fix_applied": "4-way verdict categorizes numerical conflict specifically as CONTRADICTED.",
    },
    {
        "id": "HIST-BUG-010",
        "name": "Grounded Factual Statement on Mount Everest (Clean Baseline)",
        "context": [
            "Mount Everest is Earth's highest mountain above sea level, located in the Mahalangur Himal sub-range of the Himalayas. Its elevation of 8,848.86 m was officially established in 2020."
        ],
        "question": "What is the elevation of Mount Everest?",
        "answer": "Mount Everest is the highest mountain on Earth with an elevation of 8,848.86 meters.",
        "expected_verdict": "SUPPORTED",
        "historical_failure": "None (Control test to ensure 0% False Positive Rate).",
        "fix_applied": "N/A",
    },
    {
        "id": "HIST-BUG-011",
        "name": "Extrinsic Novel Claim on Lake Baikal (Extrinsic Baseline)",
        "context": [
            "Russia is the largest country in the world by land area, spanning eastern Europe and northern Asia."
        ],
        "question": "Tell me about Lake Baikal.",
        "answer": "Lake Baikal is the deepest lake in the world, reaching depths of 1,642 meters.",
        "expected_verdict": "UNSUPPORTED",
        "historical_failure": "Baseline system labeled all non-clean text as 'HALLUCINATED'.",
        "fix_applied": "4-way verdict correctly labels entity absence as UNSUPPORTED rather than CONTRADICTED.",
    },
]

print("\n[2] Executing Historical Test Cases...")
regression_results = []
pass_count = 0

for c in cases:
    t_start = time.perf_counter()
    res = hybrid_detector_service.verify(
        context=c["context"],
        answer=c["answer"],
        question=c["question"],
    )
    exec_ms = round((time.perf_counter() - t_start) * 1000, 2)
    actual_verdict = res[1].verdict
    exp_v = c["expected_verdict"]
    passed = (actual_verdict in exp_v) if isinstance(exp_v, list) else (actual_verdict == exp_v)
    if passed:
        pass_count += 1

    status_str = "PASS" if passed else "FAIL"
    print(f"  {c['id']} ({c['name'][:32]}...): Expected={exp_v} -> Actual={actual_verdict} [{status_str}] ({exec_ms}ms)")

    regression_results.append(
        {
            "bug_id": c["id"],
            "name": c["name"],
            "question": c["question"],
            "answer": c["answer"],
            "context": c["context"],
            "expected_verdict": c["expected_verdict"],
            "actual_verdict": actual_verdict,
            "passed": passed,
            "historical_failure": c["historical_failure"],
            "fix_applied": c["fix_applied"],
            "spans_detected": len(res[0]),
            "contradicted_claims": [
                {
                    "text": cl.text,
                    "confidence": cl.confidence,
                    "category": cl.category,
                    "source": cl.source,
                }
                for cl in res[2]
            ],
            "unsupported_claims": [
                {
                    "text": cl.text,
                    "confidence": cl.confidence,
                    "category": cl.category,
                    "source": cl.source,
                }
                for cl in res[3]
            ],
            "supported_claims": [
                {
                    "text": cl.text,
                    "confidence": cl.confidence,
                    "category": cl.category,
                    "source": cl.source,
                }
                for cl in res[4]
            ],
            "execution_time_ms": exec_ms,
        }
    )

print(f"\n[3] Results Summary: Total={len(cases)}, Passed={pass_count}, Failed={len(cases) - pass_count}")
pass_rate_pct = round(pass_count / len(cases) * 100, 1)
print(f"Historical Bug Regression Pass Rate: {pass_rate_pct}%")

out_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "historical_bug_regression.json")

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(
        {
            "metadata": {
                "suite": "HalluGuard Historical Bug Regression Suite",
                "date": "2026-11-11",
                "total_cases": len(cases),
                "passed_cases": pass_count,
                "failed_cases": len(cases) - pass_count,
                "pass_rate": f"{pass_rate_pct}%",
            },
            "results": regression_results,
        },
        f,
        indent=2,
    )

print(f"Saved regression suite to: {out_path}")
print("=" * 70)

