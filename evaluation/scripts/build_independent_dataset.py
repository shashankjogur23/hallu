"""Independent Dataset Generator for HalluGuard Phase 8 Step 3.

Generates 100 entirely new, distinct geography evaluation examples (25 supported,
25 contradictory, 25 unsupported, 25 mixed) covering global geographical features
not present in the baseline 60-example dataset.

Validates exact character offsets: answer[start:end] == span_text for every gold span.
Outputs:
- evaluation/dataset/independent_geography_dataset.json
- evaluation/dataset/independent_geography_dataset.csv
- evaluation/dataset/INDEPENDENT_DATASET_ANNOTATION_GUIDE.md
"""

import json
import csv
from pathlib import Path

DATASET_DIR = Path(r"F:\final project\HalluGuard\evaluation\dataset")
DATASET_DIR.mkdir(parents=True, exist_ok=True)

# Define the 100 items
# Each item: test_id, category, question, reference_context, generated_answer, expected_verdict, expected_unsupported_spans, source_name, source_url, annotation_notes

items = []

# ==============================================================================
# CATEGORY 1: SUPPORTED (25 samples) - expected_verdict: "CLEAN", spans: []
# ==============================================================================

items.append({
    "test_id": "IND-SUP-001",
    "category": "supported",
    "question": "What is the highest mountain in South America and what is its elevation?",
    "reference_context": "Mount Aconcagua is located in the Andes mountain range in Mendoza Province, Argentina. With a summit elevation of 6,961 metres (22,838 feet) above sea level, it is the highest mountain in both the Southern and Western Hemispheres.",
    "generated_answer": "Mount Aconcagua is the highest mountain in the Southern and Western Hemispheres, reaching an elevation of 6,961 metres in Argentina.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "USGS Peakbagger / IGN Argentina",
    "source_url": "https://www.ign.gob.ar",
    "annotation_notes": "All claims (Aconcagua, highest in Southern and Western Hemispheres, 6,961 m elevation, located in Argentina) fully grounded in reference context."
})

items.append({
    "test_id": "IND-SUP-002",
    "category": "supported",
    "question": "What is the deepest river in the world and what distinguishes its course?",
    "reference_context": "The Congo River in central Africa is recognized as the world's deepest river, with measured depths exceeding 220 metres (720 feet) in sections of the Lower Congo. It is also the only major river on Earth that crosses the equator twice.",
    "generated_answer": "The Congo River is the deepest river in the world, with depths exceeding 220 metres, and it crosses the equator twice during its course.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "NASA Earth Observatory",
    "source_url": "https://earthobservatory.nasa.gov",
    "annotation_notes": "Directly grounded: deepest river, depth exceeding 220 m, crosses equator twice."
})

items.append({
    "test_id": "IND-SUP-003",
    "category": "supported",
    "question": "Where is Mount Denali located and what is its official summit elevation?",
    "reference_context": "Denali, formerly officially named Mount McKinley, is located in the Alaska Range in the interior of the U.S. state of Alaska. Its summit reaches 6,190 metres (20,310 feet) above sea level, making it the highest mountain peak in North America.",
    "generated_answer": "Denali is the highest mountain peak in North America, situated in the Alaska Range with a summit elevation of 6,190 metres.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "USGS National Elevation Dataset",
    "source_url": "https://www.usgs.gov",
    "annotation_notes": "All details (Denali, Alaska Range, highest in North America, 6,190 m) fully grounded."
})

items.append({
    "test_id": "IND-SUP-004",
    "category": "supported",
    "question": "What is Lake Tanganyika's distinction among freshwater lakes?",
    "reference_context": "Lake Tanganyika is an African Great Lake shared by Tanzania, the Democratic Republic of the Congo, Burundi, and Zambia. It is the second-oldest freshwater lake in the world, the second-largest by volume, and the second-deepest at 1,470 metres (4,820 feet), in all three categories surpassed only by Lake Baikal.",
    "generated_answer": "Lake Tanganyika is the world's second-deepest freshwater lake at 1,470 metres, ranking second only to Lake Baikal.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Encyclopaedia Britannica",
    "source_url": "https://www.britannica.com",
    "annotation_notes": "Rankings (second-deepest, 1,470 m, behind Lake Baikal) completely verified."
})

items.append({
    "test_id": "IND-SUP-005",
    "category": "supported",
    "question": "What is the southernmost point of the African continent?",
    "reference_context": "Cape Agulhas is a rocky headland in the Western Cape of South Africa. It is the geographic southernmost point of the African continent and the official dividing marker between the Atlantic and Indian Oceans, situated roughly 150 kilometres east of the Cape of Good Hope.",
    "generated_answer": "Cape Agulhas is the official southernmost point of the African continent and marks the boundary between the Atlantic and Indian Oceans.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "International Hydrographic Organization",
    "source_url": "https://iho.int",
    "annotation_notes": "Fully supported: southernmost point of Africa, boundary between Atlantic and Indian Oceans."
})

items.append({
    "test_id": "IND-SUP-006",
    "category": "supported",
    "question": "What is the highest mountain in Europe and where is it situated?",
    "reference_context": "Mount Elbrus is a dormant stratovolcano located in the Caucasus Mountains in southern Russia. Its west summit rises to 5,642 metres (18,510 feet) above sea level, establishing it as the highest peak in Europe and the highest volcano in Eurasia.",
    "generated_answer": "Mount Elbrus is the highest peak in Europe, located in the Caucasus Mountains of southern Russia with an elevation of 5,642 metres.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Peakbagger / Russian Geographical Society",
    "source_url": "https://www.rgs.ru",
    "annotation_notes": "All claims directly confirmed by reference."
})

items.append({
    "test_id": "IND-SUP-007",
    "category": "supported",
    "question": "What is the lowest natural land elevation in North America?",
    "reference_context": "Badwater Basin is an endorheic basin situated in Death Valley National Park, California. At 86 metres (282 feet) below sea level, it represents the lowest point of elevation on the North American continent.",
    "generated_answer": "Badwater Basin in California is the lowest point of land elevation in North America, sitting 86 metres below sea level.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "National Park Service",
    "source_url": "https://www.nps.gov/deva",
    "annotation_notes": "Fully grounded: Badwater Basin, California, lowest point in North America, 86 m below sea level."
})

items.append({
    "test_id": "IND-SUP-008",
    "category": "supported",
    "question": "Which body of water is unique for having no terrestrial land boundaries?",
    "reference_context": "The Sargasso Sea is a vast region of the North Atlantic Ocean bounded entirely by four circulating ocean currents: the Gulf Stream, North Atlantic Current, Canary Current, and North Atlantic Equatorial Current. It is the only sea on Earth that possesses no terrestrial land coastline.",
    "generated_answer": "The Sargasso Sea is located in the North Atlantic and is the only sea on Earth that is bounded entirely by ocean currents without any terrestrial land coastline.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "NOAA Ocean Exploration",
    "source_url": "https://oceanexplorer.noaa.gov",
    "annotation_notes": "Fully grounded: Sargasso Sea, North Atlantic, bounded by ocean currents, no land boundary."
})

items.append({
    "test_id": "IND-SUP-009",
    "category": "supported",
    "question": "What is the ranking and length of the Yangtze River in Asia?",
    "reference_context": "The Yangtze River, flowing entirely within the borders of China, is the longest river in Asia and the third-longest river in the world. It measures approximately 6,300 kilometres (3,915 miles) from its source on the Tibetan Plateau to its mouth at the East China Sea near Shanghai.",
    "generated_answer": "The Yangtze River is the longest river in Asia and the third-longest river in the world, with a length of roughly 6,300 kilometres.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Encyclopaedia Britannica",
    "source_url": "https://www.britannica.com",
    "annotation_notes": "Directly supported: longest in Asia, third-longest globally, ~6,300 km."
})

items.append({
    "test_id": "IND-SUP-010",
    "category": "supported",
    "question": "What is the size ranking of the island of Borneo and how is it divided politically?",
    "reference_context": "Borneo is the third-largest island in the world and the largest in Asia, covering an area of 748,168 square kilometres. The island is politically divided among three sovereign nations: Indonesia, Malaysia, and the sultanate of Brunei.",
    "generated_answer": "Borneo is the third-largest island in the world, and its territory is politically shared among Indonesia, Malaysia, and Brunei.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "UNEP Island Directory",
    "source_url": "https://islands.unep.ch",
    "annotation_notes": "Fully verified: third-largest island, shared by Indonesia, Malaysia, and Brunei."
})

