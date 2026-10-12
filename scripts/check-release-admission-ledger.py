#!/usr/bin/env python3
"""Fail-closed формальна перевірка релізного admission-ledger (F1–F4).

Це МЕХАНІЗМ, не ратифікація. Він не доводить семантику й не вигадує допуск:
перевіряє лише ФОРМУ записів і рахує admitted строго за наявністю всіх чотирьох
рівнів доказу, названих Contract 11.9, ПЛЮС явного `ratified=1` власника.

Рівні (language-contract.lisp): F1 donor provenance, F2 independent positive and
negative witnesses, F3 behavioural dedup against D1-D9/D10, F4 physical T5
execution — кожен окремо gated.

Fail-closed: відсутній ledger, невідома схема, зіпсований запис, дубль `sens`
або відсутнє будь-яке з F1–F4 → запис НЕ admitted. Порожній ledger → 0/0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "knowledge" / "release-admission-ledger.json"
SCHEMA = "sens-release-admission-ledger/v1"

# owner/repo@COMMIT:path:line[-line]
REF = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{7,40}:[^:\t\n]+:[1-9][0-9]*(?:-[1-9][0-9]*)?\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DEDUP = re.compile(r"D1-D9@[0-9a-f]{7,40}=NO-MATCH;D10@[0-9a-f]{7,40}=NO-MATCH\Z")
FIELDS = (
    "sens", "typed_word_sha256", "f1_donor_provenance",
    "f2_positive_witness", "f2_negative_witness", "f3_dedup",
    "f4_t5_execution", "ratified",
)


class LedgerBlocked(ValueError):
    """Ledger не допущено: форма/прованація не витримують fail-closed."""


def validate_ledger(document: object) -> dict:
    if not isinstance(document, dict):
        raise LedgerBlocked("ledger не є JSON-об'єктом")
    if document.get("schema") != SCHEMA:
        raise LedgerBlocked(f"невідома схема (очікую {SCHEMA})")
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise LedgerBlocked("entries має бути списком")

    seen: set[str] = set()
    admitted: list[dict] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or set(entry) != set(FIELDS):
            raise LedgerBlocked(f"запис {index}: набір полів не збігається з канонічним")
        sens = entry["sens"]
        if not isinstance(sens, str) or not sens.endswith(".sens") or sens.startswith("/") or ".." in sens.split("/"):
            raise LedgerBlocked(f"запис {index}: некоректний шлях sens")
        if sens in seen:
            raise LedgerBlocked(f"запис {index}: дубль sens {sens}")
        seen.add(sens)
        if not SHA256.fullmatch(str(entry["typed_word_sha256"])):
            raise LedgerBlocked(f"запис {index}: typed_word_sha256 не 64-hex")
        for field in ("f1_donor_provenance", "f2_positive_witness",
                      "f2_negative_witness", "f4_t5_execution"):
            if not REF.fullmatch(str(entry[field])):
                raise LedgerBlocked(f"запис {index}: {field} не owner/repo@COMMIT:path:line")
        if not DEDUP.fullmatch(str(entry["f3_dedup"])):
            raise LedgerBlocked(f"запис {index}: f3_dedup потребує окремих D1-D9 та D10 SHA з NO-MATCH")
        ratified = entry["ratified"]
        if ratified not in (0, 1) or isinstance(ratified, bool):
            raise LedgerBlocked(f"запис {index}: ratified має бути 0 або 1")
        if ratified == 1:
            admitted.append(entry)

    return {
        "schema": SCHEMA,
        "entries": len(entries),
        "uk_oracle_verified": len(admitted),
        "release_admitted": len(admitted),
        "admitted_sens": sorted(e["sens"] for e in admitted),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="fail-closed release admission-ledger check")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    args = parser.parse_args(argv)
    if not args.ledger.is_file():
        print(f"RELEASE_ADMISSION_BLOCKED: ledger відсутній: {args.ledger}", file=sys.stderr)
        return 2
    try:
        document = json.loads(args.ledger.read_text(encoding="utf-8"))
        receipt = validate_ledger(document)
    except (LedgerBlocked, json.JSONDecodeError, OSError) as exc:
        print(f"RELEASE_ADMISSION_BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    print(f"RELEASE_ADMISSION_PASS entries={receipt['entries']} admitted={receipt['release_admitted']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
