import os
import sys

sys.path.insert(0, r"F:\final project\HalluGuard\backend")
from app.services.hybrid_detector_service import hybrid_detector_service

hybrid_detector_service.load_models()

# Case 10: Mount Everest
ctx10 = [
    "Mount Everest is Earth's highest mountain above sea level, located in the Mahalangur Himal sub-range of the Himalayas. Its elevation of 8,848.86 m was officially established in 2020."
]
ans10 = "Mount Everest is the highest mountain on Earth with an elevation of 8,848.86 meters."
q10 = "What is the elevation of Mount Everest?"

print("*** Case 10: Mount Everest ***")
let_spans, summary, _ = hybrid_detector_service._detector.predict(ctx10, ans10, q10)
print("Lettuce Spans:", [(s.text, s.confidence, s.category) for s in let_spans])
nli_res = hybrid_detector_service._nli.analyze_answer(
    "\n\n".join(ctx10), ans10, q10
)
print("NLI Contradiction Spans:", nli_res["contradictory_spans"])
print("NLI Max Contra:", nli_res["max_contradiction_score"])
for s in nli_res["all_segments"]:
  print(
      "  Segment:",
      s["text"],
      "| Label:",
      s["label"],
      "| Contra:",
      s["prob_contradiction"],
      "| Entail:",
      s["prob_entailment"],
      "| Neutral:",
      s["prob_neutral"],
  )

# Case 6: Pacific Ocean
ctx6 = [
    "The Pacific Ocean is the largest and deepest ocean on Earth. The Atlantic"
    " Ocean is the second-largest ocean."
]
ans6 = "The Pacific Ocean is smaller than the Atlantic Ocean."
q6 = "How does the Pacific Ocean compare to the Atlantic?"
print("\n*** Case 6: Pacific Ocean ***")
let_spans6, summary6, _ = hybrid_detector_service._detector.predict(
    ctx6, ans6, q6
)
print("Lettuce Spans:", [(s.text, s.confidence, s.category) for s in let_spans6])
nli_res6 = hybrid_detector_service._nli.analyze_answer(
    "\n\n".join(ctx6), ans6, q6
)
print("NLI Contradiction Spans:", nli_res6["contradictory_spans"])
print("NLI Max Contra:", nli_res6["max_contradiction_score"])
for s in nli_res6["all_segments"]:
  print(
      "  Segment:",
      s["text"],
      "| Label:",
      s["label"],
      "| Contra:",
      s["prob_contradiction"],
      "| Entail:",
      s["prob_entailment"],
      "| Neutral:",
      s["prob_neutral"],
  )

