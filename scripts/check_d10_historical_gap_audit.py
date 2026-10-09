#!/usr/bin/env python3
"""Fail-closed historical coverage evidence: never promotes proposals to D10."""
from __future__ import annotations
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/d10-historical-coverage-gap-audit-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
DIALECT = ROOT / "docs/DIALECT-COMPARISON.md"

def verify(ledger, inv, foundation, dialect):
    assert ledger["schema"] == "d10-historical-coverage-gap-audit/v1"
    assert ledger["status"] == "RESEARCH-COVERAGE-GAPS-ONLY"
    assert ledger["snapshot"]["ratified"] == 0
    assert len(inv["rows"]) == inv["accounting"]["selected_semantic_candidates"]
    assert inv["accounting"]["ratified_d10_residents"] == 0
    selected = {r["semantic_name"].upper() for r in inv["rows"]}
    lower = {str(n).upper() for domain in foundation["domains"].values()
             for n in domain.get("residents", {}).values()}
    assert len(selected) == len(inv["rows"])
    assert len(ledger["historic_family_coverage"]) >= 10
    assert len(ledger["exact_name_absent_research"]) >= 15
    assert len({r["review_id"] for r in ledger["exact_name_absent_research"]}) == len(ledger["exact_name_absent_research"])
    assert len({r["historical_spelling"] for r in ledger["exact_name_absent_research"]}) == len(ledger["exact_name_absent_research"])
    for r in ledger["historic_family_coverage"]:
        assert r["status"] != "EXHAUSTIVE", "historical completeness was not proved"
        assert r["evidence"] and r["historical_source"].startswith("https://")
        assert r["in_repo"]
    for name in ("Franz Lisp", "ZetaLisp", "EuLisp", "ISLISP"):
        assert name in dialect, "historical omission lost from in-repo appendix"
    for r in ledger["exact_name_absent_research"]:
        name = r["historical_spelling"].upper()
        assert name not in selected | lower, f"exact name now exists: review {name}"
        assert r["status"].startswith("HOLD-")
        assert r["exact_name_in_d1_d10"] is False
        assert r["semantically_novel"] is None
        assert r["coordinate"] is None and r["ratified"] is False
        assert r["selected_in_inventory"] is False
        assert r["physical_t5_authorized"] is False
        assert r["primary_url"].startswith("https://")
        assert r["observable_question"]
        if r["status"] in ("HOLD-D2-CONTROL", "HOLD-D2-SYNTAX"):
            assert r["coordinate"] is None, "only D2 owns language control"
    for r in ledger["known_not_missing"]:
        name = r["name"].upper()
        assert name in selected | lower, f"existing identity has disappeared: {name}"
    return {"historical_families":len(ledger["historic_family_coverage"]),
            "exact_name_gaps":len(ledger["exact_name_absent_research"]),
            "newly_selected":0,"newly_ratified":0,"selected_actual":len(selected)}

def self_test(ledger, inv, foundation, dialect):
    baseline = verify(ledger, inv, foundation, dialect)
    for change in ({"coordinate":"0000000000"}, {"ratified":True},
                   {"selected_in_inventory":True}, {"semantically_novel":True},
                   {"historical_spelling":"CALL/CC"}, {"status":"RATIFIED"}):
        tmp = copy.deepcopy(ledger); tmp["exact_name_absent_research"][0].update(change)
        try: verify(tmp, inv, foundation, dialect)
        except AssertionError: pass
        else: raise AssertionError(f"unsafe research promotion not blocked: {change}")
    tmp=copy.deepcopy(ledger)
    tmp["historic_family_coverage"][0]["status"]="EXHAUSTIVE"
    try:verify(tmp,inv,foundation,dialect)
    except AssertionError:pass
    else:raise AssertionError("false exhausted history not blocked")
    return baseline

def main():
    read=lambda p: json.loads(p.read_text(encoding="utf-8"))
    z=read(LEDGER); inv=read(INVENTORY); fd=read(FOUNDATION); dialect=DIALECT.read_text(encoding="utf-8")
    result=self_test(z,inv,fd,dialect) if "--self-test" in sys.argv else verify(z,inv,fd,dialect)
    print("D10-HISTORICAL-GAPS PASS",json.dumps(result,sort_keys=True))
if __name__=="__main__": main()
