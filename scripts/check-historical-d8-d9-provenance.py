#!/usr/bin/env python3
"""Fail-closed preservation guard for historical D8/D9 candidate snapshots."""
from __future__ import annotations
import copy, json, re, subprocess, sys
from pathlib import Path
from check_d10_historical_admission_batch1 import check_growth, read as read_growth, BASE as GROWTH_BASE

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"knowledge/historical-d8-unassigned-d9-overflow-provenance-v1.json"
FOUND=ROOT/"knowledge/d1-d9-foundation.json"
D8=ROOT/"knowledge/d8-ratified.json"
D10=ROOT/"knowledge/d10-v1-semantic-inventory.json"

def norm(v):
    return re.sub(r"[^A-Z0-9?!+*/<>=.-]","",str(v).strip().upper())
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
    rel=str(p.relative_to(ROOT))
    return subprocess.run(["git","rev-parse",f"HEAD:{rel}"],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
def validate(data,foundation,d8,d10):
    errors=[]
    if data.get("schema")!="historical-d8-unassigned-and-d9-overflow-provenance/v1": errors.append("wrong schema")
    if data.get("status")!="ARCHIVAL-PROVENANCE-ONLY-REQUIRES-CURRENT-BEHAVIORAL-REVIEW": errors.append("not archival-only")
    snap=data.get("current_authority_snapshot",{})
    for k,p in (("d1_d9_foundation_blob_sha",FOUND),("d8_ratified_blob_sha",D8),("d10_inventory_blob_sha",D10)):
        if k == "d10_inventory_blob_sha":
            if snap.get(k) != read_growth(GROWTH_BASE)["origin_inventory_git_blob"]:
                errors.append("historical D10 origin hash drift")
            try: check_growth(d10)
            except AssertionError: errors.append("current D10 mutated preserved historical 625 laws")
        elif snap.get(k)!=sha(p): errors.append(f"stale authority hash: {k}")
    if d8.get("status")!="owner-ratified" or d8.get("occupancy")!=256:
        errors.append("expected current D8 owner-ratified 256/256")
    low={}
    for dom,spec in foundation["domains"].items():
        for name in spec.get("residents",{}).values(): low.setdefault(norm(name),[]).append(dom)
    high={}
    for row in d10["rows"]: high.setdefault(norm(row.get("semantic_name")),[]).append(row)
    rows=data.get("rows")
    if not isinstance(rows,list) or len(rows)!=226:
        errors.append("expected exactly 226 preserved historical rows")
        return errors
    ids=[r.get("historical_id") for r in rows]
    if len(ids)!=len(set(ids)): errors.append("duplicate historical_id")
    counts={"d8":0,"d9":0}
    stats={k:{"low":0,"high":0,"both":0,"none":0} for k in counts}
    for r in rows:
        k=norm(r.get("historical_name"))
        if r.get("coordinate","MISSING") is not None: errors.append(f"{k}: current coordinate must be null")
        if r.get("selected_d10_candidate") is not False: errors.append(f"{k}: current D10 selection must be false")
        if r.get("ratified") is not False: errors.append(f"{k}: current ratification must be false")
        if not r.get("historical_snapshot"): errors.append(f"{k}: historical placement/decision snapshot missing")
        lm=r.get("current_exact_name_matches",{}).get("d1_d9",[])
        hm=r.get("current_exact_name_matches",{}).get("d10_selected",[])
        act_l={k} if k in low else set()
        act_h={k} if k in high else set()
        if {norm(x.get("semantic_name")) for x in lm}!=act_l: errors.append(f"{k}: D1-D9 exact-name drift")
        if {norm(x.get("semantic_name")) for x in hm}!=act_h: errors.append(f"{k}: D10 exact-name drift")
        if any(x.get("coordinate") is not None for x in hm): errors.append(f"{k}: D10 match must not import coordinate")
        setname="d8" if r.get("historical_id","").startswith("d8-") else "d9" if r.get("historical_id","").startswith("d9-") else None
        if setname:
            counts[setname]+=1
            stats[setname]["low"]+=int(bool(act_l))
            stats[setname]["high"]+=int(bool(act_h))
            stats[setname]["both"]+=int(bool(act_l and act_h))
            stats[setname]["none"]+=int(bool(not act_l and not act_h))
        if not r.get("historical_behavior") or not (r.get("historical_provenance") or r.get("historical_source_provenance")):
            errors.append(f"{k}: behavior/provenance missing")
    if counts!={"d8":192,"d9":34}: errors.append(f"row counts changed: {counts}")
    expected={
      "d8_unassigned_historical":{"rows":192,"exact_name_overlap_d1_d9":stats["d8"]["low"],"exact_name_overlap_d10":stats["d8"]["high"],"both":stats["d8"]["both"],"neither_exact_name_overlap":stats["d8"]["none"]},
      "d9_overflow_historical":{"rows":34,"exact_name_overlap_d1_d9":stats["d9"]["low"],"exact_name_overlap_d10":stats["d9"]["high"],"both":stats["d9"]["both"],"neither_exact_name_overlap":stats["d9"]["none"]}
    }
    dedup=data.get("current_exact_name_dedup",{})
    if dedup.get("d8_unassigned_historical")!=expected["d8_unassigned_historical"]: errors.append("D8 summary stale")
    if dedup.get("d9_overflow_historical")!=expected["d9_overflow_historical"]: errors.append("D9 summary stale")
    return errors
def main():
    d,f,d8,d10=load(ART),load(FOUND),load(D8),load(D10)
    e=validate(d,f,d8,d10)
    if e:
        for x in e: print("FAIL:",x,file=sys.stderr)
        return 1
    print("Historical D8/D9 provenance: 192+34 rows, current dedup, no admission PASS")
    if "--self-test" in sys.argv:
        mutants=[]
        for field,val in (("coordinate","00000000"),("selected_d10_candidate",True),("ratified",True)):
            bad=copy.deepcopy(d);bad["rows"][0][field]=val;mutants.append((field,bad))
        bad=copy.deepcopy(d);bad["rows"][0]["current_exact_name_matches"]["d1_d9"]=[];mutants.append(("dedup",bad))
        missed=[name for name,bad in mutants if not validate(bad,f,d8,d10)]
        if missed:
            print("FAIL: negative controls accepted: "+", ".join(missed),file=sys.stderr);return 1
        print("4 negative provenance/admission controls: PASS")
    return 0
if __name__=="__main__": raise SystemExit(main())
