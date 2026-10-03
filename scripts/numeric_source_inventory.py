#!/usr/bin/env python3
"""Inventory numeric/domain source spellings during exact-domain migration.

This tool is observational; parser/domain contracts define semantics.

Bare W3-W6 tokens are canonical Core domain words, not numeric migration debt.
Historical bare W8 tokens are no longer canonical source under #2817 and are
tracked as legacy Function8 source debt that may only decrease.
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

CORE_DOMAIN_WORD = re.compile(r"^[01]{3,6}$")
LEGACY_FUNCTION8 = re.compile(r"^[01]{8}$")
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


def source_token_locations(text: str) -> Iterable[tuple[str, int]]:
    """Yield (token, one-based line) while ignoring comments and strings."""
    token: list[str] = []
    token_line = 1
    line = 1
    in_string = False
    escaped = False
    index = 0

    def flush() -> Iterable[tuple[str, int]]:
        nonlocal token
        if token:
            value = "".join(token)
            token = []
            return ((value, token_line),)
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
            if ch == "\n":
                line += 1
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
            line += 1
            index = newline + 1
            continue

        if ch.isspace() or ch in "()":
            yield from flush()
            if ch == "\n":
                line += 1
        else:
            if not token:
                token_line = line
            token.append(ch)
        index += 1

    yield from flush()


def source_tokens(text: str) -> Iterable[str]:
    for token, _line in source_token_locations(text):
        yield token


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
    if CORE_DOMAIN_WORD.fullmatch(token):
        return "core-domain-word"

    if LEGACY_FUNCTION8.fullmatch(token):
        return "legacy-function8-source-debt"

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


def list_category(files: Iterable[Path], category: str, bucket_name: str | None) -> int:
    count = 0
    for path in files:
        if bucket_name is not None and bucket(path) != bucket_name:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for token, line in source_token_locations(text):
            if classify(token) == category:
                print(f"{rel}:{line}:{token}")
                count += 1
    print(f"TOTAL {category} bucket={bucket_name or 'all'} count={count}")
    return 0


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
    for category in MIGRATION_SENSITIVE:
        item = data["categories"].get(category, {"tokens": 0, "files": 0})
        print(f"  {category}: tokens={item['tokens']} files={item['files']}")

    print()
    print("migration-sensitive tokens by bucket:")
    for bucket_name, counts in data["buckets"].items():
        rendered = " ".join(
            f"{category}={counts.get(category, 0)}"
            for category in MIGRATION_SENSITIVE
        )
        print(f"  {bucket_name}: {rendered}")


MIGRATION_SENSITIVE = (
    "legacy-function8-source-debt",
    "binary-shaped-multibit-number",
    "decimal-integer-needs-migration",
    "decimal-fraction-or-exponent-needs-policy",
    "rational-literal",
)


def check_baseline(data: dict, baseline_path: Path) -> int:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    for category in MIGRATION_SENSITIVE:
        current = data["categories"].get(category, {}).get("tokens", 0)
        ceiling = baseline["categories"].get(category, 0)
        if current > ceiling:
            failures.append(
                f"category {category}: current={current} exceeds ceiling={ceiling}"
            )

    all_buckets = set(data["buckets"]) | set(baseline.get("buckets", {}))
    for bucket_name in sorted(all_buckets):
        current_counts = data["buckets"].get(bucket_name, {})
        ceiling_counts = baseline.get("buckets", {}).get(bucket_name, {})
        for category in MIGRATION_SENSITIVE:
            if category not in ceiling_counts:
                continue
            current = current_counts.get(category, 0)
            ceiling = ceiling_counts[category]
            if current > ceiling:
                failures.append(
                    f"bucket {bucket_name}/{category}: "
                    f"current={current} exceeds ceiling={ceiling}"
                )

    if failures:
        print("NUMERIC SOURCE INVENTORY DRIFT DETECTED", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        print(
            "Migration-sensitive numeric source debt may decrease, but must not grow.",
            file=sys.stderr,
        )
        return 1

    print("numeric source inventory baseline: PASS")
    for category in MIGRATION_SENSITIVE:
        current = data["categories"].get(category, {}).get("tokens", 0)
        ceiling = baseline["categories"].get(category, 0)
        print(f"  {category}: {current}/{ceiling}")
    return 0


def check_active_routes(files: Iterable[Path], routes_path: Path) -> int:
    routes = json.loads(routes_path.read_text(encoding="utf-8"))
    allowed_routes = {
        "preserve-numeric-value",
        "typed-machine-notation",
        "regenerate-from-authority",
    }

    live: Counter[tuple[str, str]] = Counter()
    for path in files:
        if bucket(path) != "active-lib":
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for token, _line in source_token_locations(text):
            if classify(token) == "binary-shaped-multibit-number":
                live[(rel, token)] += 1

    declared: Counter[tuple[str, str]] = Counter()
    failures: list[str] = []
    for row in routes.get("rows", []):
        path = row.get("path")
        token = row.get("token")
        route = row.get("route")
        if route not in allowed_routes:
            failures.append(f"invalid route {route!r} for {path}:{token}")
        if not isinstance(path, str) or not isinstance(token, str):
            failures.append(f"malformed route row: {row!r}")
            continue
        declared[(path, token)] += 1

    if live != declared:
        for key in sorted(set(live) | set(declared)):
            if live[key] != declared[key]:
                failures.append(
                    f"coverage {key[0]} token={key[1]}: "
                    f"live={live[key]} declared={declared[key]}"
                )

    if failures:
        print("ACTIVE-LIB NUMERAL ROUTE COVERAGE FAILED", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(f"active-lib numeral routes: PASS ({sum(live.values())} occurrences)")
    return 0


def self_test() -> int:
    sample = r"""
; 42 101 00001100 ignored in comment
(00001100 10 101 42 1/2 3.5 1e3 "99 111")
"""
    got = [(token, classify(token)) for token in source_tokens(sample)]
    expected = [
        ("00001100", "legacy-function8-source-debt"),
        ("10", "binary-shaped-multibit-number"),
        ("101", "core-domain-word"),
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
    parser.add_argument(
        "--check-baseline",
        type=Path,
        metavar="PATH",
        help="fail if migration-sensitive counts exceed the recorded ceilings",
    )
    parser.add_argument(
        "--list-category",
        metavar="CATEGORY",
        help="print every matching path:line:token occurrence",
    )
    parser.add_argument(
        "--bucket",
        metavar="BUCKET",
        help="optional path bucket filter for --list-category",
    )
    parser.add_argument(
        "--check-active-routes",
        type=Path,
        metavar="PATH",
        help="verify that active-lib binary-shaped numerals are fully routed",
    )
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    files = tracked_lisp_files()
    if args.list_category:
        return list_category(files, args.list_category, args.bucket)
    if args.check_active_routes:
        return check_active_routes(files, args.check_active_routes)

    data = inventory(files)
    if args.check_baseline:
        result = check_baseline(data, args.check_baseline)
        if result != 0:
            return result
    if args.json:
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
        print()
    else:
        print_summary(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
