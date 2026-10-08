#!/usr/bin/env python3
"""Обчислення independence index з knowledge/independence-ledger.tsv.

Методика (зафіксована у #4464):
- одиниця виміру — ланка критичного шляху, не рядок коду;
- рівні: source / execution / dependency;
- ваги: own=1.0, partial=0.5, foreign=0.0, unknown=0.0
  (unknown рахується як НЕ-СВОЯ: прогрес має вимірюватися свідками,
  а не невідомістю);
- індекс = сума ваг / кількість ланок, у відсотках;
- жоден клас не приймається без evidence_ref.

Відтворюваність: python3 scripts/compute-independence-index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / "knowledge" / "independence-ledger.tsv"

HEADER = [
    "link_id",
    "link_name",
    "level",
    "class",
    "evidence_ref",
    "measured_on",
    "notes",
]
LEVELS = ("source", "execution", "dependency")
CLASSES = {"own": 1.0, "partial": 0.5, "foreign": 0.0, "unknown": 0.0}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load() -> list[dict[str, str]]:
    if not LEDGER.is_file():
        fail(f"ledger not found: {LEDGER}")
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    if not lines:
        fail("ledger is empty")
    header = lines[0].split("\t")
    if header != HEADER:
        fail(f"unexpected header: {header}")
    rows: list[dict[str, str]] = []
    for number, line in enumerate(lines[1:], start=2):
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != len(HEADER):
            fail(f"line {number}: expected {len(HEADER)} fields, got {len(fields)}")
        row = dict(zip(HEADER, fields))
        if row["class"] not in CLASSES:
            fail(f"line {number}: unknown class {row['class']!r}")
        if row["level"] not in LEVELS:
            fail(f"line {number}: unknown level {row['level']!r}")
        if not row["evidence_ref"].strip() or row["evidence_ref"].strip() == "-":
            fail(f"line {number}: class without evidence_ref is not allowed")
        if len(row["measured_on"]) != 10 or row["measured_on"][4] != "-":
            fail(f"line {number}: measured_on must be YYYY-MM-DD")
        rows.append(row)
    if not rows:
        fail("ledger has header but no rows")
    return rows


def validate_shape(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    per_link: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        link = row["link_id"]
        level = row["level"]
        if level in per_link.setdefault(link, {}):
            fail(f"duplicate row for {link}/{level}")
        per_link[link][level] = row
    for link, levels in sorted(per_link.items()):
        missing = [level for level in LEVELS if level not in levels]
        if missing:
            fail(f"{link}: missing levels {missing}")
    return per_link


def main() -> int:
    rows = load()
    per_link = validate_shape(rows)

    print(f"ledger: {LEDGER.relative_to(REPO_ROOT)}  links: {len(per_link)}")
    print()
    print("link_id\tlink_name\tsource\texecution\tdependency\tevidence_measured_on")
    totals = {level: 0.0 for level in LEVELS}
    for link, levels in sorted(per_link.items()):
        cells = [levels[level]["class"] for level in LEVELS]
        for level in LEVELS:
            totals[level] += CLASSES[levels[level]["class"]]
        stamp = sorted({levels[level]["measured_on"] for level in LEVELS})[-1]
        name = levels["source"]["link_name"]
        print(f"{link}\t{name}\t" + "\t".join(cells) + f"\t{stamp}")

    print()
    print("independence index (own=1, partial=0.5, foreign/unknown=0):")
    for level in LEVELS:
        value = totals[level] / len(per_link) * 100.0
        print(f"  {level:<11} = {value:5.1f}%   ({totals[level]:.1f}/{len(per_link)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
