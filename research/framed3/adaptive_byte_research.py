"""Дослід Рамки-3: обирати фізичні блоки по 1, 2, 3 ... БАЙТІВ.

Аналізує ВСЮ програму до запису: DP знаходить мінімальну кількість
реальних байтів серед наявних розбиттів, frame rank і raw-fallback.
Розряди D1–D9 описують *семантичні слова*, а не одиниці оптимізації.
Не є production .senc кодеком і не виконує SENS програми.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import research_codec as рамка

МАГІЯ = b"\xf3\xb1\x01"  # Дослідна версія, не чинний файловий контракт
МАКС_СЛІВ = 5000
МАКС_БЛОК_СЛІВ = 128
МАКС_БАЙТІВ = 2_000_000

СИРИЙ = 0
ВІРТУАЛЬНИЙ_ДІАПАЗОН = range(1, 64)
ПРЯМИЙ_ЗСУВ = 64
ПРЯМИЙ_ДІАПАЗОН = range(65, 128)


class ПомилкаБайтовоїРамки(ValueError):
    """Невалідний або неканонічний дослідний фізичний запис."""


@dataclass(frozen=True)
class Фрагмент:
    початок: int
    кінець: int
    режим: str
    байтів_тіло: int
    байтів_запис: int


@dataclass(frozen=True)
class План:
    фрагменти: tuple[Фрагмент, ...]
    фізичних_байтів: int
    базовий_сирий_розмір: int
    групи_байтів: tuple[int, ...]


def _слова(слова: Iterable[str]) -> tuple[str, ...]:
    результат = tuple(слова)
    if len(результат) > МАКС_СЛІВ:
        raise ПомилкаБайтовоїРамки("надмірна програма")
    if any(not isinstance(w, str) or not (1 <= len(w) <= 9) or set(w) - {"0", "1"}
           for w in результат):
        raise ПомилкаБайтовоїРамки("очікуються exact-width слова D1–D9")
    return результат


def _число(n: int) -> bytes:
    if not 0 <= n <= МАКС_БАЙТІВ:
        raise ПомилкаБайтовоїРамки("довжина за межами")
    b = bytearray()
    while True:
        c = n & 127
        n >>= 7
        b.append(c | (128 if n else 0))
        if not n:
            return bytes(b)


def _читати_число(data: bytes, i: int) -> tuple[int, int]:
    початок, value = i, 0
    for shift in range(0, 35, 7):
        if i >= len(data):
            raise ПомилкаБайтовоїРамки("обрізана кількість слів")
        c = data[i]
        i += 1
        value |= (c & 127) << shift
        if not c & 128:
            if value > МАКС_БАЙТІВ or data[початок:i] != _число(value):
                raise ПомилкаБайтовоїРамки("неканонічна довжина")
            return value, i
    raise ПомилкаБайтовоїРамки("переповнений varint")


def _бітове_тіло(слова: tuple[str, ...]) -> bytes:
    bits = "".join(слова)
    bits += "0" * (-len(bits) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def _сирий_запис(слова: tuple[str, ...]) -> bytes:
    # 0 + varint кількості слів + 4-bit exact widths + bytes bitstream.
    b = bytearray((СИРИЙ,))
    b.extend(_число(len(слова)))
    widths = tuple(len(w) for w in слова)
    b.extend(bytes((widths[i] << 4) | (widths[i + 1] if i + 1 < len(widths) else 0)
                   for i in range(0, len(widths), 2)))
    b.extend(_бітове_тіло(слова))
    return bytes(b)


def _сирий_розмір(n: int, bit_count: int) -> int:
    return 1 + len(_число(n)) + (n + 1) // 2 + (bit_count + 7) // 8


# Усі рамкові записи мають КАНОНІЧНУ фізичну довжину,
# відновлювану з меж бакетів, а не вгадувану з бітів.
ШИРИНА_ЗА_ТРИТОМ = {}
for фізичних_байтів, lo, hi in рамка._buckets():
    for тритів in range(lo, hi + 1):
        ШИРИНА_ЗА_ТРИТОМ[тритів] = фізичних_байтів


def _рамкова_ширина(трити: int) -> int | None:
    width = ШИРИНА_ЗА_ТРИТОМ.get(трити)
    return width if width is not None and width < 64 else None


def _ранг(трити: tuple[int, ...]) -> bytes:
    довжина = len(трити)
    width = _рамкова_ширина(довжина)
    if width is None:
        raise ПомилкаБайтовоїРамки("рамка не поміщається в дослідний бакет")
    lo = next(start for size, start, _ in рамка._buckets() if size == width)
    rank = рамка._rank(трити)
    offset = sum(рамка.capacity(n) for n in range(lo, довжина))
    return (offset + rank).to_bytes(width, "big")


def _від_рангу(payload: bytes) -> tuple[int, ...]:
    for width, lo, hi in рамка._buckets():
        if len(payload) != width:
            continue
        rank = int.from_bytes(payload, "big")
        for n in range(lo, hi + 1):
            capacity = рамка.capacity(n)
            if rank < capacity:
                trits = рамка._unrank(n, rank)
                if _ранг(trits) != payload:
                    raise ПомилкаБайтовоїРамки("неканонічний ранговий байт")
                return trits
            rank -= capacity
        raise ПомилкаБайтовоїРамки("невикористаний номер рамки")
    raise ПомилкаБайтовоїРамки("недопустима ширина рамки")


def _віртуальні_трити(слова: tuple[str, ...]) -> tuple[int, ...]:
    # Додаємо 10/01 ТІЛЬКИ до фізичної рамки, після читання їх вилучаємо.
    return tuple(int(c) for c in ("10" + "2".join(слова) + "01"))


def _пряма_рамка(слова: tuple[str, ...]) -> bool:
    if len(слова) < 2 or слова[0] != "10" or слова[-1] != "01":
        return False
    try:
        рамка._check_words(слова)
    except рамка.FrameError:
        return False
    return True


def _варіанти(слова: tuple[str, ...], i: int, j: int,
              сума_бітів: int) -> tuple[tuple[int, str, int], ...]:
    n = j - i
    варіанти = [(_сирий_розмір(n, сума_бітів), "сирий", 0)]
    # Віртуальна рамка: 10 + слова з роздільниками 2 + 01.
    тритів = 4 + сума_бітів + n - 1
    width = _рамкова_ширина(тритів)
    if width is not None:
        варіанти.append((1 + width, "віртуальний", width))
    # Справжня зовнішня рамка: крайні 10/01 вже належать програмі.
    if _пряма_рамка(слова[i:j]):
        тритів = сума_бітів + max(0, n - 3)
        width = _рамкова_ширина(тритів)
        if width is not None:
            варіанти.append((1 + width, "прямий", width))
    return tuple(варіанти)


def _план(слова: tuple[str, ...]) -> План:
    n = len(слова)
    # Важливо: службовий header НЕ залежить від кількості блоків.
    header = len(МАГІЯ) + len(_число(n))
    dp = [(10 ** 100, 10 ** 100)] * (n + 1)
    dp[n] = (0, 0)
    choice: list[tuple[int, str, int, int] | None] = [None] * (n + 1)

    for i in range(n - 1, -1, -1):
        bits = 0
        for j in range(i + 1, min(n, i + МАКС_БЛОК_СЛІВ) + 1):
            bits += len(слова[j - 1])
            for cost, mode, width in _варіанти(слова, i, j, bits):
                current = (cost + dp[j][0], 1 + dp[j][1])
                if current < dp[i]:
                    dp[i] = current
                    choice[i] = (j, mode, width, cost)

    blocks: list[Фрагмент] = []
    i = 0
    while i < n:
        item = choice[i]
        if item is None:
            raise ПомилкаБайтовоїРамки("немає допустимого фізичного плану")
        j, mode, payload, cost = item
        if mode == "сирий":
            payload = cost - 1 - len(_число(j - i)) - (j - i + 1) // 2
        blocks.append(Фрагмент(i, j, mode, payload, cost))
        i = j

    # Незалежний базис: жадібне raw-кодування тих самих слів у блоках <=128.
    base = header
    for i in range(0, n, МАКС_БЛОК_СЛІВ):
        part = слова[i:i + МАКС_БЛОК_СЛІВ]
        base += len(_сирий_запис(part))
    return План(tuple(blocks), header + dp[0][0], base,
                tuple(b.байтів_тіло for b in blocks))


def планувати(вхід: Iterable[str]) -> План:
    return _план(_слова(вхід))


def кодувати(вхід: Iterable[str]) -> bytes:
    слова = _слова(вхід)
    plan = _план(слова)
    out = bytearray(МАГІЯ + _число(len(слова)))
    for b in plan.фрагменти:
        part = слова[b.початок:b.кінець]
        if b.режим == "сирий":
            record = _сирий_запис(part)
        elif b.режим == "віртуальний":
            payload = _ранг(_віртуальні_трити(part))
            record = bytes((len(payload),)) + payload
        elif b.режим == "прямий":
            payload = рамка.encode(part)
            record = bytes((ПРЯМИЙ_ЗСУВ + len(payload),)) + payload
        else:
            raise ПомилкаБайтовоїРамки("невідомий режим пакування")
        if len(record) != b.байтів_запис:
            raise ПомилкаБайтовоїРамки("кошторис не дорівнює фізичним байтам")
        out.extend(record)
    if len(out) != plan.фізичних_байтів or len(out) > МАКС_БАЙТІВ:
        raise ПомилкаБайтовоїРамки("невідповідність фізичного запису")
    return bytes(out)


def _прочитати_сирі(data: bytes, i: int) -> tuple[tuple[str, ...], int]:
    count, i = _читати_число(data, i)
    if not 1 <= count <= МАКС_БЛОК_СЛІВ:
        raise ПомилкаБайтовоїРамки("некоректна кількість слів у блоці")
    size = (count + 1) // 2
    if i + size > len(data):
        raise ПомилкаБайтовоїРамки("обірвана карта довжин")
    map_bytes = data[i:i + size]
    i += size
    widths = tuple(c for byte in map_bytes for c in (byte >> 4, byte & 15))
    if count % 2 and widths[-1] != 0:
        raise ПомилкаБайтовоїРамки("неканонічна кінцева півбайтова ширина")
    widths = widths[:count]
    if any(not 1 <= w <= 9 for w in widths):
        raise ПомилкаБайтовоїРамки("недійсна ширина D1–D9")
    bits = sum(widths)
    size = (bits + 7) // 8
    if i + size > len(data):
        raise ПомилкаБайтовоїРамки("обірване бітове тіло")
    bitstream = "".join(f"{b:08b}" for b in data[i:i + size])
    i += size
    if "1" in bitstream[bits:]:
        raise ПомилкаБайтовоїРамки("не-нульове доповнення бітового тіла")
    out, pos = [], 0
    for w in widths:
        out.append(bitstream[pos:pos + w])
        pos += w
    return tuple(out), i


def _прочитати_віртуальні(payload: bytes) -> tuple[str, ...]:
    trits = _від_рангу(payload)
    if trits[:2] != (1, 0) or trits[-2:] != (0, 1):
        raise ПомилкаБайтовоїРамки("невірні віртуальні краї")
    middle = "".join(str(t) for t in trits[2:-2])
    out = tuple(middle.split("2")) if middle else ()
    if not out or any(not w or not 1 <= len(w) <= 9 or set(w) - {"0", "1"}
                      for w in out):
        raise ПомилкаБайтовоїРамки("рамка має некоректні слова")
    if _віртуальні_трити(out) != trits:
        raise ПомилкаБайтовоїРамки("неканонічні межі віртуальної рамки")
    return out


def декодувати(data: bytes) -> tuple[str, ...]:
    if not isinstance(data, bytes) or len(data) > МАКС_БАЙТІВ or not data.startswith(МАГІЯ):
        raise ПомилкаБайтовоїРамки("невідома версія або надмірний фізичний запис")
    target, i = _читати_число(data, len(МАГІЯ))
    if target > МАКС_СЛІВ:
        raise ПомилкаБайтовоїРамки("неприпустима довжина програми")
    out: list[str] = []
    while len(out) < target:
        if i >= len(data):
            raise ПомилкаБайтовоїРамки("обірвана програма")
        tag = data[i]
        i += 1
        if tag == СИРИЙ:
            words, i = _прочитати_сирі(data, i)
        elif tag in ВІРТУАЛЬНИЙ_ДІАПАЗОН or tag in ПРЯМИЙ_ДІАПАЗОН:
            width = tag if tag < ПРЯМИЙ_ЗСУВ else tag - ПРЯМИЙ_ЗСУВ
            if i + width > len(data):
                raise ПомилкаБайтовоїРамки("обірване рангове тіло")
            payload = data[i:i + width]
            i += width
            if tag < ПРЯМИЙ_ЗСУВ:
                words = _прочитати_віртуальні(payload)
            else:
                try:
                    words = рамка.decode(payload)
                except рамка.FrameError as exc:
                    raise ПомилкаБайтовоїРамки("невірний зовнішній D2-кадр") from exc
        else:
            raise ПомилкаБайтовоїРамки("невизначений tag рамки")
        if not words or len(words) > МАКС_БЛОК_СЛІВ or len(out) + len(words) > target:
            raise ПомилкаБайтовоїРамки("кількість відновлених слів не відповідає рамці")
        out.extend(words)
    if i != len(data):
        raise ПомилкаБайтовоїРамки("хвостові байти після програми")
    words = tuple(out)
    if кодувати(words) != data:
        raise ПомилкаБайтовоїРамки("неканонічний або неоднозначний byte-plan")
    return words
