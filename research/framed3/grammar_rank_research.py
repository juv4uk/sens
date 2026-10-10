"""Точне ранжування однокореневої D2-рамки; лише дослід, не .sens/.senc.

Слова D1–D9 лишаються побітово незмінними. Пара зовнішніх 10/01 є
відомим контекстом, не самостійною фізичною інформацією. Середина містить
точні слова 1..9 біт, розділені одним транспортним тритом 2.
"""
from __future__ import annotations

from functools import lru_cache
import research_codec as reference

MAX_TRITS = reference.MAX_TRITS


class GrammarError(ValueError):
    """Невалідна рамка, код або неприйнятна довжина."""


def _next_depth(word: str, depth: int) -> int:
    return depth + (word == "10") - (word == "01")


@lru_cache(None)
def count_middle(remaining: int, depth: int = 1) -> int:
    """Точна кількість балансованих середин заданої довжини у тритах."""
    if remaining < 0 or depth < 1:
        return 0
    if remaining == 0:
        return int(depth == 1)
    total = 0
    for width in range(1, min(9, remaining) + 1):
        # Усі слова крім спеціальних D2 OPEN=10 і CLOSE=01 — атоми.
        choices = ((depth, (1 << width) - (2 if width == 2 else 0)),)
        if width == 2:
            choices += ((depth + 1, 1), (depth - 1, 1))
        for next_depth, multiplicity in choices:
            if next_depth < 1:
                continue
            if remaining == width:
                total += multiplicity * int(next_depth == 1)
            elif remaining >= width + 2:
                total += multiplicity * count_middle(
                    remaining - width - 1, next_depth
                )
    return total


def _subtree(remaining: int, depth: int, word: str) -> int:
    width = len(word)
    if width > remaining:
        return 0
    after = _next_depth(word, depth)
    if after < 1:
        return 0
    if remaining == width:
        return int(after == 1)
    if remaining >= width + 2:
        return count_middle(remaining - width - 1, after)
    return 0


def _options(remaining: int, depth: int):
    # Стабільний порядок: ширина, потім числове значення без втрати нулів.
    for width in range(1, min(9, remaining) + 1):
        for value in range(1 << width):
            word = format(value, f"0{width}b")
            ways = _subtree(remaining, depth, word)
            if ways:
                yield word, ways


def rank_inner(words: tuple[str, ...] | list[str]) -> int:
    words = tuple(words)
    if len(words) < 2 or words[0] != "10" or words[-1] != "01":
        raise GrammarError("потрібна одна зовнішня D2-рамка")
    inner = words[1:-1]
    remaining = sum(map(len, inner)) + max(0, len(inner) - 1)
    if remaining > MAX_TRITS - 4:
        raise GrammarError("довжина поза дослідним обмеженням")
    full_length, depth, rank = remaining, 1, 0
    for word in inner:
        for candidate, ways in _options(remaining, depth):
            if candidate == word:
                break
            rank += ways
        else:
            raise GrammarError("некоректне слово або незбалансована D2-структура")
        remaining -= len(word) if remaining == len(word) else len(word) + 1
        depth = _next_depth(word, depth)
    if remaining != 0 or depth != 1 or rank >= count_middle(full_length):
        raise GrammarError("невідновна межа/структура")
    return rank


def unrank_inner(length: int, rank: int) -> tuple[str, ...]:
    if not isinstance(length, int) or not 0 <= length <= MAX_TRITS - 4:
        raise GrammarError("некоректна довжина")
    if not isinstance(rank, int) or not 0 <= rank < count_middle(length):
        raise GrammarError("номер поза скінченним корпусом")
    if length == 0:
        return ("10", "01")
    depth, remaining = 1, length
    inner = []
    while remaining:
        for word, ways in _options(remaining, depth):
            if rank < ways:
                inner.append(word)
                remaining -= len(word) if len(word) == remaining else len(word) + 1
                depth = _next_depth(word, depth)
                break
            rank -= ways
        else:
            raise GrammarError("неможливо відновити граматичний код")
    if depth != 1 or rank != 0:
        raise GrammarError("пошкоджений ранг")
    return ("10", *inner, "01")


@lru_cache(None)
def buckets() -> tuple[tuple[int, int, int], ...]:
    """Фіксована фізична довжина сама вказує діапазон довжин середини."""
    groups = []
    length, byte_count = 0, 1
    while length <= MAX_TRITS - 4:
        start, slots = length, 1 << (8 * byte_count)
        while length <= MAX_TRITS - 4 and count_middle(length) <= slots:
            slots -= count_middle(length)
            length += 1
        if start == length:
            raise GrammarError("не існує групи для довжини")
        groups.append((byte_count, start, length - 1))
        byte_count += 1
    return tuple(groups)


def encode(words: tuple[str, ...] | list[str]) -> bytes:
    words = tuple(words)
    inner = words[1:-1]
    length = sum(map(len, inner)) + max(0, len(inner) - 1)
    value = rank_inner(words)
    for width, first, last in buckets():
        if first <= length <= last:
            offset = sum(count_middle(k) for k in range(first, length))
            return (offset + value).to_bytes(width, "big")
    raise GrammarError("відсутня група")


def decode(blob: bytes) -> tuple[str, ...]:
    if not isinstance(blob, bytes) or not blob:
        raise GrammarError("потрібен явний дослідний байтовий блок")
    for width, first, last in buckets():
        if len(blob) == width:
            value = int.from_bytes(blob, "big")
            for length in range(first, last + 1):
                ways = count_middle(length)
                if value < ways:
                    words = unrank_inner(length, value)
                    if encode(words) != blob:
                        raise GrammarError("неканонічний фізичний код")
                    return words
                value -= ways
            raise GrammarError("незайнятий фізичний код")
    raise GrammarError("непідтримана кількість байтів")


@lru_cache(None)
def count_no_adjacent_22(k: int, previous: int = 0) -> int:
    if k == 0:
        return 1
    return sum(count_no_adjacent_22(k - 1, digit)
               for digit in (0, 1, 2) if not (previous == digit == 2))


def fixed_frame_identity(words: tuple[str, ...] | list[str]) -> bool:
    """Старий F3 вже має безкоштовні константи 10/01 в ранзі."""
    trits = reference.transport(tuple(words))
    return (
        trits[:2] == (1, 0) and trits[-2:] == (0, 1)
        and reference.capacity(len(trits)) == count_no_adjacent_22(len(trits) - 4)
        and len(reference.encode(words)) >= len(encode(words))
    )


if __name__ == "__main__":
    for words in (
        ("10", "01"),
        ("10", "001", "00", "000", "01"),
        ("10", "11111", "01"),
        ("10", "0", "0", "0", "0", "0", "0", "01"),
    ):
        if decode(encode(words)) != words:
            raise GrammarError("незворотний корпус")
        print(" ".join(words), "T5:", len(reference.reference_t5(words)),
              "F3:", len(reference.encode(words)), "граматика:", len(encode(words)))
    print("Кошики:", buckets()[:4])
