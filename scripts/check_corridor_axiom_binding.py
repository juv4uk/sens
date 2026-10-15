#!/usr/bin/env python3
"""Axiom binding guard: every corridor rule is DERIVED from a language-core axiom.

Uses our axioms (docs/language-core-axioms.md). The corridor rule
"Rust<->SENS crosses only the sterile Zig corridor" (#5777/#5779) must not be an
ad-hoc assertion: each guard rule is bound to the axiom it follows from.

Fail-closed:
- each known corridor rule has exactly one binding to its actual guard;
- unknown, duplicate, or unguarded rules are rejected;
- the cited axiom source is pinned, not replaceable with another document;
- every cited axiom id must exist and every binding needs a derivation.

Exit 0 = AXIOM_BINDING_OK; exit 1 = AXIOM_BINDING_BLOCKED with reasons.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BINDING = "research/zig-codecs/corridor_axioms.json"
AXIOMS_DOC = "docs/language-core-axioms.md"
SCHEMA = "sens-corridor-axiom-binding/v1"
AXIOM_ID = re.compile(r"^###\s+([GS]\d+)\s", re.M)

# Physical guard provenance, not a second language/semantic registry.
EXPECTED_RULES = {
    "R1-corridor-default-on": "scripts/check_sterile_zig_corridor.py",
    "R2-build-requires-zig": "scripts/check_sterile_zig_corridor.py",
    "R3-physical-only-abi": "scripts/check_rust_sens_zig_corridor.py",
    "R4-pinned-corridor-version": "scripts/check_rust_sens_zig_corridor.py",
    "R5-host-neutral": "scripts/check_rust_sens_zig_corridor.py",
    "S1-physical-only-exports": "scripts/check_sterile_zig_corridor.py",
    "S2-no-semantic-import": "scripts/check_sterile_zig_corridor.py",
    "S3-no-host-struct": "scripts/check_sterile_zig_corridor.py",
    "S4-sterility-contract-declared": "scripts/check_sterile_zig_corridor.py",
    "C1-host-coverage": "scripts/check_rust_sens_corridor_coverage.py",
}


def _unique_object_keys(pairs: list[tuple[str, object]]) -> dict:
    """Reject ambiguous JSON identity at every nesting level, not only at root."""
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r} in corridor axiom binding")
        result[key] = value
    return result


def check(root: Path) -> list[str]:
    problems: list[str] = []
    binding_path = root / BINDING
    if not binding_path.is_file() or binding_path.is_symlink():
        return [f"binding `{BINDING}` is missing or not a regular file"]
    data = json.loads(binding_path.read_text(encoding="utf-8"),
                      object_pairs_hook=_unique_object_keys)
    if not isinstance(data, dict):
        return ["corridor axiom binding root must be an object"]
    if data.get("schema") != SCHEMA:
        problems.append(f"corridor axiom binding schema is not {SCHEMA}")
    if data.get("axioms_doc") != AXIOMS_DOC:
        problems.append(f"corridor axiom source must be pinned to `{AXIOMS_DOC}`")
        return problems

    axioms_doc = root / AXIOMS_DOC
    if not axioms_doc.is_file() or axioms_doc.is_symlink():
        return problems + [f"axioms doc `{AXIOMS_DOC}` is missing or not regular"]
    axiom_ids = set(AXIOM_ID.findall(axioms_doc.read_text(encoding="utf-8")))

    bindings = data.get("bindings")
    if not isinstance(bindings, list):
        return problems + ["corridor axiom bindings must be a list"]
    bound_rules: set[str] = set()
    for index, b in enumerate(bindings):
        if not isinstance(b, dict):
            problems.append(f"binding at index {index} must be an object")
            continue
        rule = b.get("rule")
        if not isinstance(rule, str) or rule not in EXPECTED_RULES:
            problems.append(f"unknown corridor rule at index {index}: {rule!r}")
            continue
        if rule in bound_rules:
            problems.append(f"corridor rule `{rule}` has duplicate bindings")
        bound_rules.add(rule)
        guard = b.get("guard")
        expected_guard = EXPECTED_RULES[rule]
        if guard != expected_guard:
            problems.append(f"binding `{rule}` must use its actual guard: {expected_guard}")
        else:
            guard_path = root / guard
            if not guard_path.is_file() or guard_path.is_symlink():
                problems.append(f"binding `{rule}` names a guard that does not exist as a regular file: {guard}")
        cited = b.get("axioms")
        if not isinstance(cited, list) or not cited:
            problems.append(f"binding `{rule}` cites no axiom list")
        else:
            for axiom in cited:
                if not isinstance(axiom, str) or axiom not in axiom_ids:
                    problems.append(f"binding `{rule}` cites unknown axiom `{axiom}` in {AXIOMS_DOC}")
        derivation = b.get("derivation")
        if not isinstance(derivation, str) or not derivation.strip():
            problems.append(f"binding `{rule}` has no derivation")
    for rule in sorted(EXPECTED_RULES.keys() - bound_rules):
        problems.append(f"corridor rule `{rule}` is not bound to any axiom")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"AXIOM_BINDING_BLOCKED malformed input: {exc}", flush=True)
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
