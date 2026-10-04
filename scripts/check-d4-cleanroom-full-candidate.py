#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d4-cleanroom-full-candidate.json").read_text(encoding="utf-8"))
rows=d["rows"]
assert len(rows)==16
by={r["code"]:r for r in rows}
assert set(by)=={f"{i:04b}" for i in range(16)}
expected={
"0000":"APPLY","0001":"EVAL","0010":"LAMBDA","0011":"DEFINE",
"0100":"NOT","0101":"UNALLOCATED","0110":"CDAR","0111":"CDDR",
"1000":"CAAR","1001":"CADR","1010":"LOOKUP","1011":"BIND",
"1100":"EVCON","1101":"EVLIS","1110":"LIST","1111":"UNALLOCATED"}
assert {k:v["name"] for k,v in by.items()}==expected
assert sum(r["status"]=="hole" for r in rows)==2
assert sum(r["status"]=="irreducible-bootstrap-capability" for r in rows)==2
for r in rows:
    assert r["code"][:3]==r["parent"].split()[0]
for banned in ["SID8","Sens8","Function8"]:
    assert all(banned not in r["reason"] for r in rows)
print("D4-MINIMAL-HISTORICAL-BOOTSTRAP: PASS")
