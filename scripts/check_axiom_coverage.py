#!/usr/bin/env python3
"""Axiom-coverage guard: every language-core axiom must have executable evidence.

my-lisp-constitution.lisp calls itself "the executable proof of
docs/language-core-axioms.md's project principles and axioms (G1-G8, S1-S3)".
That claim is only true if EVERY axiom is evidenced by at least one fixture in
tests/fixtures/conformance.lisp, and if no fixture carries an invented axiom id.

Fail-closed:
- a fixture axiom tag that is not an axiom declared in docs/language-core-axioms.md;
- an axiom declared in the doc with zero fixtures;
- no fixtures at all.

Exit 0 = AXIOM_COVERAGE_OK; exit 1 = AXIOM_COVERAGE_BLOCKED with reasons.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

DOC = "docs/language-core-axioms.md"
CONFORMANCE = "tests/fixtures/conformance.lisp"

DOC_AXIOM = re.compile(r"(?m)^###\s+([GS]\d+)\s")
FIXTURE_AXIOMS = re.compile(r"\(axioms \. \(([^)]*)\)\)")


def check(root: Path) -> list[str]:
    problems: list[str] = []
    doc = (root / DOC).read_text(encoding="utf-8")
    conf = (root / CONFORMANCE).read_text(encoding="utf-8")

    declared = set(DOC_AXIOM.findall(doc))
    if not declared:
        return [f"no axioms declared in {DOC}"]

    tagged: Counter[str] = Counter()
    for group in FIXTURE_AXIOMS.findall(conf):
        for axiom in group.split():
            tagged[axiom.strip()] += 1

    if not tagged:
        return [f"no fixture carries an (axioms . (...)) tag in {CONFORMANCE}"]

    for axiom in sorted(set(tagged) - declared):
        problems.append(
            f"fixture tag `{axiom}` is not an axiom declared in {DOC} "
            "(invented or misspelled axiom id)"
        )
    for axiom in sorted(declared - set(tagged)):
        problems.append(
            f"axiom `{axiom}` is declared in {DOC} but has NO fixture evidence "
            "in conformance.lisp (the 'executable proof' claim is false for it)"
        )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except FileNotFoundError as exc:
        print(f"AXIOM_COVERAGE_BLOCKED missing file: {exc}", flush=True)
        return 1
    if problems:
        print("AXIOM_COVERAGE_BLOCKED the axiom set and its fixture evidence disagree:", flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "AXIOM_COVERAGE_OK every declared axiom (G1-G8, S1-S3) is evidenced by a "
        "conformance fixture and every fixture tag is a declared axiom",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