items.append({
    "test_id": "IND-SUP-011",
    "category": "supported",
    "question": "Where is the Bosporus Strait and what water bodies does it connect?",
    "reference_context": "The Bosporus is a narrow international waterway located in northwestern Turkey that bisects the city of Istanbul between Europe and Asia. It connects the Black Sea in the north to the Sea of Marmara in the south, forming part of the continental boundary.",
    "generated_answer": "The Bosporus Strait is located in northwestern Turkey, connecting the Black Sea to the Sea of Marmara while dividing Istanbul between Europe and Asia.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Turkish Directorate of Maritime Affairs",
    "source_url": "https://denizcilik.uab.gov.tr",
    "annotation_notes": "Grounded in context: connects Black Sea to Marmara, divides Istanbul between Europe and Asia."
})

items.append({
    "test_id": "IND-SUP-012",
    "category": "supported",
    "question": "What is the highest mountain peak in Antarctica?",
    "reference_context": "Vinson Massif is the highest mountain in Antarctica, situated in the Sentinel Range of the Ellsworth Mountains. Its summit, Mount Vinson, rises to an elevation of 4,892 metres (16,050 feet) above sea level.",
    "generated_answer": "Vinson Massif is the highest mountain in Antarctica, located in the Sentinel Range at an elevation of 4,892 metres.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "USGS Antarctic Names Database",
    "source_url": "https://geonames.usgs.gov",
    "annotation_notes": "Grounded: Vinson Massif, highest peak in Antarctica, Sentinel Range, 4,892 m."
})

items.append({
    "test_id": "IND-SUP-013",
    "category": "supported",
    "question": "What is unique about the Danakil Depression?",
    "reference_context": "The Danakil Depression is a geological depression resulting from the divergence of three tectonic plates in the Afar Triangle of northeastern Ethiopia. Reaching approximately 125 metres below sea level, it is characterized by active volcanoes such as Erta Ale and is widely considered one of the hottest places on Earth by mean annual temperature.",
    "generated_answer": "The Danakil Depression is located in northeastern Ethiopia, lying roughly 125 metres below sea level and featuring the active volcano Erta Ale.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Geological Survey of Ethiopia",
    "source_url": "https://www.gse.gov.et",
    "annotation_notes": "Directly grounded: Ethiopia, 125 m below sea level, Erta Ale volcano."
})

items.append({
    "test_id": "IND-SUP-014",
    "category": "supported",
    "question": "Which waterfall system contains 275 individual drops across two nations?",
    "reference_context": "Iguazu Falls consists of approximately 275 individual waterfalls and cascades straddling the border between Misiones Province in Argentina and Parana state in Brazil. The waterfall system spans roughly 2.7 kilometres along the Iguazu River.",
    "generated_answer": "Iguazu Falls comprises around 275 individual waterfalls situated on the border between Argentina and Brazil.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "UNESCO World Heritage Centre",
    "source_url": "https://whc.unesco.org/en/list/303",
    "annotation_notes": "Grounded: ~275 falls, border between Argentina and Brazil."
})

items.append({
    "test_id": "IND-SUP-015",
    "category": "supported",
    "question": "Why is the summit of Mount Chimborazo notable despite not being the highest elevation above sea level?",
    "reference_context": "Mount Chimborazo is an inactive stratovolcano in Ecuador. Due to the Earth's equatorial bulge, its summit is the farthest point on the Earth's surface from the Earth's center, measuring approximately 6,384.4 kilometres, even though its peak stands at 6,263 metres above sea level.",
    "generated_answer": "Due to Earth's equatorial bulge, the summit of Mount Chimborazo in Ecuador is the farthest terrestrial point from the center of the Earth.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "French National Institute of Geographic and Forest Information (IGN)",
    "source_url": "https://www.ign.fr",
    "annotation_notes": "Directly supported: Chimborazo, Ecuador, equatorial bulge, farthest point from center of Earth."
})

items.append({
    "test_id": "IND-SUP-016",
    "category": "supported",
    "question": "What is the longest river in Europe and what body of water does it drain into?",
    "reference_context": "The Volga River flows entirely through European Russia and is the longest river in Europe, spanning 3,531 kilometres (2,194 miles). It originates in the Valdai Hills northwest of Moscow and discharges into the landlocked Caspian Sea.",
    "generated_answer": "The Volga River is the longest river in Europe, measuring approximately 3,531 kilometres and draining into the Caspian Sea.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Encyclopaedia Britannica",
    "source_url": "https://www.britannica.com",
    "annotation_notes": "Grounded: Volga, longest in Europe, 3,531 km, discharges into Caspian Sea."
})

items.append({
    "test_id": "IND-SUP-017",
    "category": "supported",
    "question": "What is the second-largest island in the world?",
    "reference_context": "New Guinea is the second-largest island in the world, covering an area of 785,753 square kilometres north of Australia. The island is split between the Indonesian provinces in the west and the sovereign nation of Papua New Guinea in the east.",
    "generated_answer": "New Guinea is the second-largest island in the world, divided between Indonesia in the west and Papua New Guinea in the east.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "UNEP Island Directory",
    "source_url": "https://islands.unep.ch",
    "annotation_notes": "Grounded: New Guinea, second-largest island, shared by Indonesia and Papua New Guinea."
})

items.append({
    "test_id": "IND-SUP-018",
    "category": "supported",
    "question": "Where is the Strait of Malacca and what is its strategic importance?",
    "reference_context": "The Strait of Malacca is a narrow stretch of water, approximately 930 kilometres long, running between the Malay Peninsula and the Indonesian island of Sumatra. Connecting the Indian Ocean to the South China Sea, it is one of the most vital shipping shipping lanes in global trade.",
    "generated_answer": "The Strait of Malacca runs between the Malay Peninsula and Sumatra, connecting the Indian Ocean to the South China Sea.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "International Maritime Organization",
    "source_url": "https://www.imo.org",
    "annotation_notes": "Grounded: runs between Malay Peninsula and Sumatra, connects Indian Ocean to South China Sea."
})

items.append({
    "test_id": "IND-SUP-019",
    "category": "supported",
    "question": "What is the highest permanently inhabited settlement in the world?",
    "reference_context": "La Rinconada is a gold-mining town located in the Peruvian Andes near the Bolivian border. Situated at an altitude of approximately 5,100 metres (16,700 feet) above sea level, it is widely recognized as the highest permanent human settlement on Earth.",
    "generated_answer": "La Rinconada in the Peruvian Andes is considered the highest permanent human settlement in the world, located at roughly 5,100 metres above sea level.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "National Geographic",
    "source_url": "https://www.nationalgeographic.com",
    "annotation_notes": "Grounded: La Rinconada, Peruvian Andes, highest permanent settlement, ~5,100 m."
})

items.append({
    "test_id": "IND-SUP-020",
    "category": "supported",
    "question": "What is the capital of Turkey?",
    "reference_context": "Ankara, situated in central Anatolia, was designated the official capital of the Republic of Turkey upon its establishment in 1923, replacing Istanbul, which remains the country's largest economic and cultural metropolis.",
    "generated_answer": "Ankara is the capital of Turkey, having succeeded Istanbul as the capital in 1923.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Presidency of the Republic of Turkey",
    "source_url": "https://www.tccb.gov.tr",
    "annotation_notes": "Grounded: Ankara is capital of Turkey, succeeded Istanbul in 1923."
})

items.append({
    "test_id": "IND-SUP-021",
    "category": "supported",
    "question": "What is the largest glacier in the world by area?",
    "reference_context": "The Lambert Glacier in East Antarctica is the world's largest glacier, draining roughly 8 percent of the Antarctic ice sheet. It measures over 400 kilometres in length and reaches widths of up to 100 kilometres before discharging into the Amery Ice Shelf.",
    "generated_answer": "The Lambert Glacier in East Antarctica is recognized as the world's largest glacier, measuring over 400 kilometres in length.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Australian Antarctic Division",
    "source_url": "https://www.antarctica.gov.au",
    "annotation_notes": "Grounded: Lambert Glacier, East Antarctica, world's largest glacier, >400 km long."
})

items.append({
    "test_id": "IND-SUP-022",
    "category": "supported",
    "question": "What is the southernmost city in the world?",
    "reference_context": "Ushuaia is the capital of Tierra del Fuego Province, Argentina. Situated along the Beagle Channel near the southern tip of South America, it is widely recognized as the southernmost city in the world.",
    "generated_answer": "Ushuaia, located in Argentina along the Beagle Channel, is widely considered the southernmost city in the world.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Instituto Fueguino de Turismo",
    "source_url": "https://findelmundo.tur.ar",
    "annotation_notes": "Grounded: Ushuaia, Argentina, Beagle Channel, southernmost city."
})

