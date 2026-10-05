#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
old=json.loads((root/"knowledge/d1-d5-foundation.json").read_text(encoding="utf-8"))
prev=json.loads((root/"knowledge/d1-d6-foundation.json").read_text(encoding="utf-8"))
f=json.loads((root/"knowledge/d1-d7-foundation.json").read_text(encoding="utf-8"))
d4=json.loads((root/"knowledge/d4-cleanroom.json").read_text(encoding="utf-8"))
d5=json.loads((root/"knowledge/d5-ratified.json").read_text(encoding="utf-8"))
d6=json.loads((root/"knowledge/d6-ratified.json").read_text(encoding="utf-8"))
d7=json.loads((root/"knowledge/d7-ratified.json").read_text(encoding="utf-8"))
contract=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")
rat=(root/"contracts/d1-d7-foundation-ratification.lisp").read_text(encoding="utf-8")

assert f["status"]=="owner-ratified"
assert old["authority"]=="#3331"
assert prev["authority"]=="#3393"
assert f["authority"]=="#3572"
assert f["current_domains"]==["D1","D2","D3","D4","D5","D6","D7"]
assert f["research_domains"]==["D8"]

assert f["domains"]["D1"]["residents"]=={"0":"NO","1":"YES"}
assert f["domains"]["D2"]["residents"]=={"00":"SEPARATOR","01":"CLOSE","10":"OPEN","11":"DOT"}
assert f["domains"]["D3"]["residents"]=={
"000":"EMPTY","001":"QUOTE","010":"ATOM","011":"CDR","100":"CAR","101":"EQ","110":"COND","111":"CONS"}
assert f["domains"]["D4"]["residents"]==d4["residents"]
assert f["domains"]["D5"]["residents"]==d5["residents"]
assert f["domains"]["D6"]["residents"]==d6["residents"]
assert f["domains"]["D7"]["residents"]==d7["residents"]
assert f["domains"]["D7"]["owner_reserved_pinned"]==["0100001","0101010"]
assert len(f["domains"]["D7"]["residents"])==126
assert len(f["domains"]["D6"]["residents"])==64
assert len(set(f["domains"]["D6"]["residents"].values()))==64
assert len(f["domains"]["D5"]["residents"])==32
assert len(set(f["domains"]["D5"]["residents"].values()))==32
assert "APPEND" not in f["domains"]["D5"]["residents"].values()
assert f["domains"]["D4"]["residents"]["1111"]=="APPEND"

assert "(minor . 6)" in contract
assert "Contract 11.6" in contract
assert "#3572" in contract
assert "D7 is owner-ratified 126/128 in #3572" in contract
assert "current ratified semantic Core domains are exactly D1–D7" in current
assert "D7  owner-ratified 126/128" in current
assert "(current-domains . (D1 D2 D3 D4 D5 D6 D7))" in rat

print("D1-D7-FOUNDATION: PASS")
print("current=D1,D2,D3,D4,D5,D6,D7 research=D8")
