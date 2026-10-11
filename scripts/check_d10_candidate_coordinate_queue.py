#!/usr/bin/env python3
"""Verify all 193 non-selected D10 source names are located or lower-domain overlaps."""
import hashlib,json,sys,re
from pathlib import Path
K=Path(__file__).resolve().parents[1]/"knowledge"
def sha(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()
def read(name):return json.loads((K/name).read_text(encoding="utf-8"))
def check():
 q=read("d10-provisional-candidate-coordinate-queue-v1.json")
 cur=read("d10-v5-semantic-inventory.json")
 src=read("d10-source-universe-891-20261011.json")
 f=read("d1-d9-foundation.json")
 for key,name in [("source_inventory","d10-v5-semantic-inventory.json"),("source_universe","d10-source-universe-891-20261011.json"),("source_foundation","d1-d9-foundation.json")]:
  assert q[key]["git_blob"]==sha((K/name).read_bytes()),key
 assert q["status"]=="RESEARCH-NAME-RESERVATIONS-NOT-CANONICAL-CORE"
 assert len(cur["rows"])==715 and len(src["rows"])==891
 canon_names={r["semantic_name"].upper() for r in cur["rows"]}
 canon_codes={r["coordinate"] for r in cur["rows"]}
 lower={}
 for domain,x in f["domains"].items():
  for bits,name in x["residents"].items():
   lower.setdefault(str(name).upper(),[]).append({"domain":domain,"coordinate":bits})
 extras=[x for x in src["rows"] if x["semantic_name"].upper() not in canon_names]
 needs=[x for x in extras if x["semantic_name"].upper() not in lower]
 duplicates=[x for x in extras if x["semantic_name"].upper() in lower]
 assert (len(extras),len(needs),len(duplicates))==(193,96,97)
 qrows=q["provisional_candidates"]
 assert len(qrows)==96 and len(q["lower_name_overlap_review"])==97
 free=[format(i,"010b") for i in range(1024) if format(i,"010b") not in canon_codes]
 for i,(a,b) in enumerate(zip(qrows,needs)):
  assert a["semantic_name"]==b["semantic_name"] and a["source_priority"]==b["priority"]
  assert a["provenance"]==b["provenance"]
  assert a["provisional_coordinate"]==free[i]
  assert a["coordinate_basis"]=="NONCANONICAL-NAME-QUEUE-RESERVATION"
  assert not a["ratified_resident"] and not a["selected_in_d10"] and not a["physical_t5_authorized"]
 for a,b in zip(q["lower_name_overlap_review"],duplicates):
  assert a["semantic_name"]==b["semantic_name"]
  assert a["lower_domain_matches"]==lower[b["semantic_name"].upper()]
  assert a["source_priority"]==b["priority"] and a["provenance"]==b["provenance"]
 assert q["accounting"]=={
  "canonical_selected":715,"canonical_remaining":309,"universe_unselected_names":193,
  "exact_name_overlap_lower_domains":97,"unique_unselected_name_candidates":96,
  "provisional_coordinates_assigned":96,"available_after_reservations":213,
  "ratified_by_this_registry":0,"canonical_inventory_added_by_this_registry":0}
 assert len(set(x["provisional_coordinate"] for x in qrows))==96
 assert not (canon_codes & {x["provisional_coordinate"] for x in qrows})
 return {"canonical":715,"queued":96,"lower-name-overlap":97,"still-unselected":309,"ratified":0}
if __name__=="__main__":
 if not __debug__:sys.exit("D10-QUEUE BLOCK optimized assertions")
 try:print("D10-QUEUE PASS",json.dumps(check(),sort_keys=True))
 except (AssertionError,KeyError,TypeError,ValueError,OSError) as e:sys.exit("D10-QUEUE BLOCK "+str(e))
