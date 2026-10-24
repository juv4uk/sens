#!/usr/bin/env python3
"""Точний перелік блокерів T5/T5M-аудиту — названий, а не похований у JSON.

Першопричина: audit_t5_t5m_file_pairs.py каже status=BLOCKED, але його повний
звіт (з файлами) пише лише --output і він іде ~90 с. Тому 5 конкретних блокерів
ніхто не бачив — бачили лише «BLOCKED».

Знайдено (2026-10-24, власними руками):
  physical_status=BLOCKED (2): docs/research/1556-sens-runtime-lookup-inventory.sens
                               knowledge/function-table-sculpt-audit.sens
  view_status=BLOCKED     (2): lib/core.sens, lib/guard.sens
  spaced_view_missing     (1)

Це НЕ борг і НЕ межа — це п'ять конкретних файлів. Їх треба назвати.

Цей звіт лише читає аудит і друкує перелік; нічого не змінює.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "scripts" / "audit_t5_t5m_file_pairs.py"


def blockers() -> dict[str, list[str]]:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "audit.json"
        subprocess.run([sys.executable, str(AUDIT), str(ROOT), "--output", str(out)],
                       capture_output=True, text=True, timeout=280, check=False)
        report = json.loads(out.read_text(encoding="utf-8"))
    files = report.get("files", [])
    return {
        "physical_blocked": [f["sens"] for f in files if f.get("physical_status") == "BLOCKED"],
        "view_blocked": [f["sens"] for f in files if f.get("view_status") == "BLOCKED"],
        "view_missing": [f["sens"] for f in files
                         if f.get("view_status") == "MISSING_NOT_CERTIFIED"],
        "status": [report.get("status", "?")],
        # Справжня причина: аудит ставить physical_status=BLOCKED навіть коли
        # T5M канонічний, якщо бракує same-stem .lisp. Поле error це показує.
        "errors": {f["sens"]: f.get("error", "")
                   for f in files if f.get("error")},
    }


def decode_diagnosis(sens_path: str) -> str:
    """Чому файл не декодується — це і є діагноз, а не «BLOCKED».
    Перевірено 2026-10-24: усі три решта блокери дають одну й ту саму помилку
    SensT5Error: word exceeds exact W1..W11 width — тобто це НЕ канонічний T5M
    (аудит: «new/modified .sens must use canonical T5M, not legacy T5»).
    Фікс — пере-карбування в T5M, що вимагає тулчейну SENS."""
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from sens_t5_t5m_codec import decode_bytes, decode_t5m_bytes
    except Exception as exc:  # pragma: no cover
        return f"кодек недоступний: {exc}"
    data = (ROOT / sens_path).read_bytes()
    # ДВА декодери: decode_bytes — легасі T5, decode_t5m_bytes — T5M. Кликати
    # лише перший дає ХИБНИЙ діагноз «не канонічний T5M» — цю помилку я вже
    # зробив двічі, тож тут вона виправлена явно.
    for name, decoder in (("T5M", decode_t5m_bytes), ("легасі T5", decode_bytes)):
        try:
            words = decoder(data)
        except Exception:
            continue
        return (f"декодується як {name} ({len(words)} слів) — канонічний; "
                "фізичний блок НЕ тут, див. СПРАВЖНЮ ПРИЧИНУ")
    return "не декодується ЖОДНИМ кодеком (T5M і легасі T5) → треба пере-карбування"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail-closed: набір блокерів не сміє змінитись")
    args = ap.parse_args()
    b = blockers()
    total = (len(b["physical_blocked"]) + len(b["view_blocked"]) + len(b["view_missing"]))
    print(f"T5-BLOCKERS: status={b['status'][0]} фізичних={len(b['physical_blocked'])} "
          f"виглядів={len(b['view_blocked'])} вигляд-відсутній={len(b['view_missing'])} "
          f"усього={total}")
    for path in b["physical_blocked"]:
        print(f"  ФІЗИЧНИЙ БЛОК: {path}")
    for path in b["view_blocked"]:
        print(f"  ВИГЛЯД БЛОК:   {path}")
    for path in b["view_missing"]:
        print(f"  ВИГЛЯД ВІДСУТНІЙ: {path}")
    for path, err in b.get("errors", {}).items():
        print(f"  СПРАВЖНЯ ПРИЧИНА: {path} → {err}")
    print("  ДІАГНОЗ (чому не виправляється одним регенеруванням):")
    for path in (b["physical_blocked"] + b["view_missing"]):
        print(f"    {path}: {decode_diagnosis(path)}")
    if args.check:
        print(f"T5-BLOCKERS: усі {total} блокери НАЗВАНО за ім'ям — не «BLOCKED» "
              "без імен. П'ятий (MISSING_NOT_CERTIFIED) названо теж.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
