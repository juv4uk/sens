#!/usr/bin/env python3
"""Fail-closed audit for a pending CLASS-OF D10 proposal; never selects it."""
from __future__ import annotations
import copy,csv,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"knowledge/d10-class-of-proposal-v1.json"
LEDGER=ROOT/"knowledge/d10-proposal-ledger.tsv"
FOUND=ROOT/"knowledge/d1-d9-foundation.json"
INV=ROOT/"knowledge/d10-v1-semantic-inventory.json"
ORACLE=ROOT/"knowledge/d10-clos-slot-observation-v1.json"
REQUIRED={"proposal_id","surface_uk","surface_ukr","semantic_name","semantic_law","width","donor_provenance","dedup_check","ownership_test","blocked_source","status","ratified"}
def load(p):return json.loads(p.read_text(encoding="utf-8"))
def norm(s):
 v=str(s).strip().upper()
 if v=="()":return "()"
 return re.sub(r"[^A-Z0-9?!+*/<>=.-]","",v)
def read_ledger():
 with LEDGER.open(encoding="utf-8",newline="") as f:
  reader=csv.DictReader(f,delimiter="\t")
  if set(reader.fieldnames or [])!=REQUIRED: raise ValueError("proposal ledger header drift")
  return list(reader)
def check(data,ledger,foundation,inventory,oracle):
 errors=[]
 if data.get("schema")!="d10-class-of-proposal/v1":errors.append("wrong schema")
 if data.get("status")!="PENDING-OWNER-REVIEW":errors.append("status must stay pending")
 if data.get("semantic_name")!="CLASS-OF":errors.append("semantic name mismatch")
 if data.get("selected_d10_candidate") is not False:errors.append("must not be selected")
 if data.get("ratified") is not False:errors.append("must not be ratified")
 if data.get("coordinate","MISSING") is not None:errors.append("coordinate must be null")
 if data.get("physical_t5_authorized") is not False:errors.append("physical T5 must remain false")
 rows=[r for r in ledger if r.get("proposal_id")=="D10-20261009-CLASS-OF"]
 if len(rows)!=1:errors.append("ledger must contain exactly one CLASS-OF row")
 else:
  r=rows[0]
  expected={"surface_uk":data["surface_uk"],"surface_ukr":data["surface_ukr"],"semantic_name":"CLASS-OF","width":"D10 (10-bit global stream)","status":"pending-review","ratified":"0"}
  for k,v in expected.items():
   if r.get(k)!=v:errors.append("ledger mismatch: "+k)
  for k in REQUIRED:
   if not r.get(k,"").strip():errors.append("ledger field empty: "+k)
 low={norm(n) for spec in foundation["domains"].values() for n in spec.get("residents",{}).values()}
 high={norm(r.get("semantic_name")) for r in inventory.get("rows",[])}
 if norm("CLASS-OF") in low:errors.append("CLASS-OF now exact-name collides with D1-D9; re-review needed")
 if norm("CLASS-OF") in high:errors.append("CLASS-OF has since been selected in D10; reconcile proposal instead of double-counting")
 if norm("TYPE-OF") not in high:errors.append("expected neighboring selected TYPE-OF for behavioral comparison")
 historical={r.get("name"):r for r in oracle.get("historical_functions",[])}
 if "CLASS-OF" not in historical:errors.append("SBCL CLOS oracle artifact lacks CLASS-OF")
 ids=set(oracle.get("observed_case_ids",[]))
 for case in ("CLASS_OF_EXACT_CLASS_OBJECT","CLASS_OF_NOT_CLASS_SYMBOL","CLASS_OF_CHILD_NOT_PARENT"):
  if case not in ids:errors.append("missing oracle case "+case)
 if oracle.get("geometry",{}).get("coordinate","MISSING") is not None:errors.append("oracle artifact must not assign coordinate")
 return errors
def main():
 d=load(ART); l=read_ledger(); f=load(FOUND); i=load(INV); o=load(ORACLE)
 errors=check(d,l,f,i,o)
 if errors:
  for e in errors:print("FAIL:",e,file=sys.stderr)
  return 1
 print("CLASS-OF proposal ledger/source/dedup guard PASS; still pending and unplaced")
 if "--self-test" in sys.argv:
  mutants=[]
  bad=copy.deepcopy(d);bad["selected_d10_candidate"]=True;mutants.append(("selection",bad))
  bad=copy.deepcopy(d);bad["coordinate"]="1010101010";mutants.append(("coordinate",bad))
  bad=copy.deepcopy(d);bad["ratified"]=True;mutants.append(("ratification",bad))
  missed=[name for name,bad in mutants if not check(bad,l,f,i,o)]
  if missed:print("FAIL: admission mutation accepted: "+", ".join(missed),file=sys.stderr);return 1
  print("3 negative no-admission controls PASS")
 return 0
if __name__=="__main__":raise SystemExit(main())
