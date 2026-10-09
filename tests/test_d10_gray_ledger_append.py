#!/usr/bin/env python3
"""Regression: Gray historical selection survives NEW pending D10 proposal rows.

No weakening: history, source SHA, selected resident IDs, witnesses and
historical D10P-0009/0010 ledger rows must still match exactly.
"""
import csv
import importlib.util
import io
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MODULE=ROOT/"scripts/check_d10_gray_word_selection.py"
spec=importlib.util.spec_from_file_location("gray_selection_guard",MODULE)
gray=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=gray
spec.loader.exec_module(gray)


def base_inputs():
    return (
      gray.read(gray.INV),gray.read(gray.SRC),gray.read(gray.HIS),
      gray.read(gray.STATE),gray.read(gray.LOW),
      gray.LED.read_text(encoding="utf-8"),
      gray.DOC.read_text(encoding="utf-8"))


def rows_of(ledger):
    reader=csv.DictReader(io.StringIO(ledger),delimiter="\t")
    return reader.fieldnames,list(reader)


def tsv(fieldnames,rows):
    out=io.StringIO()
    writer=csv.DictWriter(out,fieldnames=fieldnames,delimiter="\t",
                          lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


class GrayHistoricalLedgerGrowth(unittest.TestCase):
    def test_current_original_historical_selection(self):
        self.assertTrue(gray.verify(*base_inputs()))

    def test_later_pending_candidate_may_append(self):
        inv,src,his,state,low,led,doc=base_inputs()
        names,rows=rows_of(led)
        pending=rows[-1].copy()
        pending["proposal_id"]="D10P-PENDING-APPEND-TEST"
        pending["semantic_name"]="UNSELECTED-RESEARCH-FIXTURE"
        pending["status"]="pending-review"
        rows.append(pending)
        self.assertTrue(gray.verify(inv,src,his,state,low,tsv(names,rows),doc))

    def test_two_pending_appends_do_not_retarget_history(self):
        inv,src,his,state,low,led,doc=base_inputs()
        names,rows=rows_of(led)
        for suffix in ("ALPHA","BETA"):
            pending=rows[-1].copy()
            pending["proposal_id"]="D10P-PENDING-"+suffix
            pending["semantic_name"]="RESEARCH-"+suffix
            rows.append(pending)
        self.assertTrue(gray.verify(inv,src,his,state,low,tsv(names,rows),doc))

    def test_missing_original_gray_id_is_rejected(self):
        inv,src,his,state,low,led,doc=base_inputs()
        names,rows=rows_of(led)
        rows=[r for r in rows if r["proposal_id"]!="D10P-0009"]
        with self.assertRaises(AssertionError):
            gray.verify(inv,src,his,state,low,tsv(names,rows),doc)

    def test_duplicate_original_gray_id_is_rejected(self):
        inv,src,his,state,low,led,doc=base_inputs()
        names,rows=rows_of(led)
        original=next(r for r in rows if r["proposal_id"]=="D10P-0010")
        rows.append(original.copy())
        with self.assertRaises(AssertionError):
            gray.verify(inv,src,his,state,low,tsv(names,rows),doc)

    def test_historical_source_provenance_cannot_be_forged(self):
        inv,src,his,state,low,led,doc=base_inputs()
        names,rows=rows_of(led)
        target=next(r for r in rows if r["proposal_id"]=="D10P-0009")
        target["donor_provenance"]="juv4uk/sens@"+("0"*40)+":fake:1-1"
        with self.assertRaises(AssertionError):
            gray.verify(inv,src,his,state,low,tsv(names,rows),doc)


if __name__=="__main__":
    unittest.main(verbosity=2)
