#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d5-ratified.json").read_text(encoding="utf-8"))
contract=(root/"contracts/d5-ratification.lisp").read_text(encoding="utf-8")
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")

assert d["status"]=="revoked-research-evidence"
assert d["authority"]=="#3327"
assert d["revoked_by"]=="#3327"
assert "(status . revoked-research-evidence)" in contract
assert "(former-owner-ratification . #3305)" in contract
assert "(revoked-by . #3327)" in contract
assert "(minor . 4)" in lang
assert "D5  UNRATIFIED / RESEARCH" in current
print("D5-REVOKED-EVIDENCE-GUARD: PASS")
