#!/usr/bin/env python3
"""D10 ledger ↔ append-only transition contract; regression/negative controls."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/check-d10-proposal-ledger.py"
spec = importlib.util.spec_from_file_location("d10_proposal_ledger_guard", SOURCE)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)

def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))

class SelectionLedgerTrace(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content = (ROOT / "knowledge/d10-proposal-ledger.tsv").read_text(encoding="utf-8")
        cls.inventory = read("knowledge/d10-v1-semantic-inventory.json")
        cls.baseline = read("knowledge/d10-growth-baseline-v1.json")
        cls.history = read("knowledge/d10-selection-transition-history.json")

    def test_current_five_pinned_research_roots(self):
        self.assertEqual(self.inventory["rows"][625:][0]["semantic_name"], "DPB")
        self.assertEqual([r["semantic_name"] for r in self.inventory["rows"][625:630]],
                         ["DPB", "ARRAY-DISPLACEMENT", "SLOT-BOUNDP", "SLOT-MAKUNBOUND", "REMOVE-METHOD"])
        self.assertEqual([],guard.validate(self.content))
        self.assertEqual([],guard.selection_trace_errors(self.content,self.inventory,self.baseline,self.history))

    def test_625_historical_prefix_and_empty_ledger_remain_valid(self):
        inv = copy.deepcopy(self.inventory)
        inv["rows"] = inv["rows"][:625]
        hist = {"transitions":[]}
        self.assertEqual([], guard.selection_trace_errors("\t".join(guard.FIELDS)+"\n",
                         inv,self.baseline,hist))

    def test_missing_one_record_blocks_selection(self):
        lines=self.content.splitlines()
        for index in range(1,6):
            candidate="\n".join(lines[:index]+lines[index+1:])+"\n"
            self.assertTrue(guard.selection_trace_errors(candidate,self.inventory,self.baseline,self.history))

    def test_previous_inventory_sha_must_match_transition(self):
        s=self.content.replace("D10@5a8cf8e81edecf9ffdeb313152c0e146f4df80bb",
                               "D10@73dd518469f972c55411e004b70b054ba8b3ec86",1)
        self.assertTrue(guard.selection_trace_errors(s,self.inventory,self.baseline,self.history))

    def test_injected_new_selection_requires_new_ledger_and_transition(self):
        inv=copy.deepcopy(self.inventory)
        x=copy.deepcopy(inv["rows"][-1])
        x["stable_id"]="D10-adversarial-unknown"
        x["semantic_name"]="NOT-IN-LEDGER"
        x["coordinate"]=None
        x["ratified_resident"]=False
        inv["rows"].append(x)
        self.assertTrue(guard.selection_trace_errors(self.content,inv,self.baseline,self.history))

    def test_unauthorized_current_coordinate_and_ratification(self):
        for field,value in (("coordinate","0000000000"),("ratified_resident",True)):
            inv=copy.deepcopy(self.inventory)
            inv["rows"][-1][field]=value
            with self.subTest(field=field):
                self.assertTrue(guard.selection_trace_errors(self.content,inv,self.baseline,self.history))

    def test_history_append_id_must_match(self):
        hist=copy.deepcopy(self.history)
        hist["transitions"][-1]["added_stable_ids"][-1]="not-actual-id"
        self.assertTrue(guard.selection_trace_errors(self.content,self.inventory,self.baseline,hist))

    def test_frozen_prefix_cannot_change(self):
        inv=copy.deepcopy(self.inventory)
        inv["rows"][0]["semantic_name"]="SURPRISE-RENAME"
        self.assertTrue(guard.selection_trace_errors(self.content,inv,self.baseline,self.history))

    def test_proposal_precedes_selection_without_forged_migration_block(self):
        lines=self.content.splitlines()
        fields=lines[-1].split("\t")
        fields[0]="D10P-9999"
        fields[1]="окремий-донор"
        fields[2]="незалежний-дослідний-донор"
        fields[3]="UNSELECTED-RANDOM"
        fields[4]="Research source law not selected until independent review"
        donor=self.content+"\t".join(fields)+"\n"
        self.assertEqual([],guard.validate(donor))
        self.assertEqual([],guard.selection_trace_errors(donor,self.inventory,self.baseline,self.history))
        # A legitimate proposal changes neither selected inventory nor history.
        inv=copy.deepcopy(self.inventory)
        inv["rows"].append({"semantic_name":"UNSELECTED-RANDOM", "stable_id":"forged-unreviewed",
                            "coordinate":None, "ratified_resident":False})
        self.assertTrue(guard.selection_trace_errors(donor,inv,self.baseline,self.history))
        for index,value in ((6,"unknown"),(9,"NOT-REAL-BLOCK"),(10,"selected"),(11,"1")):
            wrong=fields.copy()
            wrong[index]=value
            bad=self.content+"\t".join(wrong)+"\n"
            with self.subTest(field=index):
                self.assertTrue(guard.validate(bad), "unverified proposal must be rejected")

    def test_ledger_existing_bytes_must_be_append_only(self):
        self.assertEqual([], guard.append_only_errors(self.content, self.content + ""))
        self.assertEqual([], guard.append_only_errors(self.content, self.content + "# appended\n"))
        rewritten = self.content.replace("вкласти-біти", "переписано-біти", 1)
        self.assertTrue(guard.append_only_errors(self.content, rewritten))

    def test_new_selection_requires_exact_law_and_matching_surfaces(self):
        old = {
            "stable_id": "old", "semantic_name": "OLD", "behavior": "old law",
            "coordinate": None, "coordinate_basis": "UNPLACED",
            "ratified_resident": False, "surface_uk": "старий-закон",
            "surface_ukr": "давній-закон", "source_class": "test",
            "relation_class": "test",
        }
        new = {
            "stable_id": "new", "semantic_name": "NEW-STRICT-LAW",
            "behavior": "Exact new law", "coordinate": None,
            "coordinate_basis": "UNPLACED", "ratified_resident": False,
            "surface_uk": "новий-закон", "surface_ukr": "точний-новий-закон",
            "source_class": "test", "relation_class": "test",
            "status": "SELECTED-RESEARCH-CANDIDATE",
        }
        sha = "a" * 40
        entry = [
            "D10P-9999", "новий-закон", "точний-новий-закон", "NEW-STRICT-LAW",
            "Exact new law", "D10", f"juv4uk/sens@{sha}:lib/core1.lisp:42",
            f"D1-D9@{sha}=NO-MATCH;D10@{sha}=NO-MATCH",
            "UNIVERSAL-BORDER: новий закон незалежний від носія",
            "NOT-A-MIGRATION-BLOCK", "pending-review", "0",
        ]
        content = "\t".join(guard.FIELDS) + "\n" + "\t".join(entry) + "\n"
        before = {"rows": [old]}
        after = {"rows": [old, new]}
        self.assertEqual([], guard.new_selection_contract_errors(before, after, content))
        wrong_law = entry.copy()
        wrong_law[4] = "short paraphrase"
        wrong_content = "\t".join(guard.FIELDS) + "\n" + "\t".join(wrong_law) + "\n"
        self.assertTrue(guard.new_selection_contract_errors(before, after, wrong_content))
        wrong_surface = entry.copy()
        wrong_surface[1] = "не-та-поверхня"
        wrong_content = "\t".join(guard.FIELDS) + "\n" + "\t".join(wrong_surface) + "\n"
        self.assertTrue(guard.new_selection_contract_errors(before, after, wrong_content))

    def test_preexisting_selected_law_paraphrases_are_not_rewritten(self):
        # Current selected roots predate byte-exact law matching; preserve them.
        self.assertEqual([], guard.new_selection_contract_errors(
            self.inventory, self.inventory, self.content
        ))

    def test_migration_block_may_still_provide_true_source(self):
        records=self.content.splitlines()
        fields=records[1].split("\t")
        fields[9]=fields[6]
        changed=records.copy()
        changed[1]="\t".join(fields)
        data="\n".join(changed)+"\n"
        self.assertEqual([],guard.validate(data))
        self.assertEqual([],guard.selection_trace_errors(data,self.inventory,self.baseline,self.history))

if __name__ == "__main__":
    unittest.main(verbosity=2)
