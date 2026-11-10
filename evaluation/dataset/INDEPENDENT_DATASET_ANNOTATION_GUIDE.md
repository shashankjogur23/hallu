# Independent Geography Benchmark Dataset Annotation Guide (Phase 8 Step 3)

**Dataset Name:** `independent_geography_dataset.json` / `independent_geography_dataset.csv`  
**Dataset Version:** 1.0.0  
**Creation Date:** November 11, 2026  
**Total Samples:** 100  
**Categories:** Supported (25), Contradictory (25), Unsupported (25), Mixed (25)  
**Domain:** Physical and Political World Geography (Unseen Entities)  

---

## 1. Purpose and Independence Guarantee

The purpose of this independent benchmark is to provide a rigorous, out-of-sample validation of HalluGuard's hallucination detection capabilities, specifically comparing the baseline ModernBERT token classification model against the experimental DeBERTa-v3 NLI hybrid architecture.

### Strict Independence Protocol
1. **Zero Overlap:** None of the 100 test samples reuse, paraphrase, or duplicate facts or entities from the original 60-example geography dataset (`geography_evaluation_dataset.json`).
2. **Fresh Entity Scope:** Features entities completely absent from the baseline dataset, including:
   - *Mountains/Volcanoes:* Mount Aconcagua, Denali, Mount Elbrus, Vinson Massif, Mount Chimborazo, Mount Etna.
   - *Rivers:* Congo River, Yangtze River, Volga River.
   - *Lakes/Seas:* Lake Tanganyika, Badwater Basin, Sargasso Sea.
   - *Islands/Straits:* Borneo, New Guinea, Bosporus Strait, Strait of Malacca.
   - *Geological Wonders:* Danakil Depression, Iguazu Falls, Lambert Glacier, Ushuaia, Great Blue Hole, La Rinconada, Bern, Ankara.
3. **No Target Leakage:** The dataset was constructed before executing any evaluation runs and remained frozen without post-hoc tuning.

---

## 2. Category Definitions and Ground-Truth Rules

| Category | Sample Count | Expected Verdict | Expected Spans | Definition & Annotation Criteria |
| :--- | :---: | :---: | :---: | :--- |
| **Supported** | 25 | `CLEAN` | `[]` (Empty) | Every asserted proposition in the generated answer is directly and unambiguously entailed by the provided reference context. Includes complex sentences, multiple entities, and distractors, all factually grounded. |
| **Contradictory** | 25 | `HALLUCINATED` | 1 span per item | The generated answer contains an assertion that directly conflicts with facts stated in the reference context. Includes entity swaps, numerical falsifications, ordinal substitutions, comparative reversals, and negation reversals. |
| **Unsupported** | 25 | `HALLUCINATED` | 1 span per item | The generated answer introduces a claim, historical date, engineering detail, or biological assertion that is completely absent from the reference context, even if potentially true in the real world. |
| **Mixed** | 25 | `HALLUCINATED` | 1 span per item | The generated answer contains a compound or multi-clause sentence where one clause is factually supported by the context, but another clause contains a contradictory or unsupported claim. |

---

## 3. Ground-Truth Span Boundary Standards

1. **Character Indexing:** 0-indexed, half-open interval `[start, end)`.
2. **Exact Slice Invariant:** For every annotated span:
   $$\text{answer}[\text{start}:\text{end}] \equiv \text{span.text}$$
   This invariant is programmatically asserted during dataset compilation.
3. **Span Granularity:**
   - For **Contradictory** cases, the span isolates the exact contradictory phrase, entity, or numerical attribute (e.g. `"Chile"`, `"roughly 85 metres"`, `"second-highest mountain peak in North America, ranking just below Mount Logan"`).
   - For **Unsupported** cases, the span encompasses the complete ungrounded clause or predicate phrase.
   - For **Mixed** cases, the span isolates the non-supported clause, preserving the supported clause outside the span boundary.

---

## 4. Reference Source Standards

All reference contexts were derived from official, authoritative geographic, geodetic, and environmental databases:
- **USGS:** United States Geological Survey (National Elevation Dataset, Antarctic Names Database)
- **NASA:** Earth Observatory
- **NOAA:** National Oceanic and Atmospheric Administration (Ocean Exploration, Fisheries)
- **UNESCO:** World Heritage Centre
- **IHO:** International Hydrographic Organization
- **IGN:** Instituto Geográfico Nacional (Argentina, France)
- **National Park Service:** Death Valley National Park
- **Encyclopaedia Britannica:** Academic Geography Entries
- **UNEP:** United Nations Environment Programme Island Directory
- **INGV:** Istituto Nazionale di Geofisica e Vulcanologia (Catania, Italy)

---

## 5. Dataset Schema Specification

### JSON Format (`independent_geography_dataset.json`):
```json
[
  {
    "test_id": "IND-CON-001",
    "category": "contradictory",
    "question": "In which country is Mount Aconcagua located?",
    "reference_context": "Mount Aconcagua is located in the Andes mountain range in Mendoza Province, Argentina. It is the highest mountain in both the Southern and Western Hemispheres at 6,961 metres.",
    "generated_answer": "Mount Aconcagua is located in the Andes mountain range of Chile.",
    "expected_verdict": "HALLUCINATED",
    "expected_unsupported_spans": [
      {
        "start": 57,
        "end": 62,
        "text": "Chile"
      }
    ],
    "source_name": "IGN Argentina",
    "source_url": "https://www.ign.gob.ar",
    "annotation_notes": "Entity swap: context states Argentina; answer asserts Chile."
  }
]
```

### CSV Format (`independent_geography_dataset.csv`):
Fields:
- `test_id` (string): Unique identifier (`IND-SUP-001` through `IND-MIX-025`)
- `category` (string): `supported`, `contradictory`, `unsupported`, `mixed`
- `question` (string): Natural language query
- `reference_context` (string): Ground-truth reference context
- `generated_answer` (string): Model-generated answer to be verified
- `expected_verdict` (string): `CLEAN` or `HALLUCINATED`
- `expected_unsupported_spans` (JSON string): Serialized list of span objects
- `source_name` (string): Authority organization
- `source_url` (string): URL of reference authority
- `annotation_notes` (string): Detailed rationale explaining why the span is annotated as supported, contradictory, or unsupported.

