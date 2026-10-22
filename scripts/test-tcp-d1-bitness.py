#!/usr/bin/env python3
"""Механічний аудит чинної української TCP-проєкції та ширин Д1–Д10.

Це лише допоміжний інвентар вихідного тексту, НЕ обчислювач СЕНС.
Жодний результат цього скрипту не доводить оберненості T5M чи виконання.
Мовна істина й помилки встановлюються виключно нативним SENS/Zig.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TCP = ROOT / "lib" / "tcp.lisp"
ROW = re.compile(r"^\s*\(([01]+)\s+", re.MULTILINE)
HOST = re.compile(r"(?<!\w)(?:t|T|NIL)(?!\w)")
# Чинний D1:1 є результатом самої мови: Д3 ATOM(QUOTE ()).
# Зіставляємо лише синтаксичний свідок, не підміняємо SENS обчисленням.
D1_FALLBACK = re.compile(
    r"\(\(атом\?\s+\(як-є\s+\(\)\)\)\s+декодований-вміст\s*\)"
)
REQUIRED = (
    "протокол-передавання-слухати-на",
    "протокол-передавання-слухати",
    "протокол-передавання-обробити-декодоване",
    "протокол-передавання-читати-байти-текст",
    "протокол-передавання-читати",
    "протокол-передавання-записати-текст-байти",
    "протокол-передавання-записати-через-сирий",
    "протокол-передавання-записати",
    "кодування-юнікод-8-декодувати-рядок",
    "кодування-юнікод-8-кодувати-рядок",
    "протокол-передавання-сире-читання",
    "протокол-передавання-сирий-запис",
    "протокол-передавання-сире-слухання",
    "успішно-декодовано?",
)


def check_tcp() -> list[str]:
    if not TCP.is_file():
        return [f"TCP_SOURCE_MISSING path={TCP.relative_to(ROOT)}"]
    source = TCP.read_text(encoding="utf-8")
    active = "\n".join(
        line.split(";", 1)[0] for line in source.splitlines()
    )
    errors: list[str] = []
    for match in HOST.finditer(active):
        errors.append(f"TCP_HOST_TRUTH offset={match.start()} word={match.group()!r}")
    if len(D1_FALLBACK.findall(active)) != 1:
        errors.append("TCP_D1_FALLBACK expected=one_computed_ATOM_QUOTE actual=missing_or_duplicated")
    if "#d1:" in active:
        errors.append("TCP_RETIRED_TYPED_D1_LITERAL")
    if re.search(r"\(\s*[01]{3,10}(?=\s|\))", active):
        errors.append("TCP_RAW_BIT_CALL_HEAD")
    if re.search(r"\(\s*(?:так|ні)(?=\s|\))", active):
        errors.append("TCP_UNBOUND_TRUTH_HEAD")
    if "((функція " in active:
        errors.append("TCP_ANONYMOUS_FUNCTION_HEAD")
    for name in REQUIRED:
        if name not in active:
            errors.append(f"TCP_UKR_SURFACE_MISSING name={name}")
    return errors


def check_domain(width: int) -> list[str]:
    path = ROOT / "lib" / "domains" / f"d{width}.lisp"
    if not path.is_file():
        return [f"DOMAIN_FILE_MISSING domain=D{width}"]
    keys = ROW.findall(path.read_text(encoding="utf-8"))
    expected = 1 << width
    errors = []
    if len(keys) != expected:
        errors.append(f"DOMAIN_ROW_COUNT domain=D{width} expected={expected} actual={len(keys)}")
    for key in keys:
        if len(key) != width:
            errors.append(f"DOMAIN_WORD_WIDTH domain=D{width} word={key}")
            break
    if len(set(keys)) != len(keys):
        errors.append(f"DOMAIN_DUPLICATE_COORDINATE domain=D{width}")
    return errors


def main() -> int:
    errors = check_tcp()
    for width in range(1, 11):
        errors.extend(check_domain(width))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("TCP_D1_DOMAIN_SOURCE_MECHANICAL_PASS semantic=NOT_ATTESTED inverse=NOT_ATTESTED")
    print("NATIVE_PROOF_REQUIRED SENS=paired_and_standalone Zig=T5M_inverse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
