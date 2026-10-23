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
BITS = re.compile(r"[01]+\Z")  # T5M: слово будь-якої довжини (розділювач — тріт 2)

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
        if not BITS.fullmatch(word) or not 1 <= len(word) <= 11:
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
        if not BITS.fullmatch(word) or not 1 <= len(word) <= 11:
            raise SensT5Error(f"word {i}: requires exact W1..W11 0/1 word")
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


def parse_t5m_words(source: str) -> list[str]:
    """Розбирає T5M-проєкцію у рамці D1–24+: поточний фізичний зріз D1–D10 та D24+."""
    words = source.split()
    if not words:
        raise SensT5Error("empty/unsupported T5M program")
    for index, word in enumerate(words, 1):
        if re.fullmatch(r"[01]+", word) is None:
            raise SensT5Error(
                f"word {index}: T5M requires an exact-width binary word, got {word[:64]!r}"
            )
    return words


def encode_t5m_projection(source: str) -> bytes:
    """Reference default T5M: rank five trits in base 3 into one byte."""
    words = parse_t5m_words(source)
    trits = [ord(trit) - 48 for trit in "2".join(words)]
    trits.extend([2] * (-len(trits) % 5))
    if len(trits) // 5 > MAX_FILE_BYTES:
        raise SensT5Error("physical T5M file exceeds size limit")
    encoded = bytes(
        sum(trits[offset + i] * 3 ** (4 - i) for i in range(5))
        for offset in range(0, len(trits), 5)
    )
    if decode_t5m_bytes(encoded) != words:
        raise SensT5Error("T5M encode/decode exact word identity failed")
    return encoded


def decode_t5m_bytes(data: bytes) -> list[str]:
    """Декодує T5M, не вгадуючи семантику чи викличність слів."""
    if not data:
        raise SensT5Error("empty physical T5M")
    if len(data) > MAX_FILE_BYTES:
        raise SensT5Error("physical T5M file exceeds size limit")
    trits: list[int] = []
    for byte in data:
        if byte >= 243:
            raise SensT5Error("invalid T5M byte outside 0..242")
        group = [0] * 5
        for index in range(4, -1, -1):
            group[index] = byte % 3
            byte //= 3
        trits.extend(group)
    padding = 0
    while trits and trits[-1] == 2:
        trits.pop()
        padding += 1
    if padding >= 5:
        raise SensT5Error("more than four terminal T5M padding trits")
    if not trits or trits[0] == 2 or trits[-1] == 2:
        raise SensT5Error("empty/unsupported physical T5M")
    words: list[str] = []
    current: list[str] = []
    for trit in trits:
        if trit == 2:
            if not current:
                raise SensT5Error("noncanonical repeated or leading T5M separator")
            words.append("".join(current))
            current.clear()
        else:
            current.append("1" if trit else "0")
            if len(current) > MAX_FILE_BYTES * 5:
                raise SensT5Error("T5M word exceeds physical size limit")
    if not current:
        raise SensT5Error("noncanonical trailing T5M separator")
    words.append("".join(current))
    for index, word in enumerate(words, 1):
        if re.fullmatch(r"[01]+", word) is None:
            raise SensT5Error(f"word {index}: invalid exact-width T5M binary word")
    return words


def typed_sha256(words: list[str]) -> str:
    """Включає ширину кожного слова: 0|00 != 000."""
    digest = hashlib.sha256()
    for word in words:
        if re.fullmatch(r"[01]+", word) is None:
            raise SensT5Error("invalid typed word for digest")
        if len(word) <= 255:
            digest.update(bytes([len(word)]))
        else:
            digest.update(b"\xff" + len(word).to_bytes(4, "big"))
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
