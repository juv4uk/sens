#!/usr/bin/env python3
"""Єдина точка входу для перевіреної міграції SENS .lisp → фізичний .sens.

Не реалізує нового парсера, кодера чи семантики. Викликає вже наявні
контрактні інструменти. Жоден режим, крім admit --write, не публікує байти.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def command(args: argparse.Namespace) -> list[str]:
    """Повернути argv канонічного інструмента без shell-інтерпретації."""
    if args.action == "candidates":
        return [sys.executable, str(SCRIPTS / "report_original_migration_candidates.py"),
                "--out", str(args.report)]
    if args.action == "preview":
        # Explicit era is evidence about the source's provenance, not a
        # semantic permit. Default auto MUST block ambiguous W8/D8.
        return [sys.executable, str(SCRIPTS / "migrate-t5-batch.py"),
                *args.paths, "--root", str(ROOT), "--out", str(args.mirror),
                "--source-era", str(args.source_era), "--report", str(args.report)]
    if args.action == "admit":
        cmd = [sys.executable, str(SCRIPTS / "admit-t5-migration.py"),
               "--root", str(ROOT), "--manifest", str(args.manifest),
               "--mirror", str(args.mirror), "--reader", str(args.reader),
               "--report", str(args.report)]
        if args.write:
            cmd.append("--write")
        return cmd
    raise ValueError("невідомий режим міграції")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="action", required=True)

    census = sub.add_parser("candidates", help="виявити оригінальні ще не мігровані .lisp; тільки звіт")
    census.add_argument("--report", type=Path, required=True)

    preview = sub.add_parser("preview", help="реальний трипрохідний попередній перегляд; без запису .sens")
    preview.add_argument("paths", nargs="+", help="явні відносні шляхи до .lisp чи каталогів")
    preview.add_argument("--mirror", type=Path, required=True)
    preview.add_argument("--report", type=Path, required=True)
    preview.add_argument("--source-era", choices=("auto", "legacy", "current"),
                         default="auto",
                         help="auto BLOCKS ambiguous W8; legacy/current require independently proven source provenance")

    admit = sub.add_parser("admit", help="опублікувати .sens тільки з перевіреним маніфестом/оракулом")
    admit.add_argument("--manifest", type=Path, required=True)
    admit.add_argument("--mirror", type=Path, required=True)
    admit.add_argument("--reader", type=Path, required=True)
    admit.add_argument("--report", type=Path, required=True)
    admit.add_argument("--write", action="store_true", help="явне створення НОВОГО фізичного .sens")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    # Передаємо status без трансформації: BLOCK не має перетворюватися на PASS.
    try:
        return subprocess.run(command(args), cwd=ROOT, check=False).returncode
    except OSError as exc:
        print(f"BLOCKED: неможливо запустити міграцію: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
