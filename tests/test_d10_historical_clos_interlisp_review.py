"""Negative tests prevent a history proposal from becoming a fake D10 resident."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_d10_historical_clos_interlisp_review.py"
spec = importlib.util.spec_from_file_location("d10_history", SCRIPT)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
load = lambda p: json.loads((ROOT / p).read_text(encoding="utf-8"))

class HistoricalD10Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = load(checker.PROPOSALS)
        cls.f = load(checker.FOUNDATION)
        cls.i = load(checker.INVENTORY)

    def audit(self, d=None, f=None, i=None):
        return checker.verify(d if d is not None else self.d,
                              f if f is not None else self.f,
                              i if i is not None else self.i)

    def test_canonical_corpus(self):
        self.assertEqual(self.audit()["proposals"], 9)

    def test_coordinate_ratification_and_physical_forbidden(self):
        for change in ({"coordinate":"0000000000"}, {"ratified":True},
                       {"selected_in_d10":True}, {"physical_t5_authorized":True},
                       {"owner_review":"APPROVED"}):
            with self.subTest(change=change):
                d=copy.deepcopy(self.d);d["rows"][0].update(change)
                with self.assertRaises(ValueError): self.audit(d=d)

    def test_existing_d1_and_d10_names_forbidden(self):
        for name in ("CAR", self.i["rows"][0]["semantic_name"]):
            with self.subTest(name=name):
                d=copy.deepcopy(self.d);d["rows"][0]["historical_name"]=name
                with self.assertRaises(ValueError): self.audit(d=d)

    def test_duplicate_name_and_proposal_id_forbidden(self):
        for field in ("historical_name","proposal_id"):
            d=copy.deepcopy(self.d);d["rows"][1][field]=d["rows"][0][field]
            with self.assertRaises(ValueError): self.audit(d=d)

    def test_missing_source_or_falsifier_forbidden(self):
        for field,value in (("historical_source","https://fake.invalid/source"),("falsifier",""),
                            ("observable_law",""),("triage_status","RATIFIED")):
            with self.subTest(field=field):
                d=copy.deepcopy(self.d);d["rows"][0][field]=value
                with self.assertRaises(ValueError): self.audit(d=d)

    def test_snapshot_inflation_forbidden(self):
        for key in ("selected_added","coordinates_added","ratified_d10"):
            d=copy.deepcopy(self.d);d["snapshot"][key]=1
            with self.assertRaises(ValueError): self.audit(d=d)

if __name__=="__main__":
    unittest.main()
