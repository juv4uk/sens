#!/usr/bin/env python3
"""Literal-prohibition guard: #…: literals are FORBIDDEN unless a narrow role is ratified.

Owner law (2026-10-15): the owner did not permit literals — the owner strictly
FORBADE them. Canonical D1 is bare 0 / 1 (positional grammar); the tag #d1: is
not language law. Only individually named roles are admitted (a temporary D1
bridge, the D24+ numeric carrier at the operand boundary, and the #b/#q2/#t7/#f32
machine wires). There is NO ratified dictionary of #dN: spellings.

Fail-closed:
- any #… prefix in lib/**/*.lisp that is neither a ratified role nor a valid
  D24+ width (24*2^k) blocks;
- a registry that does not declare the owner rule / canonical D1 blocks.

The mass #d1: debt is REPORTED (never silently tolerated) but does not block;
removing it is the cutover, tracked by #5605/#5609.

Exit 0 = LITERAL_PROHIBITION_OK; exit 1 = LITERAL_PROHIBITION_BLOCKED.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REGISTRY = "research/literal-prohibition.json"
PREFIX_RE = re.compile(r"#([A-Za-z][A-Za-z0-9]*):")  # only the #name: form, not #b1010
D24_WIDTH_RE = re.compile(r"^d(24|48|96|192|384|768|1536|3072)$")


def _valid_d24(prefix: str) -> bool:
    return bool(D24_WIDTH_RE.match(prefix))


def check(root: Path) -> list[str]:
    problems: list[str] = []
    registry_path = root / REGISTRY
    if not registry_path.exists():
        return [f"registry `{REGISTRY}` is missing"]
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    if not data.get("owner_rule"):
        problems.append("registry does not declare the owner rule (literals are forbidden)")
    if not data.get("canonical_d1"):
        problems.append("registry does not declare canonical D1 (bare 0 / 1)")

    ratified = {r["prefix"] for r in data.get("ratified_roles", [])}
    debt_prefixes = {r["prefix"] for r in data.get("ratified_roles", []) if r.get("status") == "debt"}

    glob = data.get("scan", {}).get("lib_glob", "lib/**/*.lisp")
    lib_dir = root / "lib"
    files = sorted(lib_dir.rglob("*.lisp")) if lib_dir.is_dir() else []
    if not files:
        return [f"no lib files matched under {lib_dir}"]

    found: dict[str, int] = {}
    for f in files:
        for prefix in PREFIX_RE.findall(f.read_text(encoding="utf-8", errors="replace")):
            found[prefix] = found.get(prefix, 0) + 1

    for prefix in sorted(found):
        if prefix in ratified or _valid_d24(prefix):
            continue
        problems.append(
            f"UNRATIFIED literal `#{prefix}:` in lib/ ({found[prefix]}x) — "
            "no issue ratified this prefix; literals are forbidden without one"
        )

    debt = sum(n for p, n in found.items() if p in debt_prefixes)
    if debt:
        print(f"NOTE cutover debt: {debt} temporary `#d1:` literal(s) in lib/ "
              "(bridge #5605/#5609, not language law)", file=sys.stderr)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except FileNotFoundError as exc:
        print(f"LITERAL_PROHIBITION_BLOCKED missing file: {exc}", flush=True)
        return 1
    if problems:
        print("LITERAL_PROHIBITION_BLOCKED unratified #…: literals present:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "LITERAL_PROHIBITION_OK no unratified #…: literal in lib/ "
        "(only the named roles; #d1: debt reported, not tolerated)",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
