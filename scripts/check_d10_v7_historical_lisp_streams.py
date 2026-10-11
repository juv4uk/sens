#!/usr/bin/env python3
"""Fail-closed integrity gate for D10 v7's two historical Lisp stream laws."""
import csv, hashlib, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
K=ROOT/"knowledge"
def sha(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\0"+data).hexdigest()
def raw(name):
    return (K/name).read_bytes()
def obj(name):
    return json.loads(raw(name))
def need(ok,why):
    if not ok: raise ValueError(why)

NAMES=("GET-OUTPUT-STREAM-STRING","MAKE-CONCATENATED-STREAM")
EXPECTED={
 "GET-OUTPUT-STREAM-STRING":("d10.historical.clhs.get-output-stream-string.20261011","D10P-700006","витягнути-текст-буфера-потоку","отримати-й-очистити-буфер-потоку"),
 "MAKE-CONCATENATED-STREAM":("d10.historical.clhs.make-concatenated-stream.20261011","D10P-700007","створити-потік-конкатенації","читати-вхідні-потоки-послідовно"),
}
def check():
    ptr=obj("d10-current-inventory.json")
    v5=obj("d10-v5-semantic-inventory.json")
    v6=obj("d10-v6-semantic-inventory.json")
    v7=obj("d10-v7-semantic-inventory.json")
    raw5,raw6,raw7=raw("d10-v5-semantic-inventory.json"),raw("d10-v6-semantic-inventory.json"),raw("d10-v7-semantic-inventory.json")
    census_raw=raw("d10-clhs-streams-census-20261009.json")
    intake_raw=raw("d10-historical-lisp-branch-evidence-intake-20261011.json")
    foundation_raw=raw("d1-d9-foundation.json")
    oracle_raw=(ROOT/"tests/oracles/d10-clhs-streams.sbcl").read_bytes()
    manifest_raw=raw("d10-historical-lisp-streams-selected-v7-20261011.json")
    manifest=json.loads(manifest_raw)
    foundation=json.loads(foundation_raw)
    need(ptr["canonical_current"]["path"]=="knowledge/d10-v7-semantic-inventory.json","pointer path")
    need(ptr["canonical_current"]["git_blob"]==sha(raw7),"v7 pointer blob")
    need((ptr["canonical_current"]["selected"],ptr["canonical_current"]["placed"],ptr["canonical_current"]["unplaced"],ptr["canonical_current"]["ratified"])==(721,719,2,0),"pointer counts")
    need(ptr["historical_v6_research_inventory"]["path"]=="knowledge/d10-v6-semantic-inventory.json" and ptr["historical_v6_research_inventory"]["git_blob"]==sha(raw6),"frozen v6 pin")
    need(ptr["historical_v5_research_inventory"]["git_blob"]==sha(raw5),"frozen v5 pin")
    need(v6["schema"]=="d10-v6-semantic-inventory/v1" and len(v6["rows"])==719 and v5["rows"]==v6["rows"][:715],"v5-v6 archive chain")
    need(v7["schema"]=="d10-v7-semantic-inventory/v1" and v7["previous_inventory"]["git_blob"]==sha(raw6),"v7 predecessor")
    need(len(v7["rows"])==721 and v7["rows"][:719]==v6["rows"],"append-only v6 prefix")
    need(v7["sources"][-1]=="knowledge/d10-historical-lisp-streams-selected-v7-20261011.json","manifest listed as source")
    selection=ptr["current_v7_historical_lisp_selection"]
    need(selection["manifest"]["git_blob"]==sha(manifest_raw),"manifest pointer pin")
    pins=selection["source_pins"]
    observed=[sha(census_raw),sha(intake_raw),sha(oracle_raw)]
    pinned=[x["git_blob"] for x in pins]
    need(pinned==observed,"source pins: expected="+repr(pinned)+" computed="+repr(observed))
    need(manifest["baseline"]["git_blob"]==sha(raw6) and manifest["donor_oracle"]["git_blob"]==sha(oracle_raw),"manifest pins")
    names=[r["semantic_name"].upper() for r in v7["rows"]]
    ids=[r["stable_id"] for r in v7["rows"]]
    need(len(set(names))==721 and len(set(ids))==721,"duplicate identity")
    lower={str(s).upper() for d in foundation["domains"].values() for s in d.get("residents",{}).values()}
    need(not(set(NAMES)&lower),"D1-D9 exact-name conflict")
    coords=[r["coordinate"] for r in v7["rows"] if r.get("coordinate") is not None]
    need(len(coords)==719 and len(set(coords))==719 and all(re.fullmatch(r"[01]{10}",c) for c in coords),"coordinate integrity")
    a=v7["accounting"]
    need((a["selected_semantic_candidates"],a["placed_selected_candidates"],a["unplaced_selected_candidates"],a["remaining_semantic_inventory"],a["ratified_d10_residents"])==(721,719,2,303,0),"accounting")
    census={r["name"]:r for r in obj("d10-clhs-streams-census-20261009.json")["rows"]}
    intake={r["semantic_name"]:r for r in obj("d10-historical-lisp-branch-evidence-intake-20261011.json")["new_candidates"]}
    suffix={r["semantic_name"]:r for r in v7["rows"][719:]}
    with (K/"d10-proposal-ledger.tsv").open(newline="",encoding="utf-8") as f:
        ledger={r["proposal_id"]:r for r in csv.DictReader(f,delimiter="\t")}
    for name in NAMES:
        row=suffix[name]
        stable,pid,uk,ukr=EXPECTED[name]
        src,evidence=census[name],intake[name]
        need((row["stable_id"],row["proposal_id"],row["surface_uk"],row["surface_ukr"])==(stable,pid,uk,ukr),"candidate identity "+name)
        need(row["source_path"]=="knowledge/d10-clhs-streams-census-20261009.json" and row["source_git_blob"]==sha(census_raw),"candidate source SHA "+name)
        need(row["coordinate"] is None and row["ratified_resident"] is False and row["physical_t5_authorized"] is False,"unplaced/unratified "+name)
        need(row["owner_core_vs_derived_review"]=="PENDING" and row["witness_independence"]=="PENDING","review status "+name)
        need(src["selected_in_d10"] is False and src["coordinate"] is None and src["name_collision_d9"] is False and src["name_collision_d10"] is False,"census dedup flag "+name)
        need(evidence["observable_law"] and evidence["positive_witnesses"] and evidence["falsifier"] and row["positive_witnesses"] and row["falsifier"],"positive/negative witnesses "+name)
        candidate=next(c for c in manifest["candidates"] if c["semantic_name"]==name)
        need(row["behavior"]==candidate["behavior"] and row["behavior"],"manifest law "+name)
        need(pid in ledger,"proposal ledger row missing "+name)
        le=ledger[pid]
        need(le["semantic_name"]==name and le["status"]=="pending-review" and le["ratified"]=="0","proposal still pending "+name)
        need(le["dedup_check"]=="D1-D9@"+sha(foundation_raw)+"=PENDING;D10@"+sha(raw6)+"=PENDING","preselection D1-D9/D10 pins "+name)
    return {"selected":721,"placed":719,"unplaced":2,"remaining":303,"ratified":0}
if __name__=="__main__":
    try: print("D10-V7-HISTORICAL-LISP: PASS",json.dumps(check(),sort_keys=True))
    except (OSError,ValueError,KeyError,TypeError,IndexError,StopIteration) as e: raise SystemExit("D10-V7-HISTORICAL-LISP: BLOCK "+str(e))
