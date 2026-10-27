#!/usr/bin/env python3
"""Observe unqualified executable direct operands in Core4, without admission.

Contract 11.9: D1-D10 are binary domain words; only explicit D24+ numerical
objects may enter math. This structural audit is an exact *debt inventory*,
NOT a Lisp evaluator, D24 constructor, runtime parity proof, or codec.

The baseline is intentionally exact, not a ceiling: a proposed migration
must change both source and evidence together, in main, after independent
semantic tests. Silent reintroduction or relabeling fails closed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core4.lisp"
BASELINE = ROOT / "tests/data/core4-d24-direct-operand-baseline.json"
MATH_HEADS = frozenset({
    "01010", "01011", "10110", "10111", "11010", "11011",
    "001110", "001111",
})
# Capture precisely the Lisp-owned LENGTH accumulator's source-level seed,
# which is not itself syntactically a mathematical primitive call.
SEED_HEADS = frozenset({"length-onto"})
# Only explicit Lisp/D3 quote forms are proven inert at this reader stage.
# The abbreviated apostrophe reader surface is outside this narrow audit.
# D8:00000001 is now DOSEQ, not historical SID8 QUOTE. The
# current D3:001 and Ukrainian full projection are the inert heads.
QUOTE_HEADS = frozenset({"001", "як-є", "quote", "QUOTE"})
NUMERIC_TOKEN = re.compile(
    r"(?:[+-]?[0-9]+(?:/[+-]?[0-9]+)?(?:\.[0-9]+)?|#[bBoOdDxX][0-9a-fA-F]+)\Z"
)


def tokens(source: str):
    """Yield (lexeme, source line), suppressing comments and quoted strings."""
    line = 1
    index = 0
    while index < len(source):
        ch = source[index]
        if ch == "\n":
            line += 1
            index += 1
            continue
        if ch.isspace():
            index += 1
            continue
        if ch == ";":
            while index < len(source) and source[index] != "\n":
                index += 1
            continue
        if ch in "()":
            yield ch, line
            index += 1
            continue
        if ch == '"':
            starting_line = line
            index += 1
            closed = False
            while index < len(source):
                ch = source[index]
                if ch == "\\":
                    if index + 1 < len(source) and source[index + 1] == "\n":
                        line += 1
                    index += 2
                elif ch == '"':
                    index += 1
                    closed = True
                    break
                else:
                    if ch == "\n":
                        line += 1
                    index += 1
            if not closed:
                raise ValueError(f"unterminated string beginning at line {starting_line}")
            yield "<STRING>", starting_line
            continue
        first = index
        starting_line = line
        while (index < len(source)
               and not source[index].isspace()
               and source[index] not in '();"'):
            index += 1
        if index == first:
            raise ValueError(f"unsupported lexical character at line {line}")
        yield source[first:index], starting_line


def audit(source: str):
    """Identify direct scalar operands outside explicit quoted source data."""
    stack = []
    found = []
    for token, line in tokens(source):
        if token == "(":
            in_quote = False
            if stack:
                parent = stack[-1]
                items = parent["items"]
                parent_head = items[0][0] if items and items[0] else None
                in_quote = parent["quoted"] or parent_head in QUOTE_HEADS
            stack.append({"items": [], "quoted": in_quote})
        elif token == ")":
            if not stack:
                raise ValueError(f"unexpected closing parenthesis on line {line}")
            node = stack.pop()
            children = node["items"]
            head = children[0][0] if children and children[0] else None
            # Quoted SENS data may contain apparent operator-shaped forms,
            # but no mathematical call happens under this lexical boundary.
            if not node["quoted"] and (head in MATH_HEADS or head in SEED_HEADS):
                kind = "math" if head in MATH_HEADS else "seed"
                for argument_number, child in enumerate(children[1:], start=1):
                    if child is None:
                        continue
                    value, value_line = child
                    if NUMERIC_TOKEN.fullmatch(value):
                        key = f"{kind}|{head}|{argument_number}|{value}"
                        found.append({"key": key, "line": value_line})
            if stack:
                stack[-1]["items"].append(None)  # nested form, not a scalar
        elif stack:
            stack[-1]["items"].append((token, line))
    if stack:
        raise ValueError(f"unclosed source list (depth={len(stack)})")
    return found


def check(current, expected):
    counts = Counter(row["key"] for row in current)
    failures = []
    for key in sorted(set(counts) | set(expected)):
        actual = counts[key]
        wanted = expected[key]
        if actual != wanted:
            failures.append(f"{key}: current={actual}, pinned={wanted}")
    if failures:
        raise ValueError(
            "CORE4-D24-MIGRATION: source inventory changed without synchronized "
            "contract/evidence review; " + "; ".join(failures)
        )
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="fail closed when source differs from pinned inventory")
    args = parser.parse_args()
    try:
        source = SOURCE.read_text(encoding="utf-8")
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        if baseline.get("schema") != 1 or baseline.get("source") != "lib/core4.lisp":
            raise ValueError("unsupported or wrong-scope Core4 migration inventory")
        pinned = baseline["counts"]
        if not isinstance(pinned, dict) or any(
            not isinstance(key, str) or not isinstance(value, int) or value < 0
            for key, value in pinned.items()
        ):
            raise ValueError("invalid Core4 migration counter baseline")
        findings = audit(source)
        for hit in findings:
            print(f"lib/core4.lisp:{hit['line']}: {hit['key']}")
        print(f"CORE4-D24-MIGRATION: {len(findings)} unqualified direct "
              "operand/seed sites remain (SOURCE DEBT, NOT ADMITTED)")
        if args.check:
            check(findings, pinned)
            print("CORE4-D24-MIGRATION: inventory matches pinned baseline; "
                  "this is NOT runtime or release PASS")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("CORE4-D24-MIGRATION: BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
