#!/usr/bin/env python3
"""Фізичний T5-файл .sens для ТОЧНИХ двійкових слів SENS.

Семантичний payload складається тільки з 0/1 слів D1..D9.
Трит 2 існує лише між словами (ніколи не всередині SENS слова).
Один байт містить п'ять тритів (0..242), padding = 0..4 фінальних 2.
Завершувача 22 немає: кінець файла визначається кількістю байтів.
Цей транспортер НЕ встановлює семантику чи граматику Lisp.
"""
from __future__ import annotations

import hashlib
import re

MAX_FILE_BYTES = 4 * 1024 * 1024
BITS = re.compile(r"[01]{1,9}\Z")


class SensT5Error(ValueError):
    """Неканонічний або не допущений в точну бітову проєкцію файл."""


def parse_words(source: str) -> list[str]:
    """Fail closed: будь-яка назва, цифра 2, коментар або Lisp-пунктуація — BLOCK."""
    words = source.split()
    if not words:
        raise SensT5Error("empty/unsupported binary program")
    for i, word in enumerate(words, 1):
        if not BITS.fullmatch(word):
            raise SensT5Error(
                f"word {i}: requires exact D1..D9 0/1 word, got {word[:64]!r}"
            )
    return words


def encode_words(words: list[str]) -> bytes:
    if not words:
        raise SensT5Error("empty program")
    for i, word in enumerate(words, 1):
        if not BITS.fullmatch(word):
            raise SensT5Error(f"word {i}: not exact 0/1 width 1..9")
    trits = "2".join(words)
    trits += "2" * (-len(trits) % 5)
    if len(trits) // 5 > MAX_FILE_BYTES:
        raise SensT5Error("physical file exceeds size limit")
    return bytes(int(trits[i:i + 5], 3) for i in range(0, len(trits), 5))


def decode_bytes(data: bytes) -> list[str]:
    if not data:
        raise SensT5Error("empty physical .sens")
    if len(data) > MAX_FILE_BYTES:
        raise SensT5Error("physical file exceeds size limit")
    if any(byte >= 243 for byte in data):
        raise SensT5Error("invalid T5 byte outside 0..242")
    trits = "".join(
        "".join(str((byte // (3 ** exp)) % 3) for exp in (4, 3, 2, 1, 0))
        for byte in data
    )
    padding = len(trits) - len(trits.rstrip("2"))
    if padding >= 5:
        raise SensT5Error("more than four terminal padding trits")
    words = parse_words(trits[:len(trits) - padding].replace("2", " "))
    if encode_words(words) != data:
        raise SensT5Error("noncanonical byte representation")
    return words


def encode_projection(source: str) -> bytes:
    words = parse_words(source)
    encoded = encode_words(words)
    if decode_bytes(encoded) != words:
        raise SensT5Error("T5 encode/decode exact word identity failed")
    return encoded


def typed_sha256(words: list[str]) -> str:
    """Включає ширину кожного слова: 0|00 != 000."""
    digest = hashlib.sha256()
    for word in words:
        if not BITS.fullmatch(word):
            raise SensT5Error("invalid typed word for digest")
        digest.update(bytes([len(word)]))
        digest.update(int(word, 2).to_bytes((len(word) + 7) // 8, "big"))
    return digest.hexdigest()
