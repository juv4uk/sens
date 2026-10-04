#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d4-cleanroom.json").read_text(encoding="utf-8"))
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")
evidence=(root/"contracts/d4-bootstrap-ratification.lisp").read_text(encoding="utf-8")

assert d["status"]=="revoked-research-evidence"
assert d["authority"]=="#3327"
assert d["revoked_by"]=="#3327"
assert "(minor . 4)" in lang
assert "D4  UNRATIFIED / RESEARCH" in current
assert "(status . revoked-research-evidence)" in evidence
assert "(former-owner-ratification . #3272)" in evidence
assert "(revoked-by . #3327)" in evidence
print("D4-REVOKED-EVIDENCE-GUARD: PASS")
