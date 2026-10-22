#!/usr/bin/env python3
"""Лише механічний аудит сучасної української FS-проєкції й Д1–Д10.

Не інтерпретує Lisp, не встановлює істину Д1, не підміняє SENS/Zig.
Для реальної оберненості й виконання застосовувати native T5M суд.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib" / "fs.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(?:t|T|NIL)(?!\w)")
D1_FALLBACK = re.compile(r"\(\(атом\?\s+\(як-є\s+\(\)\)\)\s+декодоване\s*\)")
REQUIRED = (
    "файл-обробити-декодоване",
    "читати-файл",
    "записати-файл",
    "успішно-декодовано?",
    "кодування-юнікод-8-кодувати-рядок",
    "читати-сирий-текст-файла",
    "записати-байти-файла",
)


def check_fs() -> list[str]:
    if not SOURCE.is_file():
        return [f"FS_SOURCE_MISSING path={SOURCE.relative_to(ROOT)}"]
    text = SOURCE.read_text(encoding="utf-8")
    executable = "\n".join(
        line.split(";", 1)[0] for line in text.splitlines()
    )
    errors = []
    for token in HOST.finditer(executable):
        errors.append(f"FS_HOST_TRUTH offset={token.start()} word={token.group()!r}")
    if len(D1_FALLBACK.findall(executable)) != 1:
        errors.append("FS_D1_FALLBACK expected=one_computed_ATOM_QUOTE actual=missing_or_duplicated")
    if "#d1:" in executable:
        errors.append("FS_RETIRED_TYPED_D1_LITERAL")
    if re.search(r"\(\s*[01]{3,10}(?=\s|\))", executable):
        errors.append("FS_RAW_BIT_CALL_HEAD")
    if re.search(r"\(\s*(?:так|ні)(?=\s|\))", executable):
        errors.append("FS_UNBOUND_TRUTH_HEAD")
    if "((функція " in executable:
        errors.append("FS_ANONYMOUS_FUNCTION_HEAD")
    for name in REQUIRED:
        if name not in executable:
            errors.append(f"FS_UKR_SURFACE_MISSING name={name}")
    return errors


def check_domain(width: int) -> list[str]:
    path = ROOT / "lib" / "domains" / f"d{width}.lisp"
    if not path.is_file():
        return [f"DOMAIN_FILE_MISSING domain=D{width}"]
    words = ROW.findall(path.read_text(encoding="utf-8"))
    expected = 1 << width
    errors = []
    if len(words) != expected:
        errors.append(f"DOMAIN_ROW_COUNT domain=D{width} expected={expected} actual={len(words)}")
    for word in words:
        if len(word) != width:
            errors.append(f"DOMAIN_WORD_WIDTH domain=D{width} word={word}")
            break
    if len(set(words)) != len(words):
        errors.append(f"DOMAIN_DUPLICATE_COORDINATE domain=D{width}")
    return errors


def main() -> int:
    errors = check_fs()
    for width in range(1, 11):
        errors.extend(check_domain(width))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("FS_D1_DOMAIN_SOURCE_MECHANICAL_PASS semantic=NOT_ATTESTED inverse=NOT_ATTESTED")
    print("NATIVE_PROOF_REQUIRED SENS=paired_and_standalone Zig=T5M_inverse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