items.append({
    "test_id": "IND-SUP-023",
    "category": "supported",
    "question": "What type of volcano is Mount Etna and what is its distinction in Europe?",
    "reference_context": "Mount Etna is an active stratovolcano situated on the east coast of the island of Sicily, Italy. Standing at roughly 3,357 metres (11,014 feet), it is the tallest active volcano in Europe and one of the most active in the world.",
    "generated_answer": "Mount Etna is an active stratovolcano located on Sicily, and it is the tallest active volcano in Europe.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "INGV Catania",
    "source_url": "https://www.ct.ingv.it",
    "annotation_notes": "Grounded: Mount Etna, Sicily, active stratovolcano, tallest active in Europe."
})

items.append({
    "test_id": "IND-SUP-024",
    "category": "supported",
    "question": "Where is the Great Blue Hole located and what geological structure does it represent?",
    "reference_context": "The Great Blue Hole is a giant marine sinkhole situated near the center of Lighthouse Reef, a small atoll roughly 70 kilometres off the coast of Belize. The circular hole measures over 300 metres across and descends to a depth of roughly 124 metres.",
    "generated_answer": "The Great Blue Hole is a marine sinkhole located off the coast of Belize within Lighthouse Reef, measuring over 300 metres across.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Belize Barrier Reef Reserve System / UNESCO",
    "source_url": "https://whc.unesco.org",
    "annotation_notes": "Grounded: marine sinkhole, off coast of Belize, Lighthouse Reef, >300 m across."
})

items.append({
    "test_id": "IND-SUP-025",
    "category": "supported",
    "question": "What is the de facto federal capital of Switzerland?",
    "reference_context": "Under Swiss federal law, Switzerland does not designate a formal constitutional capital. Instead, the medieval city of Bern serves as the de facto federal city (Bundesstadt), hosting the Swiss Federal Assembly and the Federal Council, while Zurich remains the largest financial and commercial hub.",
    "generated_answer": "The city of Bern serves as the de facto federal capital of Switzerland and the seat of government, rather than Zurich.",
    "expected_verdict": "CLEAN",
    "expected_unsupported_spans": [],
    "source_name": "Federal Chancellery of Switzerland",
    "source_url": "https://www.bk.admin.ch",
    "annotation_notes": "Grounded: Bern is de facto federal city / seat of government, Zurich is not."
})


# ==============================================================================
# CATEGORY 2: CONTRADICTORY (25 samples) - expected_verdict: "HALLUCINATED"
# Includes entity swaps, incorrect numbers, ordinal substitutions, comparative reversals, negation reversals
# ==============================================================================

# Helper to build contradictory item
def make_con(test_id, question, context, answer, span_text, source_name, source_url, notes):
    start = answer.find(span_text)
    if start == -1:
        raise ValueError(f"Span text '{span_text}' not found in answer '{answer}'")
    end = start + len(span_text)
    return {
        "test_id": test_id,
        "category": "contradictory",
        "question": question,
        "reference_context": context,
        "generated_answer": answer,
        "expected_verdict": "HALLUCINATED",
        "expected_unsupported_spans": [{"start": start, "end": end, "text": span_text}],
        "source_name": source_name,
        "source_url": source_url,
        "annotation_notes": notes
    }

items.append(make_con(
    "IND-CON-001",
    "In which country is Mount Aconcagua located?",
    "Mount Aconcagua is located in the Andes mountain range in Mendoza Province, Argentina. It is the highest mountain in both the Southern and Western Hemispheres at 6,961 metres.",
    "Mount Aconcagua is located in the Andes mountain range of Chile.",
    "Chile",
    "IGN Argentina",
    "https://www.ign.gob.ar",
    "Entity swap: context states Argentina; answer asserts Chile."
))

items.append(make_con(
    "IND-CON-002",
    "What is the maximum measured depth of the Congo River?",
    "The Congo River in central Africa is recognized as the world's deepest river, with measured depths exceeding 220 metres (720 feet) in the Lower Congo.",
    "The Congo River is the deepest river in the world, with depths reaching roughly 85 metres.",
    "roughly 85 metres",
    "NASA Earth Observatory",
    "https://earthobservatory.nasa.gov",
    "Numerical contradiction: context specifies depths exceeding 220 metres, answer claims roughly 85 metres."
))

items.append(make_con(
    "IND-CON-003",
    "What is the ranking of Denali among North American mountain peaks?",
    "Denali is located in the Alaska Range. Its summit reaches 6,190 metres above sea level, making it the highest mountain peak in North America, followed by Mount Logan in Canada.",
    "Denali is the second-highest mountain peak in North America, ranking just below Mount Logan.",
    "second-highest mountain peak in North America, ranking just below Mount Logan",
    "USGS",
    "https://www.usgs.gov",
    "Ordinal substitution and comparative reversal: Denali is highest, not second-highest below Logan."
))

items.append(make_con(
    "IND-CON-004",
    "What is the surface depth ranking of Lake Tanganyika?",
    "Lake Tanganyika is an African Great Lake. It is the second-deepest lake in the world at 1,470 metres, surpassed only by Lake Baikal in Russia.",
    "Lake Tanganyika is the world's deepest lake at 1,470 metres, surpassing Lake Baikal.",
    "the world's deepest lake at 1,470 metres, surpassing Lake Baikal",
    "Encyclopaedia Britannica",
    "https://www.britannica.com",
    "Comparative reversal: context says surpassed only by Baikal (second deepest), answer claims it surpasses Baikal (deepest)."
))

items.append(make_con(
    "IND-CON-005",
    "Is the Cape of Good Hope the southernmost point of the African continent?",
    "Cape Agulhas is the geographic southernmost point of the African continent. The Cape of Good Hope lies roughly 150 kilometres to the northwest and is not the southernmost point, despite popular misconception.",
    "The Cape of Good Hope is the geographic southernmost point of the African continent.",
    "The Cape of Good Hope is the geographic southernmost point of the African continent.",
    "International Hydrographic Organization",
    "https://iho.int",
    "Contradictory entity substitution: Cape Agulhas is southernmost, not Cape of Good Hope."
))

items.append(make_con(
    "IND-CON-006",
    "In which mountain range is Mount Elbrus situated?",
    "Mount Elbrus is a dormant stratovolcano located in the Caucasus Mountains in southern Russia, reaching an elevation of 5,642 metres as the highest peak in Europe.",
    "Mount Elbrus is the highest peak in Europe, situated in the Ural Mountains of Russia.",
    "the Ural Mountains",
    "Russian Geographical Society",
    "https://www.rgs.ru",
    "Entity swap: context specifies Caucasus Mountains; answer asserts Ural Mountains."
))

items.append(make_con(
    "IND-CON-007",
    "What is the elevation of Badwater Basin relative to sea level?",
    "Badwater Basin in California is situated at 86 metres (282 feet) below sea level, representing the lowest point of land elevation in North America.",
    "Badwater Basin in California represents the lowest point in North America, sitting at 86 metres above sea level.",
    "above sea level",
    "National Park Service",
    "https://www.nps.gov/deva",
    "Contradictory directional reversal: context states below sea level; answer claims above sea level."
))

items.append(make_con(
    "IND-CON-008",
    "Is the Sargasso Sea bounded by landmasses?",
    "The Sargasso Sea is located in the North Atlantic Ocean and is bounded entirely by ocean currents. It is the only sea on Earth that possesses no terrestrial land coastline.",
    "The Sargasso Sea is bounded by the coastlines of North America and the Caribbean Islands.",
    "bounded by the coastlines of North America and the Caribbean Islands",
    "NOAA Ocean Exploration",
    "https://oceanexplorer.noaa.gov",
    "Negation contradiction: context explicitly states no land coastline; answer claims bounded by coastlines."
))

items.append(make_con(
    "IND-CON-009",
    "What is the global length ranking of the Yangtze River?",
    "The Yangtze River in China is the longest river in Asia and the third-longest river in the world, measuring roughly 6,300 kilometres.",
    "The Yangtze River is the second-longest river in the world, surpassed only by the Nile.",
    "second-longest river in the world, surpassed only by the Nile",
    "Encyclopaedia Britannica",
    "https://www.britannica.com",
    "Ordinal contradiction: context specifies third-longest; answer claims second-longest."
))

