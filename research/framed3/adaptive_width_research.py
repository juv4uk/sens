"""Дослідне адаптивне пакування ВСІЄЇ програми на основі «Рамки-3».

Динамічне програмування обирає повну фізичну довжину: прямі значення
довжини 1..9 біт, однорідні групи, циклічні комбінації ширин і F3-rank.
Це дослідний .senc, не production codec і не семантичний парсер SENS.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import research_codec as рамка

МАГІЯ = b"\xf3\xa3\x01"
МАКС_СЛІВ = 20_000
МАКС_БЛОК = 128
МАКС_БАЙТІВ = 2_000_000
РЕЖИМ_СИРИЙ = 0
РЕЖИМ_ЦИКЛ_БАЗА = 0x20
РЕЖИМ_РАМКА3 = 0x40
МАКС_ПЕРІОД = 8


class ПомилкаПакування(ValueError):
    """Невірний, неоднозначний або надмірний фізичний запис."""


@dataclass(frozen=True)
class Блок:
    початок: int
    кінець: int
    режим: int
    ширини: tuple[int, ...]
    байтів: int


@dataclass(frozen=True)
class План:
    стратегія: str
    блоки: tuple[Блок, ...]
    усього_байтів: int
    простий_базис_байтів: int


def _слова(вхід: Iterable[str]) -> tuple[str, ...]:
    результат = tuple(вхід)
    if len(результат) > МАКС_СЛІВ:
        raise ПомилкаПакування("перевищено ліміт слів")
    if any(not isinstance(w, str) or not 1 <= len(w) <= 9 or set(w) - {"0", "1"}
           for w in результат):
        raise ПомилкаПакування("очікуються точні непорожні бітові слова D1–D9")
    return результат


def _varint(n: int) -> bytes:
    if not 0 <= n <= МАКС_БАЙТІВ:
        raise ПомилкаПакування("переповнення ULEB128")
    result = bytearray()
    while True:
        b = n & 127
        n >>= 7
        result.append(b | (128 if n else 0))
        if not n:
            return bytes(result)


def _read_varint(data: bytes, off: int) -> tuple[int, int]:
    start, value = off, 0
    for shift in range(0, 35, 7):
        if off >= len(data):
            raise ПомилкаПакування("обірвана ULEB128")
        b = data[off]
        off += 1
        value |= (b & 127) << shift
        if not b & 128:
            if value > МАКС_БАЙТІВ or data[start:off] != _varint(value):
                raise ПомилкаПакування("неканонічна ULEB128")
            return value, off
    raise ПомилкаПакування("занадто довгий varint")


def _pack_bits(words: Iterable[str]) -> bytes:
    bits = "".join(words)
    bits += "0" * ((-len(bits)) % 8)
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def _unpack_bits(data: bytes, widths: Iterable[int]) -> tuple[str, ...]:
    widths = tuple(widths)
    amount = sum(widths)
    if len(data) != (amount + 7) // 8:
        raise ПомилкаПакування("довжина бітових даних невірна")
    bits = "".join(f"{byte:08b}" for byte in data)
    if any(c == "1" for c in bits[amount:]):
        raise ПомилкаПакування("ненульове кінцеве доповнення")
    out, pos = [], 0
    for w in widths:
        out.append(bits[pos:pos + w])
        pos += w
    return tuple(out)


def _pack_widths(widths: tuple[int, ...]) -> bytes:
    if any(not 1 <= w <= 9 for w in widths):
        raise ПомилкаПакування("недопустима ширина")
    return bytes((widths[i] << 4) | (widths[i + 1] if i + 1 < len(widths) else 0)
                 for i in range(0, len(widths), 2))


def _unpack_widths(data: bytes, count: int) -> tuple[int, ...]:
    if len(data) != (count + 1) // 2:
        raise ПомилкаПакування("помилковий розмір таблиці ширин")
    widths = tuple(n for x in data for n in (x >> 4, x & 15))
    if count % 2 and widths[-1] != 0:
        raise ПомилкаПакування("нульове доповнення ширин порушено")
    widths = widths[:count]
    if any(not 1 <= w <= 9 for w in widths):
        raise ПомилкаПакування("ширина слова поза D1–D9")
    return widths


def _cost(n: int, sum_bits: int, mode: int) -> int:
    # 1 байт mode, ULEB кількість слів, ширини, payload із нульовим padding.
    base = 1 + len(_varint(n)) + (sum_bits + 7) // 8
    if mode == РЕЖИМ_СИРИЙ:
        return base + (n + 1) // 2
    if 1 <= mode <= 9:
        return base
    if РЕЖИМ_ЦИКЛ_БАЗА + 2 <= mode <= РЕЖИМ_ЦИКЛ_БАЗА + МАКС_ПЕРІОД:
        return base + ((mode - РЕЖИМ_ЦИКЛ_БАЗА + 1) // 2)
    raise ПомилкаПакування("невідомий режим")


def _plan_segments(words: tuple[str, ...]) -> tuple[Блок, ...]:
    n, widths = len(words), tuple(map(len, words))
    dp = [(10 ** 100, 10 ** 100)] * (n + 1)
    dp[n] = (0, 0)
    chosen: list[tuple[int, int, tuple[int, ...]] | None] = [None] * (n + 1)
    for i in range(n - 1, -1, -1):
        total_bits = 0
        cycle_ok = [True] * (МАКС_ПЕРІОД + 1)
        uniform = True
        for j in range(i + 1, min(n, i + МАКС_БЛОК) + 1):
            m, w = j - i, widths[j - 1]
            total_bits += w
            if w != widths[i]:
                uniform = False
            modes = [РЕЖИМ_СИРИЙ]
            if uniform:
                modes.append(w)
            for period in range(2, МАКС_ПЕРІОД + 1):
                if m > period and w != widths[j - 1 - period]:
                    cycle_ok[period] = False
                if m >= period * 2 and cycle_ok[period]:
                    modes.append(РЕЖИМ_ЦИКЛ_БАЗА + period)
            for mode in modes:
                candidate = (_cost(m, total_bits, mode) + dp[j][0], 1 + dp[j][1])
                if candidate < dp[i]:
                    dp[i] = candidate
                    pattern = (widths[i:i + (mode - РЕЖИМ_ЦИКЛ_БАЗА)]
                               if mode >= РЕЖИМ_ЦИКЛ_БАЗА else
                               (widths[i],) if 1 <= mode <= 9 else ())
                    chosen[i] = (j, mode, pattern)
    blocks, pos = [], 0
    while pos < n:
        choice = chosen[pos]
        if choice is None:
            raise ПомилкаПакування("немає допустимого розбиття")
        j, mode, pattern = choice
        blocks.append(Блок(pos, j, mode, pattern, _cost(j - pos, sum(widths[pos:j]), mode)))
        pos = j
    return tuple(blocks)


def _encode_block(words: tuple[str, ...], block: Блок) -> bytes:
    chunk = words[block.початок:block.кінець]
    out = bytearray((block.режим,))
    out.extend(_varint(len(chunk)))
    if block.режим == РЕЖИМ_СИРИЙ:
        out.extend(_pack_widths(tuple(len(w) for w in chunk)))
    elif block.режим >= РЕЖИМ_ЦИКЛ_БАЗА:
        out.extend(_pack_widths(block.ширини))
    out.extend(_pack_bits(chunk))
    if len(out) != block.байтів:
        raise ПомилкаПакування("планована вартість не дорівнює реальним байтам")
    return bytes(out)


def _make(words: tuple[str, ...]) -> tuple[bytes, План]:
    blocks = _plan_segments(words)
    body = b"".join(_encode_block(words, b) for b in blocks)
    segmented = МАГІЯ + _varint(len(words)) + len(blocks).to_bytes(2, "big") + body
    raw_blocks = tuple(
        Блок(i, min(i + МАКС_БЛОК, len(words)), РЕЖИМ_СИРИЙ, (),
             _cost(min(МАКС_БЛОК, len(words) - i),
                   sum(map(len, words[i:i + МАКС_БЛОК])), РЕЖИМ_СИРИЙ))
        for i in range(0, len(words), МАКС_БЛОК)
    )
    raw_body = b"".join(_encode_block(words, b) for b in raw_blocks)
    baseline = len(МАГІЯ + _varint(len(words)) + len(raw_blocks).to_bytes(2, "big") + raw_body)
    try:
        original_frame = рамка.encode(words)
    except рамка.FrameError:
        original_frame = None
    if original_frame is not None:
        framed = (МАГІЯ + _varint(len(words)) + bytes((0, 1))
                  + bytes((РЕЖИМ_РАМКА3,)) + _varint(len(words))
                  + _varint(len(original_frame)) + original_frame)
        if len(framed) < len(segmented):
            block = Блок(0, len(words), РЕЖИМ_РАМКА3, (),
                         1 + len(_varint(len(words))) +
                         len(_varint(len(original_frame))) + len(original_frame))
            return framed, План("рамка-3", (block,), len(framed), baseline)
    return segmented, План("адаптивне-розбиття", blocks, len(segmented), baseline)


def кодувати(вхід: Iterable[str]) -> bytes:
    wire, _ = _make(_слова(вхід))
    if len(wire) > МАКС_БАЙТІВ:
        raise ПомилкаПакування("надмірний результат")
    return wire


def планувати(вхід: Iterable[str]) -> План:
    return _make(_слова(вхід))[1]


def декодувати(data: bytes) -> tuple[str, ...]:
    if not isinstance(data, bytes) or len(data) > МАКС_БАЙТІВ or not data.startswith(МАГІЯ):
        raise ПомилкаПакування("невідома рамка/версія або надмірна довжина")
    off = len(МАГІЯ)
    words_total, off = _read_varint(data, off)
    if off + 2 > len(data):
        raise ПомилкаПакування("обірвана кількість блоків")
    segments = int.from_bytes(data[off:off + 2], "big")
    off += 2
    if words_total > МАКС_СЛІВ or segments > words_total or (segments == 0) != (words_total == 0):
        raise ПомилкаПакування("некоректна кількість слів/блоків")
    out: list[str] = []
    for _ in range(segments):
        if off >= len(data):
            raise ПомилкаПакування("обірваний блок")
        mode, off = data[off], off + 1
        m, off = _read_varint(data, off)
        if m < 1 or m > МАКС_БЛОК or len(out) + m > words_total:
            if mode != РЕЖИМ_РАМКА3 or not (1 <= m <= МАКС_СЛІВ and len(out) + m <= words_total):
                raise ПомилкаПакування("некоректний розмір сегмента")
        if mode == РЕЖИМ_РАМКА3:
            size, off = _read_varint(data, off)
            if size == 0 or off + size > len(data):
                raise ПомилкаПакування("обірвана ранжована рамка")
            try:
                chunk = рамка.decode(data[off:off + size])
            except рамка.FrameError as exc:
                raise ПомилкаПакування("недійсна рамка-3") from exc
            off += size
            if len(chunk) != m:
                raise ПомилкаПакування("неправильна кількість слів framed3")
        else:
            if mode == РЕЖИМ_СИРИЙ:
                width_size = (m + 1) // 2
                if off + width_size > len(data):
                    raise ПомилкаПакування("обірвана карта ширин")
                widths = _unpack_widths(data[off:off + width_size], m)
                off += width_size
            elif 1 <= mode <= 9:
                widths = (mode,) * m
            elif РЕЖИМ_ЦИКЛ_БАЗА + 2 <= mode <= РЕЖИМ_ЦИКЛ_БАЗА + МАКС_ПЕРІОД:
                period = mode - РЕЖИМ_ЦИКЛ_БАЗА
                pattern_size = (period + 1) // 2
                if off + pattern_size > len(data):
                    raise ПомилкаПакування("обірвана маска періоду")
                pattern = _unpack_widths(data[off:off + pattern_size], period)
                off += pattern_size
                widths = tuple(pattern[i % period] for i in range(m))
            else:
                raise ПомилкаПакування("невідомий режим пакування")
            size = (sum(widths) + 7) // 8
            if off + size > len(data):
                raise ПомилкаПакування("обірвані біти")
            chunk = _unpack_bits(data[off:off + size], widths)
            off += size
        out.extend(chunk)
    if off != len(data) or len(out) != words_total:
        raise ПомилкаПакування("хвостові дані/відсутні слова")
    recovered = tuple(out)
    if кодувати(recovered) != data:
        raise ПомилкаПакування("неканонічний альтернативний план")
    return recovered
