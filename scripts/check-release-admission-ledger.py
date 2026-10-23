#!/usr/bin/env python3
"""Fail-closed перевірка релізного admission-ledger (F1–F4) + звірка з репо.

Це МЕХАНІЗМ, не ратифікація. Він не доводить семантику й не вигадує допуск.

Дві незалежні перевірки:
1. ФОРМА запису: усі чотири рівні, названі Contract 11.9, плюс явний `ratified=1`.
   F1 donor provenance, F2 independent positive and negative witnesses,
   F3 behavioural dedup against D1-D9/D10, F4 physical T5 execution.
2. КОНТЕНТ: заявлений `typed_word_sha256` мусить збігатися з реальними байтами
   `.sens` (decode через sens_t5_t5m_codec → typed_sha256). Ledger, що посилається на
   неіснуючий файл, неканонічні байти чи чужий хеш, fail-closed.

Fail-closed: відсутній ledger, невідома схема, зіпсований запис, дубль `sens`,
відсутнє будь-яке з F1–F4, або розбіжність typed_word_sha256 → НЕ admitted.
Порожній ledger → 0/0.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "knowledge" / "release-admission-ledger.json"
SCHEMA = "sens-release-admission-ledger/v1"

REF = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{7,40}:[^:\t\n]+:[1-9][0-9]*(?:-[1-9][0-9]*)?\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DEDUP = re.compile(r"D1-D9@[0-9a-f]{7,40}=NO-MATCH;D10@[0-9a-f]{7,40}=NO-MATCH\Z")
FIELDS = (
    "sens", "typed_word_sha256", "f1_donor_provenance",
    "f2_positive_witness", "f2_negative_witness", "f3_dedup",
    "f4_t5_execution", "ratified",
)


class LedgerBlocked(ValueError):
    """Ledger не допущено: форма/прованація/контент не витримують fail-closed."""


def _load_codec():
    spec = importlib.util.spec_from_file_location("sens_t5_t5m_codec_for_ledger", ROOT / "scripts" / "sens_t5_t5m_codec.py")
    if spec is None or spec.loader is None:
        raise LedgerBlocked("не вдалося завантажити sens_t5_t5m_codec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


CODEC = _load_codec()


def content_sha256(root: Path, sens: str) -> str:
    # An admission witness must be a canonical regular file within the selected
    # checkout, never a symlink into an untracked or external directory.
    # Path.resolve() alone follows symlinks, so reject every linked component.
    relative = Path(sens)
    if (relative.is_absolute() or relative.as_posix() != sens
            or relative.suffix != ".sens" or ".." in relative.parts):
        raise LedgerBlocked(f"{sens}: неканонічний шлях .sens")
    try:
        repo_root = root.resolve(strict=True)
        path = repo_root
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise LedgerBlocked(f"{sens}: symlink не може бути доказовим .sens")
        resolved = path.resolve(strict=True)
        if not resolved.is_relative_to(repo_root) or not resolved.is_file():
            raise LedgerBlocked(f"{sens}: файл .sens поза дозволеним деревом")
        # Verify the actual opened inode, not a path that could be rebound
        # between the directory check and the content read. A hardlink with
        # identical physical T5 bytes is still ambiguous release provenance.
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            inode = os.fstat(stream.fileno())
            if not stat.S_ISREG(inode.st_mode) or inode.st_nlink != 1:
                raise LedgerBlocked(
                    f"{sens}: hardlink або неунікальний regular-file inode не є доказом .sens"
                )
            words = CODEC.decode_bytes(stream.read())
    except (OSError, RuntimeError) as exc:
        raise LedgerBlocked(f"{sens}: немає доступного канонічного файла .sens ({exc})") from exc
    except CODEC.SensT5Error as exc:
        raise LedgerBlocked(f"{sens}: неканонічні T5-байти ({exc})") from exc
    return CODEC.typed_sha256(words)


def validate_ledger(document: object, *, root: Path = ROOT, verify_content: bool = True) -> dict:
    if not isinstance(document, dict):
        raise LedgerBlocked("ledger не є JSON-об'єктом")
    if document.get("schema") != SCHEMA:
        raise LedgerBlocked(f"невідома схема (очікую {SCHEMA})")
    entries = document.get("entries")
    if not isinstance(entries, list):
        raise LedgerBlocked("entries має бути списком")

    seen: set[str] = set()
    form_candidates: list[str] = []
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or set(entry) != set(FIELDS):
            raise LedgerBlocked(f"запис {index}: набір полів не збігається з канонічним")
        sens = entry["sens"]
        if not isinstance(sens, str) or not sens.endswith(".sens") or sens.startswith("/") or ".." in sens.split("/"):
            raise LedgerBlocked(f"запис {index}: некоректний шлях sens")
        if sens in seen:
            raise LedgerBlocked(f"запис {index}: дубль sens {sens}")
        seen.add(sens)
        claimed = str(entry["typed_word_sha256"])
        if not SHA256.fullmatch(claimed):
            raise LedgerBlocked(f"запис {index}: typed_word_sha256 не 64-hex")
        if verify_content and content_sha256(root, sens) != claimed:
            raise LedgerBlocked(f"запис {index}: typed_word_sha256 не збігається з .sens {sens}")
        for field in ("f1_donor_provenance", "f2_positive_witness",
                      "f2_negative_witness", "f4_t5_execution"):
            if not REF.fullmatch(str(entry[field])):
                raise LedgerBlocked(f"запис {index}: {field} не owner/repo@COMMIT:path:line")
        if str(entry["f2_positive_witness"]) == str(entry["f2_negative_witness"]):
            raise LedgerBlocked(
                f"запис {index}: F2 positive and negative witnesses must reference distinct evidence"
            )
        if not DEDUP.fullmatch(str(entry["f3_dedup"])):
            raise LedgerBlocked(f"запис {index}: f3_dedup потребує окремих D1-D9 та D10 SHA з NO-MATCH")
        ratified = entry["ratified"]
        if ratified not in (0, 1) or isinstance(ratified, bool):
            raise LedgerBlocked(f"запис {index}: ratified має бути 0 або 1")
        if ratified == 1:
            form_candidates.append(sens)

    # Exact T5 bytes prove content integrity, not SENS semantic execution.
    # F1-F4 references above are only format-checked; they are NOT independent
    # native SENS positive/negative results or an executable Ukrainian oracle.
    # Never derive release admission from byte integrity or owner ratification.
    content_verified = sorted(form_candidates) if verify_content else []
    return {
        "schema": SCHEMA,
        "validation_mode": "content_verified" if verify_content else "form_only",
        "entries": len(entries),
        "form_candidates": len(form_candidates),
        "content_verified": len(content_verified),
        "content_verified_sens": content_verified,
        "uk_oracle_verified": 0,
        "release_admitted": 0,
        "admitted_sens": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="fail-closed release admission-ledger check")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--no-verify-content", action="store_true",
                        help="перевіряти лише форму (для тестів/чернеток)")
    args = parser.parse_args(argv)
    if not args.ledger.is_file():
        print(f"RELEASE_ADMISSION_BLOCKED: ledger відсутній: {args.ledger}", file=sys.stderr)
        return 2
    try:
        document = json.loads(args.ledger.read_text(encoding="utf-8"))
        receipt = validate_ledger(document, root=args.root, verify_content=not args.no_verify_content)
    except (LedgerBlocked, json.JSONDecodeError, OSError) as exc:
        print(f"RELEASE_ADMISSION_BLOCKED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    if args.no_verify_content:
        print(f"RELEASE_ADMISSION_FORM_ONLY entries={receipt['entries']} candidates={receipt['form_candidates']} admitted=0")
    else:
        # Physical integrity does not verify F2/F4 or the native Ukrainian oracle.
        # An independently executed semantic witness is a separate release gate.
        print("RELEASE_ADMISSION_BLOCKED: F2/F4 native SENS verdict and Ukrainian oracle not verified", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
