#!/usr/bin/env python3
"""Reject source-less D10 proposal and verify real Chez clock donor transcript.

This is research evidence and ledger intake, not D10 resident admission.
"""
import argparse
import copy
import csv
import importlib.util
import io
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "knowledge/d10-hadamard-variance-proposal-20261009.json"
LEDGER = ROOT / "knowledge/d10-proposal-ledger.tsv"
INV = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUND = ROOT / "knowledge/d1-d9-foundation.json"
BASE = ROOT / "knowledge/d10-growth-baseline-v1.json"
HISTORY = ROOT / "knowledge/d10-selection-transition-history.json"
CHEZ = ROOT / "tests/oracles/d10_hadamard_chez.ss"
CHECKER = ROOT / "scripts/check-d10-proposal-ledger.py"
NAME = "HADAMARD-VARIANCE"
D10_PIN = "7683f1e2bfcf67d3a45d412d3b1790b72ad623ad"
FOUND_PIN = "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4"
SOURCE_PIN = "38c4ce09ff60c8a75816e6efd71d647e55cbaec4"
EXPECTED_IDS = (
    "THREE_ZERO_VARIANCE","UNIT_IMPULSE","NEGATIVE_SECOND_DIFF",
    "EXACT_RATIONAL_RESULT","LINEAR_FREQ_DRIFT_REJECTED",
    "QUADRATIC_FREQ_TREND_NONZERO","INVARIANT_UNDER_CONSTANT_OFFSET",
    "INVARIANT_UNDER_LINEAR_DRIFT","M2_BLOCK_MEANS",
    "EXACT_HOMOGENEITY","TOO_FEW_SAMPLES_REJECTED",
    "M_ZERO_REJECTED","M_NEGATIVE_REJECTED","M_TOO_LARGE_REJECTED",
    "INTEGER_M_REQUIRED"
)

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

