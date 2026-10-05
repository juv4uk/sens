#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ratified = json.loads((root / "knowledge/d6-ratified.json").read_text(encoding="utf-8"))
census = json.loads((root / "knowledge/d6-mechanism-census.json").read_text(encoding="utf-8"))

rows = census["rows"]
assert census["schema"] == "d6-mechanism-census/v1"
assert len(rows) == 64
assert len({row["coordinate"] for row in rows}) == 64
assert len({row["resident"] for row in rows}) == 64
assert {row["coordinate"]: row["resident"] for row in rows} == ratified["residents"]
assert all(row["identity_status"] == "RATIFIED" for row in rows)

allowed = {"DIRECT_LAW", "LOWER_DOMAIN_COMPOSITION", "LISP_OWNED", "MISSING"}
assert all(row["mechanism_status"] in allowed for row in rows)

executable = [row for row in rows if row["mechanism_status"] != "MISSING"]
missing = [row for row in rows if row["mechanism_status"] == "MISSING"]
assert census["summary"]["executable_count"] == len(executable)
assert census["summary"]["missing_count"] == len(missing)
for status in allowed:
    assert census["summary"]["by_status"][status] == sum(
        row["mechanism_status"] == status for row in rows
    )

selector_bits = {
    f"{value:06b}"
    for value in list(range(0b011000, 0b100000)) + list(range(0b100000, 0b101000))
}
selector_rows = [row for row in rows if row.get("mechanism_id") == "selector-generator-depth4"]
assert {row["coordinate"] for row in selector_rows} == selector_bits
assert all(row["mechanism_status"] == "DIRECT_LAW" for row in selector_rows)
assert all(row["negative_cross_domain_control"] for row in selector_rows)

print(
    "D6-MECHANISM-CENSUS: PASS "
    f"identity={len(rows)}/64 executable={len(executable)}/64 missing={len(missing)}/64"
)
