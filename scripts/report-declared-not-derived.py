#!/usr/bin/env python3
"""Сканер «оголошене замість виведеного»: літерали в полях-вердиктах.

Першопричина: у цій нитці я знайшов ТРИ випадки, де поле, що виглядає як
ВЕРДИКТ, насправді є КОНСТАНТОЮ:
  • D10-каталог «1024» — оголошений, не виведений;
  • numeric_domains_generated.rs — файл без споживача;
  • check-release-admission-ledger.py:152-153 — "uk_oracle_verified": 0,
    "release_admitted": 0 — літерали, які ніщо не обчислює.

Питання: це три дефекти чи ОДНА хвороба? Цей сканер рахує кандидатів.

ВАЖЛИВЕ ОБМЕЖЕННЯ (виявлене на першому ж запуску): сканер ПЕРЕОЦІНЮЄ.
Багато літералів — НАВМИСНІ: `admitted_executable_semantics = None` означає
«не допущено», `release_admitted = False` — те саме. Відрізнити навмисну
константу від НЕВИВЕДЕНОЇ евристикою НЕМОЖЛИВО: для цього треба знати, чи
поле МУСИТЬ обчислюватись. Тому звіт дає КАНДИДАТІВ, а не вирок.

Нічого не змінює.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
VERDICT_KEY = re.compile(
    r'"(?P<key>[a-z0-9_]*(?:verified|admitted|passed|accepted|ratified|approved)'
    r'[a-z0-9_]*)"\s*:\s*(?P<val>0|1|True|False|None)')
# Вирази, які РОБЛЯТЬ поле виведеним: присвоєння зі змінної або з виклику.
DERIVED = ('sum(', 'len(', 'any(', 'all(', 'bool(', '==', '!=', 'count(')


def candidates() -> list[tuple[str, str, str, bool]]:
    out = []
    for path in sorted(SCRIPTS.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in VERDICT_KEY.finditer(text):
            key, val = m.group("key"), m.group("val")
            # чи деінде в тому ж файлі поле отримує ВИВЕДЕНЕ значення?
            derived = bool(re.search(rf'"{key}"\]\s*=\s*[^"\n]', text)) or any(
                d in text.split(f'"{key}"')[-1][:120] for d in DERIVED)
            out.append((path.name, key, val, derived))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="лише звіт; сканер ПЕРЕОЦІНЮЄ, тому не fail-closed")
    args = ap.parse_args()
    rows = candidates()
    hard = [r for r in rows if not r[3]]
    print(f"DECLARED-NOT-DERIVED: полів-вердиктів із літералом={len(rows)} "
          f"без виведення={len(hard)}")
    print("DECLARED-NOT-DERIVED: УВАГА — це КАНДИДАТИ, не вирок. Багато літералів "
          "навмисні (None/False = «не допущено»). Евристика не відрізняє "
          "навмисну константу від невиведеної.")
    by_file: dict[str, int] = {}
    for name, _, _, _ in hard:
        by_file[name] = by_file.get(name, 0) + 1
    for name, count in sorted(by_file.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {name}: {count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
