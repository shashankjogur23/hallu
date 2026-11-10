"""Phase 9 Performance Test — measures latency, memory, and throughput."""
import sys, os, time, json, statistics
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

import psutil

def get_memory_mb():
    return psutil.Process().memory_info().rss / (1024 * 1024)

print("=" * 60)
print("PHASE 9 PERFORMANCE TEST")
print("=" * 60)

# 1. Model startup time
print("\n[1] Model Startup Time")
mem_before = get_memory_mb()
t0 = time.perf_counter()

from app.services.hybrid_detector_service import hybrid_detector_service
hybrid_detector_service.load_models()

startup_time = time.perf_counter() - t0
mem_after = get_memory_mb()
print(f"  Startup time: {startup_time:.2f}s")
print(f"  Memory before: {mem_before:.1f} MB")
print(f"  Memory after:  {mem_after:.1f} MB")
print(f"  Model memory:  {mem_after - mem_before:.1f} MB")

# 2. Inference latency
print("\n[2] Inference Latency")
test_cases = [
    {
        "name": "Supported (short)",
        "answer": "The capital of France is Paris.",
        "context": ["France is a country in Europe. The capital of France is Paris."],
        "question": "What is the capital of France?"
    },
    {
        "name": "Contradicted (population)",
        "answer": "The capital of France is Paris. The population of France is 69 million.",
        "context": ["France is a country in Europe. The capital of France is Paris. The population of France is 67 million."],
        "question": "What is the capital and population?"
    },
    {
        "name": "Compound (Denali ordinal)",
        "answer": "Mount Denali is the tallest peak in North America and the second tallest in the world.",
        "context": ["Mount Denali, at 6,190 meters, is the tallest peak in North America. Mount Logan, at 5,959 meters, is the second tallest peak in North America."],
        "question": "What are the tallest peaks?"
    },
    {
        "name": "Unsupported (novel claim)",
        "answer": "Lake Baikal is the deepest lake in the world, reaching depths of 1,642 meters.",
        "context": ["Russia is the largest country in the world by area."],
        "question": "Tell me about Lake Baikal"
    },
]

all_latencies = []
results_summary = []

for tc in test_cases:
    latencies = []
    for run in range(3):  # 3 runs each
        t0 = time.perf_counter()
        result = hybrid_detector_service.verify(
            answer=tc["answer"],
            context=tc["context"],
            question=tc["question"]
        )
        elapsed = (time.perf_counter() - t0) * 1000
        latencies.append(elapsed)
    
    mean_lat = statistics.mean(latencies)
    all_latencies.extend(latencies)
    # result is a tuple: (spans, summary, contradicted, unsupported, supported, breakdown, exec_time)
    verdict = result[1].verdict
    print(f"  {tc['name']}: mean={mean_lat:.0f}ms, verdict={verdict}")
    results_summary.append({
        "name": tc["name"],
        "mean_ms": round(mean_lat, 1),
        "verdict": verdict
    })

# 3. Aggregate stats
print("\n[3] Aggregate Performance")
mean_all = statistics.mean(all_latencies)
p95 = sorted(all_latencies)[int(len(all_latencies) * 0.95)]
peak_mem = get_memory_mb()
print(f"  Mean inference latency: {mean_all:.0f} ms")
print(f"  p95 inference latency:  {p95:.0f} ms")
print(f"  Peak memory (RSS):      {peak_mem:.0f} MB")

# 4. Consecutive requests
print("\n[4] Consecutive Request Stability")
consecutive_latencies = []
for i in range(5):
    t0 = time.perf_counter()
    hybrid_detector_service.verify(
        answer="The capital of France is Paris. The population is 69 million.",
        context=["France is in Europe. The capital of France is Paris. The population of France is 67 million."],
        question="France info"
    )
    elapsed = (time.perf_counter() - t0) * 1000
    consecutive_latencies.append(elapsed)

print(f"  5 consecutive requests: {[f'{x:.0f}ms' for x in consecutive_latencies]}")
print(f"  Mean: {statistics.mean(consecutive_latencies):.0f} ms")
print(f"  Std dev: {statistics.stdev(consecutive_latencies):.0f} ms")

final_mem = get_memory_mb()
print(f"\n[5] Final Memory: {final_mem:.0f} MB")

# Save results
perf_results = {
    "startup_time_s": round(startup_time, 2),
    "model_memory_mb": round(mem_after - mem_before, 1),
    "mean_latency_ms": round(mean_all, 1),
    "p95_latency_ms": round(p95, 1),
    "peak_memory_mb": round(peak_mem, 0),
    "final_memory_mb": round(final_mem, 0),
    "consecutive_mean_ms": round(statistics.mean(consecutive_latencies), 1),
    "consecutive_stdev_ms": round(statistics.stdev(consecutive_latencies), 1),
    "test_cases": results_summary
}

out_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'phase9_performance_results.json')
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, 'w') as f:
    json.dump(perf_results, f, indent=2)
print(f"\nResults saved to: {out_path}")
print("\n✅ PERFORMANCE TEST COMPLETE")
