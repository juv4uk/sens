"""Обмежений дослідний кодер однієї зовнішньої рамки D2.

Це НЕ канонічний носій .sens T5. Кінець фізичного файла задає
кількість байтів; діапазон коду визначає точну довжину у тритах.

Перше слово (`10`) приклеєне до відкриваючої дужки, останнє
(`01`) — до закриваючої; роздільник `2` стоїть лише між
внутрішніми словами. Рідер відновлює злиті краї за правилом
рамки. Останній блок не потребує транспортного заповнення.

Умови спеціально слабші від синтаксису D2: одна зовнішня рамка
`10 … 01` і відсутність сусідніх 22. Тому оцінка місткості —
верхня межа, а не семантичний парсер чи нова ратифікація домену.
"""

from functools import lru_cache

MAX_TRITS = 128   # скінченний дослід; довгі потоки перевіряються окремо


class FrameError(ValueError):
    """Input is not in this experimental codec's exact bounded domain."""


def _allowed(n: int, pos: int) -> tuple[int, ...]:
    if pos == 0:
        return (1,)
    if pos == 1:
        return (0,)
    if pos == n - 2:
        return (0,)
    if pos == n - 1:
        return (1,)
    return (0, 1, 2)


@lru_cache(maxsize=None)
def _ways(n: int, pos: int, previous: int) -> int:
    if pos == n:
        return 1
    return sum(
        _ways(n, pos + 1, digit)
        for digit in _allowed(n, pos)
        if not (previous == 2 and digit == 2)
    )


@lru_cache(maxsize=None)
def capacity(n: int) -> int:
    """Верхня межа кількості транспортних послідовностей.

    Рамка зі злитими краями займає щонайменше чотири трити
    (порожня структура `1001`). Враховано й синтаксично
    неправильні слова; оцінка не занижена.
    """
    if n < 4 or n > MAX_TRITS:
        return 0
    return _ways(n, 0, -1)


def _rank(trits: tuple[int, ...]) -> int:
    n = len(trits)
    if not 4 <= n <= MAX_TRITS:
        raise FrameError("довжина поза обмеженим дослідним профілем")
    index, previous = 0, -1
    for pos, digit in enumerate(trits):
        if digit not in _allowed(n, pos) or previous == digit == 2:
            raise FrameError("порушено зовнішню рамку або правило без 22")
        for smaller in _allowed(n, pos):
            if previous == smaller == 2:
                continue
            if smaller == digit:
                break
            index += _ways(n, pos + 1, smaller)
        previous = digit
    assert index < capacity(n)
    return index


def _unrank(n: int, index: int) -> tuple[int, ...]:
    if not 0 <= index < capacity(n):
        raise FrameError("номер поза дозволеним діапазоном довжини")
    previous = -1
    out = []
    for pos in range(n):
        for digit in _allowed(n, pos):
            if previous == digit == 2:
                continue
            possible = _ways(n, pos + 1, digit)
            if index < possible:
                out.append(digit)
                previous = digit
                break
            index -= possible
        else:
            raise AssertionError("недосяжна помилка відновлення за номером")
    return tuple(out)


@lru_cache(maxsize=None)
def _buckets() -> tuple[tuple[int, int, int], ...]:
    """Найкоротші групи за кількістю байтів і довжиною у тритах."""
    result = []
    n = 4
    byte_count = 1
    while n <= MAX_TRITS:
        start, capacity_left = n, 1 << (8 * byte_count)
        while n <= MAX_TRITS and capacity(n) <= capacity_left:
            capacity_left -= capacity(n)
            n += 1
        if start == n:
            raise AssertionError("група байтів не вміщає жодної довжини")
        result.append((byte_count, start, n - 1))
        byte_count += 1
    return tuple(result)


def _check_words(words: tuple[str, ...]) -> None:
    if len(words) < 2 or words[0] != "10" or words[-1] != "01":
        raise FrameError("потрібна одна зовнішня структура 10 ... 01")
    nesting = 0
    for pos, word in enumerate(words):
        if not 1 <= len(word) <= 9 or any(bit not in "01" for bit in word):
            raise FrameError("слово має бути точним двійковим кодом ширини D1–D9")
        if word == "10":
            nesting += 1
        elif word == "01":
            nesting -= 1
            if nesting < 0 or (nesting == 0 and pos < len(words) - 1):
                raise FrameError("незбалансовані D2-дужки або зайва верхньорівнева форма")
    if nesting:
        raise FrameError("незакрита зовнішня рамка D2")


def transport(words: tuple[str, ...] | list[str]) -> tuple[int, ...]:
    words = tuple(words)
    _check_words(words)
    trits = tuple(map(int, words[0] + "2".join(words[1:-1]) + words[-1]))
    if len(trits) > MAX_TRITS:
        raise FrameError("довга рамка потребує окремо доведеного потокового кодера")
    _rank(trits)
    return trits


def encode(words: tuple[str, ...] | list[str]) -> bytes:
    trits = transport(words)
    n = len(trits)
    for width, lo, hi in _buckets():
        if lo <= n <= hi:
            offset = sum(capacity(length) for length in range(lo, n))
            return (offset + _rank(trits)).to_bytes(width, "big")
    raise FrameError("не визначено фізичної групи")


def decode(data: bytes) -> tuple[str, ...]:
    for width, lo, hi in _buckets():
        if len(data) == width:
            code = int.from_bytes(data, "big")
            for n in range(lo, hi + 1):
                count = capacity(n)
                if code < count:
                    trits = _unrank(n, code)
                    text = "".join(map(str, trits))
                    middle = text[2:-2]
                    inner = middle.split("2") if middle else []
                    words = tuple(["10", *inner, "01"])
                    # Strict decoding must NOT admit invalid D2-shaped words,
                    # overly wide words, extra roots, or noncanonical aliases.
                    if transport(words) != trits or encode(words) != data:
                        raise FrameError("відновлена послідовність не канонічна")
                    return words
                code -= count
            raise FrameError("невикористаний фізичний код; приховане заповнення заборонено")
    raise FrameError("непідтримувана кількість фізичних байтів")


def reference_t5(words: tuple[str, ...] | list[str]) -> bytes:
    """Незалежний простий зразок байтів T5; не виконавець програми.

    Канонічний `.sens` лишається T5: тут роздільник `2` стоїть між
    усіма словами (правило A), на відміну від рамки зі злитими краями.
    """
    words = tuple(words)
    _check_words(words)
    trits = tuple(map(int, "2".join(words)))
    padded = trits + (2,) * (-len(trits) % 5)
    return bytes(
        sum(padded[pos + i] * (3 ** (4 - i)) for i in range(5))
        for pos in range(0, len(padded), 5)
    )


def main() -> None:
    print("Дослідна рамка 10 ... 01; чинний канонічний носій — T5")
    for width, lo, hi in _buckets():
        used = sum(capacity(n) for n in range(lo, hi + 1))
        print(f"  {width} байтів: довжини у тритах {lo}..{hi}; {used}/{1 << (8 * width)} кодів")
    fixtures = {
        "порожня структура D2": ("10", "01"),
        "QUOTE": ("10", "001", "00", "000", "01"),
        "CAR(CONS(1,0))": "10 100 00 10 111 00 1 00 0 01 01".split(),
    }
    for name, words in fixtures.items():
        raw = reference_t5(words)
        experimental = encode(words)
        assert decode(experimental) == tuple(words)
        print(f"  {name}: {len(transport(words))} тритів; T5={len(raw)} байтів; рамка-3={len(experimental)} байтів; шістнадцятковий код={experimental.hex()}")


if __name__ == "__main__":
    main()
