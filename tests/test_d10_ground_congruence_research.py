#!/usr/bin/env python3
"""D10 symbolic-AI: finite ground congruence independent model tests."""
import importlib.util
import itertools
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
FILE=ROOT/"scripts/check_d10_ground_congruence_research.py"
spec=importlib.util.spec_from_file_location("d10_ground_congruence",FILE)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)

def small():
    return {"nodes":[
        {"id":"a","symbol":"A","args":[]},
        {"id":"b","symbol":"B","args":[]},
        {"id":"fa","symbol":"F","args":["a"]},
        {"id":"fb","symbol":"F","args":["b"]},
        {"id":"ga","symbol":"G","args":["a"]}],
        "equalities":[["a","b"]],
        "queries":[["fa","fb"],["fa","ga"],["a","b"]]}

class D10GroundCongruenceTests(unittest.TestCase):
    def test_five_dossier_cases_have_two_separate_witnesses(self):
        self.assertEqual(len(mod.dossier()["examples"]),5)

    def test_nontrivial_congruence_is_not_plain_EQ_or_UNIFY(self):
        record=small()
        self.assertEqual(mod.union_find_closure(record)["entailed"],[True,False,True])
        self.assertEqual(mod.relation_fixed_point(record),mod.union_find_closure(record))

    def test_no_axioms_is_no_entailment_not_disequality(self):
        record=small()
        record["equalities"]=[]
        self.assertEqual(mod.union_find_closure(record)["entailed"],[False,False,False])

    def test_exhaustive_all_1024_small_ground_equality_subsets(self):
        record=small()
        ids=[n["id"] for n in record["nodes"]]
        pairs=[list(p) for p in itertools.combinations(ids,2)]
        self.assertEqual(len(pairs),10)
        for mask in range(1024):
            record["equalities"]=[p for i,p in enumerate(pairs) if mask&(1<<i)]
            self.assertEqual(mod.union_find_closure(record),
                             mod.relation_fixed_point(record),mask)

    def test_equations_idempotent_and_symmetric(self):
        record=small()
        baseline=mod.union_find_closure(record)
        record["equalities"]=[["b","a"],["a","b"],["b","a"]]
        self.assertEqual(mod.union_find_closure(record),baseline)

    def test_reject_forward_reference_cycles_and_wrong_arity(self):
        record=small()
        record["nodes"][2]["args"]=["fa"]
        with self.assertRaisesRegex(ValueError,"earlier"):
            mod.union_find_closure(record)
        record=small()
        record["nodes"].append({"id":"Fzero","symbol":"F","args":[]})
        with self.assertRaisesRegex(ValueError,"arity"):
            mod.union_find_closure(record)

    def test_bad_query_and_equation_rejected(self):
        for category,changed in (("queries",[["outside","a"]]),
                                 ("equalities",[["a"]])):
            record=small()
            record[category]=changed
            with self.assertRaises(ValueError):
                mod.union_find_closure(record)

    def test_no_premature_selection_or_ratification(self):
        data=json.loads(mod.DOSSIER.read_text(encoding="utf-8"))
        self.assertEqual(data["status"],"HOLD-CORE-VS-LIBRARY")
        self.assertIsNone(data["coordinate"])
        self.assertFalse(data["selected"])
        self.assertFalse(data["ratified_resident"])
        self.assertEqual(data["current_d9_behavioral_dedup"],"REVIEW_REQUIRED")
        self.assertIn("UNIFY",data["existing_domain_dedup"])
        self.assertIn("EQ",data["existing_domain_dedup"])

if __name__=="__main__":
    unittest.main()
