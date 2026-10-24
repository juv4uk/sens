#!/usr/bin/env python3
"""Fail-closed перевірка релізного admission-ledger (F1–F4) + звірка з репо.

Це МЕХАНІЗМ, не ратифікація. Він не доводить семантику й не вигадує допуск.

Три незалежні перевірки:
1. ФОРМА запису: усі чотири рівні, названі Contract 11.9, плюс явний `ratified=1`.
   F1 donor provenance, F2 independent positive and negative witnesses,
   F3 behavioural dedup against D1-D9/D10, F4 physical T5 execution.
2. КОНТЕНТ: заявлений `typed_word_sha256` мусить збігатися з реальними байтами
   `.sens` (decode через sens_t5_t5m_codec → typed_sha256). Ledger, що посилається на
   неіснуючий файл, неканонічні байти чи чужий хеш, fail-closed.
3. НАТИВНИЙ ВЕРДИКТ (лише за повної перевірки, без `--no-verify-content`): чекер
   ВИКЛИКАЄ `scripts/connect-release-admission-native.py` і бере вердикт ЗВІДТИ.
   `uk_oracle_verified` / `release_admitted` стають >0 ЛИШЕ якщо конектор повернув 0
   і всі записи NATIVE-VERIFIED (реальні F4-докази відтворено). Інакше — 0 і BLOCKED,
   із явним зазначенням того, ЩО САМЕ сказав конектор (щоб причина була видима).
   Чекер ніколи не вигадує й не хардкодить вердикт.

Fail-closed: відсутній ledger, невідома схема, зіпсований запис, дубль `sens`,
відсутнє будь-яке з F1–F4, розбіжність typed_word_sha256, ВІДСУТНІЙ/провалений
конектор або не всі записи NATIVE-VERIFIED → НЕ admitted.
Порожній ledger → 0/0.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "knowledge" / "release-admission-ledger.json"
SCHEMA = "sens-release-admission-ledger/v1"

# The native connector is the only component that actually runs the F4 proofs and
# reproduces the SENS verdict. The checker consults it instead of asserting a
# verdict of its own. Missing/unreadable/failed connector stays fail-closed.
CONNECTOR_NAME = "connect-release-admission-native.py"
CONNECTOR_TIMEOUT = 900.0

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
            # `.sens` is T5M by default. The legacy T5 decoder rejects valid
            # D24+ words before their typed physical hash can be inspected.
            # This remains byte integrity only, never semantic F2/F4 admission.
            words = CODEC.decode_t5m_bytes(stream.read())
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
    # The native verdict is supplied separately, by the connector (see main()).
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


def _native_verified_sens(stdout: str) -> list[str]:
    """Collect the ledger entries the connector reported NATIVE-VERIFIED.

    The connector prints one ``NATIVE-VERIFIED <sens> script=<rel> line=<n>`` line
    per entry whose native proof actually ran. Only that explicit token counts;
    BLOCKED lines, echoes and summaries are ignored here. This function never
    infers a verdict -- it reads what the connector said.
    """
    verified: list[str] = []
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "NATIVE-VERIFIED":
            verified.append(parts[1])
    return verified


def run_native_connector(ledger: Path, root: Path, timeout: float) -> tuple[int, str, str]:
    """Run scripts/connect-release-admission-native.py and return (rc, stdout, stderr).

    Fail-closed: a missing connector, a spawn failure or a timeout is reported as a
    non-zero result with no verdict -- never as verification.
    """
    connector = root / "scripts" / CONNECTOR_NAME
    if not connector.is_file():
        return 127, "", f"connector відсутній: {connector}"
    command = [
        sys.executable, str(connector),
        "--ledger", str(ledger), "--root", str(root),
    ]
    try:
        proc = subprocess.run(
            command, cwd=str(root), capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"connector timeout після {timeout:g}s"
    except OSError as exc:
        return 126, "", f"connector не запускається: {exc}"
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="fail-closed release admission-ledger check")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--no-verify-content", action="store_true",
                        help="перевіряти лише форму (для тестів/чернеток)")
    parser.add_argument("--connector-timeout", type=float, default=CONNECTOR_TIMEOUT,
                        help="таймаут виклику native-конектора, секунди")
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

    if args.no_verify_content:
        print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
        print(f"RELEASE_ADMISSION_FORM_ONLY entries={receipt['entries']} candidates={receipt['form_candidates']} admitted=0")
        return 0

    # Full verification: take the native verdict from the connector. The checker
    # runs no proof itself and never hardcodes an admission.
    rc, out, err = run_native_connector(args.ledger, args.root, args.connector_timeout)
    verified = _native_verified_sens(out)
    print(f"NATIVE-CONNECTOR-CALL ledger={args.ledger} root={args.root} rc={rc} verified={len(verified)}")
    # Surface exactly what the connector said, so a blocked verdict shows a real
    # reason instead of an unexplained constant 0. Its own lines already carry the
    # NATIVE-CONNECTOR-* provenance, so they are forwarded verbatim.
    for line in out.splitlines():
        if line.strip():
            print(line)
    for line in err.splitlines():
        if line.strip():
            print(line, file=sys.stderr)

    native_ok = rc == 0 and bool(verified) and len(verified) == receipt["entries"]
    if native_ok:
        # Real count, taken from the connector: it returned 0 only because every
        # entry's native F4 proof reproduced. Never a hardcoded 1.
        receipt["uk_oracle_verified"] = len(verified)
        receipt["release_admitted"] = len(verified)
        receipt["admitted_sens"] = sorted(verified)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))

    if not native_ok:
        print(
            "RELEASE_ADMISSION_BLOCKED: native connector did not reproduce every entry "
            f"(rc={rc}, verified={len(verified)}/{receipt['entries']}); "
            f"verdict taken from scripts/{CONNECTOR_NAME}",
            file=sys.stderr,
        )
        return 2
    print(f"RELEASE_ADMISSION_PASS native connector rc=0 verified={len(verified)}/{receipt['entries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
