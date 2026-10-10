"""Дослідний Tb-33: 6 байтів/блок з окремим ранжуванням фіналу.

Умова: повний тритовий потік не має 22 і закінчується D2 CLOSE 01.
НЕ канонічний .sens, не самостійний D2-парсер, не універсальний кодер атомів.
Повні 33-тритові блоки використовують звичайний rank; останній — ранги
всіх припустимих суфіксів довжини 1..33, що завершують глобальний потік 01.
"""

from functools import lru_cache

BLOCK_TRITS = 33
BLOCK_BYTES = 6
SLOT_COUNT = 1 << (8 * BLOCK_BYTES)


class TailError(ValueError):
    """Порушена межа, колізія або недопустиме фізичне кодування."""


@lru_cache(maxsize=None)
def ways(remaining: int, previous: int = -1) -> int:
    if remaining == 0:
        return 1
    return sum(
        ways(remaining - 1, digit)
        for digit in (0, 1, 2)
        if not (previous == digit == 2)
    )


def rank(trits: tuple[int, ...]) -> int:
    previous, result = -1, 0
    for pos, digit in enumerate(trits):
        if digit not in (0, 1, 2) or previous == digit == 2:
            raise TailError("недопустимий трит або 22")
        for smaller in range(digit):
            if not (previous == smaller == 2):
                result += ways(len(trits) - pos - 1, smaller)
        previous = digit
    return result


def unrank(length: int, code: int) -> tuple[int, ...]:
    if length < 0 or not 0 <= code < ways(length):
        raise TailError("номер поза допустимою довжиною")
    result, previous = [], -1
    for remaining in range(length - 1, -1, -1):
        for digit in (0, 1, 2):
            if previous == digit == 2:
                continue
            width = ways(remaining, digit)
            if code < width:
                result.append(digit)
                previous = digit
                break
            code -= width
        else:
            raise TailError("неіснуючий номер")
    return tuple(result)


def tail_count(length: int) -> int:
    if length == 1:
        return 1  # Останній трит 1, перед ним у попередньому блоці має бути 0.
    if 2 <= length <= BLOCK_TRITS:
        return ways(length - 2)  # Довільний префікс без 22 + кінцеве 01.
    return 0


TAIL_CAPACITY = sum(tail_count(n) for n in range(1, BLOCK_TRITS + 1))


def final_rank(tail: tuple[int, ...]) -> int:
    length = len(tail)
    if not tail_count(length):
        raise TailError("недопустима довжина останнього блока")
    if length == 1:
        if tail != (1,):
            raise TailError("одиночний хвіст може бути тільки 1 після 0")
        inside = 0
    else:
        if tail[-2:] != (0, 1):
            raise TailError("останній блок мусить закінчуватися D2:01")
        inside = rank(tail[:-2])
    return sum(tail_count(n) for n in range(1, length)) + inside


def final_unrank(code: int) -> tuple[int, ...]:
    if not 0 <= code < TAIL_CAPACITY:
        raise TailError("невикористаний 48-бітний кінцевий код")
    for length in range(1, BLOCK_TRITS + 1):
        count = tail_count(length)
        if code < count:
            return (1,) if length == 1 else unrank(length - 2, code) + (0, 1)
        code -= count
    raise TailError("недосяжне поза межами рангу")


def validate(trits: tuple[int, ...]) -> None:
    if len(trits) < 2 or trits[-2:] != (0, 1):
        raise TailError("дослідний профіль вимагає завершення 01")
    if any(d not in (0, 1, 2) for d in trits):
        raise TailError("поза тритовим алфавітом")
    if any(a == b == 2 for a, b in zip(trits, trits[1:])):
        raise TailError("22 на межі блока або всередині блока")


def encode(trits: tuple[int, ...]) -> bytes:
    validate(trits)
    full_before_last = (len(trits) - 1) // BLOCK_TRITS
    result = bytearray()
    for offset in range(0, full_before_last * BLOCK_TRITS, BLOCK_TRITS):
        block = trits[offset:offset + BLOCK_TRITS]
        result.extend(rank(block).to_bytes(BLOCK_BYTES, "big"))
    tail = trits[full_before_last * BLOCK_TRITS:]
    result.extend(final_rank(tail).to_bytes(BLOCK_BYTES, "big"))
    return bytes(result)


def decode(data: bytes) -> tuple[int, ...]:
    if not data or len(data) % BLOCK_BYTES:
        raise TailError("немає повної послідовності шестибайтних блоків")
    result = []
    for offset in range(0, len(data) - BLOCK_BYTES, BLOCK_BYTES):
        code = int.from_bytes(data[offset:offset + BLOCK_BYTES], "big")
        result.extend(unrank(BLOCK_TRITS, code))
    result.extend(final_unrank(int.from_bytes(data[-BLOCK_BYTES:], "big")))
    trits = tuple(result)
    validate(trits)
    if encode(trits) != data:
        raise TailError("неканонічні байти фізичного Tb-досліду")
    return trits
