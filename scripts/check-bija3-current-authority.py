#!/usr/bin/env python3
"""Revocation guard for former D3/bīja3 ratification #3202."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
lang=(ROOT/"language-contract.lisp").read_text(encoding="utf-8")
current=(ROOT/"CURRENT.md").read_text(encoding="utf-8")
evidence=(ROOT/"contracts/bija3-l1-l5-ratification.lisp").read_text(encoding="utf-8")

assert "(minor . 4)" in lang
assert "#3327" in lang
assert "D3  UNRATIFIED / RESEARCH" in current
assert "(status . revoked-research-evidence)" in evidence
assert "(former-owner-ratification . #3202)" in evidence
assert "(revoked-by . #3327)" in evidence
print("D3-REVOKED-EVIDENCE-GUARD: PASS")
