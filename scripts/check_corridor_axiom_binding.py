#!/usr/bin/env python3
"""Axiom binding guard: every corridor rule is DERIVED from a language-core axiom.

Uses our axioms (docs/language-core-axioms.md). The corridor rule
"Rust<->SENS crosses only the sterile Zig corridor" (#5777/#5779) must not be an
ad-hoc assertion: each guard rule is bound to the axiom it follows from.

Fail-closed:
- every corridor rule id must be bound in research/zig-codecs/corridor_axioms.json;
- every cited axiom id (G1..G8, S1..S3) must exist in docs/language-core-axioms.md;
- every binding must carry a non-empty derivation;
- the guard file named by a binding must exist.

Exit 0 = AXIOM_BINDING_OK; exit 1 = AXIOM_BINDING_BLOCKED with reasons.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BINDING = "research/zig-codecs/corridor_axioms.json"
AXIOM_ID = re.compile(r"^###\s+([GS]\d+)\s", re.M)

# The corridor rules the guards actually enforce.
EXPECTED_RULES = {
    "R1-corridor-default-on",
    "R2-build-requires-zig",
    "R3-physical-only-abi",
    "R4-pinned-corridor-version",
    "R5-host-neutral",
    "S1-physical-only-exports",
    "S2-no-semantic-import",
    "S3-no-host-struct",
    "S4-sterility-contract-declared",
    "C1-host-coverage",
}


def check(root: Path) -> list[str]:
    problems: list[str] = []
    binding_path = root / BINDING
    if not binding_path.exists():
        return [f"binding `{BINDING}` is missing"]
    data = json.loads(binding_path.read_text(encoding="utf-8"))

    axioms_doc = root / data["axioms_doc"]
    if not axioms_doc.exists():
        return [f"axioms doc `{data['axioms_doc']}` is missing"]
    axiom_ids = set(AXIOM_ID.findall(axioms_doc.read_text(encoding="utf-8")))

    bindings = data.get("bindings", [])
    bound_rules = {b.get("rule") for b in bindings}
    for rule in sorted(EXPECTED_RULES - bound_rules):
        problems.append(f"corridor rule `{rule}` is not bound to any axiom")

    for b in bindings:
        rule = b.get("rule", "<unnamed>")
        guard = b.get("guard", "")
        if guard and not (root / guard).exists():
            problems.append(f"binding `{rule}` names a guard that does not exist: {guard}")
        cited = b.get("axioms", [])
        if not cited:
            problems.append(f"binding `{rule}` cites no axiom")
        for axiom in cited:
            if axiom not in axiom_ids:
                problems.append(f"binding `{rule}` cites axiom `{axiom}` which is not in {data['axioms_doc']}")
        if not (b.get("derivation") or "").strip():
            problems.append(f"binding `{rule}` has no derivation")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except FileNotFoundError as exc:
        print(f"AXIOM_BINDING_BLOCKED missing file: {exc}", flush=True)
        return 1
    if problems:
        print("AXIOM_BINDING_BLOCKED the corridor rule is not fully derived from the axioms:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "AXIOM_BINDING_OK every corridor rule is derived from a language-core axiom",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
