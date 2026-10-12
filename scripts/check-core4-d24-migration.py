#!/usr/bin/env python3
"""Observe unqualified source operands in pinned Core4, without admitting them.

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
NUMERIC_TOKEN = re.compile(
    r"(?:[+-]?[0-9]+(?:/[+-]?[0-9]+)?(?:\\.[0-9]+)?|#[bBoOdDxX][0-9a-fA-F]+)\\Z"
)


def tokens(source: str):
    """Yield (lexeme, source line), suppressing comments and quoted strings."""
    line = 1
    index = 0
    while index < len(source):
        ch = source[index]
        if ch == "\\n":
            line += 1
            index += 1
            continue
        if ch.isspace():
            index += 1
            continue
        if ch == ";":
            while index < len(source) and source[index] != "\\n":
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
                if ch == "\\\\":
                    if index + 1 < len(source) and source[index + 1] == "\\n":
                        line += 1
                    index += 2
                elif ch == '"':
                    index += 1
                    closed = True
                    break
                else:
                    if ch == "\\n":
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
    """Identify only *direct* scalar arguments; nested calls stay distinct."""
    stack = []
    found = []
    for token, line in tokens(source):
        if token == "(":
            stack.append([])
        elif token == ")":
            if not stack:
                raise ValueError(f"unexpected closing parenthesis on line {line}")
            children = stack.pop()
            head = children[0][0] if children and children[0] else None
            if head in MATH_HEADS or head in SEED_HEADS:
                kind = "math" if head in MATH_HEADS else "seed"
                for argument_number, child in enumerate(children[1:], start=1):
                    if child is None:
                        continue
                    value, value_line = child
                    if NUMERIC_TOKEN.fullmatch(value):
                        key = f"{kind}|{head}|{argument_number}|{value}"
                        found.append({"key": key, "line": value_line})
            if stack:
                stack[-1].append(None)  # nested expression, not a scalar token
        elif stack:
            stack[-1].append((token, line))
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


def self_test():
    sample = (
        '; (01010 ignored 1)\\n'
        '(0011 f (0010 (a) (01010 a 1)))\\n'
        '(01011 (10110 a b) #d10)\\n'
        '(length-onto xs 0)\\n'
        '(01010 "<string with 2 and (01011 a 8)>" a)\\n'
    )
    actual = audit(sample)
    expected = Counter({
        "math|01010|2|1": 1,
        "math|01011|2|#d10": 1,
        "seed|length-onto|2|0": 1,
    })
    check(actual, expected)
    for damaged in (
        sample + "(01010 a 1)\\n",  # same key, increased count
        sample + "(01010 a 2)\\n",  # novel numeric spelling
        sample + "(length-onto xs 0)\\n",  # helper seed reintroduced
    ):
        try:
            check(audit(damaged), expected)
        except ValueError:
            pass
        else:
            raise ValueError("negative drift test admitted an unreviewed number")
    for invalid in ("(01010 x 1", "(01010 x 1))", '(01010 "unclosed)'):
        try:
            audit(invalid)
        except ValueError:
            pass
        else:
            raise ValueError("malformed Core4 source escaped the lexer")
    print("CORE4-D24-MIGRATION: self-test PASS (structural negative controls)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check", action="store_true",
                        help="fail closed when source differs from pinned inventory")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
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
