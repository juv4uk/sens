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

    def test_research_backfill_marker_cannot_be_used_by_unselected_donor(self):
        lines=self.content.splitlines()
        # Mutate a stable historical selected marker, not the final TSV row.
        # Legitimate pending source proposals append after the initial roots.
        fields=next(line.split("\t") for line in lines[1:]
                    if line.split("\t")[3] == "DPB")
        fields[0]="D10P-9999"
        fields[3]="UNSELECTED-RANDOM"
        bad=self.content+"\t".join(fields)+"\n"
        self.assertTrue(guard.selection_trace_errors(bad,self.inventory,self.baseline,self.history))

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
