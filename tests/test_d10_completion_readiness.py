"""Регресії: D10 не можна оголосити повним за повторні назви."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("d10_gate", ROOT / "scripts/check_d10_completion_readiness.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class Readiness(unittest.TestCase):
    def test_current_d11_gate_is_derived_from_live_inventory(self):
        r = gate.audit(ROOT)
        self.assertEqual(1024, r["capacity"])
        self.assertEqual(1024, r["selected"]+r["remaining"])
        self.assertEqual(r["inventory_full"] and r["placement_full"] and
                         r["ratified"] == r["capacity"] and not r["blocking_errors"],
                         r["ready_to_start_d11"])

    def test_current_preserves_v7_archive_and_live_accounting(self):
        report = gate.audit(ROOT)
        pointer = json.loads((ROOT / "knowledge/d10-current-inventory.json").read_text())
        state = pointer["canonical_current"]
        self.assertEqual(state["selected"], report["selected"])
        self.assertEqual(state["placed"], report["placed"])
        self.assertEqual(state["unplaced"], report["unplaced"])
        self.assertEqual(state["ratified"], report["ratified"])
        self.assertEqual(1024, report["selected"] + report["remaining"])
        self.assertGreaterEqual(report["selected"], 721)
        self.assertTrue(report["current_map_is_canonical_research"])
        self.assertFalse(report["blocking_errors"])

    def test_append_only_growth_preserves_frozen_v7_prefix(self):
        archived = [{"stable_id": "v7.one"}, {"stable_id": "v7.two"}]
        extended = archived + [{"stable_id": "future.722"}]
        self.assertTrue(gate.preserves_archived_prefix(archived, archived))
        self.assertTrue(gate.preserves_archived_prefix(extended, archived))
        self.assertFalse(gate.preserves_archived_prefix(archived[:-1], archived))
        self.assertFalse(gate.preserves_archived_prefix(
            [{"stable_id": "rewritten"}] + archived[1:], archived))

    def test_same_donor_twice_is_one_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            k=Path(td)
            sample={"candidate":{"semantic_name":"EXACT-TEST","law":"finite law",
                     "witnesses":["yes"],"falsifiers":["no"]}}
            for n in ["d10-a.json","d10-b.json"]:
                (k/n).write_text(json.dumps(sample))
            r=gate.source_queue(k,set(),set())
            self.assertEqual(1,r["distinct_source_names_unselected"])
            self.assertEqual(1,r["repeated_across_sources"])
            self.assertEqual(1,r["without_proposal"])

    def test_donor_without_negative_test_is_not_ready(self):
        with tempfile.TemporaryDirectory() as td:
            k=Path(td)
            (k/"d10-only-name.json").write_text(json.dumps({
                "candidates":[{"semantic_name":"LABEL"},{"semantic_name":"NO-TEST","law":"x","positives":[1]}]}))
            self.assertEqual(0,gate.source_queue(k,set(),set())["distinct_source_names_unselected"])

if __name__=="__main__":
    unittest.main()