def original_gate():
    spec = importlib.util.spec_from_file_location("d10_proposal_gate", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def check_static(proposal, ledger, inv, found, baseline, history, donor):
    rows = list(csv.DictReader(io.StringIO(ledger), delimiter="\t"))
    item = [r for r in rows if r["semantic_name"] == NAME]
    assert len(item)==1, "exactly one ledger proposal"
    r = item[0]
    assert r["proposal_id"]=="D10P-0008"
    assert r["width"]=="D10" and r["ratified"]=="0" and r["status"]=="pending-review"
    assert r["blocked_source"]=="NOT-A-MIGRATION-BLOCK"
    assert proposal["selected"] is False and proposal["ratified"] is False and proposal["coordinate"] is None
    assert proposal["proposal_id"]==r["proposal_id"] and proposal["semantic_name"]==NAME
    assert r["semantic_law"]==proposal["law"]
    assert r["surface_uk"]==proposal["surface_uk"]
    assert r["surface_ukr"]==proposal["surface_ukr"]
    assert r["dedup_check"]==f"D1-D9@{FOUND_PIN}=NO-MATCH;D10@{D10_PIN}=NO-MATCH"
    assert r["donor_provenance"]==f"juv4uk/sens@{SOURCE_PIN}:knowledge/d10-hadamard-variance-proposal-20261009.json:1"
    assert "UNIVERSAL-BORDER:" in r["ownership_test"]
    assert len(proposal["positive_witnesses"])>=2 and len(proposal["falsifiers"])>=3
    assert proposal["executed_donor"]["cases"]==15
    assert proposal["primary_source"]["web_url"].startswith("https://www.nist.gov/")
    assert found["status"]=="owner-ratified"
    lower={str(n).upper() for dom in found["domains"].values() for n in dom["residents"].values()}
    assert NAME not in lower, "lower D1-D9 already owns identity"
    assert len(inv["rows"])>=630
    assert inv["accounting"]["ratified_d10_residents"]==0
    live = [x for x in inv["rows"] if x["semantic_name"]==NAME]
    assert len(live)<=1
    if live:
        # This oracle must remain a donor after a separate owner-reviewed selection.
        assert live[0].get("coordinate") is None and live[0].get("ratified_resident") is False
        assert live[0].get("status")=="SELECTED-RESEARCH-CANDIDATE"
    assert all(x["semantic_name"]!=NAME for x in inv["rows"][:630]), "not part of the pre-proposal prefix"
    gate=original_gate()
    assert not gate.validate(ledger), "bad ledger canonical schema"
    assert not gate.selection_trace_errors(ledger,inv,baseline,history), "pending source proposal rejected"
    source_lines=donor.splitlines()
    observed=re.findall(r'\(observe\s+"([A-Z0-9_]+)"', donor)
    assert tuple(observed)==EXPECTED_IDS
    assert all("binary SENS" not in x for x in source_lines)
    return True

def run_negative_controls(proposal,ledger,inv,found,baseline,history,donor):
    originals=(proposal,ledger,inv,found,baseline,history,donor)
    def rejects(*args):
        try: check_static(*args)
        except (AssertionError,ValueError,KeyError,TypeError): return True
        return False
    negatives=[
        (0,lambda x: x.update({"selected":True})),
        (0,lambda x: x.update({"coordinate":"1111111111"})),
        (0,lambda x: x.update({"law":"fabricated derivative"})),
        (0,lambda x: x.update({"ratified":True})),
        (1,lambda x: x.replace("D10P-0008","D10P-9999")),
        (1,lambda x: x.replace("NOT-A-MIGRATION-BLOCK","arbitrary")),
        (1,lambda x: x.replace(SOURCE_PIN,"0"*40)),
        (2,lambda x: x["rows"].append({"semantic_name":NAME,"coordinate":"1111111111","ratified_resident":True})),
        (6,lambda x: x.replace('"THREE_ZERO_VARIANCE"','"RENAMED_TEST"')),
    ]
    for i,(pos,mutate) in enumerate(negatives):
        args=[copy.deepcopy(x) for x in originals]
        result=mutate(args[pos])
        if result is not None: args[pos]=result
        assert rejects(*args),f"negative mutation {i} unexpectedly accepted"
    print("D10-HADAMARD-LEDGER: PASS 9/9 negative controls")

def git_pinned_source():
    cmd=["git","cat-file","-e",SOURCE_PIN+":knowledge/d10-hadamard-variance-proposal-20261009.json"]
    r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=False)
    assert r.returncode==0, "pinned source commit missing; require fetch-depth:0"
    content=subprocess.run(["git","show",SOURCE_PIN+":knowledge/d10-hadamard-variance-proposal-20261009.json"],
                           cwd=ROOT,capture_output=True,text=True,check=True).stdout
    assert read(PROPOSAL)==json.loads(content), "published donor revision differed from pinned source"

def run_real_donor(scheme):
    proc=subprocess.run([scheme,"--script",str(CHEZ)],cwd=ROOT,
                        capture_output=True,text=True,check=False,timeout=120)
    assert proc.returncode==0, f"Chez donor failed exit={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    rows=[]
    summary=[]
    for line in proc.stdout.splitlines():
        if line.startswith("OBS\t"):
            parts=line.split("\t")
            assert len(parts)==3 and parts[2]=="PASS", line
            rows.append(parts[1])
        elif line.startswith("SUMMARY\t"):
            summary.append(line)
        elif line.strip():
            raise AssertionError("unrecognized donor output: "+line)
    assert tuple(rows)==EXPECTED_IDS,"independent real R6RS oracle differs from pinned cases"
    assert summary==["SUMMARY\tHADAMARD-VARIANCE-CHEZ-V1\t15"]
    print("D10-HADAMARD independent Chez R6RS donor PASS 15/15; not SENS runtime parity")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--scheme",default="scheme")
    parser.add_argument("--real-donor",action="store_true")
    parser.add_argument("--skip-source-git-check",action="store_true")
    args=parser.parse_args()
    proposal,ledger,inv,found,baseline,history,donor=(
        read(PROPOSAL),LEDGER.read_text(encoding="utf-8"),
        read(INV),read(FOUND),read(BASE),read(HISTORY),CHEZ.read_text(encoding="utf-8"))
    check_static(proposal,ledger,inv,found,baseline,history,donor)
    run_negative_controls(proposal,ledger,inv,found,baseline,history,donor)
    if not args.skip_source_git_check:
        git_pinned_source()
    if args.real_donor:
        run_real_donor(args.scheme)
    print("D10-HADAMARD: proposal recorded; selected=NO, ratified=NO, coordinates=NONE")

if __name__=="__main__":
    main()
