#!/usr/bin/env python3
"""Фізичний T5-файл .sens для ТОЧНИХ двійкових слів SENS.

Фізичний носій передає W1..W11; семантику та викличність встановлює тільки SENS.
Трит 2 існує лише між словами (ніколи не всередині SENS слова).
Один байт містить п'ять тритів (0..242), padding = 0..4 фінальних 2.
Завершувача 22 немає: кінець файла визначається кількістю байтів.
Цей транспортер НЕ встановлює семантику чи граматику Lisp.
"""
from __future__ import annotations

import hashlib
import re

MAX_FILE_BYTES = 4 * 1024 * 1024
BITS = re.compile(r"[01]{1,11}\Z")

# A physical T5 byte has exactly five base-3 symbols (0, 1, or delimiter 2).
# The fixed 243-case transport lookup avoids text formatting per byte.
TRITS_BY_BYTE = tuple(
    bytes((byte // divisor) % 3 for divisor in (81, 27, 9, 3, 1))
    for byte in range(243)
)


class SensT5Error(ValueError):
    """Неканонічний або не допущений в точну бітову проєкцію файл."""


def parse_words(source: str) -> list[str]:
    """Fail closed: будь-яка назва, цифра 2, коментар або Lisp-пунктуація — BLOCK."""
    words = source.split()
    if not words:
        raise SensT5Error("empty/unsupported binary program")
    for i, word in enumerate(words, 1):
        if not BITS.fullmatch(word) or not (1 <= len(word) <= 11):
            raise SensT5Error(
                f"word {i}: requires exact W1..W11 0/1 word, got {word[:64]!r}"
            )
    return words


def encode_typed_domain_words(words: list[tuple[str, str]]) -> bytes:
    """Pack *explicitly typed* current D1–D9 words, without widening.

    This is a transport boundary, NOT semantic or callable admission.
    D2 is syntax, D7 is data; matching numeric W8 bits never authorizes SID8.
    D10's 1024-coordinate owner codebook is ratified, but this typed
    PROGRAM admission stays pending. The separate raw W10/W11 physical
    transport remains valid and must not be disabled.
    """
    if not words:
        raise SensT5Error("empty exact-domain word stream")
    accepted = []
    for index, item in enumerate(words, 1):
        if not isinstance(item, tuple) or len(item) != 2:
            raise SensT5Error(f"word {index}: require (domain, exact bits)")
        domain, bits = item
        if domain == "D10":
            raise SensT5Error(
                f"word {index}: D10_RUNTIME_HOLD: 10-bit identity is not typed program admission"
            )
        if not isinstance(domain, str) or not re.fullmatch(r"D[1-9]", domain):
            raise SensT5Error(
                f"word {index}: explicit current D1..D9 tag required; SID8 cannot be inferred"
            )
        # Domain tags are type addresses, never parse their suffix through
        # a decimal intermediary. Values here are the already-known bit widths.
        width = {
            "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D5": 5,
            "D6": 6, "D7": 7, "D8": 8, "D9": 9,
        }[domain]
        if not isinstance(bits, str) or len(bits) != width or re.fullmatch(r"[01]+", bits) is None:
            raise SensT5Error(
                f"word {index}: {domain} requires exactly {width} binary digits"
            )
        accepted.append(bits)
    return encode_words(accepted)

def encode_words(words: list[str]) -> bytes:
    if not words:
        raise SensT5Error("empty program")
    for i, word in enumerate(words, 1):
        if not BITS.fullmatch(word) or not (1 <= len(word) <= 11):
            raise SensT5Error(f"word {i}: not exact 0/1 width 1..11")
    trits = "2".join(words)
    trits += "2" * (-len(trits) % 5)
    if len(trits) // 5 > MAX_FILE_BYTES:
        raise SensT5Error("physical file exceeds size limit")
    return bytes(int(trits[i:i + 5], 3) for i in range(0, len(trits), 5))


def decode_bytes(data: bytes) -> list[str]:
    """Decode physical T5 once, preserving exact W1..W11 word boundaries.

    Trit 2 separates two words exactly once. After the final word only
    zero to four padding trits are legal. No full-file textual trit buffer,
    re-encoding, decimal intermediary, or new domain/callability law.
    """
    if not data:
        raise SensT5Error("empty physical .sens")
    if len(data) > MAX_FILE_BYTES:
        raise SensT5Error("physical file exceeds size limit")
    words: list[str] = []
    current: list[str] = []
    padding = 0
    for byte in data:
        if byte >= 243:
            raise SensT5Error("invalid T5 byte outside 0..242")
        for trit in TRITS_BY_BYTE[byte]:
            if trit == 2:
                if current:
                    words.append("".join(current))
                    current.clear()
                    padding = 1
                else:
                    padding += 1
                if padding >= 5:
                    raise SensT5Error("more than four terminal padding trits")
            else:
                if padding > 1:
                    raise SensT5Error("noncanonical repeated separator")
                if padding and not words:
                    raise SensT5Error("noncanonical leading separator")
                padding = 0
                current.append("1" if trit else "0")
                if len(current) > 11:
                    raise SensT5Error("word exceeds exact W1..W11 width")
    if current:
        words.append("".join(current))
    if not words:
        raise SensT5Error("empty/unsupported binary program")
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


def encode_d7_uk_t5(text: str) -> bytes:
    """Ukrainian keyboard glyphs -> owner D7:W7 -> existing physical T5.

    D7:W7 space and period are text data inside this explicit record.
    D2:W2 structural separator/dot never become text or Lisp execution.
    Parentheses, tabs and newlines remain unsupported as text projections
    pending a separate context decision.
    """
    from d7_symbol_codec import D7CodecError, current_codec

    try:
        cells = current_codec().encode_text(text, "ук")
    except D7CodecError as exc:
        raise SensT5Error(f"D7_UK_INPUT: {exc}") from exc
    if not cells:
        raise SensT5Error("empty D7 text record")
    physical = encode_words(list(cells))
    if decode_d7_t5(physical, "ук") != text:
        raise SensT5Error("D7/T5 failed strict word-and-text roundtrip")
    return physical


def decode_d7_t5(data: bytes, surface: str = "ук") -> str:
    """Unpack canonical T5 and require *every* word to be admitted D7 W7.

    Never reinterpret any D2 word as D7 text. Surface translation is explicit.
    """
    from d7_symbol_codec import D7CodecError, current_codec

    words = decode_bytes(data)
    if any(len(word) != 7 for word in words):
        raise SensT5Error("D7_T5_WIDTH: only exact W7 words are allowed")
    try:
        return current_codec().render_text(words, surface)
    except D7CodecError as exc:
        raise SensT5Error(f"D7_T5_PROJECTION: {exc}") from exc
