#!/usr/bin/env python3
"""Єдина точка входу для перевіреної міграції SENS .lisp → фізичний .sens.

Не реалізує нового парсера, кодера чи семантики. Викликає вже наявні
контрактні інструменти. Жоден режим, крім admit --write, не публікує байти.
"""
from __future__ import annotations

import argparse
import json
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
        return [sys.executable, str(SCRIPTS / "migrate-t5-batch.py"),
                *args.paths, "--root", str(ROOT), "--out", str(args.mirror),
                "--report", str(args.report), "--source-era", args.source_era]
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
                         default="auto", help="auto блокує невідоме W8; явно legacy/current лише з provenance")

    admit = sub.add_parser("admit", help="опублікувати .sens тільки з перевіреним маніфестом/оракулом")
    admit.add_argument("--manifest", type=Path, required=True)
    admit.add_argument("--mirror", type=Path, required=True)
    admit.add_argument("--reader", type=Path, required=True)
    admit.add_argument("--report", type=Path, required=True)
    admit.add_argument("--write", action="store_true", help="явне створення НОВОГО фізичного .sens")
    return p


def blocked_reasons(report: Path) -> list[str]:
    """Вивести лише причини блокування; ніколи не сертифікувати семантику."""
    try:
        state = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return []
    if not isinstance(state, dict) or not isinstance(state.get("files"), list):
        return []
    reasons = []
    for entry in state["files"]:
        if not isinstance(entry, dict) or entry.get("status") != "blocked":
            continue
        source = str(entry.get("path", "?"))[:180].replace("\n", " ").replace("\r", " ")
        why = str(entry.get("reason", "непідтверджена семантика"))[:400].replace("\n", " ").replace("\r", " ")
        reasons.append(f"{source}: {why}")
    return reasons

def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    # Передаємо status без трансформації: BLOCK не має перетворюватися на PASS.
    try:
        status = subprocess.run(command(args), cwd=ROOT, check=False).returncode
        if status != 0 and args.action == "preview":
            for reason in blocked_reasons(args.report):
                print(f"BLOCKED {reason}", file=sys.stderr)
        return status
    except OSError as exc:
        print(f"BLOCKED: неможливо запустити міграцію: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
