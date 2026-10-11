#!/usr/bin/env python3
"""Verify 80 source-pinned historical D10 candidate reservations, never Core."""
import json,hashlib,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
K=R/"knowledge"
S=[
"d10-psl-interlisp-lispm-unmerged-residual-v1.json",
"d10-clos-instance-lifecycle-residual-v1.json",
"d10-clos-slot-state-historical-review-v1.json",
"d10-flavors-restarts-research-v1.json",
"d10-time-law-review-v2.json",
"d10-historical-clos-interlisp-residual-review-v1.json",
"d10-r6rs-copy-mutable-oracle-v1.json",
"d10-hobbies-source-laws-v1.json",
"d10-unify-lexical-harvest-v1.json",
"d10-prolog-constraint-hobbies-research-v1.json",
"d10-crossrepo-linguistic-v1.json",
"d10-crossrepo-knowledge-tooling-v1.json",
"d10-crossrepo-domain-v1.json",
]
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def read(p):return json.loads((R/p).read_text(encoding="utf-8"))
def check():
 q=read("knowledge/d10-historical-candidate-coordinate-queue-v1.json")
 old=read("knowledge/d10-provisional-candidate-coordinate-queue-v1.json")
 v=read("knowledge/d10-v5-semantic-inventory.json")
 f=read("knowledge/d1-d9-foundation.json")
 for label in ("source_canonical","source_initial_name_queue","source_foundation"):
  pin=q[label]
  assert pin["git_blob"]==blob((R/pin["path"]).read_bytes()),label
 assert q["schema"]=="d10-historical-research-candidate-coordinate-queue/v1" and q["status"]=="RESEARCH-HOLD-NO-CORE-ADMISSION"
 assert len(q["researched_donors"])==len(S)==13
 used=set(x["coordinate"] for x in v["rows"])
 used.update(x["provisional_coordinate"] for x in old["provisional_candidates"])
 names={x["semantic_name"].upper() for x in v["rows"]}
 prev={x["semantic_name"].upper() for x in old["provisional_candidates"]}
 lower={str(n).upper() for d in f["domains"].values() for n in d["residents"].values()}
 free=[format(i,"010b") for i in range(1024) if format(i,"010b") not in used]
 added=[];canonical=[];repeated=[];collisions=[]
 for index,filename in enumerate(S):
  path="knowledge/"+filename
  pin=q["researched_donors"][index]
  data=(R/path).read_bytes()
  assert pin["path"]==path and pin["git_blob"]==blob(data)
  doc=json.loads(data)
  entries=(doc.get("rows") or [])+(doc.get("proposals") or [])
  for src in entries:
   name=src.get("semantic_name") or src.get("historical_name") or src.get("proposed_semantic_name")
   if not isinstance(name,str) or not name.strip():continue
   key=name.upper()
   if key in names:canonical.append((name,path));continue
   if key in prev:repeated.append((name,path));continue
   if key in lower:collisions.append((name,path));continue
   if key in {x[0] for x in added}:repeated.append((name,path));continue
   added.append((name,path,blob(data),src,doc))
 assert len(added)==80 and len(free)>=80
 assert len(q["candidates"])==80
 for i,((name,path,digest,src,doc),row) in enumerate(zip(added,q["candidates"])):
  assert row["semantic_name"]==name and row["source_path"]==path
  assert row["source_git_blob"]==digest and row["provisional_coordinate"]==free[i]
  assert row["source_doc_status"]==doc.get("status")
  assert row["observable_law"]==(src.get("observable_law") or src.get("semantic_law") or src.get("observable_behavior") or src.get("behavior"))
  assert row["source_review_status"]==(src.get("triage_status") or src.get("triage") or src.get("decision") or src.get("status") or "NOT-DECIDED")
  assert row["status"]=="RESEARCH-HOLD-NO-CORE-AUTHORITY" and row["coordinate_basis"]=="ARCHIVAL-SOURCE-NAME-RESERVATION-NOT-CORE"
  assert not row["ratified_resident"] and not row["selected_in_d10"] and not row["physical_t5_authorized"]
 assert q["accounting"]=={
  "canonical":715,"earlier_candidate_reservations":96,"historical_candidate_reservations":80,
  "total_provisional_reservations":176,"unused_d10_coordinates_after_all_reservations":133,
  "source_rows_already_canonical":len(canonical),"source_names_already_in_initial_queue":len([x for x in repeated if x[0].upper() in prev]),
  "source_names_repeated_within_historical_sources":len([x for x in repeated if x[0].upper() not in prev]),
  "source_name_matches_ratified_lower":len(collisions),"ratified":0,"canonical_added":0}
 allcodes=[x["provisional_coordinate"] for x in q["candidates"]]
 assert len(allcodes)==len(set(allcodes))==80
 assert not set(allcodes)&used and all(re.fullmatch(r"[01]{10}",c) for c in allcodes)
 return {"canonical":715,"historical_provisional":80,"earlier_provisional":96,"combined_provisional":176,"still_without_reservation":133,"ratified":0}
if __name__=="__main__":
 if not __debug__:sys.exit("D10-ARCHIVAL-QUEUE BLOCK optimized assertions")
 try: print("D10-ARCHIVAL-QUEUE PASS",json.dumps(check(),sort_keys=True))
 except (AssertionError,ValueError,KeyError,TypeError,OSError) as e:sys.exit("D10-ARCHIVAL-QUEUE BLOCK "+str(e))
