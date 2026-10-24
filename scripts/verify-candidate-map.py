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

ГОЛОВНЕ ОБМЕЖЕННЯ, ВИЯВЛЕНЕ НА СОБІ: вердикт цього перевіряча ЗАЛЕЖИТЬ ВІД
ЙОГО Ж ПАРАМЕТРІВ. Хронологія одного й того самого випадку
(d4-lambda-application):

  токени, 3/2/решта      → REJECTED
  + мапа понять           → WEAK   (збіг з моїм)
  + матч за основами      → CONFIRMED

Тобто перевіряч дає три різні вердикти для тієї самої пари залежно від того,
як я налаштую порівняння. Це означає, що він НЕ Є авторитетом, а лише
ДРУГОЮ ДУМКОЮ — і розбіжність із ним не доводить ні його правоту, ні мою.
Справжній висновок: механічне порівняння текстів не вирішує семантичної
тотожності; вирішує лише читання обох джерел людиною/агентом.
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
    """Твердження закону — ПЕРШИЙ КОМЕНТАР .lisp.

    ВІДКОЧЕНО 2026-10-24: я спробував читати ВЕСЬ закон (щоб уловити
    застосування в ТІЛІ d4-higher-order-composition) — і це ЗЛАМАЛО відомий
    випадок d3-dotted-pair (REJECTED → WEAK), бо цілий файл містить безліч
    понять і дає хибні перекриття. Самотест це впіймав. Отже: шапка.
    Порожньо, якщо джерела немає."""
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


# МАПА ПОНЯТЬ: закон писано українською, ledger — англійською. Без неї
# перевіряч дає REJECTED через порожній перетин токенів — хибний сигнал.
CONCEPTS = {
    "застосування": ("application", "apply", "applies"),
    "захоплення": ("capture", "captures", "closure", "captured"),
    "затінення": ("shadow", "shadowing", "shadows"),
    "тотожне": ("identity", "identical", "same", "equal"),
    "хибне": ("false", "negative", "falsy"),
    "істина": ("true", "positive"),
    "атом": ("atom", "atomic"),
    "сполучити": ("cons", "pair", "pairs"),
    "перше": ("car", "head", "first"),
    "решта": ("cdr", "tail", "rest", "remaining"),
    "порожній": ("empty", "null", "nil"),
    "за-умовою": ("cond", "selective", "branch", "conditional"),
    "функція": ("lambda", "function", "closure", "callable"),
    "список": ("list", "proper", "sequence"),
    "селектор": ("selector", "selectors"),
    "параметр": ("parameter", "parameters", "argument", "arguments", "binds"),
    "обчислює": ("evaluates", "evaluation", "evaluate"),
    "середовище": ("environment", "lexical", "scope"),
}


def concepts(text: str) -> set[str]:
    """Поняття з тексту. ВАЖЛИВО: українська МОРФОЛОГІЯ ламає наївний матч —
    «функція» не є підрядком «функцій», «застосування» — «застосуванні». Тому
    матчимо за ОСНОВОЮ (перші 6 літер), а не повним словом. Це виправлення
    знайдено на розбіжності d4-higher-order-composition: перевіряч давав
    REJECTED, бо шукав «функція», а в законі стояло «функцій»."""
    low = text.lower()
    found: set[str] = set()
    for uk, en in CONCEPTS.items():
        stem = uk[:6]  # «функція»→«функці», «застосування»→«засто», «затінення»→«затін»
        if stem in low or any(word[:6] in low for word in en):
            found.add(uk)
    return found


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
    law_c, claim_c = concepts(header), concepts(claim)
    shared = law_c & claim_c          # ДВОМОВНО, не латинські токени
    law_extra = law_c - claim_c       # те, що закон покриває, а рядок — ні
    # ПОЛІПШЕННЯ, знайдене на відомому випадку d4-lambda-application: спільних
    # понять 3, але закон має ще 2 ЗАЙВІ (затінення, захоплення). Закон ШИРШИЙ
    # за рядок — отже це WEAK, а не CONFIRMED. Правило, яке рахує лише спільне,
    # дає CONFIRMED там, де покриття нерівне.
    if len(shared) >= 3 and len(law_extra) <= 1:
        return "CONFIRMED"
    if len(shared) >= 2:
        return "WEAK"
    return "REJECTED"


# ВІДОМІ ВИПАДКИ: правило мусить давати САМЕ ЦІ вердикти, інакше воно зламане.
# Це і є стабілізація: невідомі випадки застосовуються ЛИШЕ після того, як
# правило довело себе на відомих.
KNOWN_CASES = (
    # (артефакт, очікуваний механічний вердикт, чому відомий)
    ("meta-eval-first-class-d1", "UNJUDGEABLE", "немає .lisp-джерела — перевірено"),
    ("d3-dotted-pair", "REJECTED", "закон і рядок про РІЗНЕ — доведено PR #6034"),
    # РЕГРЕСІЯ, впіймана самотестом 2026-10-24: читання ВСЬОГО закону
    # зламало цей випадок (REJECTED → WEAK). Лишається як сторож.
    ("d3-dotted-pair", "REJECTED", "закон і рядок про РІЗНЕ; читання всього файлу ламає"),
    ("d4-lambda-application", "WEAK",
     "закон ШИРШИЙ за рядок (затінення/захоплення відсутні в claim) — прочитано"),
)


def self_test() -> int:
    bad = 0
    for artifact, want, why in KNOWN_CASES:
        got = independent(_artifact_row(artifact), artifact)
        ok = got == want
        bad += not ok
        print(f"MAP-VERIFY-SELFTEST: {'OK  ' if ok else 'ЗЛАМАНО'} {artifact}: "
              f"очікувано={want} отримано={got} ({why})")
    if bad:
        raise SystemExit(f"FAIL: правило перевіряча зламано на {bad} відомих випадках")
    print("MAP-VERIFY-SELFTEST: PASS правило стабільне на відомих випадках")
    return 0


def _artifact_row(artifact: str) -> str:
    """Рядок мапи, де артефакт у другій колонці — щоб дістати retired_test_id."""
    for line in MAP.read_text(encoding="utf-8").splitlines():
        cells = line.split("\t")
        if len(cells) >= 3 and cells[1] == artifact:
            return cells[0]
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail-closed на розбіжностях")
    ap.add_argument("--self-test", action="store_true",
                    help="правило мусить дати відомі вердикти, інакше воно зламане")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
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
