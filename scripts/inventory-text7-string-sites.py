#!/usr/bin/env python3
"""Reproducible live String/Text7 consumer inventory for sens#1700.

Scans only Rust production-source trees (crates/*/src/**/*.rs) for the three
canonical String-shape markers that the original one-off inventory used:
ExprKind::String, Value::String, TAG_STRING.

Classification is intentionally fail-closed. A new matched source path must be
assigned an explicit migration role here before the generated TSV can refresh.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/research/data/1700-string-sites-current.tsv"
MARKERS = ("ExprKind::String", "Value::String", "TAG_STRING")


def classify(path: str) -> tuple[str, str]:
    if path.startswith((
        "crates/sens-host/src/",
        "crates/sens-cli/src/",
        "crates/sens-lsp/src/",
        "crates/sens-wasm/src/",
    )):
        return "human-boundary", "host/UI adapter keeps UTF-8 outside canonical Text7"

    if path == "crates/sens/src/presentation.rs":
        return "human-boundary", "human presentation is a projection, not Text7 identity"

    if path.startswith("crates/xtask/src/"):
        return "mechanism", "tooling/oracle adapter observes syntax mechanically"

    if path == "crates/sens/src/syntax.rs":
        return "mechanism", "AST/FASL/wire String transport is migration mechanism debt"

    if path in {
        "crates/sens/src/parser.rs",
        "crates/sens/src/value.rs",
    } or path.startswith("crates/sens/src/eval/"):
        return "textual-language-data", "live language String producer/consumer to migrate by role"

    # Reserved for an explicitly proven compatibility-only source path.
    legacy_paths: set[str] = set()
    if path in legacy_paths:
        return "legacy", "explicit compatibility-only String path"

    raise ValueError(f"unclassified live String consumer path: {path}")


def rust_code_lines(path: Path):
    """Yield (line_number, code_without_comments) with lightweight comment stripping."""
    in_block = False
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw
        out = []
        i = 0
        in_string = False
        escape = False
        while i < len(line):
            if in_block:
                end = line.find("*/", i)
                if end < 0:
                    i = len(line)
                    continue
                in_block = False
                i = end + 2
                continue

            ch = line[i]
            nxt = line[i + 1] if i + 1 < len(line) else ""

            if in_string:
                out.append(ch)
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                i += 1
                continue

            if ch == '"':
                in_string = True
                out.append(ch)
                i += 1
                continue
            if ch == "/" and nxt == "/":
                break
            if ch == "/" and nxt == "*":
                in_block = True
                i += 2
                continue

            out.append(ch)
            i += 1

        yield number, "".join(out)


def collect() -> list[tuple[str, int, str, str, str]]:
    rows: list[tuple[str, int, str, str, str]] = []
    for path in sorted(ROOT.glob("crates/*/src/**/*.rs")):
        rel = path.relative_to(ROOT).as_posix()
        role = None
        rationale = None
        for line_number, code in rust_code_lines(path):
            for marker in MARKERS:
                if marker not in code:
                    continue
                if role is None:
                    role, rationale = classify(rel)
                rows.append((rel, line_number, marker, role, rationale))
    return rows


def render(rows: list[tuple[str, int, str, str, str]]) -> str:
    header = "path\tline\tmarker\trole\trationale\n"
    body = "".join(
        f"{path}\t{line}\t{marker}\t{role}\t{rationale}\n"
        for path, line, marker, role, rationale in rows
    )
    return header + body


def role_counts(rows):
    counts: dict[str, int] = {}
    for _, _, _, role, _ in rows:
        counts[role] = counts.get(role, 0) + 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="refresh the generated TSV")
    mode.add_argument("--check", action="store_true", help="fail if the generated TSV is stale")
    args = parser.parse_args()

    try:
        rows = collect()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    generated = render(rows)
    counts = role_counts(rows)
    summary = " ".join(f"{role}={counts[role]}" for role in sorted(counts))
    print(f"String/Text7 live sites: total={len(rows)} {summary}")

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(generated, encoding="utf-8")
        return 0

    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != generated:
            print(f"stale generated inventory: {OUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        return 0

    sys.stdout.write(generated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
