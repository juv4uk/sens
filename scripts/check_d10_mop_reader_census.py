#!/usr/bin/env python3
"""MOP reader census: 17 donor names != 17 D10 residents.

Uses real SBCL as independent historical donor when --run-sbcl is set.
"""
import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CENSUS=ROOT/"knowledge/d10-mop-metaobject-reader-census-20261009.json"
FOUND=ROOT/"knowledge/d1-d9-foundation.json"
INV=ROOT/"knowledge/d10-v1-semantic-inventory.json"
ORACLE=ROOT/"tests/oracles/d10_mop_readers_sbcl.lisp"
BASE="a55f307c27f17091795d75ebfcd7d051547d80bc"
SOURCE="https://clos-mop.hexstreamsoft.com/generic-functions-and-methods/"
CLASSES=set("CLASS-NAME CLASS-SLOTS CLASS-DIRECT-SLOTS CLASS-DEFAULT-INITARGS CLASS-DIRECT-DEFAULT-INITARGS CLASS-PRECEDENCE-LIST CLASS-DIRECT-SUPERCLASSES CLASS-DIRECT-SUBCLASSES CLASS-FINALIZED-P CLASS-PROTOTYPE".split())
GENERICS=set("GENERIC-FUNCTION-NAME GENERIC-FUNCTION-METHODS GENERIC-FUNCTION-LAMBDA-LIST GENERIC-FUNCTION-ARGUMENT-PRECEDENCE-ORDER GENERIC-FUNCTION-DECLARATIONS GENERIC-FUNCTION-METHOD-CLASS GENERIC-FUNCTION-METHOD-COMBINATION".split())
REVIEW={"CLASS-PRECEDENCE-LIST","CLASS-DIRECT-SLOTS","GENERIC-FUNCTION-METHODS","GENERIC-FUNCTION-ARGUMENT-PRECEDENCE-ORDER"}

def read(p):
    return json.loads(p.read_text(encoding="utf-8"))

def git_blob_sha(raw):
    d=raw.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(d)).encode("ascii")+b"\0"+d).hexdigest()

def verify(census, foundation, inventory, present_sha):
    assert census["schema"]=="d10-amop-metaobject-readers-census/v1"
    assert census["status"]=="RESEARCH-CENSUS-ONLY-ZERO-ADMISSIONS"
    assert census["total_dictionary_names"] == 17
    assert census["family_counts"] == {"class-readers":10,"generic-function-readers":7}
    assert census["citation"] == SOURCE and census["as_of_inventory_blob"] == BASE
    entries=census["entries"]
    assert len(entries)==17
    assert set(r["source_name"] for r in entries)==CLASSES|GENERICS
    assert len(set(r["id"] for r in entries))==17
    assert foundation["status"]=="owner-ratified"
    assert inventory["domain"]=="D10" and inventory["width"]==10
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert inventory["accounting"]["selected_semantic_candidates"]==len(inventory["rows"])
    assert len(inventory["rows"])>=630
    lower={str(name).upper() for d in foundation["domains"].values() for name in d["residents"].values()}
    selected={r["semantic_name"].upper() for r in inventory["rows"]}
    review=[]
    for row in entries:
        name=row["source_name"]
        expected_family="class-readers" if name in CLASSES else "generic-function-readers"
        assert row["family"]==expected_family
        assert row["source_url"]==SOURCE
        assert row["result_count"]==1 and row["arity"]=="one metaobject"
        assert row["selected"] is False and row["ratified"] is False and row["coordinate"] is None
        assert row["source_kind"]=="generic-function-reader"
        assert row["decision"]==("REVIEW-SEMANTIC-LAW" if name in REVIEW else "HOLD-INTROSPECTION-OR-DERIVED")
        if name in REVIEW:
            assert len(row["positive_witnesses"])>=2 and row["falsifier"]
            assert row["semantic_law"]
            review.append(name)
        if present_sha == BASE:
            assert row["exact_in_d1_d9"] == (name in lower)
            assert row["exact_in_selected_d10"] == (name in selected)
        else:
            # Historical snapshot may differ from current selected set; do not
            # fail just because separate owner-approved selection grew later.
            assert isinstance(row["exact_in_d1_d9"], bool)
            assert isinstance(row["exact_in_selected_d10"], bool)
        assert name not in lower, "ratified D1-D9 name collision: "+name
    assert set(review)==REVIEW
    return {"census":len(entries),"review":len(review),"hold":len(entries)-len(review),
            "live_selected":len(inventory["rows"]),"ratified":0}

def negative_controls(census,found,inv,sha):
    verify(census,found,inv,sha)
    transforms=[
        lambda a: a["entries"].append(copy.deepcopy(a["entries"][-1])),
        lambda a: a["entries"][0].update({"coordinate":"0000000000"}),
        lambda a: a["entries"][0].update({"selected":True}),
        lambda a: a["entries"][0].update({"ratified":True}),
        lambda a: a["entries"][0].update({"source_url":"https://invalid.example"}),
        lambda a: a["entries"][0].update({"source_name":"NEW-INVENTED-FUNCTION"}),
        lambda a: a["entries"][0].update({"decision":"SELECT-D10-CANDIDATE"}),
    ]
    for n,change in enumerate(transforms,1):
        bad=copy.deepcopy(census)
        change(bad)
        try:verify(bad,found,inv,sha)
        except (AssertionError, KeyError):continue
        raise AssertionError("unsafe mutation accepted: "+str(n))
    print("D10 MOP 17-reader census 7/7 fail-closed negative controls PASS")

def run_real_sbcl(binary):
    r=subprocess.run([binary,"--script",str(ORACLE)],cwd=ROOT,
                     check=False,text=True,capture_output=True,timeout=90)
    if r.returncode:
        raise AssertionError("SBCL donor failure:\n"+r.stdout+"\n"+r.stderr)
    observed=[]
    summaries=[]
    versions=[]
    for line in r.stdout.splitlines():
        if line.startswith("OBS\t"):
            parts=line.split("\t")
            assert len(parts)==3 and parts[-1]=="PASS",line
            observed.append(parts[1])
        elif line.startswith("MOP-SUMMARY\t"):summaries.append(line)
        elif line.startswith("MOP-DONOR\t"):versions.append(line)
        elif line.strip():raise AssertionError("unrecognized oracle output: "+line)
    assert len(observed)==15 and len(set(observed))==15
    assert summaries==["MOP-SUMMARY\tSB-MOP-READER-OBS\t15"]
    assert len(versions)==1 and versions[0].startswith("MOP-DONOR\tSBCL\t")
    print("SBCL independent MOP donor oracle: 15/15 PASS",versions[0])
    print("No SENS parity proved; MOP selected additions 0; ratified 0")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--run-sbcl", action="store_true")
    p.add_argument("--sbcl",default="sbcl")
    args=p.parse_args()
    census=read(CENSUS)
    found=read(FOUND)
    inv=read(INV)
    sha=git_blob_sha(INV.read_text(encoding="utf-8"))
    result=verify(census,found,inv,sha)
    negative_controls(census,found,inv,sha)
    print("D10 MOP source census PASS",json.dumps(result,sort_keys=True))
    if args.run_sbcl:
        run_real_sbcl(args.sbcl)