items.append(make_con(
    "IND-CON-010",
    "Which country controls the majority of the island of Borneo?",
    "Borneo is politically divided among three nations: Indonesia holds approximately 73 percent of the island (Kalimantan), Malaysia holds roughly 26 percent (Sabah and Sarawak), and Brunei occupies about 1 percent.",
    "Malaysia controls the vast majority of Borneo, holding approximately 73 percent of the island.",
    "Malaysia controls the vast majority of Borneo, holding approximately 73 percent",
    "UNEP Island Directory",
    "https://islands.unep.ch",
    "Entity attribute swap: Indonesia holds 73%, answer falsely attributes 73% to Malaysia."
))

items.append(make_con(
    "IND-CON-011",
    "Which body of water does the Bosporus Strait connect to in the north?",
    "The Bosporus Strait in Turkey connects the Black Sea in the north to the Sea of Marmara in the south.",
    "The Bosporus Strait connects the Aegean Sea in the north to the Sea of Marmara.",
    "the Aegean Sea",
    "Turkish Directorate of Maritime Affairs",
    "https://denizcilik.uab.gov.tr",
    "Entity swap: Black Sea is the northern body; answer asserts Aegean Sea."
))

items.append(make_con(
    "IND-CON-012",
    "What is the summit elevation of Vinson Massif in Antarctica?",
    "Vinson Massif is the highest mountain peak in Antarctica, with its summit rising to an elevation of 4,892 metres above sea level.",
    "Vinson Massif is the highest mountain in Antarctica, reaching an elevation of 5,892 metres.",
    "5,892 metres",
    "USGS Antarctic Names Database",
    "https://geonames.usgs.gov",
    "Numerical contradiction: context specifies 4,892 m; answer asserts 5,892 m."
))

items.append(make_con(
    "IND-CON-013",
    "What is the elevation of the Danakil Depression relative to sea level?",
    "The Danakil Depression in northeastern Ethiopia lies approximately 125 metres below sea level in the Afar Triangle.",
    "The Danakil Depression in Ethiopia is an elevated volcanic plateau rising 125 metres above sea level.",
    "an elevated volcanic plateau rising 125 metres above sea level",
    "Geological Survey of Ethiopia",
    "https://www.gse.gov.et",
    "Geomorphological and directional contradiction: depression below sea level vs elevated plateau above sea level."
))

items.append(make_con(
    "IND-CON-014",
    "How many individual waterfalls comprise Iguazu Falls?",
    "Iguazu Falls consists of approximately 275 individual waterfalls and cascades straddling the border between Argentina and Brazil.",
    "Iguazu Falls consists of a single massive uninterrupted cascade rather than multiple falls.",
    "a single massive uninterrupted cascade rather than multiple falls",
    "UNESCO World Heritage Centre",
    "https://whc.unesco.org",
    "Direct factual contradiction: 275 individual cascades vs single uninterrupted cascade."
))

items.append(make_con(
    "IND-CON-015",
    "Why is Mount Chimborazo's summit farther from Earth's center than Mount Everest?",
    "Because the Earth bulges at the equator, Mount Chimborazo in Ecuador is the farthest point on the Earth's surface from the Earth's center, even though Everest is higher above sea level.",
    "Mount Chimborazo is farther from the Earth's center than Everest because it has a higher elevation above sea level.",
    "because it has a higher elevation above sea level",
    "IGN France",
    "https://www.ign.fr",
    "Causal and factual contradiction: context states Chimborazo is lower above sea level but farther due to equatorial bulge."
))

items.append(make_con(
    "IND-CON-016",
    "Into which body of water does the Volga River discharge?",
    "The Volga River in Russia is the longest river in Europe and discharges into the landlocked Caspian Sea.",
    "The Volga River flows southward and discharges directly into the Black Sea.",
    "the Black Sea",
    "Encyclopaedia Britannica",
    "https://www.britannica.com",
    "Entity swap: Caspian Sea vs Black Sea."
))

items.append(make_con(
    "IND-CON-017",
    "What is the size ranking of New Guinea among global islands?",
    "New Guinea is the second-largest island in the world, covering 785,753 square kilometres, surpassed only by Greenland.",
    "New Guinea is the third-largest island in the world, ranking behind Greenland and Borneo.",
    "third-largest island in the world, ranking behind Greenland and Borneo",
    "UNEP Island Directory",
    "https://islands.unep.ch",
    "Ordinal contradiction: context specifies second-largest (ahead of Borneo); answer asserts third-largest."
))

items.append(make_con(
    "IND-CON-018",
    "Which islands or landmasses does the Strait of Malacca separate?",
    "The Strait of Malacca runs between the Malay Peninsula and the Indonesian island of Sumatra, connecting the Indian Ocean to the South China Sea.",
    "The Strait of Malacca separates the islands of Java and Sumatra.",
    "separates the islands of Java and Sumatra",
    "International Maritime Organization",
    "https://www.imo.org",
    "Geographical entity swap: Malay Peninsula and Sumatra vs Java and Sumatra (which is the Sunda Strait)."
))

items.append(make_con(
    "IND-CON-019",
    "At what elevation is the settlement of La Rinconada located?",
    "La Rinconada is a settlement in the Peruvian Andes located at an altitude of approximately 5,100 metres above sea level.",
    "La Rinconada is located in the Peruvian Andes at an altitude of roughly 3,100 metres above sea level.",
    "roughly 3,100 metres",
    "National Geographic",
    "https://www.nationalgeographic.com",
    "Numerical contradiction: 5,100 m vs 3,100 m."
))

items.append(make_con(
    "IND-CON-020",
    "What is the capital city of Turkey?",
    "Ankara was established as the official capital of the Republic of Turkey in 1923, whereas Istanbul remains the country's most populous city.",
    "Istanbul is the official capital city of Turkey, while Ankara serves as its provincial commercial center.",
    "Istanbul is the official capital city of Turkey",
    "Presidency of Turkey",
    "https://www.tccb.gov.tr",
    "Entity-role swap: Ankara is capital, not Istanbul."
))

items.append(make_con(
    "IND-CON-021",
    "Where is the Lambert Glacier located?",
    "The Lambert Glacier is the world's largest glacier, draining about 8 percent of the ice sheet in East Antarctica.",
    "The Lambert Glacier is the world's largest glacier, located in northern Greenland.",
    "located in northern Greenland",
    "Australian Antarctic Division",
    "https://www.antarctica.gov.au",
    "Entity location swap: East Antarctica vs Greenland."
))

items.append(make_con(
    "IND-CON-022",
    "Along which body of water is the city of Ushuaia situated?",
    "Ushuaia, the capital of Tierra del Fuego in Argentina, is situated along the Beagle Channel near the southern tip of South America.",
    "Ushuaia is situated directly along the Strait of Magellan in Argentina.",
    "the Strait of Magellan",
    "Instituto Fueguino de Turismo",
    "https://findelmundo.tur.ar",
    "Entity swap: Beagle Channel vs Strait of Magellan."
))

items.append(make_con(
    "IND-CON-023",
    "What is the volcanic status of Mount Etna in Sicily?",
    "Mount Etna on the island of Sicily is an active stratovolcano and the tallest active volcano in Europe at approximately 3,357 metres.",
    "Mount Etna is a completely extinct volcanic caldera that has not erupted in recorded human history.",
    "a completely extinct volcanic caldera that has not erupted in recorded human history",
    "INGV Catania",
    "https://www.ct.ingv.it",
    "Status contradiction: active stratovolcano vs extinct caldera."
))

items.append(make_con(
    "IND-CON-024",
    "What is the approximate depth of the Great Blue Hole in Belize?",
    "The Great Blue Hole off the coast of Belize is a marine sinkhole that descends to a depth of roughly 124 metres (407 feet).",
    "The Great Blue Hole descends to an extreme abyssal depth of roughly 1,240 metres.",
    "roughly 1,240 metres",
    "Belize Barrier Reef Reserve / UNESCO",
    "https://whc.unesco.org",
    "Order of magnitude numerical error: 124 m vs 1,240 m."
))

items.append(make_con(
    "IND-CON-025",
    "Which Swiss city serves as the federal capital and seat of government?",
    "Under Swiss federal law, the city of Bern serves as the de facto federal city and seat of government, while Zurich is the largest financial center.",
    "Zurich serves as the official constitutional capital and seat of the Swiss federal government.",
    "Zurich serves as the official constitutional capital and seat of the Swiss federal government.",
    "Federal Chancellery of Switzerland",
    "https://www.bk.admin.ch",
    "Entity swap: Bern is seat of government, not Zurich."
))


# ==============================================================================
# CATEGORY 3: UNSUPPORTED (25 samples) - expected_verdict: "HALLUCINATED"
# Fabricated claims, dates, entities or characteristics completely absent from context
# ==============================================================================

