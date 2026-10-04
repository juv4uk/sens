#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
d = json.loads((root / "knowledge/d4-cleanroom.json").read_text(encoding="utf-8"))
contract = (root / "language-contract.lisp").read_text(encoding="utf-8")
core = (root / "docs/language-core.md").read_text(encoding="utf-8")
current = (root / "CURRENT.md").read_text(encoding="utf-8")
rat = (root / "contracts/d4-bootstrap-ratification.lisp").read_text(encoding="utf-8")

expected = {
    "0000":"APPLY","0001":"EVAL","0010":"LAMBDA","0011":"DEFINE",
    "0100":"NOT","0101":"NULL","0110":"CDAR","0111":"CDDR",
    "1000":"CAAR","1001":"CADR","1010":"LOOKUP","1011":"BIND",
    "1100":"EVCON","1101":"EVLIS","1110":"LIST","1111":"APPEND",
}

assert d["status"] == "owner-ratified"
assert d["authority"] == "#3272"
assert d["residents"] == expected
assert len(d["residents"]) == 16
assert set(d["residents"]) == {f"{i:04b}" for i in range(16)}

for code,name in expected.items():
    assert f"{code}  {name}" in core, (code,name)
    assert f"(D4:{code} {name})" in rat, (code,name)

contract_sentence = (
    "0000 APPLY, 0001 EVAL, 0010 LAMBDA, 0011 DEFINE, "
    "0100 NOT, 0101 NULL, 0110 CDAR, 0111 CDDR, "
    "1000 CAAR, 1001 CADR, 1010 LOOKUP, 1011 BIND, "
    "1100 EVCON, 1101 EVLIS, 1110 LIST, 1111 APPEND"
)
assert contract_sentence in contract
assert "#3272" in contract
assert "D4  full compact bootstrap" in current
assert "0101 NULL" in current and "1111 APPEND" in current
assert d["semantic_distinctions"]["NOT_vs_NULL"].startswith("PredicateBit NO is not structural EMPTY")
assert set(d["classification"]["generated_selectors"]) == {"CAAR","CADR","CDAR","CDDR"}

print("D4-CURRENT-AUTHORITY: PASS")
