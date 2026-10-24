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


def main() -> int:
    ap = argparse.ArgumentParser()
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
    if args.check:
        print("SEMANTIC-BACKLOG: PASS квитанцій на не-COVERED немає (закон чесноти тримається)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