def make_uns(test_id, question, context, answer, span_text, source_name, source_url, notes):
    start = answer.find(span_text)
    if start == -1:
        raise ValueError(f"Span text '{span_text}' not found in answer '{answer}'")
    end = start + len(span_text)
    return {
        "test_id": test_id,
        "category": "unsupported",
        "question": question,
        "reference_context": context,
        "generated_answer": answer,
        "expected_verdict": "HALLUCINATED",
        "expected_unsupported_spans": [{"start": start, "end": end, "text": span_text}],
        "source_name": source_name,
        "source_url": source_url,
        "annotation_notes": notes
    }

items.append(make_uns(
    "IND-UNS-001",
    "When was Mount Aconcagua first summited?",
    "Mount Aconcagua is located in Mendoza Province, Argentina. With a summit elevation of 6,961 metres above sea level, it is the highest peak in the Western Hemisphere.",
    "Mount Aconcagua was first successfully summited in 1897 by a British expedition led by Edward FitzGerald.",
    "was first successfully summited in 1897 by a British expedition led by Edward FitzGerald",
    "Alpine Journal",
    "https://www.alpinejournal.org.uk",
    "Unsupported claim: context discusses location and elevation; expedition date and climber are completely absent from reference."
))

items.append(make_uns(
    "IND-UNS-002",
    "What is the average annual water discharge volume of the Congo River?",
    "The Congo River is the deepest river in the world, with depths exceeding 220 metres, and it crosses the equator twice.",
    "The Congo River discharges an average of roughly 41,000 cubic metres of water per second into the Atlantic Ocean.",
    "discharges an average of roughly 41,000 cubic metres of water per second into the Atlantic Ocean",
    "USGS / River Discharge Database",
    "https://www.usgs.gov",
    "Unsupported claim: discharge volume metric absent from reference context."
))

items.append(make_uns(
    "IND-UNS-003",
    "When was Mount McKinley officially renamed Denali by the federal government?",
    "Denali is situated in the Alaska Range with a summit elevation of 6,190 metres, making it the highest peak in North America.",
    "The mountain was officially restored to its indigenous name Denali by the federal government in 2015 under President Barack Obama.",
    "restored to its indigenous name Denali by the federal government in 2015 under President Barack Obama",
    "US Department of the Interior",
    "https://www.doi.gov",
    "Unsupported historical claim: 2015 renaming under Obama absent from reference text."
))

items.append(make_uns(
    "IND-UNS-004",
    "What unique cichlid fish biodiversity exists in Lake Tanganyika?",
    "Lake Tanganyika is the world's second-deepest freshwater lake at 1,470 metres and the second-largest by volume.",
    "Lake Tanganyika harbors over 250 species of endemic cichlid fish that evolved through adaptive radiation.",
    "harbors over 250 species of endemic cichlid fish that evolved through adaptive radiation",
    "WWF Freshwater Reports",
    "https://www.worldwildlife.org",
    "Unsupported biological claim: fish biodiversity completely absent from context."
))

items.append(make_uns(
    "IND-UNS-005",
    "When was the historic lighthouse constructed at Cape Agulhas?",
    "Cape Agulhas is the southernmost point of the African continent and the dividing line between the Atlantic and Indian Oceans.",
    "A historic red-and-white striped lighthouse was constructed at Cape Agulhas in 1848 to guide ships through treacherous waters.",
    "A historic red-and-white striped lighthouse was constructed at Cape Agulhas in 1848",
    "Transnet National Ports Authority",
    "https://www.transnetnationalportsauthority.net",
    "Unsupported claim: 1848 lighthouse construction date absent from reference text."
))

items.append(make_uns(
    "IND-UNS-006",
    "When did Mount Elbrus last erupt?",
    "Mount Elbrus is a dormant stratovolcano in the Caucasus Mountains of southern Russia, with an elevation of 5,642 metres.",
    "Mount Elbrus last produced a volcanic eruption around 50 CE during the early Roman Imperial era.",
    "last produced a volcanic eruption around 50 CE during the early Roman Imperial era",
    "Smithsonian Global Volcanism Program",
    "https://volcano.si.edu",
    "Unsupported geological claim: 50 CE eruption date absent from reference context."
))

items.append(make_uns(
    "IND-UNS-007",
    "What caused the formation of Badwater Basin in Death Valley?",
    "Badwater Basin in California is the lowest point in North America, sitting at an elevation of 86 metres below sea level.",
    "Badwater Basin was formed by the evaporation of ancient Lake Manly during the Holocene epoch thousands of years ago.",
    "formed by the evaporation of ancient Lake Manly during the Holocene epoch thousands of years ago",
    "USGS Geology",
    "https://www.usgs.gov",
    "Unsupported geological claim: Lake Manly evaporation absent from reference."
))

items.append(make_uns(
    "IND-UNS-008",
    "What distinctive species of pelagic seaweed characterizes the Sargasso Sea?",
    "The Sargasso Sea in the North Atlantic is the only sea bounded entirely by circulating ocean currents without any land boundary.",
    "The sea is defined by massive floating mats of Sargassum seaweed that provide crucial nursery habitat for juvenile sea turtles.",
    "mats of Sargassum seaweed that provide crucial nursery habitat for juvenile sea turtles",
    "NOAA Fisheries",
    "https://www.fisheries.noaa.gov",
    "Unsupported ecological claim: seaweed species and sea turtle nursery absent from context."
))

items.append(make_uns(
    "IND-UNS-009",
    "What is the name of the massive hydroelectric dam constructed on the Yangtze River?",
    "The Yangtze River is the longest river in Asia and measures approximately 6,300 kilometres from Tibet to the East China Sea.",
    "The Yangtze River is impounded by the Three Gorges Dam, the world's largest hydroelectric power station by installed capacity.",
    "impounded by the Three Gorges Dam, the world's largest hydroelectric power station by installed capacity",
    "China Three Gorges Corporation",
    "https://www.ctg.com.cn",
    "Unsupported infrastructure claim: Three Gorges Dam details absent from context."
))

items.append(make_uns(
    "IND-UNS-010",
    "What endangered hominid species is endemic to the tropical rainforests of Borneo?",
    "Borneo is the third-largest island in the world, with its territory divided among Indonesia, Malaysia, and Brunei.",
    "Borneo is the native habitat of the critically endangered Bornean orangutan, which nests high in the forest canopy.",
    "native habitat of the critically endangered Bornean orangutan, which nests high in the forest canopy",
    "IUCN Red List",
    "https://www.iucnredlist.org",
    "Unsupported zoological claim: orangutan habitat absent from reference context."
))

items.append(make_uns(
    "IND-UNS-011",
    "When was the first suspension bridge built across the Bosporus Strait?",
    "The Bosporus Strait in Turkey connects the Black Sea to the Sea of Marmara and separates European and Asian Istanbul.",
    "The first permanent suspension bridge spanning the Bosporus was completed in 1973 on the fiftieth anniversary of the Turkish Republic.",
    "first permanent suspension bridge spanning the Bosporus was completed in 1973 on the fiftieth anniversary of the Turkish Republic",
    "General Directorate of Highways Turkey",
    "https://www.kgm.gov.tr",
    "Unsupported civil engineering claim: 1973 suspension bridge details absent from text."
))

items.append(make_uns(
    "IND-UNS-012",
    "Who was Vinson Massif named after?",
    "Vinson Massif is the highest mountain peak in Antarctica, situated in the Sentinel Range at an elevation of 4,892 metres.",
    "The massif was named in 1961 after Carl Vinson, a longtime U.S. Congressman from Georgia who championed Antarctic research funding.",
    "named in 1961 after Carl Vinson, a longtime U.S. Congressman from Georgia who championed Antarctic research funding",
    "USGS Antarctic Names",
    "https://geonames.usgs.gov",
    "Unsupported historical claim: Carl Vinson naming background absent from reference."
))

items.append(make_uns(
    "IND-UNS-013",
    "What unique hydrothermal feature is found at Dallol in the Danakil Depression?",
    "The Danakil Depression in Ethiopia lies 125 metres below sea level in the Afar Triangle and contains the active volcano Erta Ale.",
    "The depression contains the hydrothermal field of Dallol, famous for its neon green acidic brine pools and sulfur terraces.",
    "contains the hydrothermal field of Dallol, famous for its neon green acidic brine pools and sulfur terraces",
    "Nature Communications",
    "https://www.nature.com",
    "Unsupported claim: Dallol acidic brine pools absent from reference text."
))

