"""Historical FIND-METHOD contract and adversarial mutation checks."""
import copy
import json
import unittest
from pathlib import Path
from scripts.check_d10_find_method_selected_v1 import (
  ROOT, MANIFEST, INVENTORY, STATE, FOUNDATION, DONOR, ContractError, audit, find_exact_method
)

class FindMethodReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = lambda p: json.loads((ROOT/p).read_text(encoding="utf-8"))
        cls.source = (r(MANIFEST),r(INVENTORY),r(STATE),r(FOUNDATION),r(DONOR))
        cls.methods = [
            {"identity":"PRIMARY-BASE", "qualifiers":[], "specializers":["BASE"],"called":False},
            {"identity":"BEFORE-BASE", "qualifiers":[":before"], "specializers":["BASE"],"called":False},
            {"identity":"AFTER-BASE", "qualifiers":[":after"], "specializers":["BASE"],"called":False},
        ]

    def test_ledger_and_source(self):
        self.assertGreaterEqual(audit(*self.source)["selected"],626)

    def test_primary_before_separate_objects_and_no_execution(self):
        p = find_exact_method(self.methods,1,[],["BASE"])
        b = find_exact_method(self.methods,1,[":before"],["BASE"])
        self.assertIs(p,self.methods[0])
        self.assertIs(b,self.methods[1])
        self.assertIsNot(p,b)
        self.assertFalse(any(m["called"] for m in self.methods))

    def test_exact_specializer_not_subtype_applicability(self):
        self.assertIsNone(find_exact_method(self.methods,1,[],["CHILD"],False))
        self.assertIs(find_exact_method(self.methods,1,[],["BASE"]),self.methods[0])

    def test_nonexistent_qualifier_and_errorp(self):
        self.assertIsNone(find_exact_method(self.methods,1,[":around"],["BASE"],False))
        with self.assertRaises(LookupError):
            find_exact_method(self.methods,1,[":around"],["BASE"])

    def test_required_specializer_length_mismatch_always_errors(self):
        for errorp in (True,False):
            with self.subTest(errorp=errorp):
                with self.assertRaises(ContractError):
                    find_exact_method(self.methods,1,[],[],errorp)

    def test_registration_permutation_no_semantic_delta(self):
        found = find_exact_method(list(reversed(self.methods)),1,[":before"],["BASE"],False)
        self.assertIs(found,self.methods[1])

    def test_owner_coordinate_mutation_fail_closed(self):
        for edit in ({"coordinate":"0000000000"},{"ratified_resident":True},{"status":"RATIFIED"}):
            data = copy.deepcopy(self.source)
            r = next(x for x in data[1]["rows"] if x["semantic_name"]=="FIND-METHOD")
            r.update(edit)
            with self.subTest(edit=edit), self.assertRaises(ContractError):
                audit(*data)

    def test_collision_or_selected_count_drift_fail_closed(self):
        for edit in ("duplicate","count","D9-name"):
            data = copy.deepcopy(self.source)
            if edit=="duplicate":
                data[1]["rows"].append(copy.deepcopy(data[1]["rows"][-1]))
            elif edit=="count":
                data[2]["target"]["selected_semantic_candidates"]+=1
            else:
                # Duplicate a ratified lower-domain identity inside selected D10.
                data[1]["rows"][0]["semantic_name"]="CAR"
                data[1]["rows"][-1]["semantic_name"]="CAR"
            with self.subTest(edit=edit), self.assertRaises(ContractError):
                audit(*data)

    def test_historical_evidence_drift_fail_closed(self):
        data = copy.deepcopy(self.source)
        next(x for x in data[4]["rows"] if x["proposal_id"]=="CLOS-01")["historical_source"]="https://invalid.example"
        with self.assertRaises(ContractError):
            audit(*data)

if __name__=="__main__":
    unittest.main()
