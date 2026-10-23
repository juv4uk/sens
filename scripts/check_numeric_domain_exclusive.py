#!/usr/bin/env python3
"""New-reality test (#5789): numeric domains are D12+ ONLY; D1-D10 are never operands.

Authored to the CURRENT reality, not the past:
- one source of domain widths: contracts/numeric-domains-ratification.lisp,
  growth law D(12 * 2^n), arithmetic-exclusivity (D1-D10 are exact binary words,
  never arithmetic operands or inferred numbers);
- the current D12 owner extension is parsed directly from Lisp;
- crates/sens/src/binary_number.rs carries an explicit numeric domain, and the
  unqualified pathway is the *historic* one, not the default;
- D11 is out: the transport caps at D10 (no 11-bit T5).

Fail-closed N1-N5. Exit 0 = NUMERIC_DOMAIN_EXCLUSIVE_OK; 1 = ..._BLOCKED.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CONTRACT = "contracts/numeric-domains-ratification.lisp"
BINNUM = "crates/sens/src/binary_number.rs"
TRANSPORTS = ("research/zig-codecs/t5/t5.zig", "research/zig-codecs/transport_abi.zig")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from domain_tables import number_domains  # noqa: E402


def check(root: Path) -> list[str]:
    problems: list[str] = []

    # N1 -- the ratified contract is the single source and states the laws.
    cp = root / CONTRACT
    if not cp.is_file():
        return [f"N1: missing {CONTRACT}"]
    c = cp.read_text(encoding="utf-8")
    if "owner-ratified" not in c:
        problems.append("N1: numeric-domain contract is not owner-ratified")
    if "arithmetic-exclusivity" not in c:
        problems.append("N1: contract does not state the arithmetic-exclusivity law")
    if "D(12 * 2^n)" not in c and "24 * 2^n" not in c:
        problems.append("N1: contract does not state the growth law D(12 * 2^n)")
    if not all(name in c for name in ("D12", "D24", "D48", "D96", "D192")):
        problems.append("N1: contract does not name D12/D24/D48/D96/D192")

    # N2 -- the sole current owner form must parse and double from D12.
    try:
        domains = number_domains(cp)
        if domains[:5] != (
            ("D12", 12), ("D24", 24), ("D48", 48),
            ("D96", 96), ("D192", 192),
        ):
            problems.append(f"N2: current D12 prefix drift: {domains!r}")
    except (OSError, ValueError) as exc:
        problems.append(f"N2: invalid current Lisp numeric law: {exc}")

    # N3 -- the numeric domain is explicit; the unqualified path is historic.
    bp = root / BINNUM
    if not bp.is_file():
        problems.append(f"N3: missing {BINNUM}")
    else:
        b = bp.read_text(encoding="utf-8")
        if "numeric_domain_width" not in b:
            problems.append("N3: BinaryNumber carries no explicit numeric domain field")
        if "historic" not in b and "unqualified" not in b:
            problems.append("N3: BinaryNumber does not mark the unqualified path as historic")

    # N4 -- D11 is out: the transport caps at D10.
    cap_seen = False
    for rel in TRANSPORTS:
        p = root / rel
        if not p.is_file():
            continue
        s = p.read_text(encoding="utf-8")
        if "max_width" in s and "10" in s:
            cap_seen = True
        if re.search(r"11\s*bit|width\s*==\s*11|D11", s):
            problems.append(f"N4: {rel} mentions an 11-bit/D11 width -- D11 must stay out")
    if not cap_seen:
        problems.append("N4: no transport caps the width at D10 (D11 could leak into T5)")

    # N5 -- the сід8-era is physically impossible: the sterile corridor modules
    # carry no сід8/сенс8/Function8/W8 marker (legacy is provenance, not the ladder).
    legacy_re = re.compile(r"SID8|Sens8|Function8|\bW8\b|pre-rebuild")
    for rel in ("research/zig-codecs/t5/t5.zig", "research/zig-codecs/transport_abi.zig",
                "research/zig-codecs/f3c/f3c.zig", "research/zig-codecs/transport.zig"):
        p = root / rel
        if not p.is_file():
            continue
        s = p.read_text(encoding="utf-8")
        if legacy_re.search(s):
            problems.append(f"N5: {rel} names a SID8-era token -- legacy is provenance, "
                            "never the corridor's ladder")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except (OSError, ValueError) as exc:
        print(f"NUMERIC_DOMAIN_EXCLUSIVE_BLOCKED: {exc}", flush=True)
        return 1
    if problems:
        print("NUMERIC_DOMAIN_EXCLUSIVE_BLOCKED:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print("NUMERIC_DOMAIN_EXCLUSIVE_OK numeric domains are D12+ only from one ratified "
          "source; D1-D10 are never operands; D11 stays out", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
