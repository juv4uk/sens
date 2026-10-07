#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
review=json.loads((root/"knowledge/d10-crossrepo-clojure-reference-v1.json").read_text(encoding="utf-8"))
matrix=json.loads((root/"knowledge/d10-owner-repo-donor-matrix-v2.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))

assert review["schema"]=="d10-crossrepo-clojure-reference-v1/v1"
assert review["status"]=="REVIEW-COMPLETE-NO-ADMISSION"
assert review["authority"]=="#4053"
assert review["accounting"]=={
    "repositories_reviewed":2,
    "selected_d10_candidates":0,
    "reclassified_to_reference":2,
    "d10_inventory_delta":0,
    "historical_donor_queue_reviewed":"11/11",
    "ratified_d10_residents":0,
}

rows=review["reviewed_repositories"]
assert len(rows)==2
assert {r["repository"] for r in rows}=={"juv4uk/Clojure-code","juv4uk/clojure-cookbook"}
assert all(r["classification"]=="REFERENCE-OR-UPSTREAM" for r in rows)
assert all(r["selected_d10_candidates"]==0 for r in rows)
assert all(r["decision"]=="NO-DIRECT-CORE-ADMISSION" for r in rows)

by={r["repository"]:r for r in matrix["rows"]}
for repo in ("juv4uk/Clojure-code","juv4uk/clojure-cookbook"):
    assert by[repo]["primary_class"]=="REFERENCE-OR-UPSTREAM"
    assert by[repo]["d10_action"]=="REFERENCE-ONLY"
    assert by[repo]["deep_review_status"]=="BOUNDARY-VERIFIED"
    assert by[repo]["candidate_issue"] is None

assert matrix["class_counts"]=={
    "REFERENCE-OR-UPSTREAM":33,
    "PACKAGE-OR-DOMAIN":33,
    "BACKEND-OR-MECHANISM":11,
    "CORE-HISTORICAL-DONOR":9,
    "CORE-LANGUAGE-DONOR":1,
}
assert matrix["followup_queues"]["historical_core_review"]=="COMPLETE #4053"

# This correction is an ownership/provenance correction only.
assert inventory["accounting"]["selected_semantic_candidates"]>=504
assert inventory["accounting"]["ratified_d10_residents"]==0

print("D10-CLOJURE-REFERENCE-REVIEW=PASS")
print("reviewed=2 selected=0 historical-queue=11/11")
