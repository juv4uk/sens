#!/usr/bin/env python3
"""Кожен guard-скрипт мусить когось мати, хто його ЗАПУСКАЄ.

Першопричина: 120 guard-подібних скриптів у scripts/, і 16 із них не запускає
жоден workflow, тест чи інший скрипт. Серед них — check-d6-definition-bindings.py
і check-d10-definition-bindings.py: генератори таблиць bindings для D6 і D10.
D5 і D9 У CI Є (ci-hosted.yml:69, d5-exact-definition-bindings.yml:14), а D6 і
D10 — ні. Тобто їхні таблиці можуть старіти НЕПОМІТНО, і ніхто не дізнається.

Guard, якого ніхто не запускає, — це фальшива безпека.

Правило: guard (check-*/verify-*/audit-*) мусить мати виконуваного споживача
(workflow, тест, інший скрипт, Makefile). Наявний борг названо; НОВИЙ сирота
падає.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
GUARD_PREFIXES = ("check-", "verify-", "audit-", "guard-")
CONSUMER_GLOBS = (
    ".github/workflows/*.yml", ".github/workflows/*.yaml",
    "tests/*.py", "scripts/tests/*.py", "scripts/*.py", "scripts/*.mjs",
    "Makefile", "packaging/**/*.py",
)
# Перевірені вручну 2026-10-24. НОВИЙ сирота падає — тут його немає.
KNOWN_ORPHANS = {
    "audit-foundation-d7-version.py",
    "audit-test-languages.py",
    "audit-three-pass-d11-resident-shadow.py",
    "check-core-universal-contract.py",
    "check-d10-island-bridge-v1.py",
    "check-d10-lisp-machine-evaluator-harvest-v1.py",
    "check-domain-bitness-witness.py",
    "check-lisp15-arithmetic-provenance.py",
    "check-meta-eval-evidence.py",
    "check-od005-d5-baseline.py",
    "check-semantic-coverage-ledger.py",
    "check-world-knowledge-authority.py",
}


def guards() -> set[str]:
    return {p.name for p in SCRIPTS.glob("*.py") if p.name.startswith(GUARD_PREFIXES)}


SELF = Path(__file__).name


def runner_texts() -> list[tuple[str, str]]:
    """Тексти потенційних ЗАПУСКАЧІВ. Себе виключаємо: інакше список
    KNOWN_ORPHANS у цьому файлі зробив би всіх названих «спожитими» —
    самореферентна помилка, яку цей чекер і виявив на собі."""
    out = []
    for pattern in CONSUMER_GLOBS:
        for path in ROOT.glob(pattern):
            if not path.is_file() or path.name == SELF:
                continue
            try:
                out.append((str(path.relative_to(ROOT)),
                            path.read_text(encoding="utf-8", errors="ignore")))
            except OSError:
                continue
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail-closed на нові сироти")
    args = ap.parse_args()
    all_guards = guards()
    runners = runner_texts()
    orphan, wired = [], []
    for name in sorted(all_guards):
        # ЗГАДКА ≠ ЗАПУСК. Шукаємо виклик із шляхом `scripts/<ім'я>`, як у
        # workflow (`python3 scripts/check-d9-…`) чи тесті (subprocess).
        # Інакше тест, який лише називає guard у перевірці, «підключив» би
        # його — самореферентна помилка, яку цей чекер виявив на собі.
        # Запуск буває у ДВОХ формах:
        #   • рядковий шлях:  `python3 scripts/check-x.py` (workflow);
        #   • конструювання:  ROOT / "scripts" / "check-x.py" (тест).
        # Лише перша форма пропускала тести — і хибно оголошувала
        # check-release-admission-ledger.py та check-required-checks.py
        # сиротами, хоча їх запускають tests/test_check_*.py.
        needles = (f"scripts/{name}", f'"scripts" / "{name}"')
        who = [rel for rel, text in runners
               if any(n in text for n in needles) and Path(rel).name != name]
        (wired if who else orphan).append((name, who))
    print(f"GUARDS-RUNNERS: guard-скриптів={len(all_guards)} "
          f"мають запуск={len(wired)} борг={len(orphan)}")
    for name, who in orphan:
        print(f"  {name}: НІХТО не запускає")
    # Себе не вважаємо «новим»: чекер не може вимагати власного запуску,
    # а підключення до CI — окреме рішення (AGENTS.md: без нових workflow).
    new = sorted({n for n, _ in orphan} - KNOWN_ORPHANS - {SELF})
    if new:
        raise SystemExit(f"FAIL: нові guard-скрипти без запуску: {new}")
    if args.check:
        print("GUARDS-RUNNERS: PASS нових guard-сиріт немає (борг названо)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
