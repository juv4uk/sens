#!/usr/bin/env python3
"""НЕЗАЛЕЖНИЙ перевіряч моєї судженої мапи.

Причина: у проєкті 120 guard-скриптів і ЖОДНОГО, який перевіряє СУДЖЕННЯ
агента. Усі п'ять моїх помилок виявила власна перевірка, не охорона. Автор не
може бути своїм екзаменатором.

Цей скрипт бере мою мапу й НЕЗАЛЕЖНО виводить вердикт із тих самих джерел за
механічним правилом (перетин розпізнавальних токенів між твердженням закону —
перший коментар .lisp — і claim_slice рядка ledger'а). Потім ПОРІВНЮЄ з моїм
вердиктом і друкує розбіжності.

Механічне правило СЛАБШЕ за судження: розбіжність не доводить, що я помилився,
але й не дає мені права не помічати її.

ОБМЕЖЕННЯ, ВИЯВЛЕНЕ НА ПЕРШОМУ Ж ЗАПУСКУ: закон писано УКРАЇНСЬКОЮ, а
claim_slice — АНГЛІЙСЬКОЮ. Тож перетин латинських токенів майже порожній, і
правило дає REJECTED там, де насправді мовна невідповідність, а не семантична.
Це означає: «незалежний=REJECTED» для d4-lambda-application і
d4-higher-order-composition НЕ є доказом моєї помилки — це артефакт мови.
Перевіряч мусить або знати обидві мови, або порівнювати структурно.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs/archaeology/semantic-candidate-map-2026-10-24.tsv"
LEDGER = ROOT / "docs/archaeology/semantic-coverage-ledger-2026-10-14.tsv"
SEMANTIC = ROOT / "tests/semantic"
VERDICTS = ("CONFIRMED", "WEAK", "UNJUDGEABLE", "REJECTED")
STOP = {"the", "and", "that", "with", "from", "into", "its", "must", "does", "не"}


def toks(text: str) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9]+", text.lower())
            if len(w) > 3 and w not in STOP and not w.isdigit()}


def law_header(artifact: str) -> str:
    """Твердження закону — перший коментар .lisp. Порожньо, якщо джерела немає."""
    for cand in (f"{artifact}-law.lisp", f"{artifact}.lisp"):
        path = SEMANTIC / cand
        if path.is_file():
            for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip().startswith(";"):
                    return line.lstrip("; ").strip()
            return ""
    return ""


def map_entries() -> list[tuple[str, str]]:
    out = []
    for line in MAP.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") or not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) >= 3 and cells[2] in VERDICTS:
            out.append((cells[0], cells[2]))
    return out


def independent(row_id: str, artifact: str) -> str:
    """Механічний вердикт: перетин токенів закону й claim_slice."""
    header = law_header(artifact)
    if not header:
        return "UNJUDGEABLE"
    claims = {r["retired_test_id"]: r.get("claim_slice", "")
              for r in csv.DictReader(LEDGER.open(encoding="utf-8"), delimiter="\t")}
    claim = claims.get(row_id, "")
    if not claim:
        return "UNJUDGEABLE"
    shared = toks(header) & toks(claim)
    if len(shared) >= 3:
        return "CONFIRMED"
    if len(shared) == 2:
        return "WEAK"
    return "REJECTED"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail-closed на розбіжностях")
    args = ap.parse_args()
    disagree = []
    for row_id, mine in map_entries():
        # артефакт — з другої колонки мапи
        line = next((l for l in MAP.read_text(encoding="utf-8").splitlines()
                     if l.split("\t")[0] == row_id and len(l.split("\t")) >= 3), None)
        if not line:
            continue
        art = line.split("\t")[1]
        theirs = independent(row_id, art)
        mark = "OK " if theirs == mine else "РОЗБІЖНІСТЬ"
        print(f"MAP-VERIFY: {mark} {art}: моє={mine} незалежне={theirs}")
        if theirs != mine:
            disagree.append((art, mine, theirs))
    if args.check and disagree:
        raise SystemExit(f"FAIL: {len(disagree)} розбіжностей — можлива шоста помилка")
    if args.check:
        print("MAP-VERIFY: PASS незалежний вердикт збігається з моїм")
    return 0


if __name__ == "__main__":
    sys.exit(main())
