"""Дослід: усі кінцеві D2:01 відновлюються з глибини вкладеності.

НЕ кодек .sens/.senc, НЕ семантичний оракул замість Rust. Цей обмежений
прототип працює з уже розмежованими точними словами D1–D9.
При обрізанні або відсутності довіреної зовнішньої рамки він НЕ гарантує
виявлення пошкодження: скорочені коди загалом не є prefix-free.
"""
from __future__ import annotations

import re

EXACT_WORD = re.compile(r"[01]{1,9}\Z")
MAX_WORDS = 512
OPEN, CLOSE, SEP, DOT = "10", "01", "00", "11"


class SuffixError(ValueError):
    """Неправильна D2-послідовність або некоректний дослідний носій."""


def _words(raw: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    if not isinstance(raw, (tuple, list)) or not 0 < len(raw) <= MAX_WORDS:
        raise SuffixError("порожній/надто довгий або неточний список слів")
    words = tuple(raw)
    if any(not isinstance(x, str) or not EXACT_WORD.fullmatch(x) for x in words):
        raise SuffixError("потрібні точні D1–D9 слова 1..9 біт")
    return words


def validate(words: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Точне структурне правило Core.D2 із чинного canonical_reader.rs.

    Це окремий bounded falsifier, не нове джерело семантичної влади.
    W1 і W3..W9 тут навмисно неподільні payload-слова.
    W2: 00 separator, 01 close, 10 open, 11 dot.
    """
    data = _words(words)
    position = 0

    def skip() -> None:
        nonlocal position
        while position < len(data) and data[position] == SEP:
            position += 1

    def expr() -> None:
        nonlocal position
        if position >= len(data):
            raise SuffixError("очікується вираз")
        word = data[position]
        if word == OPEN:
            position += 1
            list_expr()
        elif len(word) == 2:
            raise SuffixError("D2:00/01/11 не є атомом або головою виразу")
        else:
            position += 1

    def list_expr() -> None:
        nonlocal position
        elements = 0
        while True:
            skip()
            if position >= len(data):
                raise SuffixError("незакрита D2-структура")
            word = data[position]
            if word == CLOSE:
                position += 1
                return
            if word == DOT:
                if elements == 0:
                    raise SuffixError("крапка D2 потребує голову")
                position += 1
                skip()
                if position >= len(data) or data[position] in (CLOSE, DOT):
                    raise SuffixError("крапка D2 потребує один хвіст")
                expr()
                skip()
                if position >= len(data) or data[position] != CLOSE:
                    raise SuffixError("крапка D2 допускає лише один хвіст")
                position += 1
                return
            expr()
            elements += 1

    while position < len(data):
        skip()
        if position == len(data):
            break
        expr()
    return data


def trim(words: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Вилучити ВСІ завершальні D2 CLOSE після суворої перевірки оригіналу."""
    data = validate(words)
    i = len(data)
    while i and data[i - 1] == CLOSE:
        i -= 1
    if i == 0:
        raise SuffixError("відсутня непорожня відновлювана основа")
    return data[:i]


def restore(short: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Відновити лише кінцеві D2:01; зовнішня межа є передумовою.

    Дозволяє семантично правильне відновлення, але не перевіряє CRC,
    обрив повідомлення чи походження фізичного EOF.
    """
    body = _words(short)
    depth = 0
    for w in body:
        if w == OPEN:
            depth += 1
        elif w == CLOSE:
            depth -= 1
            if depth < 0:
                raise SuffixError("передчасна D2-закривальна дужка")
    if depth + len(body) > MAX_WORDS:
        raise SuffixError("перевищення межі відновлення")
    restored = body + (CLOSE,) * depth
    validate(restored)
    if trim(restored) != body:
        raise SuffixError("невірний канонічний короткий запис")
    return restored


def trit_count(words: tuple[str, ...] | list[str]) -> int:
    """Гіпотетичні трити T5 до/після; короткий запис НЕ є .sens."""
    data = _words(words)
    return sum(map(len, data)) + len(data) - 1


def possible_t5_bytes(words: tuple[str, ...] | list[str]) -> int:
    return (trit_count(words) + 4) // 5


def measure(words: tuple[str, ...] | list[str]) -> dict[str, int]:
    data = validate(words)
    short = trim(data)
    if restore(short) != data:
        raise SuffixError("необоротне скорочення")
    removed = len(data) - len(short)
    before, after = trit_count(data), trit_count(short)
    if before - after != 3 * removed:
        raise SuffixError("неправильний облік тритів")
    return {
        "closes_removed": removed,
        "trits_saved": before - after,
        "hypothetical_t5_bytes_before": possible_t5_bytes(data),
        "hypothetical_t5_bytes_after": possible_t5_bytes(short),
    }


if __name__ == "__main__":
    examples = [
        ("10", "01"),
        ("10", "10", "111", "01", "01"),
        ("10", "0", "11", "10", "111", "01", "01"),
        ("10", "1", "01", "10", "000000000", "01"),
    ]
    for words in examples:
        compact = trim(words)
        print(" ".join(words), "→", " ".join(compact), measure(words))
