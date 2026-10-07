#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
arch=json.loads((root/"knowledge/archipelago-map-v1.json").read_text(encoding="utf-8"))
matrix=json.loads((root/"knowledge/d10-owner-repo-donor-matrix-v3.json").read_text(encoding="utf-8"))
manifest=json.loads((root/"packaging/islands-manifest-v1.json").read_text(encoding="utf-8"))
bridge=json.loads((root/"knowledge/d10-island-bridge-factorization-v1.json").read_text(encoding="utf-8"))
noncore=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))
review=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))
restoration=json.loads((root/"knowledge/d10-single-stream-restoration-v1.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))

assert arch["schema"]=="sens-archipelago-map/v1"
assert arch["status"]=="EXECUTION-ARCHITECTURE-SEMANTIC-OWNERSHIP-SUPERSEDED"
assert arch["owner_correction"]=="#4162"

repos=arch["repository_archipelago"]["repositories"]
assert arch["repository_archipelago"]["repository_count"]==87
assert len(repos)==87
assert len({row["repository"] for row in repos})==87
assert {row["repository"] for row in repos}=={row["repository"] for row in matrix["rows"]}
assert arch["repository_archipelago"]["source"]=="knowledge/d10-owner-repo-donor-matrix-v3.json"
assert arch["repository_archipelago"]["semantic_namespace_rule"]=="ONE-GLOBAL-D10-BITSTREAM"

assert matrix["policy_counts"]=={
    "EVIDENCE-DONOR":33,
    "DIRECT-SEMANTIC-DONOR":43,
    "SEMANTIC-DONOR-WITH-MECHANISM-GATE":11,
}

manifest_islands=[row["key"] for row in manifest["islands"]]
arch_islands=[row["key"] for row in arch["execution_islands"]]
assert manifest_islands==["common-lisp","prolog","clips","datalog"]
assert arch_islands==manifest_islands
assert all(row["core_authority"] is False for row in arch["execution_islands"])

expected_bridge={row["semantic_name"] for row in bridge["selected"]}
arch_bridge={row["semantic_name"] for row in arch["core_border"]["d10_bridge_meanings"]}
assert arch_bridge==expected_bridge
assert len(expected_bridge)==6

historical_reclassified={row["stable_id"] for row in noncore["rows"]} | {row["stable_id"] for row in review["rows"]}
restored={row["stable_id"] for row in restoration["rows"]}
current_ids={row["stable_id"] for row in inventory["rows"]}
assert len(historical_reclassified)==70
assert historical_reclassified==restored
assert restored <= current_ids
assert arch["package_reclassification"]["status"]=="REVERSED-BY-OWNER-CORRECTION-4162"
assert arch["package_reclassification"]["restored_rows"]==70

gate=arch["d10_gate"]
selected=inventory["accounting"]["selected_semantic_candidates"]
remaining=inventory["accounting"]["remaining_semantic_inventory"]
assert selected>=504
assert remaining==1024-selected
assert gate["selected_semantic_candidates"]==504
assert gate["law_forced_coordinates"]==256
assert gate["unplaced_selected_candidates"]==248
assert gate["remaining_semantic_inventory"]==520
assert gate["ratified_d10_residents"]==0
assert gate["ownership_status"]=="SINGLE-STREAM-OWNER-CORRECTED"
assert gate["restored_prior_reclassification_rows"]==70
assert gate["bridge_meanings_selected"]==6

assert state["archipelago"]["status"]=="EXECUTION-MECHANISM-ONLY"
assert state["owner_correction_single_stream"]["authority"]=="#4162"
assert state["owner_repo_donor_matrix"]["namespace_rule"]=="ONE-GLOBAL-D10-BITSTREAM"
assert state["target"]["ratified_residents"]==0

print("ARCHIPELAGO-V1=EXECUTION-ONLY-PASS")
print("repos=87 semantic-namespace=single-D10 restored=70 execution-islands=4 bridge=6")
