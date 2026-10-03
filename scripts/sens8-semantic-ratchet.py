#!/usr/bin/env python3
"""#2835 — classify and ratchet live Sens8/Sid8 semantic debt.

Migration hygiene only. This scanner does not define language meaning.

Existing semantic debt may stay flat or shrink in files changed by a PR; it may
not grow. The exact-width paradigm one-way guard separately forbids adding
legacy identity dependencies to exact-width Rust surfaces.
"""

from __future__ import annotations

import argparse
import collections
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

LEGACY_RE = re.compile(
    r"\b(?:Sens8|Sid8|Function8)\b|sens!\([01]{8}\)"
)

TEXT_SUFFIXES = {
    ".rs", ".py", ".sh", ".lisp", ".md", ".yml", ".yaml",
    ".json", ".toml", ".txt",
}
SKIP_DIRS = {".git", "target", "node_modules", "vendor", "dist", "build"}

EXPLICIT_COMPATIBILITY = {
    "crates/sens/src/sens.rs",
    "crates/sens/src/sid.rs",
}

BACKEND_MECHANISM = {
    "crates/sens/src/eval/capabilities.rs",
    "crates/sens-cli/src/island_invoke.rs",
}

GUARD_POLICY = {
    "scripts/domain-paradigm-one-way-guard.sh",
    "scripts/test-domain-paradigm-one-way-guard.sh",
    "scripts/sid-binary-identity-guard.sh",
    "scripts/sens8-semantic-ratchet.py",
    ".github/workflows/ci.yml",
}


def norm(path: str) -> str:
    return path.replace("\\", "/")


def classify(path: str, line: str) -> str:
    path = norm(path)
    stripped = line.lstrip()

    # Pure comments/documentation are provenance, not executable dependency.
    # Tests and string literals remain visible because they can encode live
    # authority; only comment-only lines are excluded from semantic debt.
    if stripped.startswith(("//", "/*", "*", ";;")):
        return "historical-doc"

    if path in EXPLICIT_COMPATIBILITY:
        return "compatibility"
    if path in GUARD_POLICY:
        return "guard-policy"

    if path == "crates/sens/src/binary_framing.rs":
        return "transport-backend"

    # syntax.rs is mixed: legacy FASL/wire byte mechanics are transport, while
    # ExprKind::Sid/Call and reader identity are still semantic migration debt.
    if path == "crates/sens/src/syntax.rs" and re.search(
        r"TAG_BINARY|packed_byte|from_packed_byte|\bfasl\b|\bwire\b",
        line,
        re.IGNORECASE,
    ):
        return "transport-backend"

    if path in BACKEND_MECHANISM:
        return "backend-mechanism"

    if (
        path.startswith("docs/research/")
        or path.startswith("docs/reports/")
        or path.startswith("evidence/")
        or path == "README.md"
    ):
        return "historical-doc"

    # Fail closed for live source/tooling/authority. A narrower compatibility
    # lane must be named explicitly above rather than inferred from spelling.
    if (
        path.startswith("crates/")
        or path.startswith("lib/")
        or path.startswith("contracts/")
        or path.startswith("knowledge/")
        or path.startswith("scripts/")
    ):
        return "semantic-blocker"

    return "historical-doc"


def matching_tokens(line: str) -> tuple[str, ...]:
    return tuple(match.group(0) for match in LEGACY_RE.finditer(line))


def scan_text(path: str, text: str):
    for number, line in enumerate(text.splitlines(), 1):
        tokens = matching_tokens(line)
        if not tokens:
            continue
        yield {
            "path": norm(path),
            "line": number,
            "class": classify(path, line),
            "tokens": tokens,
            "snippet": line.strip(),
        }


def walk_worktree():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if path.suffix not in TEXT_SUFFIXES and path.name != "README.md":
                continue
            rel = path.relative_to(ROOT).as_posix()
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            yield from scan_text(rel, content)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def changed_paths(base: str, head: str) -> list[str]:
    proc = git("diff", "--name-only", "--no-renames", base, head)
    return [line for line in proc.stdout.splitlines() if line]


def text_at(ref: str, path: str) -> str | None:
    proc = git("show", f"{ref}:{path}", check=False)
    return proc.stdout if proc.returncode == 0 else None


def scan_ref_paths(ref: str, paths: list[str]):
    for path in paths:
        if Path(path).suffix not in TEXT_SUFFIXES and path != "README.md":
            continue
        content = text_at(ref, path)
        if content is not None:
            yield from scan_text(path, content)


def blocker_count(records) -> int:
    return sum(
        len(row["tokens"])
        for row in records
        if row["class"] == "semantic-blocker"
    )


