#!/usr/bin/env python3
"""Міжмовний бенчмарк компактності: C/JS/Python/Rust проти SENS.

Чесна межа: порівнюємо В МЕЖАХ шару «запис змісту». Для кожної мови даємо
розмір джерела (байти); для SENS — і джерело (людська проєкція з бінарними
кодами), і машинну фізичну форму .sens (байти/слова) через чинний мігратор.
Без незалежного оракула .sens НЕ публікуємо — тут лише розмір-план (dry-run).
Джерела інших мов — benchmarks/cross-language/native-baseline/programs/*.
SENS-програми — benchmarks/sens-surface/results/*/programs/*-sens.lisp.
"""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "benchmarks/cross-language/native-baseline/programs"
SURFACE = sorted((ROOT / "benchmarks/sens-surface").glob("results/*/programs/*-sens.lisp"))


def size(path: Path) -> int:
    return path.stat().st_size if path.is_file() else -1


def native_rows():
    for stem in ("workload", "tree"):
        for ext in ("c", "js", "py", "rs"):
            p = NATIVE / f"{stem}.{ext}"
            yield f"{stem}.{ext}", size(p)


def sens_rows():
    for p in SURFACE:
        yield f"{p.name} (source)", size(p)


def main() -> int:
    print("# Міжмовна компактність (розмір запису змісту)")
    print("## Інші мови — джерело (байти)")
    for name, n in native_rows():
        print(f"  {name:14s} {n:6d}")
    print("## SENS — людська проєкція (байти) і машинна .sens")
    for name, n in sens_rows():
        print(f"  {name:34s} {n:6d}")
    print("## .sens (машинна форма)")
    print("  admission awaits independent oracle — no .sens published without parity proof")
    print("VERDICT: compactness measured; .sens parity gate is separate (no admission without oracle)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
