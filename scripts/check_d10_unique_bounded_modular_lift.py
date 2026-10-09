#!/usr/bin/env python3
"""Source- and scope-grade admission barrier for bounded modular lift research.

A mathematical donor oracle is NOT native SENS binary execution or a D10 resident.
"""
import argparse
import copy
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOSSIER=ROOT/"knowledge/d10-unique-bounded-modular-lift-20261009.json"
INVENTORY=ROOT/"knowledge/d10-v1-semantic-inventory.json"
FOUNDATION=ROOT/"knowledge/d1-d9-foundation.json"
SCHEME=ROOT/"tests/oracles/d10_unique_bounded_modular_lift_chez.ss"
NAME="UNIQUE-BOUNDED-MODULAR-LIFT"
SOURCE_HARDWARE="https://look.ams-osram.com/m/7059eac7531a86fd/original/AS5600-DS000365.pdf"
SOURCE_NUMPY="https://numpy.org/doc/stable/reference/generated/numpy.unwrap.html"
IDS=(
"AS5600_WRAP_UNIQUE","AS5600_NO_MATCH","AS5600_MULTI_TURN_ALIAS",
"NEGATIVE_TURNS_AMBIG","NEGATIVE_BOUNDARY_UNIQUE","NONE_BETWEEN_CYCLES",
"INCLUSIVE_ENDPOINT_TWICE","NEGATIVE_SINGLE","SHIFTED_INTERVAL_UNIQUE",
"LENGTH_PERIOD_PLUS_ONE_AMBIG","BAD_MODULUS","BAD_RESIDUE",
"BAD_NEGATIVE_RESIDUE","BAD_REVERSED_INTERVAL",
"BAD_FRACTIONAL_BOUND","INTEGER_NOT_REAL_FLOAT"
)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def guard(d,inv,foundation,shell):
    assert d["schema"]=="d10-unique-bounded-modular-lift-research/v1"
    assert d["status"]=="SOURCE-REVIEW-PENDING-CORE-VS-LIBRARY"
    assert d["selected"] is False and d["ratified"] is False
    assert d["coordinate"] is None and d["physical_t5_authorized"] is False
    c=d["candidate"]
    assert c["semantic_name"]==NAME
    assert c["arity"]==4
    assert c["surface_uk"] and c["surface_ukr"]
    assert "NONE" in c["law"] and "UNIQUE" in c["law"] and "AMBIGUOUS" in c["law"]
    assert "kmin" in c["math"] and "kmax" in c["math"]
    assert len(c["positives"])>=7 and len(c["falsifiers"])>=5
    assert len({(x["M"],x["r"],x["lo"],x["hi"]) for x in c["positives"]})==len(c["positives"])
    assert len(c["nearby"])>=4
    assert len(c["hobby_fanout"])>=5
    src=d["sources"]
    assert len(src)==3
    assert src[0]["url"]==SOURCE_HARDWARE and src[0]["type"]=="HARDWARE-PRIMARY"
    assert src[1]["url"]==SOURCE_NUMPY and src[1]["type"]=="NUMERICAL-REFERENCE"
    assert src[2]["type"]=="NEW-MATHEMATICAL-LAW" and src[2]["url"] is None
    assert d["real_oracle"]=="tests/oracles/d10_unique_bounded_modular_lift_chez.ss"
    assert d["independent_crosscheck"]=="tests/test_d10_unique_bounded_modular_lift.py"
    assert foundation["status"]=="owner-ratified"
    lower={str(s).upper() for v in foundation["domains"].values() for s in v["residents"].values()}
    assert NAME not in lower
    rows=inv["rows"]
    assert len(rows)>=634
    assert len(rows)==inv["accounting"]["selected_semantic_candidates"]
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert len({r["stable_id"] for r in rows})==len(rows)
    assert len({r["semantic_name"] for r in rows})==len(rows)
    assert NAME not in {r["semantic_name"] for r in rows}, "separate owner approval needed for selection"
    assert re.findall(r'\(check\s+"([A-Z0-9_]+)"',shell)==list(IDS)
    assert "NOT binary SENS runtime" in shell
    return len(rows)

def negative_controls(d,inv,foundation,shell):
    cases=[
        (0,lambda a:a.update({"selected":True})),
        (0,lambda a:a.update({"coordinate":"0000000000"})),
        (0,lambda a:a.update({"ratified":True})),
        (0,lambda a:a["candidate"].update({"semantic_name":"D10_FAKE"})),
        (0,lambda a:a["candidate"].update({"positives":[]})),
        (0,lambda a:a["sources"][0].update({"url":"https://fake.invalid"})),
        (0,lambda a:a["sources"][2].update({"type":"ANSI-DEFINED-OPCODE"})),
        (1,lambda a:a["rows"].append({"stable_id":"fake","semantic_name":NAME})),
        (3,lambda a:a.replace('"AS5600_WRAP_UNIQUE"','"FAKED_OBSERVATION"'))
    ]
    saved=(d,inv,foundation,shell)
    for i,(pos,change) in enumerate(cases,1):
        xs=[copy.deepcopy(x) for x in saved]
        modified=change(xs[pos])
        if modified is not None:xs[pos]=modified
        try:guard(*xs)
        except (AssertionError,KeyError,TypeError):continue
        raise AssertionError("forged source/selection escaped: "+str(i))
    print("D10 modular lift source and authority 9/9 adverse mutations REJECTED")

def real_chez(binary,shell):
    proc=subprocess.run([binary,"--script",str(SCHEME)],cwd=ROOT,text=True,
                       capture_output=True,timeout=90,check=False)
    if proc.returncode:
        raise AssertionError("independent Chez donor FAIL\n"+proc.stdout+"\n"+proc.stderr)
    ids=[]
    summaries=[]
    for line in proc.stdout.splitlines():
        if line.startswith("OBS\t"):
            fields=line.split("\t")
            assert len(fields)==3 and fields[-1]=="PASS"
            ids.append(fields[1])
        elif line.startswith("SUMMARY\t"):summaries.append(line)
        elif line.strip():raise AssertionError("unexpected donor output: "+line)
    assert tuple(ids)==IDS
    assert summaries==["SUMMARY\tUNIQUE-BOUNDED-MODULAR-LIFT-CHEZ-V1\t16"]
    print("Independent real Chez Scheme modular lift donor: 16/16 PASS (not SENS runtime)")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--real-chez",action="store_true")
    a.add_argument("--scheme",default="scheme")
    args=a.parse_args()
    d,inv,f,s=read(DOSSIER),read(INVENTORY),read(FOUNDATION),SCHEME.read_text(encoding="utf-8")
    count=guard(d,inv,f,s)
    negative_controls(d,inv,f,s)
    print(f"D10 cyclic bounded lift research HOLD PASS; selected main={count}; delta=0")
    if args.real_chez:real_chez(args.scheme,s)

if __name__=="__main__":main()
