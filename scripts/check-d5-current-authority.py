#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d5-ratified.json").read_text(encoding="utf-8"))
contract=(root/"contracts/d5-ratification.lisp").read_text(encoding="utf-8")
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")
core=(root/"docs/language-core.md").read_text(encoding="utf-8")

assert d["status"]=="owner-ratified"
assert d["authority"]=="#3305"
assert d["capacity"]==32 and d["occupancy"]==32 and d["distinct_residents"]==32
assert d["lower_domain_duplicates"]==0
assert len(d["residents"])==32
assert set(d["residents"])=={f"{i:05b}" for i in range(32)}
assert len(set(d["residents"].values()))==32
assert "APPEND" not in d["residents"].values()
assert d["residents"]["10100"]=="REVERSE"
assert d["residents"]["10101"]=="REVERSE-ONTO"
assert d["relation_classes"]=={
    "COORDINATE-HISTORICAL":4,
    "MULTI-DELTA-FAMILY":2,
    "LOCAL-ALGEBRA":5,
    "SEMANTIC-GENERATOR":5,
}

for bits,name in d["residents"].items():
    assert f"(D5:{bits} {name})" in contract,(bits,name)

assert "(minor . 3)" in lang
assert "#3305" in lang
assert "D5  full compact 32/32" in current
assert "D5 **OWNER-RATIFIED #3305**" in core
assert "D6  UNRATIFIED / RESEARCH" in current
assert "D8  UNRATIFIED / RESEARCH" in current

print("D5-CURRENT-AUTHORITY: PASS")
print("occupancy=32/32 distinct=32 duplicates=0 generator=5 local-algebra=5 multi-delta=2 historical=4")