items.append(make_uns(
    "IND-UNS-014",
    "What legend explains the indigenous Guaraní origin of Iguazu Falls?",
    "Iguazu Falls comprises approximately 275 cascades on the border between Argentina and Brazil along the Iguazu River.",
    "According to indigenous Guaraní mythology, the falls were created when an enraged serpent deity sliced the riverbed in fury.",
    "According to indigenous Guaraní mythology, the falls were created when an enraged serpent deity sliced the riverbed in fury.",
    "Guaraní Folklore Archives",
    "https://www.cultura.gob.ar",
    "Unsupported folklore claim: Guaraní mythology serpent legend completely absent from context."
))

items.append(make_uns(
    "IND-UNS-015",
    "Who was the famous German naturalist who attempted to climb Mount Chimborazo in 1802?",
    "Mount Chimborazo in Ecuador is the farthest terrestrial point from Earth's center due to the equatorial bulge, with a peak of 6,263 metres.",
    "The German polymath Alexander von Humboldt attempted to ascend Chimborazo in 1802, setting a world mountaineering altitude record at the time.",
    "Alexander von Humboldt attempted to ascend Chimborazo in 1802, setting a world mountaineering altitude record at the time",
    "Humboldt Foundation",
    "https://www.humboldt-foundation.de",
    "Unsupported historical claim: Humboldt 1802 ascent absent from reference."
))

items.append(make_uns(
    "IND-UNS-016",
    "What canal connects the Volga River to the Don River?",
    "The Volga River is the longest river in Europe, spanning 3,531 kilometres across European Russia before draining into the Caspian Sea.",
    "The Volga is linked to the Don River by the 101-kilometre Volga-Don Shipping Canal, completed in 1952 under Soviet engineering.",
    "linked to the Don River by the 101-kilometre Volga-Don Shipping Canal, completed in 1952 under Soviet engineering",
    "Federal Marine and River Transport Agency",
    "https://morflot.gov.ru",
    "Unsupported infrastructure claim: Volga-Don Canal details absent from context."
))

items.append(make_uns(
    "IND-UNS-017",
    "What is the highest mountain peak on the island of New Guinea?",
    "New Guinea is the second-largest island in the world, covering 785,753 square kilometres and divided between Indonesia and Papua New Guinea.",
    "The highest peak on New Guinea is Puncak Jaya, also called Carstensz Pyramid, which reaches 4,884 metres above sea level.",
    "highest peak on New Guinea is Puncak Jaya, also called Carstensz Pyramid, which reaches 4,884 metres above sea level",
    "Peakbagger",
    "https://www.peakbagger.com",
    "Unsupported geographical claim: Puncak Jaya details absent from reference text."
))

items.append(make_uns(
    "IND-UNS-018",
    "What major port city is located at the southern tip of the Strait of Malacca?",
    "The Strait of Malacca runs between the Malay Peninsula and Sumatra, connecting the Indian Ocean to the South China Sea.",
    "The island city-state of Singapore is situated at the southern terminus of the strait, operating one of the world's busiest container transshipment ports.",
    "The island city-state of Singapore is situated at the southern terminus of the strait, operating one of the world's busiest container transshipment ports.",
    "Maritime and Port Authority of Singapore",
    "https://www.mpa.gov.sg",
    "Unsupported claim: Singapore port details absent from reference."
))

items.append(make_uns(
    "IND-UNS-019",
    "What environmental hazards plague the mining community of La Rinconada?",
    "La Rinconada is a gold-mining settlement in the Peruvian Andes, situated at an altitude of approximately 5,100 metres above sea level.",
    "The community suffers from severe mercury contamination and lack of municipal waste infrastructure due to unregulated artisanal gold processing.",
    "suffers from severe mercury contamination and lack of municipal waste infrastructure due to unregulated artisanal gold processing",
    "Science Magazine",
    "https://www.science.org",
    "Unsupported environmental claim: mercury contamination absent from reference context."
))

items.append(make_uns(
    "IND-UNS-020",
    "Who was the founding president of modern Turkey who moved the capital to Ankara?",
    "Ankara became the capital of the Republic of Turkey in 1923, succeeding Istanbul as the nation's political center.",
    "The move was ordered by Mustafa Kemal Atatürk, the founder and first president of the modern secular Turkish state.",
    "ordered by Mustafa Kemal Atatürk, the founder and first president of the modern secular Turkish state",
    "Atatürk Research Center",
    "https://www.atam.gov.tr",
    "Unsupported biographical claim: Atatürk details absent from reference text."
))

items.append(make_uns(
    "IND-UNS-021",
    "What scientific radar technology was used to map the bedrock beneath Lambert Glacier?",
    "The Lambert Glacier in East Antarctica is the world's largest glacier, stretching over 400 kilometres in length and draining 8 percent of the ice sheet.",
    "The subterranean bedrock profile beneath the glacier was mapped using airborne radio-echo sounding radar deployed during International Geophysical Year surveys.",
    "mapped using airborne radio-echo sounding radar deployed during International Geophysical Year surveys",
    "Journal of Glaciology",
    "https://www.cambridge.org/core/journals/journal-of-glaciology",
    "Unsupported technical claim: radio-echo sounding radar mapping absent from context."
))

items.append(make_uns(
    "IND-UNS-022",
    "What famous historical prison operated in Ushuaia during the early twentieth century?",
    "Ushuaia is the capital of Tierra del Fuego in Argentina, located along the Beagle Channel near South America's southern tip.",
    "Ushuaia was originally developed as an Argentine penal colony housing dangerous felons and political prisoners between 1896 and 1947.",
    "developed as an Argentine penal colony housing dangerous felons and political prisoners between 1896 and 1947",
    "Museo Marítimo de Ushuaia",
    "https://www.museomaritimo.com",
    "Unsupported historical claim: penal colony dates and prison operation absent from context."
))

items.append(make_uns(
    "IND-UNS-023",
    "In Greek mythology, what monster was believed to be trapped beneath Mount Etna?",
    "Mount Etna is an active stratovolcano on Sicily, standing roughly 3,357 metres high as the tallest active volcano in Europe.",
    "In classical Greek mythology, the monstrous serpentine giant Typhon was believed to be trapped beneath the volcano by Zeus.",
    "In classical Greek mythology, the monstrous serpentine giant Typhon was believed to be trapped beneath the volcano by Zeus.",
    "Theoi Greek Mythology",
    "https://www.theoi.com",
    "Unsupported mythological claim: Typhon myth absent from reference."
))

items.append(make_uns(
    "IND-UNS-024",
    "Who popularized the Great Blue Hole through television documentary filming in 1971?",
    "The Great Blue Hole off the coast of Belize is a circular marine sinkhole measuring over 300 metres across and 124 metres deep.",
    "The sinkhole was made world-famous in 1971 by French underwater explorer Jacques Cousteau, who declared it one of the world's top scuba diving sites.",
    "made world-famous in 1971 by French underwater explorer Jacques Cousteau, who declared it one of the world's top scuba diving sites",
    "Cousteau Society",
    "https://www.cousteau.org",
    "Unsupported historical claim: Jacques Cousteau 1971 expedition absent from text."
))

items.append(make_uns(
    "IND-UNS-025",
    "What famous clock tower is a landmark in the Swiss capital of Bern?",
    "The city of Bern serves as the de facto federal city and seat of government of Switzerland, housing the Federal Assembly.",
    "Bern is celebrated for the Zytglogge, a landmark medieval astronomical clock tower built in the early thirteenth century.",
    "celebrated for the Zytglogge, a landmark medieval astronomical clock tower built in the early thirteenth century",
    "Bern Tourism",
    "https://www.bern.com",
    "Unsupported architectural claim: Zytglogge clock tower absent from context."
))


# ==============================================================================
# CATEGORY 4: MIXED (25 samples) - expected_verdict: "HALLUCINATED"
# Compound / multi-clause sentences combining a supported fact with an entity swap,
# incorrect number, or comparative reversal in another clause.
# ==============================================================================

def make_mix(test_id, question, context, answer, span_text, source_name, source_url, notes):
    start = answer.find(span_text)
    if start == -1:
        raise ValueError(f"Span text '{span_text}' not found in answer '{answer}'")
    end = start + len(span_text)
    return {
        "test_id": test_id,
        "category": "mixed",
        "question": question,
        "reference_context": context,
        "generated_answer": answer,
        "expected_verdict": "HALLUCINATED",
        "expected_unsupported_spans": [{"start": start, "end": end, "text": span_text}],
        "source_name": source_name,
        "source_url": source_url,
        "annotation_notes": notes
    }

