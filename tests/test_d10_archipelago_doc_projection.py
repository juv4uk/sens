#!/usr/bin/env python3
"""Doc arithmetic stays a current D10 inventory projection, not ratification."""
import copy
import importlib.util
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/check-d10-archipelago-doc-projection.py"
spec = importlib.util.spec_from_file_location("d10_archipelago_doc_projection", PATH)
guard = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = guard
spec.loader.exec_module(guard)


class D10ArchipelagoProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = guard.DOC.read_text(encoding="utf-8")
        cls.inventory = json.loads(guard.INVENTORY.read_text(encoding="utf-8"))
        cls.matrix = json.loads(guard.MATRIX.read_text(encoding="utf-8"))

    def test_real_document_matches_single_stream_625_selection(self):
        result = guard.validate(self.doc, self.inventory, self.matrix)
        self.assertEqual(result["selected"], self.inventory["accounting"]["selected_semantic_candidates"])
        self.assertEqual(result["remaining"], self.inventory["accounting"]["remaining_semantic_inventory"])
        self.assertEqual(result["ratified"], 0)
        self.assertEqual(result["donor_repositories"], 87)

    def test_changed_inventory_demands_same_pr_document_update(self):
        changed = copy.deepcopy(self.inventory)
        changed["accounting"]["selected_semantic_candidates"] += 1
        changed["accounting"]["remaining_semantic_inventory"] -= 1
        changed["accounting"]["unplaced_selected_candidates"] += 1
        changed["rows"].append(dict(changed["rows"][-1]))
        with self.assertRaisesRegex(ValueError, "stale or missing"):
            guard.validate(self.doc, changed, self.matrix)

    def test_stale_434_pretended_current_must_fail(self):
        with self.assertRaisesRegex(ValueError, "stale"):
            guard.validate(self.doc.replace(f'{self.inventory["accounting"]["selected_semantic_candidates"]}/1024', "434/1024"), self.inventory, self.matrix)

    def test_duplicated_or_reversed_marker_must_fail(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            guard.validate(self.doc + guard.BEGIN, self.inventory, self.matrix)
        reordered = self.doc.replace(guard.BEGIN, "__X__").replace(
            guard.END, guard.BEGIN).replace("__X__", guard.END)
        with self.assertRaisesRegex(ValueError, "misordered"):
            guard.validate(reordered, self.inventory, self.matrix)

    def test_no_per_package_hidden_semantic_namespace(self):
        with self.assertRaisesRegex(ValueError, "single-stream"):
            guard.validate(self.doc.replace("#4162", "#9999"), self.inventory, self.matrix)
        with self.assertRaisesRegex(ValueError, "package-exclusion"):
            guard.validate(self.doc.replace("не є підставою відхиляти", "слід виключити"),
                           self.inventory, self.matrix)

    def test_current_donor_class_counts_are_invariant(self):
        changed = copy.deepcopy(self.matrix)
        changed["policy_counts"]["EVIDENCE-DONOR"] -= 1
        changed["policy_counts"]["DIRECT-SEMANTIC-DONOR"] += 1
        with self.assertRaisesRegex(ValueError, "stale donor-class"):
            guard.validate(self.doc, self.inventory, changed)

    def test_unratified_coordinates_cannot_be_silently_promoted(self):
        changed = copy.deepcopy(self.inventory)
        changed["accounting"]["ratified_d10_residents"] = 1
        with self.assertRaisesRegex(ValueError, "inconsistent"):
            guard.validate(self.doc, changed, self.matrix)
        with self.assertRaisesRegex(ValueError, "boundary missing"):
            guard.validate(self.doc.replace("coordinate=null", "coordinate=1010101010"),
                           self.inventory, self.matrix)

    def test_bridge_meaning_is_not_optional_or_a_hidden_namespace(self):
        with self.assertRaisesRegex(ValueError, "missing required island border meaning"):
            guard.validate(self.doc.replace("\nISLAND-CALL\n", "\nISLAND-OPCODE\n"),
                           self.inventory, self.matrix)


if __name__ == "__main__":
    unittest.main()