def render_summary(records) -> str:
    classes = collections.Counter()
    blockers = collections.Counter()

    for row in records:
        classes[row["class"]] += len(row["tokens"])
        if row["class"] == "semantic-blocker":
            blockers[row["path"]] += len(row["tokens"])

    lines = ["SENS8_SEMANTIC_INVENTORY\tclass\toccurrences"]
    for cls in (
        "semantic-blocker",
        "compatibility",
        "transport-backend",
        "backend-mechanism",
        "guard-policy",
        "historical-doc",
    ):
        lines.append(f"SENS8_SEMANTIC_INVENTORY\t{cls}\t{classes[cls]}")

    for path, count in blockers.most_common():
        lines.append(f"SENS8_SEMANTIC_BLOCKER\t{path}\t{count}")

    return "\n".join(lines)


def inventory_mode() -> int:
    print("class\tpath\tline\ttokens\tsnippet")
    for row in walk_worktree():
        tokens = ",".join(row["tokens"])
        snippet = row["snippet"].replace("\t", " ")
        print(
            f"{row['class']}\t{row['path']}\t{row['line']}\t"
            f"{tokens}\t{snippet}"
        )
    return 0


def diff_mode(base: str, head: str) -> int:
    git("rev-parse", "--verify", f"{base}^{{commit}}")
    git("rev-parse", "--verify", f"{head}^{{commit}}")

    paths = changed_paths(base, head)
    before = list(scan_ref_paths(base, paths))
    after = list(scan_ref_paths(head, paths))

    before_count = blocker_count(before)
    after_count = blocker_count(after)

    print(
        f"SENS8-SEMANTIC-RATCHET changed_files={len(paths)} "
        f"semantic_blockers={before_count}->{after_count}"
    )

    before_by = collections.Counter(
        row["path"]
        for row in before
        for _ in row["tokens"]
        if row["class"] == "semantic-blocker"
    )
    after_by = collections.Counter(
        row["path"]
        for row in after
        for _ in row["tokens"]
        if row["class"] == "semantic-blocker"
    )
    for path in sorted(set(before_by) | set(after_by)):
        if before_by[path] != after_by[path]:
            print(f"  {path}: {before_by[path]} -> {after_by[path]}")

    if after_count > before_count:
        print(
            "SENS8-SEMANTIC-RATCHET violation: semantic legacy identity debt grew",
            file=sys.stderr,
        )
        return 1

    print("SENS8-SEMANTIC-RATCHET: PASS")
    return 0


def self_test() -> int:
    cases = [
        ("crates/sens/src/sens.rs", "pub struct Sens8(u8);", "compatibility"),
        ("crates/sens/src/sid.rs", "pub type Sid8 = Sens8;", "compatibility"),
        (
            "crates/sens/src/binary_framing.rs",
            "fn encode(value: Sens8) {}",
            "transport-backend",
        ),
        (
            "crates/sens/src/syntax.rs",
            "TAG_BINARY => Sens8::from_packed_byte(byte)",
            "transport-backend",
        ),
        ("crates/sens/src/syntax.rs", "Sid(Sens8),", "semantic-blocker"),
        (
            "crates/sens/src/eval/lower.rs",
            "const QUOTE: Sens8 = crate::sens!(00000001);",
            "semantic-blocker",
        ),
        (
            "crates/sens/src/eval/capabilities.rs",
            "fn host(id: Sens8) {}",
            "backend-mechanism",
        ),
        ("docs/research/old.md", "Sens8 was the old identity", "historical-doc"),
        (
            "scripts/domain-paradigm-one-way-guard.sh",
            "legacy_pattern='Sens8|Sid8'",
            "guard-policy",
        ),
        (
            "crates/sens/src/domain_identity.rs",
            "/// No implicit conversion from Sens8.",
            "historical-doc",
        ),
    ]

    failures = 0
    for path, line, expected in cases:
        got = classify(path, line)
        ok = got == expected
        print(f"  [{'ok' if ok else 'FAIL'}] {path}: {got}")
        failures += 0 if ok else 1

    if matching_tokens("Value::Sid(CallableIdentity::legacy8(1)) sens!(00000001)") != (
        "sens!(00000001)",
    ):
        failures += 1
        print("  [FAIL] token matcher")

    if failures:
        print(f"sens8-semantic-ratchet self-test: FAIL ({failures})")
        return 1

    print("sens8-semantic-ratchet self-test: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--inventory", action="store_true")
    mode.add_argument("--summary", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    mode.add_argument("--diff", nargs=2, metavar=("BASE_SHA", "HEAD_SHA"))
    args = parser.parse_args()

    if args.inventory:
        return inventory_mode()
    if args.summary:
        print(render_summary(list(walk_worktree())))
        return 0
    if args.self_test:
        return self_test()

    assert args.diff is not None
    return diff_mode(args.diff[0], args.diff[1])


if __name__ == "__main__":
    raise SystemExit(main())
