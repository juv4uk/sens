#!/usr/bin/env python3
"""Verify append-only D10 v5 research admission. No ratification."""
import json,hashlib,re,copy,sys
from pathlib import Path
K=Path(__file__).resolve().parents[1]/"knowledge"
S=[("d10-crossrepo-linguistic-v1.json",["TOKENIZE-SENTENCES","TOKENIZE-WORDS","LEMMATIZE-TEXT","INFLECT-WORD","MORPHO-SYNTACTIC-TAG"]),("d10-clos-slot-state-historical-review-v1.json",["SLOT-EXISTS-P"]),("d10-clos-instance-lifecycle-residual-v1.json",["MAKE-INSTANCES-OBSOLETE","FUNCTION-KEYWORDS"])]
def sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def read(f):return json.loads((K/f).read_text(encoding="utf-8"))
def check():
 p=read("d10-current-inventory.json");v5=read("d10-v5-semantic-inventory.json");v4=read("d10-v4-semantic-inventory.json")
 assert p["historical_v5_research_inventory"]["git_blob"]==sha((K/"d10-v5-semantic-inventory.json").read_bytes())
 assert p["historical_v4_research_inventory"]["git_blob"]==sha((K/"d10-v4-semantic-inventory.json").read_bytes())
 assert v5["previous_inventory"]["git_blob"]==p["historical_v4_research_inventory"]["git_blob"]
 assert p["historical_v5_research_inventory"]["selected"]==715
 assert v5["schema"]=="d10-v5-semantic-inventory/v1" and v5["status"]=="RESEARCH-UNRATIFIED-PARTIAL"
 assert len(v4["rows"])==707 and len(v5["rows"])==715 and v5["rows"][:707]==v4["rows"]
 assert v5["accounting"]["selected_semantic_candidates"]==715 and v5["accounting"]["remaining_semantic_inventory"]==309
 codes={x["coordinate"] for x in v4["rows"]};free=[format(i,"010b") for i in range(1024) if format(i,"010b") not in codes]
 assert len(v5["research_v5_candidate_sources"])==3
 k=0
 for j,(fn,names) in enumerate(S):
  pin=v5["research_v5_candidate_sources"][j];donor=read(fn)
  assert pin["path"]=="knowledge/"+fn and pin["git_blob"]==sha((K/fn).read_bytes()) and pin["names"]==names
  for name in names:
   d=next(x for x in donor["rows"] if (x.get("semantic_name") or x.get("historical_name"))==name)
   row=v5["rows"][707+k];k+=1
   assert row["semantic_name"]==name and row["coordinate"]==free[k-1]
   assert row["behavior"]==(d.get("behavior") or d.get("observable_law"))
   assert row["source_git_blob"]==pin["git_blob"] and row["source_path"]==pin["path"]
   assert row["ratified_resident"] is False and row["physical_t5_authorized"] is False
   assert row["witness_independence"]=="PENDING" and row["independent_oracle"]=="NOT-EXECUTED-FOR-SENS"
   assert (d.get("decision")=="SELECT" and d.get("independent_law_witness")) if j==0 else (d.get("triage") or d.get("triage_status","")).startswith("REVIEW")
 assert k==8
 codes=[x["coordinate"] for x in v5["rows"]]
 assert len(set(codes))==715 and all(re.fullmatch("[01]{10}",c) for c in codes)
 assert len({x["stable_id"] for x in v5["rows"]})==715
 assert len({x["semantic_name"].upper() for x in v5["rows"]})==715
 assert all(x.get("ratified_resident") is False for x in v5["rows"])
 assert p["current_v5_candidate_selection"]["selected_added"]==8
 return {"selected":715,"added":8,"missing":309,"ratified":0}
if __name__=="__main__":
 if not __debug__:sys.exit("D10-V5 BLOCK optimized assertions")
 try: print("D10-V5 PASS",json.dumps(check(),sort_keys=True))
 except (AssertionError,KeyError,ValueError,StopIteration,OSError) as e:sys.exit("D10-V5 BLOCK "+str(e))
