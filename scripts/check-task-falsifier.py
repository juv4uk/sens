#!/usr/bin/env python3
"""Conservative semantic-quality judge for FALSIFIER task fields (#2532).

This checker consumes canonical records parsed by task_schema_record.py.
It does not parse Markdown independently and it does not try to understand
domain semantics.

Verdicts:
  ok              explicit observation/condition that could defeat the LAW
  empty           field is structurally present but blank
  placeholder     TODO/TBD/"test more"/similar
  restatement     repeats the LAW instead of attacking it
  non-falsifying  command/positive-example only, no failure condition
  unknown         prose is non-empty but not safe to classify mechanically

UNKNOWN is deliberate: CI must not invent semantic understanding.
"""

from __future__ import annotations

import re
import sys

from task_schema_record import parse_record, structural_verdict


_SPACE = re.compile(r"\s+")
_PUNCT = re.compile(r"[\x60*_#]+")
_PLACEHOLDER = re.compile(
    r"^(?:todo|tbd|fixme|test more|more testing|check ci|verify law|"
    r"needs testing|pending)$",
    re.I,
)
_EXPLICIT_UNKNOWN = re.compile(
    r"^(?:unknown|unresolved|not yet known|not yet determined|pending evidence)$",
    re.I,
)
_COMMAND_ONLY = re.compile(
    r"^(?:(?:run|execute|check)\s+)?(?:cargo\s+test|pytest|python3?\b.*|"
    r"gh\s+workflow\b.*|ci|tests?)\s*[.;]?$",
    re.I,
)
_POSITIVE_ONLY = re.compile(
    r"^(?:positive\s+example|example|witness)\s*:\s*.+$",
    re.I,
)

# This is intentionally a syntax-level gate, not semantic NLP.
# Accepted text must name a counter-condition or failure observation.
_DISPROOF_SIGNAL = re.compile(
    r"\b(?:falsif(?:y|ied|ies)|counterexample|fails?\s+if|"
    r"reject(?:ed)?\s+if|breaks?\s+if|would\s+fail\s+if|"
    r"disproved?\s+if|must\s+fail\s+when|if\b.+\bthen\b.+\bfail|"
    r"if\b.+(?:!=|≠|changes?|collides?|diverges?|becomes?|accepts?|rejects?))",
    re.I,
)


def _norm(text: str) -> str:
    text = _PUNCT.sub("", text or "")
    text = text.strip(" \t\r\n.;:")
    return _SPACE.sub(" ", text).lower()


def falsifier_verdict(law: str, falsifier: str) -> str:
    raw = (falsifier or "").strip()
    if not raw:
        return "empty"

    norm = _norm(raw)
    law_norm = _norm(law or "")

    if _EXPLICIT_UNKNOWN.fullmatch(norm):
        return "unknown"
    if _PLACEHOLDER.fullmatch(norm):
        return "placeholder"
    if law_norm and norm == law_norm:
        return "restatement"

    # Trivial wrappers do not become falsifiers merely by adding "not".
    if law_norm and norm in {
        f"not {law_norm}",
        f"law fails {law_norm}",
        f"the law fails {law_norm}",
        f"falsify {law_norm}",
    }:
        return "restatement"

    if _COMMAND_ONLY.fullmatch(norm):
        return "non-falsifying"
    if _POSITIVE_ONLY.fullmatch(raw) and not _DISPROOF_SIGNAL.search(raw):
        return "non-falsifying"

    if _DISPROOF_SIGNAL.search(raw):
        return "ok"

    return "unknown"


def record_verdict(body: str) -> str | None:
    record = parse_record(body or "")
    if not record.marked:
        return None

    if structural_verdict(record, "FALSIFIER") != "OK":
        # Structure checker owns missing/duplicate/empty. Keep only empty here
        # when a unique field exists but has no payload.
        rows = record.occurrences.get("FALSIFIER", ())
        if len(rows) == 1 and not rows[0].value.strip():
            return "empty"
        return None

    law_rows = record.occurrences.get("LAW", ())
    fal_rows = record.occurrences.get("FALSIFIER", ())
    law = law_rows[0].value if len(law_rows) == 1 else ""
    return falsifier_verdict(law, fal_rows[0].value)


def self_test() -> int:
    cases = [
        ("x -> y", "", "empty"),
        ("x -> y", "TBD", "placeholder"),
        ("x -> y", "test more", "placeholder"),
        ("x -> y", "check CI", "placeholder"),
        ("x -> y", "x -> y", "restatement"),
        ("x -> y", "not x -> y", "restatement"),
        ("x -> y", "run cargo test", "non-falsifying"),
        ("x -> y", "example: x=1 gives y=2", "non-falsifying"),
        ("x -> y", "UNKNOWN", "unknown"),
        (
            "axis refinements commute",
            "FALSIFIED if swapping refinement order changes the endpoint",
            "ok",
        ),
        (
            "same bits do not imply same domain law",
            "counterexample: cross-domain apply accepts instead of DOMAIN-MISMATCH",
            "ok",
        ),
        (
            "coordinate law is permutation-stable",
            "reject if an admissible relabel changes the claimed invariant",
            "ok",
        ),
        ("x -> y", "compare three implementations", "unknown"),
    ]

    failures = 0
    for law, fal, expected in cases:
        got = falsifier_verdict(law, fal)
        ok = got == expected
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] {got:15} expected={expected:15} {fal!r}")

    body = """## BINARY-DOMAIN RECORD
DOMAIN: D5
BINARY OBJECT: 00101
LAW: two axes commute
WITNESS: #1
FALSIFIER: fails if reversing axis order changes the endpoint
STATUS: hypothesis
RELATION: Core-only
"""
    assert record_verdict(body) == "ok"

    legacy = "LAW: x\nFALSIFIER: fails if x changes\n"
    assert record_verdict(legacy) is None

    if failures:
        print(f"FALSIFIER-QUALITY-SELFTEST=FAIL failures={failures}")
        return 1
    print("FALSIFIER-QUALITY-SELFTEST=PASS")
    print("AMBIGUOUS-PROSE=UNKNOWN")
    print("PARSER=task_schema_record.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(self_test())
