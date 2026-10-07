#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
arch=json.loads((root/"knowledge/archipelago-map-v1.json").read_text(encoding="utf-8"))
matrix=json.loads((root/"knowledge/d10-owner-repo-donor-matrix-v2.json").read_text(encoding="utf-8"))
manifest=json.loads((root/"packaging/islands-manifest-v1.json").read_text(encoding="utf-8"))
bridge=json.loads((root/"knowledge/d10-island-bridge-factorization-v1.json").read_text(encoding="utf-8"))
noncore=json.loads((root/"knowledge/d10-noncore-reclassification-v1.json").read_text(encoding="utf-8"))
review=json.loads((root/"knowledge/d10-review-reclassification-v2.json").read_text(encoding="utf-8"))
inventory=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))

assert arch["schema"]=="sens-archipelago-map/v1"
assert arch["status"]=="CURRENT-ARCHITECTURE"
assert arch["authority"]=="#4140"

# All owner repositories are accounted for exactly once.
repos=arch["repository_archipelago"]["repositories"]
assert arch["repository_archipelago"]["repository_count"]==87
assert len(repos)==87
assert len({row["repository"] for row in repos})==87
assert {row["repository"] for row in repos}=={row["repository"] for row in matrix["rows"]}
assert not any(row["primary_class"]=="REVIEW-REQUIRED" for row in repos)
assert arch["repository_archipelago"]["zone_counts"]=={
    "REFERENCE-WATERS":33,
    "PACKAGE-ISLAND":33,
    "SUBSTRATE-ISLAND":11,
    "HISTORICAL-DONOR":9,
    "CORE-DONOR":1,
}

# Execution island identity must match the packaging manifest exactly.
manifest_islands=[row["key"] for row in manifest["islands"]]
arch_islands=[row["key"] for row in arch["execution_islands"]]
assert manifest_islands==["common-lisp","prolog","clips","datalog"]
assert arch_islands==manifest_islands
assert all(row["core_authority"] is False for row in arch["execution_islands"])

# Core border is exactly the factorized bridge set, not native island algorithms.
expected_bridge={row["semantic_name"] for row in bridge["selected"]}
arch_bridge={row["semantic_name"] for row in arch["core_border"]["d10_bridge_meanings"]}
assert expected_bridge=={
    "ISLAND-CALL",
    "EXECUTION-WITNESS",
    "NATIVE-OBSERVATION",
    "RESULT-COUNT",
    "BRIDGE",
    "MISSING-CAPABILITY",
}
assert arch_bridge==expected_bridge
current_by_name={row["semantic_name"]:row for row in inventory["rows"]}
for name in expected_bridge:
    row=current_by_name[name]
    assert row["source_class"]=="ISLAND-BRIDGE-FACTORIZATION"
    assert row["coordinate"] is None
    assert row["ratified_resident"] is False

# Reclassified package/island semantics must not re-enter D10 Core.
reclassified={row["stable_id"] for row in noncore["rows"]} | {row["stable_id"] for row in review["rows"]}
current_ids={row["stable_id"] for row in inventory["rows"]}
assert not (reclassified & current_ids)
assert arch["package_reclassification"]["preserved_rows"]==len(reclassified)==70

# D10 remains ownership-clean and unratified.
gate=arch["d10_gate"]
assert gate["selected_semantic_candidates"]==inventory["accounting"]["selected_semantic_candidates"]
assert gate["law_forced_coordinates"]==inventory["accounting"]["law_forced_coordinates"]
assert gate["unplaced_selected_candidates"]==inventory["accounting"]["unplaced_selected_candidates"]
assert gate["remaining_semantic_inventory"]==inventory["accounting"]["remaining_semantic_inventory"]
assert gate["ratified_d10_residents"]==0
assert gate["ownership_status"]=="OWNERSHIP-DEBT-CLEARED"
assert gate["definite_noncore_selected"]==0
assert gate["review_required_selected"]==0
assert gate["bridge_meanings_selected"]==6

assert state["archipelago"]=={
    "artifact":"knowledge/archipelago-map-v1.json",
    "authority":"#4140",
    "execution_islands":["common-lisp","prolog","clips","datalog"],
    "repository_count":87,
    "core_bridge_meanings":6,
    "ownership_rule":"Core owns semantic border/bridges; islands/packages/substrates own native semantics.",
    "ownership_debt_selected":0,
}
assert state["target"]["ratified_residents"]==0

print("ARCHIPELAGO-V1=PASS")
print("repos=87 execution-islands=4 core-bridge=6 reclassified-preserved=70")
print(f"D10={gate['selected_semantic_candidates']}/1024 ownership-debt=0 ratified=0")
