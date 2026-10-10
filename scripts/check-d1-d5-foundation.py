#!/usr/bin/env python3
import json
from pathlib import Path

# Оптимізований Python прибирає assert: без них фундамент не атестовано.
if not __debug__:
    raise SystemExit("D1-D9-FOUNDATION: BLOCKED — Python -O вимикає перевірки")

root=Path(__file__).resolve().parents[1]
old=json.loads((root/"knowledge/d1-d5-foundation.json").read_text(encoding="utf-8"))
d6f=json.loads((root/"knowledge/d1-d6-foundation.json").read_text(encoding="utf-8"))
d7f=json.loads((root/"knowledge/d1-d7-foundation.json").read_text(encoding="utf-8"))
d8f=json.loads((root/"knowledge/d1-d8-foundation.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
d4=json.loads((root/"knowledge/d4-cleanroom.json").read_text(encoding="utf-8"))
d5=json.loads((root/"knowledge/d5-ratified.json").read_text(encoding="utf-8"))
d6=json.loads((root/"knowledge/d6-ratified.json").read_text(encoding="utf-8"))
d7=json.loads((root/"knowledge/d7-ratified.json").read_text(encoding="utf-8"))
d8=json.loads((root/"knowledge/d8-ratified.json").read_text(encoding="utf-8"))
d9=json.loads((root/"knowledge/d9-ratified.json").read_text(encoding="utf-8"))
contract=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")
rat=(root/"contracts/d1-d9-foundation-ratification.lisp").read_text(encoding="utf-8")

assert foundation["status"]=="owner-ratified"
assert old["authority"]=="#3331"
assert d6f["authority"]=="#3393"
assert d7f["authority"]=="#3572"
assert d8f["authority"]=="#3960"
assert foundation["authority"]=="#4008"
assert foundation["current_domains"]==["D1","D2","D3","D4","D5","D6","D7","D8","D9"]
assert foundation["research_domains"]==[]

assert foundation["domains"]["D1"]["residents"]=={"0":"NO","1":"YES"}
assert foundation["domains"]["D2"]["residents"]=={"00":"SEPARATOR","01":"CLOSE","10":"OPEN","11":"DOT"}
assert foundation["domains"]["D3"]["residents"]=={
"000":"EMPTY","001":"QUOTE","010":"ATOM","011":"CDR","100":"CAR","101":"EQ","110":"COND","111":"CONS"}
assert foundation["domains"]["D4"]["residents"]==d4["residents"]
assert foundation["domains"]["D5"]["residents"]==d5["residents"]
assert foundation["domains"]["D6"]["residents"]==d6["residents"]
assert foundation["domains"]["D7"]["residents"]==d7["residents"]
assert foundation["domains"]["D8"]["residents"]==d8["residents"]
assert foundation["domains"]["D9"]["residents"]==d9["residents"]
assert len(foundation["domains"]["D7"]["residents"])==126
assert len(foundation["domains"]["D8"]["residents"])==256
assert len(foundation["domains"]["D9"]["residents"])==512
assert len(set(foundation["domains"]["D9"]["residents"].values()))==512

assert "(minor . 8)" in contract
assert "Contract 11.8" in contract
assert "#4008" in contract
assert "Core.D9 is OWNER-RATIFIED 512/512 under #4008" in contract
assert "Contract 11.8 D1–D9 foundation contract" in current
assert "D9  full compact 512/512" in current
assert "(current-domains . (D1 D2 D3 D4 D5 D6 D7 D8 D9))" in rat

print("D1-D9-FOUNDATION: PASS")
print("current=D1,D2,D3,D4,D5,D6,D7,D8,D9 research=none")
