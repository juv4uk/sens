#!/usr/bin/env python3
"""1958 GPS finite difference/operator/subgoal source-reconstruction review.

Research only: independently executed SWI-Prolog Boolean examples, not IPL-V,
not historical GPS implementation, not binary SENS semantics.
"""
import argparse
import copy
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOSSIER=ROOT/"knowledge/d10-gps-means-ends-historical-research-20261009.json"
FOUND=ROOT/"knowledge/d1-d9-foundation.json"
INV=ROOT/"knowledge/d10-v1-semantic-inventory.json"
ORACLE=ROOT/"tests/oracles/d10_gps_means_ends_swi.pl"
REVIEW={
 "GPS-FINITE-STATE-DIFFERENCES",
 "GPS-OPERATOR-DIFFERENCE-WITNESS",
 "GPS-OPERATOR-PRECONDITION-SUBGOALS",
}
HOLD={
 "GPS-GOAL-STACK","GPS-DIFFERENCE-PRIORITY","GPS-COMPLETE-PLAN",
 "IPL-LIST-MEMORY-ACCESS","GPS-OPERATOR-APPLY",
}
SOURCE="https://home.mis.u-picardie.fr/~furst/docs/Newell_Simon_General_Problem_Solving_1959.pdf"
EXPECTED=(
"missing_atom",
"missing_precondition_creates_subgoal",
"unwanted_true_atom_is_difference",
"unwanted_removal_blocked",
"irrelevant_side_effect",
"complete_goal_has_no_relevant_effect",
"relevant_not_progress_certificate",
"add_satisfied_goal_not_witness",
"precondition_unrelated_to_relevance",
"irrelevant_operator_can_be_applicable",
"empty_universe",
"negative_invalid_state",
"negative_invalid_goal",
"negative_invalid_precondition",
"negative_conflicting_add_delete_effect",
"negative_duplicate_atoms_forbidden",
"negative_unsorted_atoms_forbidden",
)

def load(p):
    return json.loads(p.read_text(encoding="utf-8"))

def verify(dossier, foundation, inventory, program):
    assert dossier["schema"]=="d10-early-symbolic-ai-gps-difference-links/v1"
    assert dossier["status"]=="HISTORICAL-RESEARCH-HOLD-NO-SELECTION"
    source=dossier["historic_source"]
    assert source["url"]==SOURCE
    assert source["primary_pages"]==[10,11]
    assert "modern formal reconstruction" in source["reconstruction_warning"]
    assert foundation["status"]=="owner-ratified"
    assert inventory["domain"]=="D10" and inventory["width"]==10
    assert inventory["accounting"]["selected_semantic_candidates"]==len(inventory["rows"])
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert len(inventory["rows"])>=635
    names={str(x).upper() for d in foundation["domains"].values() for x in d["residents"].values()}
    names|={r["semantic_name"].upper() for r in inventory["rows"]}
    selected=dossier["research"]
    assert len(selected)==3
    assert {r["semantic_name"] for r in selected}==REVIEW
    assert all(r["semantic_name"] not in names for r in selected)
    for x in selected:
        assert x["status"]=="REVIEW-DERIVABLE"
        assert x["uk"] and x["ukr"] and x["law"]
        assert len(x["witnesses"])>=2 and len(x["falsifiers"])>=2
        assert x["nearest_existing"] and x["complexity"]
        assert any("D9 " in n or "STRIPS" in n for n in x["nearest_existing"])
    holds=dossier["hold_hypotheses"]
    assert len(holds)==5 and {x["label"] for x in holds}==HOLD
    assert all(x["status"].startswith("HOLD-") and x["reason"] for x in holds)
    border=dossier["prior_semantic_boundary"]
    assert border["unselected"] is True
    assert border["ledger_appended"] is False
    assert border["binary_coordinate"] is None
    assert border["d10_ratified"]==0
    assert dossier["test_oracle"]==str(ORACLE.relative_to(ROOT))
    assert dossier["guard"]==str(Path(__file__).relative_to(ROOT))
    observed=tuple(re.findall(r"(?m)^\s+check\(([a-z][a-z0-9_]+),",program))
    assert observed==EXPECTED, "GPS independent witness list changed"
    assert "(role research-only)" in program
    assert "(semantic-authority-change none)" in program
    assert "RECONSTRUCTION-NOT-ORIGINAL-IPL" in program
    return {"names":3,"hold":5,"oracle_cases":len(observed),
            "d10_live_selected":len(inventory["rows"]),"d10_new_selected":0}

def negative_controls(d,f,i,p):
    verify(d,f,i,p)
    trials=[
        (0,lambda x:x.update({"status":"SELECTED-RESEARCH-CANDIDATE"})),
        (0,lambda x:x["historic_source"].update({"url":"https://invalid.example"})),
        (0,lambda x:x["prior_semantic_boundary"].update({"binary_coordinate":"0000000000"})),
        (0,lambda x:x["prior_semantic_boundary"].update({"d10_ratified":1})),
        (0,lambda x:x["research"][0].update({"semantic_name":"SEARCH"})),
        (0,lambda x:x["research"][1].update({"witnesses":[]})),
        (0,lambda x:x["research"][2].update({"falsifiers":[]})),
        (0,lambda x:x["hold_hypotheses"][0].update({"status":"SELECTED"})),
        (3,lambda x:x.replace("negative_unsorted_atoms_forbidden","renamed_oracle")),
        (2,lambda x:x["accounting"].update({"ratified_d10_residents":1}))
    ]
    for pos,fn in trials:
        args=[copy.deepcopy(d),copy.deepcopy(f),copy.deepcopy(i),p]
        replacement=fn(args[pos])
        if replacement is not None:args[pos]=replacement
        try:verify(*args)
        except (AssertionError,KeyError,TypeError):continue
        raise AssertionError("unsafe GPS historical admission mutation accepted")
    print("D10 GPS SOURCE GATE 10/10 negative controls PASS")

def run_swi(binpath):
    result=subprocess.run([binpath,"-q","-f",str(ORACLE)],
                          cwd=ROOT,check=False,capture_output=True,
                          text=True,timeout=120)
    if result.returncode:
        raise AssertionError(f"SWI-Prolog failed: {result.returncode}\n{result.stdout}\n{result.stderr}")
    observations=[]
    summary=[]
    donor=[]
    for line in result.stdout.splitlines():
        if line.startswith("GPS-OBS\t"):
            parts=line.split("\t")
            assert len(parts)==3 and parts[-1]=="PASS",line
            observations.append(parts[1])
        elif line.startswith("GPS-SUMMARY\t"):summary.append(line)
        elif line.startswith("GPS-DONOR\t"):donor.append(line)
        elif line.strip():raise AssertionError("unrecognized real donor line: "+line)
    assert tuple(observations)==EXPECTED
    assert summary==["GPS-SUMMARY\tRECONSTRUCTION-NOT-ORIGINAL-IPL\t17"]
    assert len(donor)==1 and donor[0].startswith("GPS-DONOR\tSWI-PROLOG\t")
    print(f"D10 GPS actual SWI donor 17/17 PASS; {donor[0]}; not historical IPL runtime")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--real-prolog",action="store_true")
    ap.add_argument("--swipl",default="swipl")
    args=ap.parse_args()
    d,f,i,p=load(DOSSIER),load(FOUND),load(INV),ORACLE.read_text(encoding="utf-8")
    print("D10 GPS HISTORICAL RESEARCH: ",verify(d,f,i,p))
    negative_controls(d,f,i,p)
    if args.real_prolog:run_swi(args.swipl)

if __name__=="__main__":
    main()