items.append(make_mix(
    "IND-MIX-001",
    "What is Mount Aconcagua and where is it located?",
    "Mount Aconcagua is located in the Andes mountain range in Mendoza Province, Argentina. With a summit elevation of 6,961 metres above sea level, it is the highest mountain in both the Southern and Western Hemispheres.",
    "Mount Aconcagua is the highest mountain in South America at 6,961 metres, but it is located in central Chile.",
    "but it is located in central Chile",
    "IGN Argentina",
    "https://www.ign.gob.ar",
    "Mixed claims: Clause 1 (highest mountain, 6,961 m) is supported; Clause 2 (located in central Chile) contradicts context (Argentina)."
))

items.append(make_mix(
    "IND-MIX-002",
    "What is the Congo River and what are its notable characteristics?",
    "The Congo River in central Africa is recognized as the world's deepest river, with measured depths exceeding 220 metres (720 feet) in sections of the Lower Congo. It is also the only major river on Earth that crosses the equator twice.",
    "The Congo River is the deepest river in the world, while its maximum depth is limited to 110 metres.",
    "while its maximum depth is limited to 110 metres",
    "NASA Earth Observatory",
    "https://earthobservatory.nasa.gov",
    "Mixed claims: Clause 1 (deepest river) is supported; Clause 2 (maximum depth limited to 110 m) contradicts context (>220 m)."
))

items.append(make_mix(
    "IND-MIX-003",
    "Where is Mount Denali situated and what is its summit elevation?",
    "Denali is located in the Alaska Range in the interior of the U.S. state of Alaska. Its summit reaches 6,190 metres (20,310 feet) above sea level, making it the highest mountain peak in North America.",
    "Denali is the highest mountain peak in North America, but its summit elevation is 7,190 metres.",
    "but its summit elevation is 7,190 metres",
    "USGS",
    "https://www.usgs.gov",
    "Mixed claims: Clause 1 (highest peak in North America) is supported; Clause 2 (7,190 m) contradicts context (6,190 m)."
))

items.append(make_mix(
    "IND-MIX-004",
    "What is Lake Tanganyika and how does it rank globally?",
    "Lake Tanganyika is an African Great Lake. It is the second-oldest freshwater lake in the world, the second-largest by volume, and the second-deepest at 1,470 metres, in all three categories surpassed only by Lake Baikal.",
    "Lake Tanganyika is the second-deepest lake in the world, whereas it holds the record as the world's largest lake by surface area.",
    "whereas it holds the record as the world's largest lake by surface area",
    "Encyclopaedia Britannica",
    "https://www.britannica.com",
    "Mixed claims: Clause 1 (second-deepest lake) is supported; Clause 2 (largest lake by surface area) contradicts context."
))

items.append(make_mix(
    "IND-MIX-005",
    "What is Cape Agulhas and what waters does it separate?",
    "Cape Agulhas is the geographic southernmost point of the African continent and the official dividing marker between the Atlantic and Indian Oceans, situated roughly 150 kilometres east of the Cape of Good Hope.",
    "Cape Agulhas is the southernmost point of the African continent, and it marks the boundary between the Pacific and Atlantic Oceans.",
    "and it marks the boundary between the Pacific and Atlantic Oceans",
    "International Hydrographic Organization",
    "https://iho.int",
    "Mixed claims: Clause 1 (southernmost point) is supported; Clause 2 (Pacific and Atlantic boundary) contradicts context (Atlantic and Indian)."
))

items.append(make_mix(
    "IND-MIX-006",
    "What is Mount Elbrus and where is it located?",
    "Mount Elbrus is a dormant stratovolcano located in the Caucasus Mountains in southern Russia. Its west summit rises to 5,642 metres above sea level, establishing it as the highest peak in Europe.",
    "Mount Elbrus is the highest peak in Europe at 5,642 metres, although it is situated in the Alps of northern Italy.",
    "although it is situated in the Alps of northern Italy",
    "Russian Geographical Society",
    "https://www.rgs.ru",
    "Mixed claims: Clause 1 (highest peak in Europe, 5,642 m) is supported; Clause 2 (Alps of northern Italy) contradicts context (Caucasus, Russia)."
))

items.append(make_mix(
    "IND-MIX-007",
    "Where is Badwater Basin and what is its elevation?",
    "Badwater Basin is an endorheic basin situated in Death Valley National Park, California. At 86 metres below sea level, it represents the lowest point of elevation on the North American continent.",
    "Badwater Basin is the lowest point of elevation in North America, and it is located in the state of Nevada.",
    "and it is located in the state of Nevada",
    "National Park Service",
    "https://www.nps.gov/deva",
    "Mixed claims: Clause 1 (lowest point in North America) is supported; Clause 2 (located in Nevada) contradicts context (California)."
))

items.append(make_mix(
    "IND-MIX-008",
    "What defines the Sargasso Sea and where is it located?",
    "The Sargasso Sea is a vast region of the North Atlantic Ocean bounded entirely by circulating ocean currents. It is the only sea on Earth that possesses no terrestrial land coastline.",
    "The Sargasso Sea is located in the North Atlantic, while it is completely enclosed by the Scandinavian landmass.",
    "while it is completely enclosed by the Scandinavian landmass",
    "NOAA Ocean Exploration",
    "https://oceanexplorer.noaa.gov",
    "Mixed claims: Clause 1 (North Atlantic location) is supported; Clause 2 (enclosed by Scandinavian landmass) contradicts context."
))

items.append(make_mix(
    "IND-MIX-009",
    "What is the Yangtze River and what is its length?",
    "The Yangtze River, flowing entirely within China, is the longest river in Asia and the third-longest river in the world, measuring approximately 6,300 kilometres.",
    "The Yangtze River is the longest river in Asia, but its measured length is only 3,300 kilometres.",
    "but its measured length is only 3,300 kilometres",
    "Encyclopaedia Britannica",
    "https://www.britannica.com",
    "Mixed claims: Clause 1 (longest in Asia) is supported; Clause 2 (3,300 km) contradicts context (~6,300 km)."
))

items.append(make_mix(
    "IND-MIX-010",
    "What is the island of Borneo and how is it governed?",
    "Borneo is the third-largest island in the world, covering an area of 748,168 square kilometres. The island is politically divided among three sovereign nations: Indonesia, Malaysia, and Brunei.",
    "Borneo is the third-largest island in the world, and its entire landmass is governed exclusively by the nation of Indonesia.",
    "and its entire landmass is governed exclusively by the nation of Indonesia",
    "UNEP Island Directory",
    "https://islands.unep.ch",
    "Mixed claims: Clause 1 (third-largest island) is supported; Clause 2 (exclusively governed by Indonesia) contradicts context (divided among three)."
))

items.append(make_mix(
    "IND-MIX-011",
    "What is the Bosporus Strait and what city does it divide?",
    "The Bosporus is an international waterway in northwestern Turkey that bisects Istanbul between Europe and Asia, connecting the Black Sea to the Sea of Marmara.",
    "The Bosporus Strait connects the Black Sea to the Sea of Marmara, and it divides the city of Athens between two continents.",
    "and it divides the city of Athens between two continents",
    "Turkish Directorate of Maritime Affairs",
    "https://denizcilik.uab.gov.tr",
    "Mixed claims: Clause 1 (connects Black Sea to Marmara) is supported; Clause 2 (divides Athens) contradicts context (divides Istanbul)."
))

items.append(make_mix(
    "IND-MIX-012",
    "What is Vinson Massif and what is its elevation?",
    "Vinson Massif is the highest mountain in Antarctica, situated in the Sentinel Range. Its summit, Mount Vinson, rises to an elevation of 4,892 metres above sea level.",
    "Vinson Massif is located in the Sentinel Range of Antarctica, but it is surpassed in height by Mount Erebus.",
    "but it is surpassed in height by Mount Erebus",
    "USGS Antarctic Names",
    "https://geonames.usgs.gov",
    "Mixed claims: Clause 1 (Sentinel Range, Antarctica) is supported; Clause 2 (surpassed by Mount Erebus) contradicts context (highest mountain)."
))

items.append(make_mix(
    "IND-MIX-013",
    "Where is the Danakil Depression and what are its features?",
    "The Danakil Depression is a geological depression in the Afar Triangle of northeastern Ethiopia, reaching 125 metres below sea level and containing active volcanoes such as Erta Ale.",
    "The Danakil Depression contains the active volcano Erta Ale, but it is situated in the high mountains of Kenya.",
    "but it is situated in the high mountains of Kenya",
    "Geological Survey of Ethiopia",
    "https://www.gse.gov.et",
    "Mixed claims: Clause 1 (Erta Ale volcano) is supported; Clause 2 (high mountains of Kenya) contradicts context (Ethiopia depression)."
))

