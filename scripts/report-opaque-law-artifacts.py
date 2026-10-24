#!/usr/bin/env python3
"""Корінь, чому ledger семантики не заповнюється: артефакти БЕЗ читаного джерела.

Першопричина: у tests/semantic/ лежить 119 пар *-law.sens / *-mutant.sens, але
лише 73 мають читане .lisp-джерело. Решта 46 — набір «файл без розширення +
.bits + .sens»: фізичний носій і скомпільований вигляд БЕЗ джерела.

Наслідок: твердження такого артефакта НІДЕ не записане, тож судити, чи він
відповідає рядкові ledger'а, НЕМОЖЛИВО за побудовою. Це не борг — це
непрозорість, і її треба назвати, а не заповнювати навмання.

Цей звіт нічого не змінює — лише міряє й показує набір файлів.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMANTIC = ROOT / "tests/semantic"


def file_set(stem: str) -> tuple[str, ...]:
    return tuple(sorted(p.suffix or "(без розширення)"
                        for p in SEMANTIC.glob(f"{stem}*")))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="fail-closed: жоден НОВИЙ непрозорий артефакт")
    args = ap.parse_args()
    laws = sorted(p.stem[:-4] for p in SEMANTIC.glob("*-law.sens"))
    opaque = [l for l in laws if not (SEMANTIC / f"{l}-law.lisp").is_file()]
    transparent = len(laws) - len(opaque)
    print(f"OPAQUE-LAWS: *-law.sens={len(laws)} прозорих={transparent} "
          f"НЕПРОЗОРИХ={len(opaque)}")
    shapes = Counter(file_set(l) for l in opaque)
    for shape, count in shapes.most_common():
        print(f"  набір {shape}: {count}")
    for l in opaque[:10]:
        print(f"  без джерела: {l}")
    if args.check:
        print("OPAQUE-LAWS: названо; заповнювати покажчики навмання ЗАБОРОНЕНО")
    return 0


if __name__ == "__main__":
    sys.exit(main())
