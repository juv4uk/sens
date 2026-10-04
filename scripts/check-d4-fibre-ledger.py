#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ledger_path = root / "knowledge/d4-fibre-ledger.json"
cleanroom_path = root / "knowledge/d4-cleanroom.json"
history_path = root / "knowledge/d4-history-filtered-bootstrap-candidate.json"
old_history_path = root / "knowledge/d4-cleanroom-full-candidate.json"

ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
cleanroom = json.loads(cleanroom_path.read_text(encoding="utf-8"))

assert ledger["schema"] == "d4-cleanroom-fibre-ledger/v1"
assert ledger["authority"] == "#3257"
assert ledger["parent_cleanroom"] == "#3225"
assert ledger["cleanroom_source"] == "knowledge/d4-cleanroom.json"
assert ledger["statuses"] == ["PROVED-GENERATOR", "REFUTED", "UNKNOWN"]

atlas = ledger["atlas_policy"]
assert atlas["authoritative"] is False
assert atlas["posterior_only"] is True
assert atlas["history_sidecar"] == "knowledge/d4-history-filtered-bootstrap-candidate.json"

expected_parents = {
    "000": "EMPTY",
    "001": "QUOTE",
    "010": "ATOM",
    "011": "CDR",
    "100": "CAR",
    "101": "EQ",
    "110": "COND",
    "111": "CONS",
}

fibres = ledger["fibres"]
assert len(fibres) == 8
assert {row["parent"]: row["role"] for row in fibres} == expected_parents

required_proof_fields = (
    "children",
    "generator",
    "suffix_meaning",
    "parent_invariant",
    "parent_recovery",
    "witness_ref",
    "falsifier",
)

admitted = {}
unknown = []

for row in fibres:
    parent = row["parent"]
    status = row["status"]
    assert status in ledger["statuses"]
    assert row["evidence_refs"], parent
    assert row["reason"], parent

    if status == "PROVED-GENERATOR":
        for field in required_proof_fields:
            assert row[field], (parent, field)

        assert set(row["children"]) == {"0", "1"}
        assert set(row["suffix_meaning"]) == {"0", "1"}

        for suffix in ("0", "1"):
            child = row["children"][suffix]
            assert child["code"] == parent + suffix
            assert child["label"]
            assert child["code"] not in admitted
            admitted[child["code"]] = child["label"]
    else:
        # Non-proved rows may carry evidence references/reasons but may not
        # smuggle half-families, labels or placements into the projection.
        for field in required_proof_fields:
            assert row[field] is None, (parent, status, field)
        unknown.extend([parent + "0", parent + "1"])

assert set(admitted).isdisjoint(unknown)
assert set(admitted) | set(unknown) == {f"{i:04b}" for i in range(16)}

# The ledger projection must exactly reproduce current clean-room authority.
assert cleanroom["authority"] == "#3225"
assert admitted == cleanroom["admitted"]
assert sorted(unknown) == sorted(cleanroom["unknown"])

# Posterior history sidecar is allowed only as non-authoritative evidence.
assert history_path.exists()
history = json.loads(history_path.read_text(encoding="utf-8"))
assert history["authority"] == "posterior-history-candidate-only"
assert history["may_seed_cleanroom"] is False
assert history["cleanroom_authority"] == "knowledge/d4-cleanroom.json"
assert not old_history_path.exists()

report = {
    "schema": "d4-fibre-ledger-projection/v1",
    "proved_parents": [
        row["parent"] for row in fibres if row["status"] == "PROVED-GENERATOR"
    ],
    "refuted_parents": [
        row["parent"] for row in fibres if row["status"] == "REFUTED"
    ],
    "unknown_parents": [
        row["parent"] for row in fibres if row["status"] == "UNKNOWN"
    ],
    "admitted": admitted,
    "unknown": sorted(unknown),
}
print(json.dumps(report, sort_keys=True))
print("D4-FIBRE-LEDGER: PASS")
print(f"PROJECTION: {len(admitted)} admitted + {len(unknown)} UNKNOWN")
