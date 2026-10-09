#!/usr/bin/env python3
"""Historical PSL/Interlisp/Lisp Machine research-only fail-closed census."""
import argparse
import copy
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
LEDGER = BASE / "knowledge/d10-psl-interlisp-lispm-unmerged-residual-v1.json"
LOWER = BASE / "knowledge/d1-d9-foundation.json"
D10 = BASE / "knowledge/d10-v1-semantic-inventory.json"

def sha(path):
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=BASE, text=True).strip()

def check(j, f, d, pin=True):
    assert j["status"] == "RESEARCH-HOLD-NO-ADMISSION"
    assert j["accounting"]["added_selected"] == j["accounting"]["added_ratified"] == j["accounting"]["assigned_coordinates"] == 0
    assert j["snapshot"]["d10_ratified"] == d["accounting"]["ratified_d10_residents"] == 0
    assert j["snapshot"]["d10_selected"] == d["accounting"]["selected_semantic_candidates"] == 625
    assert j["snapshot"]["d10_capacity"] == d["capacity"] == 1024
    if pin:
        assert sha(LOWER) == j["snapshot"]["foundation_blob"], "foundation changed — review"
        assert sha(D10) == j["snapshot"]["selected_blob"], "D10 inventory changed — review"
    low = {str(v).upper() for domain in f["domains"].values() for v in domain["residents"].values()}
    high = {r["semantic_name"].upper() for r in d["rows"]}
    rows = j["proposals"]
    assert len(rows) == j["accounting"]["rows"] == 21
    assert sum(r["donor"].startswith("PSL-") for r in rows) == j["accounting"]["psl"] == 9
    assert sum(r["donor"].startswith("INTERLISP-") for r in rows) == j["accounting"]["interlisp"] == 5
    assert sum(r["donor"].startswith("LISPM-") for r in rows) == j["accounting"]["lispm"] == 7
    assert len({r["historical_name"] for r in rows}) == len(rows)
    ids=set()
    for r in rows:
        assert r["id"] not in ids
        ids.add(r["id"])
        assert r["historical_name"].upper() not in low, f"already D1-D9 {r['historical_name']}"
        assert r["historical_name"].upper() not in high, f"already D10 {r['historical_name']}"
        assert r["coordinate"] is None and r["selected"] is False and r["ratified"] is False
        assert r["exact_in_ratified_D1_D9"] is False and r["exact_in_selected_D10"] is False
        assert r["triage"].startswith("HOLD-")
        assert r["source_verified"] == "MANUAL-ATTESTED"
        assert r["surface_uk"] and r["surface_ukr"]
        assert r["source_blocker"].startswith("NONE")
        assert r["dedup_basis"] == f"D1-D9 {j['snapshot']['foundation_blob']}; D10 selected {j['snapshot']['selected_blob']}"
        assert r["primary_source_url"].startswith("https://") and r["primary_section"]
        assert r["observable_behavior"] and r["positive_witness_spec"] and r["falsifier_spec"]
        assert r["conceptual_existing_neighbors"] and r["owner"]
        assert r["priority"] in ("P0","P1","P2")
        if r["triage"].startswith(("HOLD-D2-", "HOLD-CONTROL")):
            assert r["owner"] in ("D2-EXCLUSIVE-CONTROL", "D2-CONTROL-REVIEW")
        if r["donor"] == "LISPM-1984":
            assert "later Lisp Machine Manual" in r["primary_section"]
    return True

def self_test(j, f, d):
    check(j, f, d)
    def bad(mutate):
        sample = copy.deepcopy(j)
        mutate(sample)
        try: check(sample, f, d, pin=False)
        except AssertionError: return
        raise AssertionError("adversarial example was falsely admitted")
    bad(lambda x: x["proposals"][0].__setitem__("coordinate", "0000000000"))
    bad(lambda x: x["proposals"][0].__setitem__("ratified", True))
    bad(lambda x: x["proposals"][0].__setitem__("selected", True))
    bad(lambda x: x["proposals"][0].__setitem__("triage", "SELECTED"))
    bad(lambda x: x["proposals"][0].__setitem__("historical_name", "CAR"))
    bad(lambda x: x["proposals"][0].__setitem__("historical_name", "GETD"))
    bad(lambda x: x["proposals"][0].__setitem__("surface_uk", ""))
    bad(lambda x: x["proposals"][0].__setitem__("falsifier_spec", ""))
    bad(lambda x: x["proposals"][9].__setitem__("owner", "D10-CONTROL"))
    bad(lambda x: x["proposals"][20].__setitem__("primary_section", "1981"))
    bad(lambda x: x["proposals"].append(copy.deepcopy(x["proposals"][0])))
    bad(lambda x: x["accounting"].__setitem__("added_selected",1))
    print("PASS: 21 research-only rows, D1-D9/D10 exact-name guard, 12 adversarial negative controls")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    j,f,d=[json.loads(path.read_text(encoding="utf-8")) for path in (LEDGER,LOWER,D10)]
    if args.self_test: self_test(j,f,d)
    else:
        check(j,f,d)
        print("PASS: historical audit, no semantic admissions")

if __name__ == "__main__":
    main()
