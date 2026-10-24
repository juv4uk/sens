#!/usr/bin/env python3
"""Міряє стек семантичного боргу: 221 відставлений Rust-тест проти закону COVERED.

Першопричина: проєкт має ЗАКОН ЧЕСНОТИ — жоден Rust/Python/TSV/blob не доводить
семантику SENS (див. докстрінг check-semantic-coverage-ledger.py). Але стек із
221 рядка PENDING ніде не вимірювався як СТЕК: скільки закрито, скільки мають
кандидата-свідка, скільки — ні. Без виміру прогрес невидимий.

Цей звіт НЕ змінює ledger і не оголошує нічого COVERED. Він лише міряє й
друкує точний контракт доказу, витягнутий із validate() самої охорони.

Контракт COVERED (7 вимог, з validate():132-151):
  1) candidate_sens_witness закінчується на .sens  (UNVERIFIED_NATIVE_PHYSICAL)
  2) negative_sens_witness починається з tests/ і закінчується на .sens,
     і файл ІСНУЄ в дереві
  3) claim_slice непорожній і довший за 20 символів
  4) native_run_receipt_sha256 — 64-символьний hex
  5) native_run_url — справжній URL на GitHub Actions run
  6) native_run_commit_sha — 40-символьний hex
  7) навіть структурно повний рядок НЕ є доказом: квитанцію мусить бути
     звірено з її реальним логом.

А для PENDING діє FALSE_RECEIPT_ON_UNCOVERED: рядок без статусу COVERED не має
права нести квитанцію. Тобто квитанцію НЕ МОЖНА підробити.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/archaeology/semantic-coverage-ledger-2026-10-14.tsv"


def rows() -> list[dict[str, str]]:
    with LEDGER.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def filled(row: dict[str, str], column: str) -> bool:
    return row.get(column, "-") not in ("-", "")


def blockers(row: dict[str, str], root: Path) -> list[str]:
    """Які саме з вимог COVERED не виконано — ТЗ для конкретного рядка.
    Правила взяті з validate():132-151 самої охорони, не з прози."""
    out: list[str] = []
    candidate = row.get("candidate_sens_witness", "-")
    negative = row.get("negative_sens_witness", "-")
    if candidate in ("-", ""):
        out.append("NO_CANDIDATE_WITNESS")
    elif not candidate.endswith(".sens"):
        out.append(f"UNVERIFIED_NATIVE_PHYSICAL (кандидат {Path(candidate).suffix}, треба .sens)")
    elif not (root / candidate).is_file():
        out.append("CANDIDATE_FILE_MISSING")
    if negative in ("-", ""):
        out.append("MISSING_NEGATIVE_SENS")
    elif not (negative.startswith("tests/") and negative.endswith(".sens")
              and (root / negative).is_file()):
        out.append(f"MISSING_NEGATIVE_SENS (негатив {Path(negative).suffix} або поза tests/)")
    if len(row.get("claim_slice", "-").strip()) <= 20:
        out.append("UNMAPPED_SEMANTIC_CLAIM")
    # 4-6: квитанція/url/commit; 7: звірка з логом — статично не перевіряється.
    out.append("NEEDS_NATIVE_RUN (SHA256+URL+commit)")
    return out


def tokens(text: str) -> set[str]:
    """Розпізнавальні токени: латинські слова довші за 3, з розділювачами.
    Числа й короткі слова відкидаємо — вони дають хибні збіги."""
    return {w for w in re.split(r"[^a-z0-9]+", text.lower())
            if len(w) > 3 and not w.isdigit()}


def suggest(row_id: str, laws: list[str], threshold: int = 2) -> list[str]:
    """Артефакти, які ТЕМАТИЧНО перетинаються з рядком. Це ПІДКАЗКА, не
    зіставлення: дослівних збігів немає (перевірено), тож автозаповнення
    покажчиків неможливе — потрібне судження."""
    row_tokens = tokens(row_id)
    scored = []
    for law in laws:
        shared = row_tokens & tokens(law)
        if len(shared) >= threshold:
            scored.append((len(shared), law, sorted(shared)))
    scored.sort(reverse=True)
    return [f"{law} (спільні: {', '.join(shared)})" for _, law, shared in scored[:3]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suggest", action="store_true",
                    help="тематичні підказки для рядків без кандидата (не зіставлення!)")
    ap.add_argument("--ready", action="store_true",
                    help="показати, які вимоги COVERED не виконано для рядків із кандидатом")
    ap.add_argument("--check", action="store_true",
                    help="fail-closed: жоден PENDING не сміє нести квитанцію")
    args = ap.parse_args()
    data = rows()
    statuses = Counter(r["status"] for r in data)
    scopes = Counter(r.get("scope", "?") for r in data)
    with_candidate = [r for r in data if filled(r, "candidate_sens_witness")]
    with_negative = [r for r in data if filled(r, "negative_sens_witness")]
    with_receipt = [r for r in data
                    if filled(r, "native_run_receipt_sha256") or filled(r, "native_run_url")]
    print(f"SEMANTIC-BACKLOG: рядків={len(data)} "
          f"COVERED={statuses['COVERED']} EXCLUDED={statuses['EXCLUDED']} "
          f"PENDING={statuses['PENDING']}")
    print(f"SEMANTIC-BACKLOG: з кандидатом-свідком={len(with_candidate)} "
          f"з негативним={len(with_negative)} з квитанцією={len(with_receipt)} "
          f"без кандидата={len(data) - len(with_candidate)}")
    for scope, count in scopes.most_common():
        print(f"  scope {scope}: {count}")
    # FALSE_RECEIPT_ON_UNCOVERED: квитанція лише на COVERED
    bad = [r for r in with_receipt if r["status"] != "COVERED"]
    if bad:
        raise SystemExit(
            f"FAIL: FALSE_RECEIPT_ON_UNCOVERED — {len(bad)} не-COVERED рядків несуть квитанцію")
    if args.ready:
        print("SEMANTIC-BACKLOG: готовність рядків із кандидатом")
        for row in with_candidate:
            print(f"  {row['retired_test_id'][:64]}")
            print(f"    кандидат: {row['candidate_sens_witness']}")
            for blocker in blockers(row, ROOT):
                print(f"    ✗ {blocker}")
    if args.suggest:
        laws = sorted(p.stem[:-4] for p in (ROOT / "tests/semantic").glob("*-law.sens"))
        print(f"SEMANTIC-BACKLOG: підказки (артефактів {len(laws)}, рядків без кандидата "
              f"{len(data) - len(with_candidate)})")
        shown = 0
        for row in data:
            if filled(row, "candidate_sens_witness"):
                continue
            hints = suggest(row["retired_test_id"], laws)
            if hints:
                print(f"  {row['retired_test_id'][:66]}")
                for hint in hints:
                    print(f"    ~ {hint}")
                shown += 1
            if shown >= 12:
                break
        print(f"SEMANTIC-BACKLOG: рядків із підказками показано={shown}")
        print("SEMANTIC-BACKLOG: це ПІДКАЗКИ, не зіставлення. Перевірений "
              "контрприклад: підказка d3-dotted-pair для рядка "
              "mccarthy.rs::a_dotted_pair_used_directly_as_code_is_an_invalid_form "
              "ХИБНА — закон каже «пара не стає атомом», а рядок — «пара як код "
              "є недійсною формою». Тематична близькість не є тотожністю.")
    if args.check:
        print("SEMANTIC-BACKLOG: PASS квитанцій на не-COVERED немає (закон чесноти тримається)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
