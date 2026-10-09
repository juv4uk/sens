#!/usr/bin/env python3
"""#3005 — classify SET/SETQ siblings by consuming merged #2589 evidence."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
owner = json.loads((ROOT / "knowledge/d5-historical-full-map.json").read_text())
factor = (ROOT / "crates/sens/tests/post_d4_set_setq_factor.rs").read_text()
result = json.loads((ROOT / "knowledge/d5-set-setq-sibling-law.json").read_text())

rows = {row["coordinate"]: row for row in owner["coordinates"]}
assert rows["00110"]["name"] == "SET"
assert rows["00111"]["name"] == "SETQ"

for witness in (
    "set_and_setq_have_identical_mutation_signature_after_target_normalization",
    "both_select_the_same_nearest_existing_location",
    "both_share_the_same_fail_closed_missing_binding_policy",
    "acquisition_policy_is_observable_but_separate_from_mutation_core",
    "missing_computed_target_is_an_acquisition_failure_not_mutation_semantics",
    "factorization_verdict_is_width_conservative",
):
    assert witness in factor, witness

assert 'target_acquisition: "separate-d4-composable"' in factor
assert 'mutation_factor: "shared-nearest-existing-fail"' in factor
assert result["classification"] == "LOCAL-SIBLING-LAW"
assert result["relation_class"] == "SEMANTIC-LAW"
assert result["one_delta_axis"] is True
assert result["delta_axis"] == "target-symbol-acquisition"
assert result["d4_define_parenthood"] == "NOT-INFERRED"
assert result["d6_search_scope_axis"] == "OUT-OF-SCOPE"
assert result["d6_missing_name_axis"] == "OUT-OF-SCOPE"
assert result["owner_map_mutation"] == "NONE"

print("D5-SET-SETQ-SIBLING-LAW=PASS")
print("00110=SET")
print("00111=SETQ")
print("SHARED-CORE=nearest-existing/fail")
print("DELTA-AXIS=target-symbol-acquisition")
print("CLASSIFICATION=LOCAL-SIBLING-LAW")
print("RELATION=SEMANTIC-LAW")
print("DEFINE-PARENTHOOD=NOT-INFERRED")
print("D6-POLICY-AXES=OUT-OF-SCOPE")
print("OWNER-MAP-MUTATION=NONE")
