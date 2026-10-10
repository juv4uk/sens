#!/usr/bin/env python3
"""Безумовний контроль CSV-вимірювань чинного прямого виконання T5.

Це перевірка вимірювань, а не семантики SENS чи фізичного кодека.
Перевірки діють і під Python -O; відсутня фікстура завжди означає відмову.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path
import sys

COLUMNS = (
    "fixture", "bytes", "forms", "t5_decode_parse_lower_ns",
    "visible_parse_lower_ns", "cached_lowered_eval_ns",
)
FIXTURES = {
    "quote": "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "atom": "tests/fixtures/migration-atom-cohort/atom-empty.sens",
    "cond": "tests/fixtures/migration-d1-cond-cohort/branch.sens",
}
# Закріплені SHA-256 реальних канонічних T5-файлів. Без цього підміна
# фізичного свідка іншими байтами тієї ж довжини була б невидимою.
# Контракт порівняння вимірювань змінюється лише окремим доказовим PR.
FIXTURE_SHA256 = {
    "quote": "90b993c83b34932d65b1001547f8833987eac2e44b238155a983cb8e5f68c978",
    "atom": "4270498d024be1e03a69800223d3dac8e04d9b05deb6fc18c6986b0329e211f0",
    "cond": "6568d9888039c0e33ace2378a39f0201f7d4ed67c71f23a6bb61605353976904",
}
TIMINGS = COLUMNS[3:]


class EvidenceError(ValueError):
    """CSV бенчмарка не можна атестувати як повне вимірювання."""


def check(csv_path: Path, root: Path) -> dict[str, float]:
    """Validate benchmark rows against authentic committed T5 fixtures."""
    if not csv_path.is_file():
        raise EvidenceError(f"відсутній CSV: {csv_path}")
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, restkey="__extra__")
        if reader.fieldnames != list(COLUMNS):
            raise EvidenceError("незатверджені стовпці CSV або їхній порядок")
        rows = list(reader)
    if len(rows) != len(FIXTURES):
        raise EvidenceError(f"очікувано {len(FIXTURES)} рядки, отримано {len(rows)}")
    observed: set[str] = set()
    totals = {key: 0.0 for key in TIMINGS}
    for row in rows:
        if set(row) != set(COLUMNS) or any(v is None for v in row.values()):
            raise EvidenceError("неповний або зайвий стовпець CSV")
        name = row["fixture"]
        if name not in FIXTURES or name in observed:
            raise EvidenceError(f"невідомий/повторний зразок: {name!r}")
        observed.add(name)
        fixture = root / FIXTURES[name]
        if not fixture.is_file() or fixture.is_symlink():
            raise EvidenceError(f"відсутня або символьна фізична фікстура: {fixture}")
        try:
            raw_bytes = int(row["bytes"])
            forms = int(row["forms"])
        except ValueError as exc:
            raise EvidenceError(f"нецілі обсяги/форми: {name}") from exc
        if raw_bytes <= 0 or raw_bytes != fixture.stat().st_size or forms != 1:
            raise EvidenceError(f"неправильний розмір або число форм: {name}")
        if hashlib.sha256(fixture.read_bytes()).hexdigest() != FIXTURE_SHA256[name]:
            raise EvidenceError(f"змінилася фізична T5-фікстура: {name}")
        for key in TIMINGS:
            try:
                elapsed = float(row[key])
            except ValueError as exc:
                raise EvidenceError(f"некоректне вимірювання: {name}/{key}") from exc
            if not math.isfinite(elapsed) or not (0 < elapsed < 1e12):
                raise EvidenceError(f"недостовірне значення: {name}/{key}")
            totals[key] += elapsed
    if observed != set(FIXTURES):
        raise EvidenceError("бракує обов'язкової фікстури")
    return totals


def main() -> int:
    """Validate one timing CSV and return a fail-closed process status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        check(args.csv_path, args.root)
    except (OSError, UnicodeError, csv.Error, EvidenceError) as exc:
        print(f"DIRECT-T5-TIMING: BLOCKED: {exc}", file=sys.stderr)
        return 2
    print("DIRECT-T5-TIMING: PASS — повні фізичні свідки, лише вимірювання")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
