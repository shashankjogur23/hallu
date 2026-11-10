"""Unit Test Suite for Robust Proposition and Clause Segmentation in HalluGuard.

Validates that:
1. Two-item coordinated noun lists are never fragmented.
2. Three-item coordinated noun lists without Oxford commas are preserved.
3. Three-item coordinated noun lists with Oxford commas are preserved intact.
4. Multi-clause sentences containing coordinated noun lists split into true independent clauses.
5. Contrasting and subordinating conjunctions (while, whereas, but, although, etc.) split clauses correctly.
6. Multi-sentence answers split into individual sentences and preserve character offset integrity.
"""

import sys
import unittest
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = ROOT_DIR / "evaluation" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from nli_service import nli_service


class TestClauseSegmentation(unittest.TestCase):

    def test_two_item_list(self):
        """Two-item coordinated noun list should not produce fragmented sub-clauses."""
        text = "The territory is shared between Indonesia and Malaysia."
        segments = nli_service.segment_answer(text)
        # Should contain full_answer, but NO spurious clause fragments
        clause_segments = [s for s in segments if s[3] == "clause"]
        self.assertEqual(len(clause_segments), 0, f"Expected 0 clauses, got: {clause_segments}")
        # Verify text invariant
        for start, end, seg_text, _ in segments:
            self.assertEqual(text[start:end], seg_text)

    def test_three_item_list_without_oxford_comma(self):
        """Three-item list without Oxford comma should remain intact without fragmentation."""
        text = "The island is politically divided among Indonesia, Malaysia and Brunei."
        segments = nli_service.segment_answer(text)
        clause_segments = [s for s in segments if s[3] == "clause"]
        self.assertEqual(len(clause_segments), 0, f"Expected 0 clauses, got: {clause_segments}")
        for start, end, seg_text, _ in segments:
            self.assertEqual(text[start:end], seg_text)

    def test_three_item_list_with_oxford_comma(self):
        """Three-item list with Oxford comma must not fragment at ', and '."""
        text = "The treaty was signed by France, Germany, and Italy in 1957."
        segments = nli_service.segment_answer(text)
        clause_segments = [s for s in segments if s[3] == "clause"]
        self.assertEqual(len(clause_segments), 0, f"Expected 0 clauses, got: {clause_segments}")
        # Ensure 'and Italy' is not carved out as an isolated clause
        for start, end, seg_text, _ in segments:
            self.assertEqual(text[start:end], seg_text)
            self.assertNotEqual(seg_text.strip(), "Italy.")
            self.assertNotEqual(seg_text.strip(), "Italy")

    def test_multi_clause_with_coordinated_list(self):
        """Multi-clause sentence with an Oxford-comma list must split between clauses, not inside list."""
        text = (
            "Borneo is the third-largest island in the world, and its territory is politically "
            "shared among Indonesia, Malaysia, and Brunei."
        )
        segments = nli_service.segment_answer(text)
        clause_segments = [s for s in segments if s[3] == "clause"]

        # Expected: exactly 2 clauses
        self.assertEqual(len(clause_segments), 2, f"Expected 2 clauses, got: {clause_segments}")
        c1_text = clause_segments[0][2]
        c2_text = clause_segments[1][2]

        self.assertEqual(c1_text, "Borneo is the third-largest island in the world")
        self.assertEqual(c2_text, "its territory is politically shared among Indonesia, Malaysia, and Brunei.")

        # Crucial: verify that 'Brunei' or 'Indonesia, Malaysia' was NOT fragmented
        all_texts = [s[2] for s in segments]
        self.assertNotIn("Brunei.", all_texts)
        self.assertNotIn("its territory is politically shared among Indonesia, Malaysia", all_texts)

        # Character offset exactness
        for start, end, seg_text, _ in segments:
            self.assertEqual(text[start:end], seg_text)

    def test_contrasting_clauses_while_and_whereas(self):
        """Sentences with 'while' and 'whereas' must split into their constituent clauses."""
        text = "Canberra is the capital of Australia, while Melbourne is the country's most populous city."
        segments = nli_service.segment_answer(text)
        clause_segments = [s for s in segments if s[3] == "clause"]

        self.assertEqual(len(clause_segments), 2)
        self.assertEqual(clause_segments[0][2], "Canberra is the capital of Australia")
        self.assertEqual(clause_segments[1][2], "Melbourne is the country's most populous city.")

        for start, end, seg_text, _ in segments:
            self.assertEqual(text[start:end], seg_text)

    def test_contrasting_clause_with_but(self):
        """Sentences with 'but' introducing an independent proposition must split correctly."""
        text = "Denali is the highest mountain peak in North America, but its summit elevation is 7,190 metres."
        segments = nli_service.segment_answer(text)
        clause_segments = [s for s in segments if s[3] == "clause"]

        self.assertEqual(len(clause_segments), 2)
        self.assertEqual(clause_segments[0][2], "Denali is the highest mountain peak in North America")
        self.assertEqual(clause_segments[1][2], "its summit elevation is 7,190 metres.")

        for start, end, seg_text, _ in segments:
            self.assertEqual(text[start:end], seg_text)

    def test_ordinary_sentence_splitting(self):
        """Multi-sentence input must split into proper sentence segments."""
        text = "Mount Elbrus is located in Russia. It is the highest peak in Europe."
        segments = nli_service.segment_answer(text)
        sentence_segments = [s for s in segments if s[3] == "sentence"]

        self.assertEqual(len(sentence_segments), 2)
        self.assertEqual(sentence_segments[0][2], "Mount Elbrus is located in Russia.")
        self.assertEqual(sentence_segments[1][2], "It is the highest peak in Europe.")

        for start, end, seg_text, _ in segments:
            self.assertEqual(text[start:end], seg_text)


if __name__ == "__main__":
    unittest.main()

