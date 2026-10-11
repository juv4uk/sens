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
    def test_current_is_not_d11(self):
        r = gate.audit(ROOT)
        self.assertEqual(1024, r["capacity"])
        self.assertEqual(1024, r["selected"]+r["remaining"])
        self.assertFalse(r["ready_to_start_d11"])

    def test_current_v6_has_every_selected_coordinate(self):
        report = gate.audit(ROOT)
        self.assertEqual(719, report["selected"])
        self.assertEqual(719, report["placed"])
        self.assertEqual(0, report["unplaced"])
        self.assertEqual(463, report["research_gauge_allocated"])
        self.assertTrue(report["current_map_is_canonical_research"])
        self.assertEqual(305, report["remaining"])
        self.assertEqual(0, report["ratified"])
        self.assertFalse(report["blocking_errors"])

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