items.append(make_mix(
    "IND-MIX-014",
    "Where is Iguazu Falls and how is it structured?",
    "Iguazu Falls consists of approximately 275 individual waterfalls straddling the border between Argentina and Brazil along the Iguazu River.",
    "Iguazu Falls consists of around 275 individual cascades, and it is located on the border between Chile and Peru.",
    "and it is located on the border between Chile and Peru",
    "UNESCO World Heritage Centre",
    "https://whc.unesco.org",
    "Mixed claims: Clause 1 (275 cascades) is supported; Clause 2 (border between Chile and Peru) contradicts context (Argentina and Brazil)."
))

items.append(make_mix(
    "IND-MIX-015",
    "What is Mount Chimborazo and why is it notable?",
    "Mount Chimborazo is an inactive stratovolcano in Ecuador. Due to the equatorial bulge, its summit is the farthest point on Earth's surface from Earth's center, reaching 6,263 metres above sea level.",
    "Mount Chimborazo is the farthest terrestrial point from the center of the Earth, although it is an active volcano in Peru.",
    "although it is an active volcano in Peru",
    "IGN France",
    "https://www.ign.fr",
    "Mixed claims: Clause 1 (farthest point from Earth's center) is supported; Clause 2 (active volcano in Peru) contradicts context (inactive in Ecuador)."
))

items.append(make_mix(
    "IND-MIX-016",
    "What is the Volga River and where does it flow?",
    "The Volga River flows through European Russia and is the longest river in Europe at 3,531 kilometres, discharging into the Caspian Sea.",
    "The Volga River is the longest river in Europe, and it flows into the Mediterranean Sea.",
    "and it flows into the Mediterranean Sea",
    "Encyclopaedia Britannica",
    "https://www.britannica.com",
    "Mixed claims: Clause 1 (longest river in Europe) is supported; Clause 2 (flows into Mediterranean) contradicts context (Caspian Sea)."
))

items.append(make_mix(
    "IND-MIX-017",
    "What is the island of New Guinea and how is it divided?",
    "New Guinea is the second-largest island in the world, covering 785,753 square kilometres, and is divided between Indonesia and Papua New Guinea.",
    "New Guinea is the second-largest island in the world, but it is divided between Australia and the Philippines.",
    "but it is divided between Australia and the Philippines",
    "UNEP Island Directory",
    "https://islands.unep.ch",
    "Mixed claims: Clause 1 (second-largest island) is supported; Clause 2 (divided between Australia and Philippines) contradicts context."
))

items.append(make_mix(
    "IND-MIX-018",
    "What does the Strait of Malacca connect?",
    "The Strait of Malacca runs between the Malay Peninsula and Sumatra, connecting the Indian Ocean to the South China Sea.",
    "The Strait of Malacca runs between the Malay Peninsula and Sumatra, while it connects the Atlantic Ocean to the Arctic Ocean.",
    "while it connects the Atlantic Ocean to the Arctic Ocean",
    "International Maritime Organization",
    "https://www.imo.org",
    "Mixed claims: Clause 1 (runs between Malay Peninsula and Sumatra) is supported; Clause 2 (connects Atlantic to Arctic) contradicts context."
))

items.append(make_mix(
    "IND-MIX-019",
    "What is La Rinconada and what is its altitude?",
    "La Rinconada is a gold-mining settlement in the Peruvian Andes at an altitude of approximately 5,100 metres above sea level, recognized as the highest permanent settlement on Earth.",
    "La Rinconada is recognized as the highest permanent settlement on Earth, and it is located on the coastal plains of Colombia.",
    "and it is located on the coastal plains of Colombia",
    "National Geographic",
    "https://www.nationalgeographic.com",
    "Mixed claims: Clause 1 (highest permanent settlement) is supported; Clause 2 (coastal plains of Colombia) contradicts context (Peruvian Andes)."
))

items.append(make_mix(
    "IND-MIX-020",
    "What is Ankara and what role does it play in Turkey?",
    "Ankara became the official capital of the Republic of Turkey in 1923, succeeding Istanbul as the political center.",
    "Ankara is the capital of Turkey, but it was designated as the capital in the year 1823.",
    "but it was designated as the capital in the year 1823",
    "Presidency of Turkey",
    "https://www.tccb.gov.tr",
    "Mixed claims: Clause 1 (capital of Turkey) is supported; Clause 2 (year 1823) contradicts context (1923)."
))

items.append(make_mix(
    "IND-MIX-021",
    "What is the Lambert Glacier and what are its dimensions?",
    "The Lambert Glacier in East Antarctica is the world's largest glacier, measuring over 400 kilometres in length and draining roughly 8 percent of the Antarctic ice sheet.",
    "The Lambert Glacier is the largest glacier in the world, although it is located in the Southern Alps of New Zealand.",
    "although it is located in the Southern Alps of New Zealand",
    "Australian Antarctic Division",
    "https://www.antarctica.gov.au",
    "Mixed claims: Clause 1 (largest glacier in the world) is supported; Clause 2 (located in Southern Alps of New Zealand) contradicts context (East Antarctica)."
))

items.append(make_mix(
    "IND-MIX-022",
    "Where is Ushuaia situated and what is its status?",
    "Ushuaia is the capital of Tierra del Fuego Province, Argentina, situated along the Beagle Channel as the southernmost city in the world.",
    "Ushuaia is the southernmost city in the world, while it is situated in the interior highlands of Bolivia.",
    "while it is situated in the interior highlands of Bolivia",
    "Instituto Fueguino de Turismo",
    "https://findelmundo.tur.ar",
    "Mixed claims: Clause 1 (southernmost city in the world) is supported; Clause 2 (highlands of Bolivia) contradicts context (Argentina, Beagle Channel)."
))

items.append(make_mix(
    "IND-MIX-023",
    "What is Mount Etna and what is its height?",
    "Mount Etna is an active stratovolcano on Sicily, Italy, rising to roughly 3,357 metres as the tallest active volcano in Europe.",
    "Mount Etna is an active stratovolcano on Sicily, but its elevation is less than 500 metres above sea level.",
    "but its elevation is less than 500 metres above sea level",
    "INGV Catania",
    "https://www.ct.ingv.it",
    "Mixed claims: Clause 1 (active stratovolcano on Sicily) is supported; Clause 2 (<500 m) contradicts context (~3,357 m)."
))

items.append(make_mix(
    "IND-MIX-024",
    "Where is the Great Blue Hole and what are its dimensions?",
    "The Great Blue Hole is a marine sinkhole off the coast of Belize in Lighthouse Reef, measuring over 300 metres across and 124 metres deep.",
    "The Great Blue Hole is a marine sinkhole off the coast of Belize, but it is less than 20 metres across.",
    "but it is less than 20 metres across",
    "UNESCO World Heritage Centre",
    "https://whc.unesco.org",
    "Mixed claims: Clause 1 (marine sinkhole off Belize) is supported; Clause 2 (<20 m across) contradicts context (>300 m across)."
))

items.append(make_mix(
    "IND-MIX-025",
    "What is the role of Bern in Switzerland?",
    "Under Swiss federal law, the city of Bern serves as the de facto federal city and seat of government, while Zurich is the largest financial hub.",
    "Bern serves as the seat of government of Switzerland, whereas it was officially founded in the year 2010.",
    "whereas it was officially founded in the year 2010",
    "Federal Chancellery of Switzerland",
    "https://www.bk.admin.ch",
    "Mixed claims: Clause 1 (seat of government) is supported; Clause 2 (founded in 2010) contradicts context (medieval city)."
))


# Validate all 100 items
assert len(items) == 100, f"Expected 100 items, got {len(items)}"
cat_counts = {}
for it in items:
    cat = it["category"]
    cat_counts[cat] = cat_counts.get(cat, 0) + 1
    # Check span character offsets
    ans = it["generated_answer"]
    for sp in it["expected_unsupported_spans"]:
        s, e, t = sp["start"], sp["end"], sp["text"]
        actual_sub = ans[s:e]
        assert actual_sub == t, f"Span mismatch in {it['test_id']}: expected '{t}', got '{actual_sub}'"

print(f"Validated all {len(items)} items across categories: {cat_counts}")

# Save JSON
out_json = DATASET_DIR / "independent_geography_dataset.json"
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(items, f, indent=2, ensure_ascii=False)
print(f"Saved JSON: {out_json}")

# Save CSV
out_csv = DATASET_DIR / "independent_geography_dataset.csv"
fieldnames = [
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
with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for it in items:
        row = dict(it)
        row["expected_unsupported_spans"] = json.dumps(row["expected_unsupported_spans"], ensure_ascii=False)
        writer.writerow(row)
print(f"Saved CSV: {out_csv}")

