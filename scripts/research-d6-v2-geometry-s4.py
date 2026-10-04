#!/usr/bin/env python3
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ledger = json.loads((ROOT / "knowledge/d6-v2-law-first-ledger.json").read_text(encoding="utf-8"))
families_doc = json.loads((ROOT / "knowledge/d6-v2-binary-law-families.json").read_text(encoding="utf-8"))
candidate = json.loads((ROOT / "knowledge/d6-v2-gauge-fixed-candidate.json").read_text(encoding="utf-8"))

rows = ledger["rows"]
families = sorted(families_doc["families"], key=lambda f: f["id"])
free = sorted(row["coordinate"] for row in rows if row["status"] == "UNKNOWN")
free_prefixes = sorted({coord[:5] for coord in free})

assert len(rows) == 64
assert len(free) == 32
assert len(free_prefixes) == 16
assert len(families) == 16
assert len({f["id"] for f in families}) == 16
assert all(len(f["members"]) == 2 for f in families)

# S3: every free fibre is exactly an LSB pair.
for prefix in free_prefixes:
    assert prefix + "0" in free
    assert prefix + "1" in free

family_permutations = math.factorial(16)
local_orientations = 2 ** 16
oriented_representatives = family_permutations * local_orientations

assert family_permutations == 20_922_789_888_000
assert local_orientations == 65_536
assert oriented_representatives == 1_371_195_958_099_968_000

# Canonical gauge convention: opaque family-id order -> free-prefix order.
expected_mapping = []
for family, prefix in zip(families, free_prefixes):
    expected_mapping.append({
        "family_id": family["id"],
        "prefix5": prefix,
        "bit0": family["members"][0],
        "bit1": family["members"][1],
    })

assert candidate["status"] == "research-gauge-fixed-not-ratified"
assert candidate["selection_rule"]["semantic_score"] == 0
assert candidate["selection_rule"]["consumes_historical_d6_map"] is False
assert candidate["selection_rule"]["consumes_human_names_for_scoring"] is False
assert candidate["ratification"] == "NONE"
assert candidate["mapping"] == expected_mapping

candidate_rows = candidate["rows"]
assert len(candidate_rows) == 64
assert {r["coordinate"] for r in candidate_rows} == {f"{i:06b}" for i in range(64)}
assert len({r["name"] for r in candidate_rows}) == 64
assert all(r["name"] is not None for r in candidate_rows)
assert not any(r["status"] == "UNKNOWN" for r in candidate_rows)

# Existing 32 rows must be byte-for-byte semantic-preserved apart from row ordering.
original = {r["coordinate"]: r for r in rows if r["status"] != "UNKNOWN"}
emitted = {r["coordinate"]: r for r in candidate_rows}
for coordinate, source in original.items():
    assert emitted[coordinate] == source

# Newly filled rows must be gauge-marked, never smuggled in as proof.
for coordinate in free:
    assert emitted[coordinate]["status"] == "GAUGE-FIXED-CANDIDATE"
    assert emitted[coordinate]["law_status"] == "S4-CANONICAL-GAUGE"

print("D6-V2-GEOMETRY-S4: PASS")
print(f"semantic=64/64 coordinate-candidate=64/64")
print(f"gauge=16!*2^16={oriented_representatives}")
print("ratification=NONE")
