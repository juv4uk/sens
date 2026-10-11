#!/usr/bin/env python3
import json
from pathlib import Path

# Python -O прибирає assert, тому запуск без перевірок має завершуватися відмовою.
if not __debug__:
    raise SystemExit("D6-CURRENT-AUTHORITY: BLOCKED — Python -O вимикає перевірки")

root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d6-ratified.json").read_text(encoding="utf-8"))
source=json.loads((root/"knowledge/d6-v2-gauge-fixed-candidate.json").read_text(encoding="utf-8"))
contract=(root/"contracts/d6-ratification.lisp").read_text(encoding="utf-8")
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")

assert d["status"]=="owner-ratified"
assert d["authority"]=="#3393"
assert d["capacity"]==64 and d["occupancy"]==64 and d["distinct_residents"]==64
assert len(d["residents"])==64
assert set(d["residents"])=={f"{i:06b}" for i in range(64)}
assert len(set(d["residents"].values()))==64

source_map={row["coordinate"]:row["name"] for row in source["rows"]}
assert d["residents"]==source_map

basis=[row["coordinate_basis"] for row in d["rows"]]
assert basis.count("proved-selector-generator")==16
assert basis.count("owner-ratified-law-anchored-coordinate")==16
assert basis.count("owner-ratified-s4-gauge-choice")==32

for bits,name in d["residents"].items():
    assert f"(D6:{bits} {name})" in contract,(bits,name)

assert "(minor . 8)" in lang
assert "Contract 11.8" in lang
assert "#3393" in lang
assert "D6  full compact 64/64" in current
assert "D7  owner-ratified 126/128" in current
assert "D8  full compact 256/256" in current
assert "D9  full compact 512/512" in current

print("D6-CURRENT-AUTHORITY: PASS")
print("occupancy=64/64 distinct=64 selector-proof=16 law-anchored=16 owner-gauge=32")
