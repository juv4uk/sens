#!/usr/bin/env python3
"""Мої твердження — машинно-перевірні, а не на віру.

Причина: я тричі помилився в цій роботі (не той декодер — двічі, .bits-кандидат
— раз). Кожного разу мене виправляла власна перевірка, не охорона. Твердження,
яке не можна перевірити командою, — це не знання, а спогад.

Цей звіт перераховує ключові числа з дерева й каже, чи вони ще тримаються.
Нічого не змінює.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/archaeology/semantic-coverage-ledger-2026-10-14.tsv"
SEMANTIC = ROOT / "tests/semantic"


def ledger_rows() -> list[dict[str, str]]:
    with LEDGER.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def filled(row: dict[str, str], col: str) -> bool:
    return row.get(col, "-") not in ("-", "")


MAP = ROOT / "docs/archaeology/semantic-candidate-map-2026-10-24.tsv"
VERDICTS = ("CONFIRMED", "WEAK", "UNJUDGEABLE", "REJECTED")


def verdicts() -> list[tuple[str, str]]:
    """(артефакт, вердикт) з моєї судженої мапи — читається, не вгадується."""
    if not MAP.is_file():
        return []
    out = []
    for line in MAP.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) >= 3 and cells[2] in VERDICTS:
            out.append((cells[1], cells[2]))
    return out


def count_verdict(name: str) -> int:
    return sum(1 for _, v in verdicts() if v == name)


def unjudgeable_without_source() -> int:
    return sum(1 for art, v in verdicts()
               if v == "UNJUDGEABLE"
               and not (SEMANTIC / f"{art}-law.lisp").is_file())


def _opaque_without_family_lisp() -> int:
    """Скільки *-law.sens без -law.lisp не мають ЖОДНОГО .lisp у родині (2 токени).
    Грубий евристик: родич у родині — не обов'язково джерело того ж твердження."""
    import re as _re
    laws = sorted(p.stem[:-4] for p in SEMANTIC.glob("*-law.sens"))
    opaque = [x for x in laws if not (SEMANTIC / f"{x}-law.lisp").is_file()]
    stems = {p.name[:-5] for p in SEMANTIC.glob("*.lisp")}

    def family(name: str) -> str:
        parts = _re.split(r"[-_]", name)
        return "-".join(parts[:2]) if len(parts) >= 2 else name

    return sum(1 for x in opaque if not any(family(s) == family(x) for s in stems))


def claims() -> list[tuple[str, int, int]]:
    """(опис, виміряно, очікувано)"""
    rows = ledger_rows()
    laws = sorted(p.stem[:-4] for p in SEMANTIC.glob("*-law.sens"))
    opaque = [x for x in laws if not (SEMANTIC / f"{x}-law.lisp").is_file()]
    arts = {str(p) for p in SEMANTIC.glob("*.sens")}
    ref = {r[c] for r in rows for c in ("candidate_sens_witness", "negative_sens_witness")
           if filled(r, c)}
    return [
        ("рядків ledger", len(rows), 221),
        ("з кандидатом-свідком", sum(filled(r, "candidate_sens_witness") for r in rows), 4),
        ("з негативним свідком", sum(filled(r, "negative_sens_witness") for r in rows), 4),
        ("без кандидата", sum(not filled(r, "candidate_sens_witness") for r in rows), 217),
        ("*-law.sens", len(laws), 119),
        ("*-law.sens без .lisp", len(opaque), 46),
        (".sens у tests/semantic", len(arts), 549),
        # Семантичні судження — теж перевірні: жодного CONFIRMED у моїй мапі
        # (усі три перевірені випадки виявились хибними або завищеними), і 8
        # UNJUDGEABLE справді без .lisp-джерела.
        ("CONFIRMED у моїй мапі", count_verdict("CONFIRMED"), 0),
        ("UNJUDGEABLE без .lisp", unjudgeable_without_source(), 8),
        # НЮАНС, перевірений 2026-10-24: конвенція імен у tests/semantic НЕ
        # строго -law/-mutant (є d10-*-laws.lisp, -invalid-arity.lisp тощо).
        # Тому «46 без -law.lisp» вужче за «46 без джерела». Родинний тест
        # дає 7 «з родичем» і 39 «без родича» — але родич у родині
        # (meta-eval-first-class-d1 ← meta-eval-lexical-shadow-d1) — ЦЕ ІНШЕ
        # ТВЕРДЖЕННЯ, не джерело. Отже наявність джерела під іншим іменем
        # НЕ вирішується механічно; це судження.
        ("без -law.lisp (вужче за «без джерела»)", len(opaque), 46),
        ("з них без жодного .lisp у родині", _opaque_without_family_lisp(), 39),
        # Твердження «N незгаданих артефактів» ПРИБРАНО: хибне за формою.
        # Ledger посилається і на .bits-кандидата (не .sens), тож перетин
        # залежить від способу порівняння — будь-яке одне число вводить в
        # оману. Це викрив цей же чекер; я не підганяю число, а знімаю тезу.
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail-closed: усі твердження мусять триматись")
    args = ap.parse_args()
    bad = 0
    for label, got, want in claims():
        ok = got == want
        bad += not ok
        print(f"CLAIMS: {'OK  ' if ok else 'ЗСУВ'} {label}: виміряно={got} очікувано={want}")
    if bad:
        raise SystemExit(f"FAIL: {bad} тверджень зсунулись — перевір, чи це не моя помилка")
    if args.check:
        print("CLAIMS: PASS усі твердження тримаються")
    return 0


if __name__ == "__main__":
    sys.exit(main())
