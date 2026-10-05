#!/usr/bin/env python3
"""Current authority guard for owner-ratified D3/bīja3 A (#3202 / Contract 11.6)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def require(text: str, needle: str, where: str) -> None:
    assert needle in text, f"{where}: missing current-authority fragment: {needle!r}"

def forbid(text: str, needle: str, where: str) -> None:
    assert needle not in text, f"{where}: superseded current-authority fragment returned: {needle!r}"

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

contract = read("language-contract.lisp")
core = read("docs/language-core.md")
current = read("CURRENT.md")
ratified = read("contracts/bija3-l1-l5-ratification.lisp")
readme = read("README.md")
paradigm = read("docs/domain-paradigm.uk.md")
bench_readme = read("benchmarks/domain1234-dispatch/README.md")
bench_c = read("benchmarks/domain1234-dispatch/d34_dispatch.c")
bench_py = read("benchmarks/domain1234-dispatch/run.py")

contract_sentence = (
    "000 structural empty (), 001 QUOTE, 010 ATOM, 011 CDR, "
    "100 CAR, 101 EQ, 110 COND, 111 CONS"
)
require(contract, contract_sentence, "language-contract.lisp")
require(contract, "Contract 11.6", "language-contract.lisp")
require(contract, "(major . #d11) (minor . 6)", "language-contract.lisp")
require(contract, "#3202", "language-contract.lisp")

for line in EXPECTED:
    require(core, line, "docs/language-core.md")

require(
    current,
    "000 (), 001 QUOTE, 010 ATOM, 011 CDR, 100 CAR, 101 EQ, 110 COND, 111 CONS",
    "CURRENT.md",
)
require(ratified, "(owner-ratification . #3202)", "contracts/bija3-l1-l5-ratification.lisp")

for word, name in [
    ("000", "EMPTY"), ("001", "QUOTE"), ("010", "ATOM"), ("011", "CDR"),
    ("100", "CAR"), ("101", "EQ"), ("110", "COND"), ("111", "CONS"),
]:
    require(ratified, f"(D3:{word} {name})", "contracts/bija3-l1-l5-ratification.lisp")

for prefix, left, right in [
    ("00", "EMPTY", "QUOTE"),
    ("01", "ATOM", "CDR"),
    ("10", "CAR", "EQ"),
    ("11", "COND", "CONS"),
]:
    require(
        ratified,
        f"(D2:{prefix} {left} {right})",
        "contracts/bija3-l1-l5-ratification.lisp",
    )

# Current explanatory surfaces must follow current authority. Historical and
# research provenance is deliberately outside this guard.
require(readme, "Contract **11.6**", "README.md")
forbid(readme, "Contract **11.1**", "README.md")

require(paradigm, "011  CDR\n100  CAR", "docs/domain-paradigm.uk.md")
forbid(paradigm, "101  CAR\n110  CDR", "docs/domain-paradigm.uk.md")

require(
    bench_readme,
    "current ratified D3 roots `100 CAR`, `011 CDR`",
    "benchmarks/domain1234-dispatch/README.md",
)
forbid(
    bench_readme,
    "ratified D3 roots `101 CAR`, `110 CDR`",
    "benchmarks/domain1234-dispatch/README.md",
)

for needle in [
    "{0, 0, 3, 0b100},",
    "{1, 1, 3, 0b011},",
    "{2, 2, 4, 0b1000},",
    "{3, 3, 4, 0b1001},",
    "{4, 4, 4, 0b0110},",
    "{5, 5, 4, 0b0111},",
    "if (call->bits == 0b100) return step(value, 0);",
    "if (call->bits == 0b011) return step(value, 1);",
    "if (root != 0b100 && root != 0b011)",
    "return step(value, root == 0b011);",
]:
    require(bench_c, needle, "benchmarks/domain1234-dispatch/d34_dispatch.c")

for needle in [
    "{0, 0, 3, 0b101},",
    "{1, 1, 3, 0b110},",
    "if (call->bits == 0b101) return step(value, 0);",
    "if (call->bits == 0b110) return step(value, 1);",
    "if (root != 0b101 && root != 0b110)",
    "return step(value, root == 0b110);",
]:
    forbid(bench_c, needle, "benchmarks/domain1234-dispatch/d34_dispatch.c")

require(
    bench_py,
    "current ratified D3 roots 100 CAR / 011 CDR",
    "benchmarks/domain1234-dispatch/run.py",
)
forbid(
    bench_py,
    "ratified 101/110 roots",
    "benchmarks/domain1234-dispatch/run.py",
)

print("BIJA3-CURRENT-AUTHORITY: PASS")
