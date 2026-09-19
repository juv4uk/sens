#!/usr/bin/env python3
"""Перевіряє рівноправність UK/EN/SA від status-free byte-SID authority.

Кожна identity має фіксовані en/uk/ukr/sa/sym слоти.
Слот містить spelling або (); окремої системи stable/candidate/missing немає.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "lib" / "surface" / "semantic-registry.lisp"
HUMAN_SURFACES = ("uk", "en", "sa")
ALL_SURFACES = ("en", "uk", "ukr", "sa", "sym")
ENTRY = re.compile(r'^\s*\("([01]{8})"\s+(.*)\)\s*$')
SURFACE = re.compile(
    r'\((en|uk|ukr|sa|sym)\s+(\(\)|"(?:\\.|[^"])*"|[^\s()]+)\)'
)


@dataclass(frozen=True)
class Entry:
    identity: str
    surfaces: dict[str, str | None]


def decode_name(raw: str) -> str | None:
    if raw == "()":
        return None
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    return raw


def parse_entries(source: str) -> list[Entry]:
    entries: list[Entry] = []
    seen: set[str] = set()
    for line_number, line in enumerate(source.splitlines(), start=1):
        match = ENTRY.match(line)
        if not match:
            continue
        identity, body = match.groups()
        if identity == "00000000":
            if body.strip() != "()":
                raise ValueError("Canon 0 row must be exactly ground-only")
            continue
        if identity in seen:
            raise ValueError(f"line {line_number}: duplicate semantic ID {identity}")
        seen.add(identity)

        matches = list(SURFACE.finditer(body))
        residue = SURFACE.sub("", body).strip()
        if residue:
            raise ValueError(f"line {line_number}: malformed semantic entry {identity}")

        surfaces: dict[str, str | None] = {}
        for item in matches:
            language, raw_name = item.groups()
            if language in surfaces:
                raise ValueError(f"line {line_number}: duplicate {language} in {identity}")
            surfaces[language] = decode_name(raw_name)

        if tuple(surfaces.keys()) != ALL_SURFACES:
            raise ValueError(
                f"{identity}: expected fixed surface order {ALL_SURFACES}, got {tuple(surfaces.keys())}"
            )
        entries.append(Entry(identity, surfaces))

    if not entries:
        raise ValueError("byte-SID semantic registry contains no entries")
    return entries


def counts(entries: list[Entry], language: str) -> tuple[int, int]:
    present = sum(entry.surfaces[language] is not None for entry in entries)
    return present, len(entries) - present


def is_release_complete(entries: list[Entry]) -> bool:
    return all(
        all(entry.surfaces[language] is not None for language in HUMAN_SURFACES)
        for entry in entries
    )


def render_report(entries: list[Entry]) -> str:
    denominator = len(entries)
    symbolic = sum(entry.surfaces["sym"] is not None for entry in entries)
    lines = [
        "Рівноправність людських поверхонь від status-free byte-SID authority",
        f"semantic identities: {denominator}",
        f"shared symbolic identities: {symbolic}",
        "",
        "surface  present  empty  present/total",
    ]
    for language in HUMAN_SURFACES:
        present, empty = counts(entries, language)
        lines.append(
            f"{language.upper():<7}{present:>7}{empty:>7}{present:>9}/{denominator}"
        )

    complete = sum(
        all(entry.surfaces[language] is not None for language in HUMAN_SURFACES)
        for entry in entries
    )
    lines.extend(
        [
            "",
            f"trilingual present identities: {complete}/{denominator}",
            f"release parity: {'CONFIRMED' if is_release_complete(entries) else 'OPEN'}",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="fail until UK, EN and SA slots are non-empty for every byte SID",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        entries = parse_entries(REGISTRY.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"surface registry error: {error}")
        return 2

    print(render_report(entries))
    if args.require_complete and not is_release_complete(entries):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
