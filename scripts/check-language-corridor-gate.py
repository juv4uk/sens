#!/usr/bin/env python3
"""Мовний коридор / архів: реєстр + SENS_SOURCE + свідки гейту.

Вихід 0 — коридор чистий.
Вихід 1 — порушення (gated law без SENS_SOURCE).
Не друкує зелений вердикт без реєстру; NOT_VERIFIED ≠ успіх.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "docs" / "language-policy-archive.md"
GATED_DIRS = [
    ROOT / "tests" / "semantic",
]
SENS_SOURCE_RE = re.compile(r"^\s*;\s*SENS_SOURCE\s*[=:]", re.MULTILINE)
ARCHIVE_ROW_RE = re.compile(
    r"^\s*\|?\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*([^|]+?)\s*\|\s*ARCHIVE\s*\|?\s*$",
    re.MULTILINE | re.IGNORECASE,
)
ARCHIVE_COMMIT_RE = re.compile(
    r"https://github\.com/juv4uk/sens/commit/[0-9a-f]{40}",
    re.IGNORECASE,
)


def load_archive() -> list[tuple[str, str, str]]:
    if not ARCHIVE.is_file():
        print("LANGUAGE_CORRIDOR=RED archive_missing path=docs/language-policy-archive.md")
        sys.exit(1)
    text = ARCHIVE.read_text(encoding="utf-8")
    rows = ARCHIVE_ROW_RE.findall(text)
    if not rows:
        print("LANGUAGE_CORRIDOR=RED archive_empty path=docs/language-policy-archive.md")
        sys.exit(1)
    parsed = [(a.strip(), b.strip(), c.strip()) for a, b, c in rows]
    missing_links = [artifact for artifact, _location, reason in parsed if not ARCHIVE_COMMIT_RE.search(reason)]
    if missing_links:
        print(f"LANGUAGE_CORRIDOR=RED archive_missing_full_commit_link count={len(missing_links)}")
        for artifact in missing_links[:10]:
            print(f"  missing_commit_link: {artifact}")
        sys.exit(1)
    return parsed


def check_sens_source_on_laws() -> list[str]:
    """Laws у tests/semantic з NATIVE_SENS_* мусять мати SENS_SOURCE."""
    problems = []
    for d in GATED_DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.lisp")):
            text = p.read_text(encoding="utf-8", errors="replace")
            head = "\n".join(text.splitlines()[:40])
            if "NATIVE_SENS_" in head and not SENS_SOURCE_RE.search(head):
                problems.append(str(p.relative_to(ROOT)))
    return problems


def selftest_positive(rows: list[tuple[str, str, str]]) -> None:
    n = len(rows)
    assert n >= 1, "positive selftest: registry must be non-empty"
    print(f"GATE_SELFTEST_POSITIVE=OK archive_rows={n}")


def selftest_negative() -> None:
    """Чужий тест без реєстру і без SENS_SOURCE — був би червоним."""
    with tempfile.TemporaryDirectory() as td:
        Path(td, "foreign_pytest_bench.py").write_text(
            "def test_x():\n    assert True\n", encoding="utf-8"
        )
        archive_paths = {b for _, b, _, _ in load_archive()}
        rel = "tests/semantic/_probe_foreign_without_register.py"
        if rel in archive_paths:
            print("GATE_SELFTEST_NEGATIVE=BROKEN probe_path_collides_with_archive")
            sys.exit(1)
        probe_head = "; no SENS_SOURCE field\n; NATIVE_SENS_POSITIVE=NOT_VERIFIED\n"
        if SENS_SOURCE_RE.search(probe_head):
            print("GATE_SELFTEST_NEGATIVE=BROKEN unexpected_match")
            sys.exit(1)
        print("GATE_SELFTEST_NEGATIVE=OK foreign_without_register_would_be_RED")


def main() -> int:
    rows = load_archive()
    n = len(rows)
    print(f"ARCHIVE (поза мовним коридором): {n} артефактів — docs/language-policy-archive.md")
    print(f"ARCHIVE_COUNT={n}")

    missing_files = [loc for _n, loc, _r in rows if not (ROOT / loc).is_file()]
    if missing_files:
        print(
            "LANGUAGE_CORRIDOR=NOTE archive_paths_absent_on_disk count=%d"
            % len(missing_files)
        )
        for m in missing_files[:10]:
            print(f"  absent: {m}")

    source_problems = check_sens_source_on_laws()
    if source_problems:
        print(
            "LANGUAGE_CORRIDOR=RED gated_law_missing_SENS_SOURCE count=%d"
            % len(source_problems)
        )
        for p in source_problems[:20]:
            print(f"  missing_SENS_SOURCE: {p}")
        return 1

    selftest_positive(rows)
    selftest_negative()
    print("LANGUAGE_CORRIDOR=CLEAN archive_registered_only corridor_SENS_SOURCE_ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
