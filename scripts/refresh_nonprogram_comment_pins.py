#!/usr/bin/env python3
"""Оновити пін Git blob після українізації КОМЕНТАРІВ, не коду чи даних.

Без --apply: лише аудит. З --apply: оновлення перевірених маніфестів.
Зміна хоча б одного Lisp-токена забороняє автоматичне перепінування.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from check_ukr_callsite_migration import tokenize
from report_original_migration_candidates import NONPROGRAM_MANIFESTS

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r"[0-9a-f]{40}\Z")


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def source_tokens(data: bytes) -> tuple[tuple[str, str], ...]:
    source = data.decode("utf-8", errors="strict")
    return tuple((token.kind, token.text) for token in tokenize(source))


def repin_row(root: Path, row: dict) -> tuple[str, str] | None:
    """Оновити SHA лише тоді, коли всі Lisp-токени без змін."""
    path, old = row.get("path"), row.get("git_blob_sha1")
    if not isinstance(path, str) or not isinstance(old, str) or not SHA.fullmatch(old):
        raise ValueError("некоректний шлях або SHA маніфесту")
    rel = Path(path)
    if (rel.is_absolute() or rel.suffix != ".lisp" or rel.as_posix() != path
            or any(part in ("", ".", "..") for part in path.split("/"))):
        raise ValueError(f"небезпечний шлях: {path}")
    if any((root / Path(*rel.parts[:i])).is_symlink()
           for i in range(1, len(rel.parts) + 1)):
        raise ValueError(f"символічне посилання: {path}")
    src = root / rel
    if not src.is_file() or src.with_suffix(".sens").exists():
        raise ValueError(f"джерело відсутнє або має .sens: {path}")
    now_bytes = src.read_bytes()
    now = blob_sha(now_bytes)
    if now == old:
        return None
    previous = subprocess.run(
        ["git", "-C", str(root), "cat-file", "blob", old],
        capture_output=True, check=False,
    )
    if previous.returncode or blob_sha(previous.stdout) != old:
        raise ValueError(f"немає попереднього Git blob для перевірки: {path}")
    try:
        old_tokens = source_tokens(previous.stdout)
        new_tokens = source_tokens(now_bytes)
    except (UnicodeError, ValueError) as exc:
        raise ValueError(f"нечитабельні Lisp-токени {path}: {exc}") from exc
    if old_tokens != new_tokens:
        raise ValueError(f"ЗМІНА СЕМАНТИКИ АБО ДАНИХ: {path}; SHA не оновлено")
    return old, now


def refresh(root: Path, manifests: list[str], *, apply: bool = False) -> dict:
    root = root.resolve(strict=True)
    choices = {name: count for _, name, count in NONPROGRAM_MANIFESTS}
    changes: list[tuple[Path, bytes, dict, int]] = []
    reviewed = 0
    for name in manifests:
        if name not in choices:
            raise ValueError(f"невідомий маніфест: {name}")
        file = root / name
        if not file.is_file() or file.is_symlink():
            raise ValueError(f"маніфест відсутній або посилання: {name}")
        before = file.read_bytes()
        record = json.loads(before.decode("utf-8", errors="strict"))
        entries = record.get("entries")
        if (record.get("schema") != "sens-migration-nonprogram-manifest-1"
                or record.get("automatic_sens_companion") is not False
                or record.get("issue") != 4460
                or not isinstance(entries, list) or len(entries) != choices[name]):
            raise ValueError(f"некоректний маніфест: {name}")
        seen: set[str] = set()
        changed = 0
        for row in entries:
            if not isinstance(row, dict) or row.get("path") in seen:
                raise ValueError(f"повтор або неправильний рядок: {name}")
            seen.add(row["path"])
            updated = repin_row(root, row)
            if updated:
                row["git_blob_sha1"] = updated[1]
                changed += 1
                print(f"ЛИШЕ КОМЕНТАРІ: {row['path']} {updated[0]} -> {updated[1]}")
            reviewed += 1
        if changed:
            changes.append((file, before, record, changed))
    # Спершу перевіряємо весь обраний корпус, потім застосовуємо.
    if apply:
        for file, before, _, _ in changes:
            if file.read_bytes() != before:
                raise ValueError(f"маніфест змінився після огляду: {file}")
        for file, _, record, _ in changes:
            tmp = None
            try:
                with tempfile.NamedTemporaryFile("w", encoding="utf-8",
                        dir=file.parent, prefix=".sens-pin-", delete=False) as output:
                    tmp = Path(output.name)
                    json.dump(record, output, ensure_ascii=False, indent=2)
                    output.write("\n")
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(tmp, file)
            finally:
                if tmp is not None:
                    tmp.unlink(missing_ok=True)
    return {
        "reviewed": reviewed,
        "comment_only_changes": sum(item[3] for item in changes),
        "manifests_updated": len(changes) if apply else 0,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--manifest", action="append")
    p.add_argument("--apply", action="store_true")
    args = p.parse_args(argv)
    names = args.manifest or [name for _, name, _ in NONPROGRAM_MANIFESTS]
    try:
        result = refresh(args.root, names, apply=args.apply)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"ВІДМОВА: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
