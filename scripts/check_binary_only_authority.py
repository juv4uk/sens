#!/usr/bin/env python3
"""#1707 binary-only semantic-authority ratchet.

This tool is mechanism-only. It does not define SENS semantics.
The TSV policy classifies known non-binary host representations on active
Rust language/runtime paths. Existing classified debt may decrease but must
not grow; a known smell in an unclassified path fails closed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_POLICY = ROOT / "evidence" / "binary-only-authority-baseline.tsv"
ALLOWED = {
    "human-boundary",
    "debug",
    "provenance",
    "transition-debt",
    "mechanism-private",
    "violation",
}


@dataclass(frozen=True)
class Rule:
    pattern_id: str
    pattern: re.Pattern[str]
    path: re.Pattern[str]
    classification: str
    owner: str
    target: str


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=True,
    )


def read_rules(path: Path) -> list[Rule]:
    rules: list[Rule] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw or raw.startswith("#"):
            continue
        cols = raw.split("\t")
        if len(cols) != 6:
            raise ValueError(f"{path}:{line_no}: expected 6 TSV columns")
        pattern_id, regex, path_regex, classification, owner, target = cols
        if classification not in ALLOWED:
            raise ValueError(f"{path}:{line_no}: bad classification {classification!r}")
        rules.append(
            Rule(
                pattern_id,
                re.compile(regex),
                re.compile(path_regex),
                classification,
                owner,
                target,
            )
        )
    if not rules:
        raise ValueError(f"{path}: no rules")
    by_id: dict[str, str] = {}
    for rule in rules:
        previous = by_id.setdefault(rule.pattern_id, rule.pattern.pattern)
        if previous != rule.pattern.pattern:
            raise ValueError(
                f"{path}: pattern_id {rule.pattern_id!r} has multiple regexes"
            )
    return rules


def tracked_runtime_files() -> list[str]:
    out = git("ls-files", "-z", "crates/sens/src").stdout
    return sorted(p for p in out.split("\0") if p.endswith(".rs"))


def current_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def base_text(base: str, path: str) -> str:
    proc = git("show", f"{base}:{path}", check=False)
    return proc.stdout if proc.returncode == 0 else ""


def count(rule: Rule, source: str) -> int:
    return sum(1 for _ in rule.pattern.finditer(source))


def check(base: str, rules: list[Rule]) -> int:
    failures: list[str] = []
    groups: dict[str, list[Rule]] = {}
    row_totals: dict[Rule, int] = {r: 0 for r in rules}
    for rule in rules:
        groups.setdefault(rule.pattern_id, []).append(rule)

    for path in tracked_runtime_files():
        now = current_text(path)
        before = base_text(base, path)

        for pattern_id, group in groups.items():
            probe = group[0]
            now_count = count(probe, now)
            if not now_count:
                continue

            matching = [rule for rule in group if rule.path.fullmatch(path)]
            if not matching:
                failures.append(
                    f"UNCLASSIFIED {pattern_id}: {path} has {now_count} match(es)"
                )
                continue
            if len(matching) != 1:
                failures.append(
                    f"AMBIGUOUS {pattern_id}: {path} matches {len(matching)} classifications"
                )
                continue

            rule = matching[0]
            row_totals[rule] += now_count
            before_count = count(probe, before)
            if now_count > before_count:
                failures.append(
                    f"GROWTH {pattern_id}: {path} {before_count} -> {now_count} "
                    f"[{rule.classification}, owner={rule.owner}, target={rule.target}]"
                )

            if rule.classification == "violation":
                failures.append(
                    f"VIOLATION {pattern_id}: {path} has {now_count} match(es)"
                )

    print("BINARY-ONLY AUTHORITY INVENTORY")
    for rule in rules:
        print(
            f"{rule.pattern_id}\t{row_totals[rule]}\t"
            f"{rule.classification}\t{rule.owner}\t{rule.target}\t"
            f"path={rule.path.pattern}"
        )

    if failures:
        print("BINARY-ONLY AUTHORITY RATCHET FAILED", file=sys.stderr)
        for item in failures:
            print(f"  - {item}", file=sys.stderr)
        print(
            "Classified debt may decrease but must not grow. "
            "New non-binary authority needs an explicit reviewed classification.",
            file=sys.stderr,
        )
        return 1

    print("binary-only authority ratchet: PASS")
    return 0


def self_test() -> int:
    rule = Rule(
        "symbol",
        re.compile(r"ExprKind::Symbol"),
        re.compile(r"^crates/sens/src/.*[.]rs$"),
        "transition-debt",
        "#1696",
        "zero",
    )
    if count(rule, "ExprKind::Symbol(x); ExprKind::Number(y)") != 1:
        print("self-test count failed", file=sys.stderr)
        return 1
    if not rule.path.fullmatch("crates/sens/src/parser.rs"):
        print("self-test path failed", file=sys.stderr)
        return 1
    if rule.path.fullmatch("tests/parser.rs"):
        print("self-test path scope failed", file=sys.stderr)
        return 1
    print("binary-only authority self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", help="git revision to compare against")
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if not args.base:
        parser.error("--base is required unless --self-test is used")

    return check(args.base, read_rules(args.policy))


if __name__ == "__main__":
    raise SystemExit(main())
