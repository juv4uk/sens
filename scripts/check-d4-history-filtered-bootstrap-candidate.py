#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
candidate_path = root / "knowledge/d4-history-filtered-bootstrap-candidate.json"
cleanroom_path = root / "knowledge/d4-cleanroom.json"

d = json.loads(candidate_path.read_text(encoding="utf-8"))
c = json.loads(cleanroom_path.read_text(encoding="utf-8"))

assert d["schema"] == "d4-history-filtered-bootstrap-candidate/v3"
assert d["authority"] == "posterior-history-candidate-only"
assert d["may_seed_cleanroom"] is False
assert d["cleanroom_authority"] == "knowledge/d4-cleanroom.json"
assert d["quarantine_issue"] == "#3260"

rows = d["rows"]
assert len(rows) == 16
by = {r["code"]: r for r in rows}
assert set(by) == {f"{i:04b}" for i in range(16)}
assert sum(r["status"] == "hole" for r in rows) == 2
assert sum(r["status"] == "irreducible-bootstrap-capability" for r in rows) == 2
for r in rows:
    assert r["code"][:3] == r["parent"].split()[0]

# Posterior sidecar must not mutate or supersede canonical clean-room authority.
assert c["authority"] == "#3225"
assert c["admitted"] == {
    "0110": "CDAR",
    "0111": "CDDR",
    "1000": "CAAR",
    "1001": "CADR",
}
assert len(c["unknown"]) == 12
assert set(c["admitted"]) | set(c["unknown"]) == {f"{i:04b}" for i in range(16)}

cleanroom_text = cleanroom_path.read_text(encoding="utf-8")
assert "d4-history-filtered-bootstrap-candidate" not in cleanroom_text
assert "d4-cleanroom-full-candidate" not in cleanroom_text

# Historical labels are permitted only in this quarantined sidecar.
for banned in ["SID8", "Sens8", "Function8"]:
    assert all(banned not in r["reason"] for r in rows)

print("D4-HISTORY-CANDIDATE-QUARANTINE: PASS")
print("CLEANROOM-AUTHORITY-UNCHANGED: 4 admitted + 12 UNKNOWN")
