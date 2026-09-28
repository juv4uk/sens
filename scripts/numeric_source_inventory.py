#!/usr/bin/env python3
"""Inventory numeric source spellings before the binary-first reader migration.

This tool is observational. It does not define SENS numeric semantics.
It scans tracked *.lisp files, ignores comments and string contents, and
classifies source tokens so #1614 can migrate them deliberately.

Exact eight-bit binary tokens are SENS function identities, never numbers.
Human presentation is out of scope: #1622 preserves exact-rational display.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent

SENS_FUNCTION = re.compile(r"^[01]{8}$")
SIGNED_INTEGER = re.compile(r"^[+-]?[0-9]+$")
RATIONAL = re.compile(r"^[+-]?[0-9]+/[+-]?[0-9]+$")
DECIMAL_OR_SCIENTIFIC = re.compile(
    r"^[+-]?(?:(?:[0-9]+(?:[.,][0-9]*)?)|(?:[.,][0-9]+))(?:[eE][+-]?[0-9]+)?$"
)


def tracked_lisp_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files", "-z", "*.lisp"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    )
    return [
        REPO_ROOT / raw.decode("utf-8")
        for raw in completed.stdout.split(b"\0")
        if raw
    ]


def source_tokens(text: str) -> Iterable[str]:
    """Yield Lisp tokens while ignoring semicolon comments and strings."""
    token: list[str] = []
    in_string = False
    escaped = False
    index = 0

    def flush() -> Iterable[str]:
        nonlocal token
        if token:
            value = "".join(token)
            token = []
            return (value,)
        return ()

    while index < len(text):
        ch = text[index]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            index += 1
            continue

        if ch == '"':
            yield from flush()
            in_string = True
            index += 1
            continue

        if ch == ";":
            yield from flush()
            newline = text.find("\n", index)
            if newline < 0:
                break
            index = newline + 1
            continue

        if ch.isspace() or ch in "()":
            yield from flush()
        else:
            token.append(ch)
        index += 1

    yield from flush()


def bucket(path: Path) -> str:
    rel = path.relative_to(REPO_ROOT).as_posix()
    if rel.startswith("lib/generated/"):
        return "generated"
    if rel.startswith("lib/"):
        return "active-lib"
    if rel.startswith("scripts/"):
        return "tooling"
    if rel.startswith("contracts/"):
        return "contracts"
    if rel.startswith("knowledge/"):
        return "knowledge"
    if rel.startswith("tests/fixtures/"):
        return "fixtures"
    if "/" not in rel:
        return "root"
    return "other"


def classify(token: str) -> str | None:
    if SENS_FUNCTION.fullmatch(token):
        return "sens-function"

    if RATIONAL.fullmatch(token):
        return "rational-literal"

    if SIGNED_INTEGER.fullmatch(token):
        unsigned = token[1:] if token[:1] in "+-" else token
        if set(unsigned) <= {"0", "1"}:
            if len(unsigned) == 1:
                return "base-neutral-single-bit-number"
            return "binary-shaped-multibit-number"
        return "decimal-integer-needs-migration"

    if DECIMAL_OR_SCIENTIFIC.fullmatch(token) and any(ch in token for ch in ".,eE"):
        return "decimal-fraction-or-exponent-needs-policy"

    return None


def inventory(files: Iterable[Path]) -> dict:
    category_counts: Counter[str] = Counter()
    category_files: dict[str, set[str]] = defaultdict(set)
    bucket_counts: dict[str, Counter[str]] = defaultdict(Counter)
    examples: dict[str, list[dict[str, str]]] = defaultdict(list)

    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        path_bucket = bucket(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in source_tokens(text):
            category = classify(token)
            if category is None:
                continue
            category_counts[category] += 1
            category_files[category].add(rel)
            bucket_counts[path_bucket][category] += 1
            if len(examples[category]) < 24:
                examples[category].append({"path": rel, "token": token})

    categories = {}
    for category in sorted(category_counts):
        categories[category] = {
            "tokens": category_counts[category],
            "files": len(category_files[category]),
            "examples": examples[category],
        }

    return {
        "schema": 1,
        "scope": "tracked-*.lisp",
        "authority": "observation-only",
        "categories": categories,
        "buckets": {
            name: dict(sorted(counts.items()))
            for name, counts in sorted(bucket_counts.items())
        },
    }


def print_summary(data: dict) -> None:
    print("NUMERIC SOURCE INVENTORY")
    print("=" * 72)
    print("authority: observation-only")
    for category, item in data["categories"].items():
        print(
            f"{category}: tokens={item['tokens']} files={item['files']}"
        )
    print()
    print("migration-sensitive categories:")
    for category in (
        "binary-shaped-multibit-number",
        "decimal-integer-needs-migration",
        "decimal-fraction-or-exponent-needs-policy",
        "rational-literal",
    ):
        item = data["categories"].get(category, {"tokens": 0, "files": 0})
        print(f"  {category}: tokens={item['tokens']} files={item['files']}")


def self_test() -> int:
    sample = r"""
; 42 101 00001100 ignored in comment
(00001100 10 101 42 1/2 3.5 1e3 "99 111")
"""
    got = [(token, classify(token)) for token in source_tokens(sample)]
    expected = [
        ("00001100", "sens-function"),
        ("10", "binary-shaped-multibit-number"),
        ("101", "binary-shaped-multibit-number"),
        ("42", "decimal-integer-needs-migration"),
        ("1/2", "rational-literal"),
        ("3.5", "decimal-fraction-or-exponent-needs-policy"),
        ("1e3", "decimal-fraction-or-exponent-needs-policy"),
    ]
    if got != expected:
        print("SELF-TEST FAILED", file=sys.stderr)
        print(f"expected: {expected!r}", file=sys.stderr)
        print(f"got:      {got!r}", file=sys.stderr)
        return 1
    print("numeric source inventory self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    data = inventory(tracked_lisp_files())
    if args.json:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
        print()
    else:
        print_summary(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
