#!/usr/bin/env python3
"""Current authority guard for owner-ratified D3/bīja3 A (#3202)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = [
    "000  structural empty ()",
    "001  QUOTE",
    "010  ATOM",
    "011  CDR",
    "100  CAR",
    "101  EQ",
    "110  COND",
    "111  CONS",
]

contract = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")
core = (ROOT / "docs/language-core.md").read_text(encoding="utf-8")
current = (ROOT / "CURRENT.md").read_text(encoding="utf-8")
ratified = (ROOT / "contracts/bija3-l1-l5-ratification.lisp").read_text(encoding="utf-8")

contract_sentence = (
    "000 structural empty (), 001 QUOTE, 010 ATOM, 011 CDR, "
    "100 CAR, 101 EQ, 110 COND, 111 CONS"
)
assert contract_sentence in contract
assert "(minor . 1)" in contract
assert "#3202" in contract

for line in EXPECTED:
    assert line in core, line

assert "000 (), 001 QUOTE, 010 ATOM, 011 CDR, 100 CAR, 101 EQ, 110 COND, 111 CONS" in current
assert "(owner-ratification . #3202)" in ratified

for word, name in [
    ("000", "EMPTY"), ("001", "QUOTE"), ("010", "ATOM"), ("011", "CDR"),
    ("100", "CAR"), ("101", "EQ"), ("110", "COND"), ("111", "CONS"),
]:
    assert f"(D3:{word} {name})" in ratified

for prefix, left, right in [
    ("00", "EMPTY", "QUOTE"),
    ("01", "ATOM", "CDR"),
    ("10", "CAR", "EQ"),
    ("11", "COND", "CONS"),
]:
    assert f"(D2:{prefix} {left} {right})" in ratified

print("BIJA3-CURRENT-AUTHORITY: PASS")
