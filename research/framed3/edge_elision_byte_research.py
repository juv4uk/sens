"""Дослід усунення ВСІХ початкових OPEN і ВСІХ кінцевих CLOSE.

Уся семантика перевіряється чинним bounded D2 дослідом із main.
Байтова мінімізація використовує самостійний експериментальний
adaptive_byte_research. НЕ production runtime і НЕ затверджений .senc-формат.

Режими: 0 без змін, 1 лише кінцеві D2:01,
2 зовнішній OPEN для одного кореня, 3..254 = кількість
початкових OPEN (mode-2), 255 = extended canonical ULEB128 count.
Без кодування числа початкових OPEN згортання не ін'єктивне.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import zlib

import adaptive_byte_research as байти
import trailing_closers_research as дужки

МАГІЯ = b"\xf3\xd2\x01"
БЕЗ_ЗМІН, БЕЗ_ЗАКРИТТІВ, БЕЗ_КРАЇВ = 0, 1, 2
ПРЕФІКС_ПЕРШИЙ, ПРЕФІКС_ОСТАННІЙ, ПРЕФІКС_РОЗШИРЕНИЙ = 3, 254, 255
МАКС_ПЕРЕБІР_ПРЕФІКСІВ = 16
МАКС_БАЙТІВ = байти.МАКС_БАЙТІВ


class ПомилкаСкорочення(ValueError):
    """Помилковий режим, обрізання, недопущені D2 або псевдоканонічні байти."""


@dataclass(frozen=True)
class Оцінка:
    режим: int
    вилучено_відкривальних: int
    вилучено_закривальних: int
    байтів_після: int
    байтів_без_скорочення: int


def _одна_зовнішня(слова: tuple[str, ...]) -> bool:
    """Перша D2:10 закривається САМЕ останнім D2:01; немає другого кореня."""
    if len(слова) < 2 or слова[0] != дужки.OPEN or слова[-1] != дужки.CLOSE:
        return False
    глибина = 0
    for i, слово in enumerate(слова):
        глибина += (слово == дужки.OPEN) - (слово == дужки.CLOSE)
        if глибина < 0 or (глибина == 0 and i < len(слова) - 1):
            return False
    return глибина == 0


def _кількість_відкриттів(слова: tuple[str, ...]) -> int:
    k = 0
    while k < len(слова) and слова[k] == дужки.OPEN:
        k += 1
    return k


def _режим_за_кількістю(k: int) -> int:
    if not 1 <= k <= дужки.MAX_WORDS:
        raise ПомилкаСкорочення("недопустима кількість початкових D2 OPEN")
    return k + 2 if k <= ПРЕФІКС_ОСТАННІЙ - 2 else ПРЕФІКС_РОЗШИРЕНИЙ


def _кількість_за_режимом(режим: int, додаткова: int | None = None) -> int:
    if ПРЕФІКС_ПЕРШИЙ <= режим <= ПРЕФІКС_ОСТАННІЙ:
        if додаткова is not None:
            raise ПомилкаСкорочення("зайвий префіксний лічильник")
        return режим - 2
    if режим == ПРЕФІКС_РОЗШИРЕНИЙ:
        if додаткова is None or not (ПРЕФІКС_ОСТАННІЙ - 1 <= додаткова <= дужки.MAX_WORDS):
            raise ПомилкаСкорочення("неканонічна розширена кількість OPEN")
        return додаткова
    raise ПомилкаСкорочення("непридатний режим префікса")


def _скорочення(слова: tuple[str, ...]) -> tuple[tuple[int, tuple[str, ...]], ...]:
    candidates = [(БЕЗ_ЗМІН, слова)]
    try:
        verified = дужки.validate(слова)
    except (дужки.SuffixError, ValueError):
        return tuple(candidates)
    short = дужки.trim(verified)
    if short != verified:
        candidates.append((БЕЗ_ЗАКРИТТІВ, short))
        if _одна_зовнішня(verified):
            candidates.append((БЕЗ_КРАЇВ, short[1:]))
    # Часткові k (до 16) + УСІ початкові відкриття.
    # Це пошук найменших БАЙТІВ серед явно перелічених кандидатів,
    # а не припущення, що більше вилучених слів => менший файл.
    prefix = _кількість_відкриттів(short)
    counts = list(range(1, min(prefix, МАКС_ПЕРЕБІР_ПРЕФІКСІВ) + 1))
    if prefix > МАКС_ПЕРЕБІР_ПРЕФІКСІВ:
        counts.append(prefix)
    for k in counts:
        candidates.append((_режим_за_кількістю(k), short[k:]))
    return tuple(candidates)


def _серіалізація_слів(слова: tuple[str, ...]) -> bytes:
    return байти._число(len(слова)) + b"".join(
        bytes((len(w),)) + w.encode("ascii") for w in слова
    )


def _загорнути(режим: int, слова: tuple[str, ...],
               повні: tuple[str, ...]) -> bytes:
    payload = байти.кодувати(слова)
    marker = bytes((режим,))
    if режим == ПРЕФІКС_РОЗШИРЕНИЙ:
        marker += байти._число(_кількість_відкриттів(повні))
    return (МАГІЯ + marker + байти._число(len(payload)) +
            zlib.crc32(_серіалізація_слів(повні)).to_bytes(4, "big") + payload)


def _вибір(слова: tuple[str, ...]) -> tuple[bytes, Оцінка]:
    options = []
    for mode, reduced in _скорочення(слова):
        physical = _загорнути(mode, reduced, слова)
        options.append((len(physical), mode, physical))
    best_len, best_mode, best = min(options)
    baseline = next(item for item in options if item[1] == БЕЗ_ЗМІН)
    removed_close = 0
    removed_open = (1 if best_mode == БЕЗ_КРАЇВ else
                    _кількість_за_режимом(
                        best_mode,
                        _кількість_відкриттів(слова)
                        if best_mode == ПРЕФІКС_РОЗШИРЕНИЙ else None
                    ) if best_mode >= ПРЕФІКС_ПЕРШИЙ else 0)
    if best_mode != БЕЗ_ЗМІН:
        removed_close = len(слова) - len(дужки.trim(слова))
    if best_len > МАКС_БАЙТІВ:
        raise ПомилкаСкорочення("завелика фізична рамка")
    return best, Оцінка(best_mode, removed_open, removed_close,
                        best_len, baseline[0])


def планувати(вхід) -> Оцінка:
    return _вибір(байти._слова(вхід))[1]


def кодувати(вхід) -> bytes:
    return _вибір(байти._слова(вхід))[0]


def _відновити(режим: int, short: tuple[str, ...], k: int | None = None) -> tuple[str, ...]:
    if режим == БЕЗ_ЗМІН:
        return short
    if режим == БЕЗ_ЗАКРИТТІВ:
        try:
            return дужки.restore(short)
        except дужки.SuffixError as exc:
            raise ПомилкаСкорочення("не можна відновити кінцеві D2") from exc
    if режим == БЕЗ_КРАЇВ:
        try:
            full = дужки.restore((дужки.OPEN,) + short)
        except дужки.SuffixError as exc:
            raise ПомилкаСкорочення("не можна відновити зовнішню D2-структуру") from exc
        if not _одна_зовнішня(full):
            raise ПомилкаСкорочення("вилучена зовнішня рамка не була єдиним коренем")
        return full
    if режим >= ПРЕФІКС_ПЕРШИЙ:
        count = _кількість_за_режимом(режим, k)
        try:
            restored = дужки.restore((дужки.OPEN,) * count + short)
        except дужки.SuffixError as exc:
            raise ПомилкаСкорочення("не відновити довільний D2-префікс") from exc
        return restored
    raise ПомилкаСкорочення("невідомий режим")


def декодувати(data: bytes) -> tuple[str, ...]:
    if not isinstance(data, bytes) or len(data) > МАКС_БАЙТІВ or not data.startswith(МАГІЯ):
        raise ПомилкаСкорочення("непідтримувана фізична рамка/версія")
    pos = len(МАГІЯ)
    if pos >= len(data):
        raise ПомилкаСкорочення("немає режиму")
    mode = data[pos]
    pos += 1
    k = None
    if mode == ПРЕФІКС_РОЗШИРЕНИЙ:
        try:
            k, pos = байти._читати_число(data, pos)
        except байти.ПомилкаБайтовоїРамки as exc:
            raise ПомилкаСкорочення("пошкоджена довжина серії відкриттів") from exc
        _кількість_за_режимом(mode, k)
    try:
        length, pos = байти._читати_число(data, pos)
    except байти.ПомилкаБайтовоїРамки as exc:
        raise ПомилкаСкорочення("неканонічна довжина фізичного payload") from exc
    if length == 0 or pos + 4 + length != len(data):
        raise ПомилкаСкорочення("недопустима фізична довжина чи trailing bytes")
    check = int.from_bytes(data[pos:pos + 4], "big")
    pos += 4
    try:
        reduced = байти.декодувати(data[pos:])
    except байти.ПомилкаБайтовоїРамки as exc:
        raise ПомилкаСкорочення("неприпустиме внутрішнє пакування") from exc
    restored = _відновити(mode, reduced, k)
    if zlib.crc32(_серіалізація_слів(restored)) != check:
        raise ПомилкаСкорочення("контрольна сума слів не відповідає програмі")
    # Збитий EOF іноді стає іншою валідною програмою: довжина, CRC і
    # canonical re-encode захищають цей демо-контейнер лише в межах
    # моделі випадкових пошкоджень; CRC НЕ є MAC.
    if кодувати(restored) != data:
        raise ПомилкаСкорочення("не канонічний режим або зміна розбиття")
    return restored
