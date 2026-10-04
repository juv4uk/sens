#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d4-cleanroom-full-candidate.json").read_text(encoding="utf-8"))
rows=d["rows"]
assert len(rows)==16
assert len({r["code"] for r in rows})==16
assert {r["code"] for r in rows}=={f"{i:04b}" for i in range(16)}
for r in rows:
    assert r["code"][:3] == r["parent"].split()[0]
    assert r["capability"]
    assert r["law"]

by={r["code"]:r["capability"] for r in rows}
assert by["0110"]=="CDAR"
assert by["0111"]=="CDDR"
assert by["1000"]=="CAAR"
assert by["1001"]=="CADR"

text=(root/"knowledge/d4-cleanroom-full-candidate.json").read_text(encoding="utf-8")
for banned in ["SID8","Sens8","Function8"]:
    # allowed only in forbidden_premises, not capability labels/laws
    assert all(banned not in r["capability"] and banned not in r["law"] for r in rows)

print("D4-CLEANROOM-FULL-CANDIDATE: PASS")
