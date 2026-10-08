#!/usr/bin/env python3
"""Negative proof that raw D10 source records cannot become resident identities."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/check-d10-library-source-symbols-v1.py"
spec = importlib.util.spec_from_file_location("check_d10_library_source_symbols_v1", PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def evidence():
    read = lambda p: json.loads(p.read_text(encoding="utf-8"))
    return [read(mod.RAW), read(mod.SELECTED_LIBRARY), read(mod.INVENTORY),
            read(mod.STATE)]


class D10RawNotResidents(unittest.TestCase):
    def test_102_raw_definitions_are_source_pinned_and_never_selected(self):
        result = mod.validate(*evidence())
        self.assertEqual(result["raw_definitions_checked"], 102)
        self.assertEqual(result["selected_authority_unchanged"], 625)
        self.assertEqual(result["ratified_residents"], 0)
        self.assertEqual(result["newly_selected_from_raw_harvest"], 0)
        self.assertEqual(result["exact_name_duplicates_with_selected"], 15)
        self.assertEqual(result["source_counts"]["lib/reason.lisp"], 0)

    def test_restored_39_selected_are_distinct_from_102_symbols(self):
        raw, lib, inv, state = evidence()
        self.assertEqual(lib["accounting"]["selected_d10_candidates"], 39)
        lib["schema"] = raw["schema"]
        with self.assertRaisesRegex(ValueError, "39 independently selected"):
            mod.validate(raw, lib, inv, state)

    def test_raw_cannot_inject_coordinate_or_claim_ratification(self):
        for mutation in ("coordinate", "status", "ratified_resident"):
            raw, lib, inv, state = evidence()
            if mutation == "coordinate":
                raw["candidates"][0]["coordinate"] = "0000000000"
            elif mutation == "status":
                raw["candidates"][0]["status"] = "SELECTED"
            else:
                raw["candidates"][0]["ratified_resident"] = True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                mod.validate(raw, lib, inv, state)

    def test_source_pin_line_and_name_must_match_actual_git_blob(self):
        for mutation in ("blob", "line", "name", "source"):
            raw, lib, inv, state = evidence()
            row = raw["candidates"][0]
            if mutation == "blob":
                row["blob_sha"] = "0" * 40
            elif mutation == "line":
                row["line"] = row["line"] + 1
            elif mutation == "name":
                row["name"] = "fake-lisp-resident"
            else:
                raw["sources"][0]["blob_sha"] = "0" * 40
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                mod.validate(raw, lib, inv, state)

    def test_duplicate_definition_and_count_drift_are_rejected(self):
        raw, lib, inv, state = evidence()
        raw["candidates"].append(copy.deepcopy(raw["candidates"][0]))
        raw["count"] += 1
        with self.assertRaises(ValueError):
            mod.validate(raw, lib, inv, state)

    def test_no_raw_harvest_can_forge_selected_semantic_inventory(self):
        raw, lib, inv, state = evidence()
        state["target"]["selected_semantic_candidates"] = 727
        with self.assertRaisesRegex(ValueError, "selected/remaining"):
            mod.validate(raw, lib, inv, state)

    def test_true_39_row_cannot_be_deleted_without_failing(self):
        raw, lib, inv, state = evidence()
        lib["rows"].pop()
        with self.assertRaisesRegex(ValueError, "39 independently selected"):
            mod.validate(raw, lib, inv, state)


if __name__ == "__main__":
    unittest.main()
