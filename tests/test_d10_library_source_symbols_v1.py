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

    def test_37_historical_reason_binders_are_visible_but_not_new_residents(self):
        result = mod.validate(*evidence())
        donor = result["historical_alternate_head_donor"]
        self.assertEqual(donor["path"], "lib/reason.lisp")
        self.assertEqual(donor["blob_sha"], "dadc52a2f40f2f30ad77642898afb81980044c08")
        self.assertEqual(donor["source_head"], "00001011")
        self.assertEqual(donor["top_level_definitions_observed"], 37)
        self.assertEqual(donor["semantic_meanings_selected_from_history"], 0)
        self.assertEqual(donor["new_D10_coordinates"], 0)
        self.assertEqual(len(donor["selected_exact_name_duplicates"]), 6)
        names = {d["name"] for d in donor["definitions"]}
        self.assertIn("reason-index-build-scan", names)
        self.assertIn("prove-goal-state", names)
        self.assertIn("prove-rule", donor["selected_exact_name_duplicates"])
        self.assertIn("map-goal-results", donor["selected_exact_name_duplicates"])
        self.assertEqual(result["source_counts"]["lib/reason.lisp"], 0)
        self.assertTrue(all(d["semantic_admission"] is False for d in donor["definitions"]))
        self.assertTrue(all(d["classification"] == "HISTORICAL_TOP_LEVEL_BINDER_SHAPE_ONLY"
                            for d in donor["definitions"]))

    def test_alternate_head_scanner_excludes_comments_strings_quotes_and_nested_data(self):
        forms = [
            "; (00001011 comment spoof)",
            "'(00001011 quoted-spoof (00000001 ()))",
            '(00000001 "(00001011 quoted-data)")',
            "(00001011 real-meaning (00001000 (x) x))",
            "(00001000 (x)",
            "(00001011 inner-shape (00000001 ()))",
            ")",
            '"(00001011 string-spoof)"',
            "(00001011 last-one (00000001 ())) ; (00001011 fake-comment)",
        ]
        observed = mod.historical_top_level_define_rows(forms)
        self.assertEqual([x["name"] for x in observed],
                         ["real-meaning", "last-one"])
        self.assertEqual([x["line"] for x in observed], [4, 9])

    def test_multiline_historical_binder_name_is_a_complete_top_level_definition(self):
        source = [
            "(00001011 newline-terminated",
            "  (00001000 (x) (00000001 ())))",
        ]
        found = mod.historical_top_level_define_rows(source)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["line"], 1)
        self.assertEqual(found[0]["name"], "newline-terminated")

    def test_historical_donor_parser_rejects_unbalanced_and_string_damage(self):
        with self.assertRaisesRegex(ValueError, "unbalanced"):
            mod.historical_top_level_define_rows(["(00001011 first ())", ")"])
        with self.assertRaisesRegex(ValueError, "unclosed"):
            mod.historical_top_level_define_rows(["(00001011 first (00001000 (x) x)"])
        with self.assertRaisesRegex(ValueError, "unclosed"):
            mod.historical_top_level_define_rows(['(00001011 first "not closed)'])

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
