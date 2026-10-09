#!/usr/bin/env python3
"""Fail-closed archival guard for the early-Lisp graph research corpus."""
from __future__ import annotations
import copy,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"knowledge/early-lisp-graph-historical-evidence-v1.json"
FOUND=ROOT/"knowledge/d1-d9-foundation.json"
D10=ROOT/"knowledge/d10-v1-semantic-inventory.json"
D3=ROOT/"lib/domains/d3.lisp"
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def sha(p):
 rel=str(p.relative_to(ROOT))
 return subprocess.run(["git","rev-parse",f"HEAD:{rel}"],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
def norm(v):
 s=str(v).strip().upper().replace("()","EMPTY-LIST")
 return re.sub(r"[^A-Z0-9?!+*/<>=.-]","",s)
def expected_crosswalk():
 return {
 "()":{"historical_code":"000","current_d3_code":"000","current_name":"()"},
 "QUOTE":{"historical_code":"001","current_d3_code":"001","current_name":"QUOTE"},
 "ATOM":{"historical_code":"010","current_d3_code":"010","current_name":"ATOM"},
 "EQ":{"historical_code":"011","current_d3_code":"101","current_name":"EQ"},
 "CONS":{"historical_code":"100","current_d3_code":"111","current_name":"CONS"},
 "CAR":{"historical_code":"101","current_d3_code":"100","current_name":"CAR"},
 "CDR":{"historical_code":"110","current_d3_code":"011","current_name":"CDR"},
 "COND":{"historical_code":"111","current_d3_code":"110","current_name":"COND"}}
def validate(d,f,d10,d3):
 errors=[]
 if d.get("schema")!="early-lisp-graph-historical-evidence/v1": errors.append("wrong schema")
 if d.get("status")!="RESEARCH-ARCHIVE-NOT-CANONICAL-SEMANTIC-AUTHORITY": errors.append("status must remain archive-only")
 snap=d.get("current_authority_snapshot",{})
 for key,path in (("d1_d9_foundation_blob_sha",FOUND),("d10_inventory_blob_sha",D10),("d3_table_blob_sha",D3)):
  if snap.get(key)!=sha(path): errors.append("stale authority hash: "+key)
 if d.get("current_d3_crosswalk")!=expected_crosswalk(): errors.append("D3 crosswalk mismatch")
 if d.get("current_d3_crosswalk")!=expected_crosswalk(): return errors
 for code,name in [("000","()"),("001","QUOTE"),("010","ATOM"),("011","CDR"),("100","CAR"),("101","EQ"),("110","COND"),("111","CONS")]:
  if f"({code} " not in d3: errors.append("canonical D3 row missing: "+code+" "+name)
 counts=d.get("dataset_counts",{})
 expected={"nodes":34,"edges":129,"falsifications":10,"equivalence_evidence":3,"bija3_pressure":16,"selector_relation_kernel":4}
 if counts!=expected: errors.append("dataset counts mismatch")
 sets=d.get("datasets",{})
 for key,total in (("nodes",34),("edges",129),("falsification_ledger",10),("equivalence_evidence",3),("bija3_pressure",16),("selector_relation_kernel",4)):
  rows=sets.get(key,[])
  if len(rows)!=total: errors.append(key+" row count mismatch")
  for row in rows:
   if row.get("coordinate","MISSING") is not None: errors.append(key+": active coordinate must be null")
   if row.get("selected_d10_candidate") is not False: errors.append(key+": D10 selected flag must be false")
   if row.get("ratified") is not False: errors.append(key+": ratified flag must be false")
 for n in sets.get("nodes",[]):
  snaprow=n.get("historical_snapshot",{})
  if not snaprow: errors.append("node lost historical code snapshot: "+n.get("historical_id","?"))
  for match in n.get("current_exact_name_matches",{}).get("d10_selected",[]):
   if match.get("coordinate") is not None: errors.append("node D10 match imported coordinate")
 if any(n.get("current_d3_crosswalk") and n["current_d3_crosswalk"].get("current_d3_code")!=expected_crosswalk()[n["current_d3_crosswalk"]["current_name"]]["current_d3_code"] for n in sets.get("nodes",[])):
  errors.append("node crosswalk mismatch")
 if any(row.get("status") not in {"falsified","superseded-premise"} for row in sets.get("falsification_ledger",[])):
  errors.append("falsification ledger introduced non-falsified premise status")
 return errors
def main():
 d,f,d10=load(ART),load(FOUND),load(D10); d3=D3.read_text(encoding="utf-8")
 errors=validate(d,f,d10,d3)
 if errors:
  for e in errors: print("FAIL:",e,file=sys.stderr)
  return 1
 print("Early-Lisp graph archive: 34 nodes, 129 edges, bounded countermodels, corrected D3 crosswalk PASS")
 if "--self-test" in sys.argv:
  cases=[]
  bad=copy.deepcopy(d);bad["datasets"]["nodes"][0]["coordinate"]="011";cases.append(("coordinate",bad))
  bad=copy.deepcopy(d);bad["datasets"]["nodes"][0]["selected_d10_candidate"]=True;cases.append(("selected",bad))
  bad=copy.deepcopy(d);bad["current_d3_crosswalk"]["CAR"]["current_d3_code"]="101";cases.append(("crosswalk",bad))
  failures=[label for label,item in cases if not validate(item,f,d10,d3)]
  if failures: print("FAIL: negative controls accepted: "+", ".join(failures),file=sys.stderr);return 1
  print("3 negative archive/authority controls PASS")
 return 0
if __name__=="__main__": raise SystemExit(main())
