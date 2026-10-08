#!/usr/bin/env python3
"""Дослідні нетекстові .sens носії для точних доменних слів.

НЕ є ратифікованим .sens форматом і НЕ перевіряє семантику виконання.
Два алгоритми справді кодують/декодують фізичні байти, а не ASCII "01".
Вертикальні рядки — лише людська проєкція.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Відома D7 текстова ідентичність; використання як межі/EOS лише гіпотеза.
D7_SPACE = "1100000"
D7_NEWLINE = "1100001"  # *експериментальний* транспортний EOS, не нова семантика.
WIDTH_TO_TAG = {**{i: i for i in range(1, 10)}, 24: 10, 48: 11, 96: 12, 192: 13}
TAG_TO_WIDTH = {v: k for k, v in WIDTH_TO_TAG.items()}
HEADER_BITS = 4
MAX_PROGRAM_BITS = 8_000_000


class CodecError(ValueError):
    pass


def ratified_widths(root=ROOT):
    foundation = json.loads((root / "knowledge/d1-d9-foundation.json").read_text())
    numbers = json.loads((root / "knowledge/number-width-ratified.json").read_text())
    if foundation.get("status") != "owner-ratified" or numbers.get("status") != "owner-ratified":
        raise CodecError("width authority is not owner-ratified")
    domains = foundation.get("domains", {})
    for n in range(1, 10):
        desc = domains.get(f"D{n}", {})
        if desc.get("width") != n or not desc.get("residents"):
            raise CodecError(f"D{n} absent in ratified source")
    if domains["D7"]["residents"].get(D7_SPACE) != "sign.space":
        raise CodecError("D7 sign.space coordinate drift")
    if domains["D7"]["residents"].get(D7_NEWLINE) != "sign.newline":
        raise CodecError("D7 sign.newline coordinate drift")
    widths = numbers.get("ratified_prefix_bits")
    if widths != [24, 48, 96, 192]:
        raise CodecError("Number width authority drift")
    return set(range(1, 10)) | set(widths)


def source_words(lines: str, allowed=None) -> tuple[str, ...]:
    """По одному доменному слову в рядку, без роздільників у фізичному файлі."""
    allowed = ratified_widths() if allowed is None else allowed
    if not lines or not lines.endswith("\n"):
        raise CodecError("vertical display must end with newline")
    words = tuple(lines.splitlines())
    if not words or any(not w or set(w) - {"0", "1"} for w in words):
        raise CodecError("one 0/1 word per line; no extra spaces or blank lines")
    if any(len(w) not in allowed for w in words):
        raise CodecError("word outside ratified D1-D9/Number width ladder")
    if sum(map(len, words)) > MAX_PROGRAM_BITS:
        raise CodecError("experiment size limit")
    return words


def render_vertical(words: tuple[str, ...]) -> str:
    return "".join(w + "\n" for w in words)


def _pack(bits: str) -> bytes:
    # Єдине фізичне вирівнювання — в кінці файла; його вартість обов'язкова.
    return bytes(int((bits[i:i+8] + "0" * 8)[:8], 2) for i in range(0, len(bits), 8))


def _bits(data: bytes) -> str:
    if not data:
        raise CodecError("empty file")
    if len(data) * 8 > 2 * MAX_PROGRAM_BITS + 8 * MAX_PROGRAM_BITS:
        raise CodecError("experiment size limit")
    return "".join(f"{b:08b}" for b in data)


def _canonical_tail(bits: str, pos: int) -> None:
    if pos > len(bits) or len(bits) - pos >= 8 or any(b != "0" for b in bits[pos:]):
        raise CodecError("noncanonical trailing bits or extra bytes")


def encode_width4(words: tuple[str, ...]) -> bytes:
    """Контейнер А: 4-бітний тег ширини перед кожним n-бітовим словом, tag 0000 = EOS."""
    if not words:
        raise CodecError("no words")
    allowed = ratified_widths()
    if any(len(w) not in allowed or set(w) - {"0", "1"} for w in words):
        raise CodecError("unsupported width/word")
    bits = "".join(f"{WIDTH_TO_TAG[len(w)]:04b}" + w for w in words) + "0000"
    return _pack(bits)


def decode_width4(data: bytes) -> tuple[str, ...]:
    bits = _bits(data)
    pos, words = 0, []
    while True:
        if pos + 4 > len(bits):
            raise CodecError("missing width tag or EOS")
        tag = int(bits[pos:pos+4], 2)
        pos += 4
        if tag == 0:
            if not words:
                raise CodecError("no words")
            _canonical_tail(bits, pos)
            result = tuple(words)
            if encode_width4(result) != data:
                raise CodecError("noncanonical width carrier")
            return result
        width = TAG_TO_WIDTH.get(tag)
        if width is None or pos + width > len(bits):
            raise CodecError("unknown width or truncated word")
        words.append(bits[pos:pos+width])
        pos += width
        if pos > MAX_PROGRAM_BITS:
            raise CodecError("size limit")


def _safe_word(bits: str) -> str:
    """0->0; 1->10; усі слова закінчуються на 0, тому всередині немає '11'."""
    return "".join("10" if bit == "1" else "0" for bit in bits)


def encode_d7_marker(words: tuple[str, ...]) -> bytes:
    """Контейнер Б: D7 SPACE-маркер + експериментальний D7 NEWLINE/EOS.

    Вміст кодовано 0->0, 1->10, тому маркер '11...' ніколи
    не з'явиться всередині кодованого слова. Не означає, що
    D7 текстове значення стало структурою D2.
    """
    if not words:
        raise CodecError("no words")
    allowed = ratified_widths()
    if any(len(w) not in allowed or set(w) - {"0", "1"} for w in words):
        raise CodecError("unsupported width/word")
    return _pack(D7_SPACE.join(_safe_word(w) for w in words) + D7_NEWLINE)


def decode_d7_marker(data: bytes) -> tuple[str, ...]:
    bits = _bits(data)
    i, current, words = 0, [], []
    while i < len(bits):
        if bits.startswith("11", i):
            marker = bits[i:i+7]
            if len(marker) != 7 or marker not in (D7_SPACE, D7_NEWLINE):
                raise CodecError("unsupported marker/invalid escape")
            if not current:
                raise CodecError("empty domain word")
            word = "".join(current)
            if len(word) not in ratified_widths():
                raise CodecError("invalid domain-word width")
            words.append(word)
            current.clear()
            i += 7
            if marker == D7_NEWLINE:
                _canonical_tail(bits, i)
                result = tuple(words)
                if encode_d7_marker(result) != data:
                    raise CodecError("noncanonical D7 marker carrier")
                return result
        elif bits.startswith("10", i):
            current.append("1")
            i += 2
        elif bits[i] == "0":
            current.append("0")
            i += 1
        else:
            raise CodecError("truncated protected bit")
        if i > 2 * MAX_PROGRAM_BITS:
            raise CodecError("size limit")
    raise CodecError("missing experimental EOF marker")


def physical_stats(words: tuple[str, ...], algorithm: str) -> dict:
    if algorithm == "width4":
        data = encode_width4(words)
        read = decode_width4(data)
        boundary = 4 * (len(words) + 1)
        stuffed = 0
    elif algorithm == "d7-marker":
        data = encode_d7_marker(words)
        read = decode_d7_marker(data)
        boundary = 7 * len(words)  # n-1 spaces + 1 EOS
        stuffed = sum(w.count("1") for w in words)
    else:
        raise CodecError("unknown algorithm")
    semantic = sum(map(len, words))
    logical = semantic + boundary + stuffed
    return {
        "algorithm": algorithm,
        "word_widths": [len(w) for w in words],
        "word_count": len(words),
        "semantic_bits": semantic,
        "boundary_and_eos_bits": boundary,
        "escaped_extra_bits": stuffed,
        "encoded_bits": logical,
        "physical_bytes": len(data),
        "physical_bits": len(data) * 8,
        "tail_unused_bits": len(data) * 8 - logical,
        "roundtrip_exact_words": read == words,
        "hex": data.hex(),
        "ratified_file_format": False,
        "semantics_oracle_checked": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vertical_source", type=Path)
    parser.add_argument("--write-prototypes", type=Path, default=None,
                        help="directory for research carriers; do not treat as canonical .sens")
    args = parser.parse_args()
    words = source_words(args.vertical_source.read_text())
    out = []
    for algorithm in ("width4", "d7-marker"):
        stats = physical_stats(words, algorithm)
        out.append(stats)
        if args.write_prototypes:
            args.write_prototypes.mkdir(parents=True, exist_ok=True)
            writer = encode_width4 if algorithm == "width4" else encode_d7_marker
            (args.write_prototypes / f"candidate-{algorithm}.bin").write_bytes(writer(words))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
