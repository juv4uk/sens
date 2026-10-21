#!/usr/bin/env python3
"""Оборотна ASCII-латинка для українського тексту.

`uk-latynka-1` призначена не для видавничої транслітерації, а для випадків,
коли український коментар треба зберегти в середовищі, що вимагає 1-байтового
ASCII. Кодування є точним і оборотним навіть для змішаного тексту з латинськими
ідентифікаторами, URL та іншими Unicode-символами.

Українські фрагменти записуються як `~[...]`. Усередині такого фрагмента
використовується префіксно-однозначний алфавіт: звичайні літери мають короткі
латинські коди, а додаткові українські літери починаються з `q`/`Q`.
Будь-який інший не-ASCII символ записується як `~uHEX;`, а буквальний `~`
екранується як `~~`.

Приклади:
    Україна -> ~[Ukraqina]
    об'єкт Value -> ~[ob]'~[qjekt] Value

Використання:
    python3 scripts/uk-latynka.py encode [FILE|-]
    python3 scripts/uk-latynka.py decode [FILE|-]
    python3 scripts/uk-latynka.py self-test
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


LOWER = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "h",
    "ґ": "g",
    "д": "d",
    "е": "e",
    "є": "qj",
    "ж": "qz",
    "з": "z",
    "и": "y",
    "і": "i",
    "ї": "qi",
    "й": "j",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "qh",
    "ц": "qc",
    "ч": "qx",
    "ш": "qs",
    "щ": "qw",
    "ь": "qb",
    "ю": "qu",
    "я": "qa",
}

ENCODE = dict(LOWER)
ENCODE.update({letter.upper(): code.upper() for letter, code in LOWER.items()})
DECODE = {code: letter for letter, code in ENCODE.items()}


class LatynkaError(ValueError):
    """Помилка пошкодженого або неканонічного `uk-latynka-1` тексту."""


def encode(text: str) -> str:
    """Перетворити довільний Unicode-текст на точний ASCII `uk-latynka-1`."""

    out: list[str] = []
    ukrainian_run: list[str] = []

    def flush_run() -> None:
        if ukrainian_run:
            out.append("~[")
            out.append("".join(ukrainian_run))
            out.append("]")
            ukrainian_run.clear()

    for char in text:
        code = ENCODE.get(char)
        if code is not None:
            ukrainian_run.append(code)
            continue

        flush_run()
        if char == "~":
            out.append("~~")
        elif ord(char) < 128:
            out.append(char)
        else:
            out.append(f"~u{ord(char):04X};")

    flush_run()
    encoded = "".join(out)
    if not encoded.isascii():
        raise AssertionError("uk-latynka-1 encode має повертати лише ASCII")
    return encoded


def _decode_ukrainian_run(payload: str) -> str:
    result: list[str] = []
    index = 0

    while index < len(payload):
        first = payload[index]
        if first in ("q", "Q"):
            if index + 1 >= len(payload):
                raise LatynkaError("обірваний q/Q-код в українському фрагменті")
            token = payload[index : index + 2]
            index += 2
        else:
            token = first
            index += 1

        letter = DECODE.get(token)
        if letter is None:
            raise LatynkaError(f"невідомий код української літери: {token!r}")
        result.append(letter)

    return "".join(result)


def decode(text: str) -> str:
    """Відновити початковий Unicode-текст з `uk-latynka-1`."""

    result: list[str] = []
    index = 0

    while index < len(text):
        if text[index] != "~":
            result.append(text[index])
            index += 1
            continue

        if index + 1 >= len(text):
            raise LatynkaError("самотній '~' наприкінці тексту")

        marker = text[index + 1]
        if marker == "~":
            result.append("~")
            index += 2
            continue

        if marker == "[":
            end = text.find("]", index + 2)
            if end < 0:
                raise LatynkaError("незакритий український фрагмент '~[...]'")
            result.append(_decode_ukrainian_run(text[index + 2 : end]))
            index = end + 1
            continue

        if marker == "u":
            end = text.find(";", index + 2)
            if end < 0:
                raise LatynkaError("незакритий Unicode escape '~uHEX;'")
            raw = text[index + 2 : end]
            if not raw or any(char not in "0123456789abcdefABCDEF" for char in raw):
                raise LatynkaError(f"неправильний Unicode escape: {raw!r}")
            codepoint = int(raw, 16)
            if codepoint > 0x10FFFF:
                raise LatynkaError(f"Unicode codepoint поза діапазоном: {raw!r}")
            result.append(chr(codepoint))
            index = end + 1
            continue

        raise LatynkaError(f"невідомий escape після '~': {marker!r}")

    return "".join(result)


def self_test() -> None:
    """Довести ASCII-вихід та точний round-trip на характерних прикладах."""

    alphabet = "АБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯабвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
    samples = [
        alphabet,
        "Українська — перша і головна.",
        "об'єкт п'ять зв'язок",
        "Код Value::Pair лишається латинкою.",
        "Deutsch: Größe; English: value; ~ []",
        "Ще один рядок\nі другий.",
    ]

    for sample in samples:
        encoded = encode(sample)
        if not encoded.isascii():
            raise AssertionError(f"не-ASCII вихід: {encoded!r}")
        restored = decode(encoded)
        if restored != sample:
            raise AssertionError(
                f"round-trip розійшовся:\n  input={sample!r}\n  encoded={encoded!r}\n  restored={restored!r}"
            )

    malformed = ["~", "~[q]", "~[c]", "~uZZ;", "~u110000;"]
    for value in malformed:
        try:
            decode(value)
        except LatynkaError:
            continue
        raise AssertionError(f"пошкоджений запис мав бути відхилений: {value!r}")


def read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Оборотна українська ASCII-латинка uk-latynka-1")
    parser.add_argument("mode", choices=("encode", "decode", "self-test"))
    parser.add_argument("path", nargs="?", default="-")
    args = parser.parse_args()

    if args.mode == "self-test":
        self_test()
        print("uk-latynka-1: PASS")
        return 0

    source = read_input(args.path)
    try:
        output = encode(source) if args.mode == "encode" else decode(source)
    except LatynkaError as error:
        print(f"uk-latynka-1: ERROR: {error}", file=sys.stderr)
        return 2

    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
