#!/usr/bin/env python3
"""D10 v6 historical CLOS intake: no ratification, preserve source HOLD."""
import argparse,copy,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];K=R/"knowledge"
class Blocked(ValueError):pass
def need(ok,msg):
    if not ok:raise Blocked(msg)
def load(n):return json.loads((K/n).read_text(encoding="utf-8"))
def sha(path):
    b=(R/path).read_bytes()
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def check(pointer,old,new,proof,queue):
    need(pointer["canonical_current"]["path"]=="knowledge/d10-v6-semantic-inventory.json","current path")
    need(pointer["canonical_current"]["git_blob"]==sha("knowledge/d10-v6-semantic-inventory.json"),"current SHA")
    need(pointer["historical_v5_research_inventory"]["git_blob"]==sha("knowledge/d10-v5-semantic-inventory.json"),"historical SHA")
    need(new["previous_inventory"]["git_blob"]==sha("knowledge/d10-v5-semantic-inventory.json"),"previous inventory")
    need(proof["historical_queue_blob"]==sha("knowledge/d10-historical-candidate-coordinate-queue-v1.json"),"source queue")
    need(new["schema"]=="d10-v6-semantic-inventory/v1","schema")
    need(len(old["rows"])==715 and len(new["rows"])==719 and new["rows"][:715]==old["rows"],"append-only prefix")
    need(len(proof["candidates"])==4,"four selected laws")
    need(len({r["coordinate"] for r in new["rows"]})==719,"code collision")
    need(len({r["semantic_name"].upper() for r in new["rows"]})==719,"duplicate names")
    need(len({r["stable_id"] for r in new["rows"]})==719,"duplicate stable identifiers")
    need(all(re.fullmatch(r"[01]{10}",r["coordinate"]) for r in new["rows"]),"code width")
    need(all(r.get("ratified_resident") is False for r in new["rows"]),"fabricated ratification")
    for row,entry in zip(new["rows"][715:],proof["candidates"]):
        q=next(r for r in queue["candidates"] if r["semantic_name"]==entry["name"])
        need(row["semantic_name"]==entry["name"]==q["semantic_name"],"candidate identity")
        need(row["coordinate"]==entry["coordinate"]==q["provisional_coordinate"],"gauge")
        need(row["behavior"]==entry["law"]==q["observable_law"],"observed law")
        need(row["source_git_blob"]==q["source_git_blob"]==sha(q["source_path"]),"source SHA")
        need(row["positive_witnesses"]==[q["witness"]] and row["falsifiers"]==[q["falsifier"]],"proof/counterexample")
        need(row["source_review_status"]==q["source_review_status"] and row["witness_independence"]=="PENDING","source HOLD boundary")
        need(row["physical_t5_authorized"] is False and row["ratified_resident"] is False,"authorization")
    a=new["accounting"]
    need((a["selected_semantic_candidates"],a["placed_selected_candidates"],a["remaining_semantic_inventory"],a["ratified_d10_residents"])==(719,719,305,0),"counts")
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--self-test",action="store_true");args=ap.parse_args()
    p=load("d10-current-inventory.json");a=load("d10-v5-semantic-inventory.json");b=load("d10-v6-semantic-inventory.json");proof=load("d10-v6-historical-clos-selection-20261011.json");q=load("d10-historical-candidate-coordinate-queue-v1.json")
    check(p,a,b,proof,q)
    if args.self_test:
        for mutate in (lambda x:x["rows"].pop(),lambda x:x["rows"][-1].update(coordinate=x["rows"][-2]["coordinate"]),lambda x:x["rows"][-1].update(behavior="FAKE"),lambda x:x["rows"][-1].update(ratified_resident=True)):
            test=copy.deepcopy(b);mutate(test)
            try:check(p,a,test,proof,q)
            except Blocked:continue
            raise Blocked("negative mutation passed")
    print("D10-V6 PASS selected=719 placed=719 missing=305 ratified=0")
if __name__=="__main__":
    try:main()
    except (Blocked,KeyError,TypeError,OSError,StopIteration) as e:raise SystemExit("D10-V6 BLOCK "+str(e))
