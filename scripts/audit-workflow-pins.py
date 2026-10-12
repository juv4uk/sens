#!/usr/bin/env python3
"""Звіт (НЕ гейт): стан пінів Actions/toolchain у воркфлоу.

Показує, які воркфлоу використовують нерухомі 40-hex SHA для `actions/...`, який
toolchain ref вони просять, і окремо позначає воркфлоу, чиї чеки **гейтять реліз**
(набір REQUIRED_CHECKS у scripts/verify_release_ci.py). Це інформація для рішення
власника щодо CI: сам release-шлях уже піниться й локується
scripts/check-release-pins.py.

Fail-open за замовчуванням (це звіт, exit 0). `--strict` повертає 1, якщо
будь-який реліз-гейтний воркфлоу має непінені `actions/...`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEP = re.compile(r"^\s*-\s")
USES_LINE = re.compile(r"^\s*-?\s*uses:\s*(\S+)(?:\s+#.*)?\s*$")
SHA = re.compile(r"[0-9a-f]{40}\Z")
LOCAL = re.compile(r"\./\S+\Z")

# Воркфлоу, чиї чеки входять у REQUIRED_CHECKS релізного гейта.
GATING = {
    ".github/workflows/ci-hosted.yml": "portable critical gates",
    ".github/workflows/important-file-guard.yml": "Physical SENS T5 file-admission oracle",
    ".github/workflows/binary-program-e2e.yml": "physical T5 to D2 D3 D4 D7 runtime",
    ".github/workflows/vertical-day-smoke.yml": "Lisp-owned pair to real CPU",
}


def _uses_refs(text: str) -> list[str]:
    refs: list[str] = []
    for line in text.splitlines():
        match = USES_LINE.match(line)
        if match and not LOCAL.fullmatch(match.group(1)):
            refs.append(match.group(1))
    return refs


def scan(root: Path = ROOT) -> list[dict]:
    rows: list[dict] = []
    for path in sorted((root / ".github" / "workflows").glob("*.yml")):
        rel = path.relative_to(root).as_posix()
        pinned = floating = 0
        toolchains: set[str] = set()
        floating_refs: list[str] = []
        for ref in _uses_refs(path.read_text(encoding="utf-8")):
            action, _, pin = ref.rpartition("@")
            if action == "dtolnay/rust-toolchain":
                toolchains.add(pin)
            elif SHA.fullmatch(pin):
                pinned += 1
            elif "@" in ref:
                floating += 1
                floating_refs.append(ref)
        if pinned or floating or toolchains:
            rows.append({
                "workflow": rel,
                "pinned_actions": pinned,
                "floating_actions": floating,
                "toolchains": sorted(toolchains),
                "floating_refs": sorted(set(floating_refs)),
                "gating_check": GATING.get(rel),
            })
    rows.sort(key=lambda r: (-r["floating_actions"], r["workflow"]))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="workflow action/toolchain pin survey")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 if any release-gating workflow has floating actions")
    args = parser.parse_args(argv)
    rows = scan()
    total_pinned = sum(r["pinned_actions"] for r in rows)
    total_floating = sum(r["floating_actions"] for r in rows)
    gating_floating = [r for r in rows if r["gating_check"] and r["floating_actions"]]
    print(f"workflows scanned: {len(rows)}  sha-pinned actions: {total_pinned}  floating actions: {total_floating}")
    print("--- release-gating workflows ---")
    for row in rows:
        if row["gating_check"]:
            print(f"  {row['workflow']}  gate={row['gating_check']!r}  "
                  f"pinned={row['pinned_actions']} floating={row['floating_actions']} "
                  f"toolchains={row['toolchains']}")
    print("--- top floating workflows ---")
    for row in rows[:12]:
        print(f"  {row['floating_actions']:3d} floating  {row['workflow']}  "
              f"pinned={row['pinned_actions']} toolchains={row['toolchains']}")
    if args.strict and gating_floating:
        print(f"AUDIT_BLOCKED: {len(gating_floating)} release-gating workflow(s) have floating actions", file=sys.stderr)
        return 1
    print("AUDIT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
