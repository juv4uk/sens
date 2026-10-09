#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sens_binary_language_model.py — виконувана МОДЕЛЬ ядра «справді двійкової мови» SENS.

НАВІЩО. У Rust уже є субстрат: `Bits<N>` (точні ширини), `BitPacker`/`PackedBitstream`
(канонічне бітове пакування, MSB-first), `source_words` (бінарне джерело .lisp),
`domain_words` (носії без семантики на бітах). Цей файл — НЕ заміна того коду й НЕ
компілятор. Це виконувана модель ТОГО САМОГО контракту, яку можна прогнати без cargo,
щоб (а) зафіксувати правило, (б) мати оракул для Rust-реалізації, (в) ловити дрейф.

ЩО МОДЕЛЮЄ (дослівно контракт Rust):
  • слово — це (width, value) з width у 1..=9 і 0 <= value < 2**width;
  • пакування — MSB-first, неперервним потоком бітів, БЕЗ вирівнювання по байтах;
  • фізичний байт — лише носій; межа слова може перетинати межу байта;
  • на біт-патерн НЕ навішується семантика — лише (домен, ширина, значення);
  • доменна координата — окремий шар (драбина D1..D10), не властивість бітів.

ЧОГО НЕ РОБИТЬ: не виконує семантику, не ратифікує домени, не вигадує координат.
Координати подаються ззовні — власником/драбиною, не цією моделлю.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, List, Tuple


class BinaryLanguageError(Exception):
    """Помилка контракту — fail-closed, як і належить."""


@dataclass(frozen=True)
class Word:
    """Одне точне слово: ширина + значення. Без семантики на бітах."""
    width: int
    value: int

    def __post_init__(self) -> None:
        if not (1 <= self.width <= 9):
            raise BinaryLanguageError(f"ширина {self.width} поза 1..=9")
        if not (0 <= self.value < (1 << self.width)):
            raise BinaryLanguageError(
                f"значення {self.value} не влізає в ширину {self.width}"
            )

    def bits(self) -> str:
        """MSB-first рядок бітів рівно завдовжки width."""
        return format(self.value, f"0{self.width}b")

    def __str__(self) -> str:  # видиме бінарне джерело
        return self.bits()


@dataclass(frozen=True)
class Coordinate:
    """Доменна координата — ОКРЕМИЙ шар, не властивість бітів.

    Модель НЕ перевіряє правильність координати щодо драбини: це робить
    авторитет драбини (власник). Тут лише носій для round-trip.
    """
    domain: str      # напр. "D5"
    width: int       # ширина щабля, з якою координата узгоджена
    ordinal: int     # порядковий номер у щаблі (0-based)


# ---------------------------------------------------------------------------
# ПАКУВАННЯ: неперервний MSB-first потік бітів, без вирівнювання по байтах
# ---------------------------------------------------------------------------

def pack(words: Iterable[Word]) -> Tuple[bytes, int]:
    """Пакує слова в один неперервний бітопотік.

    Повертає (payload_bytes, valid_bits). Фізичні байти — лише носій;
    останній байт може мати «хвіст» невикористаних бітів (valid_bits каже скільки).
    """
    acc = 0
    nbits = 0
    for w in words:
        acc = (acc << w.width) | w.value
        nbits += w.width
    payload = acc.to_bytes((nbits + 7) // 8, "big") if nbits else b""
    return payload, nbits


def unpack(payload: bytes, widths: List[int], valid_bits: int) -> List[Word]:
    """Обернена до pack(). widths задають межі слів; valid_bits — довжину потоку."""
    total = sum(widths)
    if total != valid_bits:
        raise BinaryLanguageError(
            f"сума ширин {total} != valid_bits {valid_bits} (fail-closed)"
        )
    if (valid_bits + 7) // 8 != len(payload):
        raise BinaryLanguageError("довжина payload не відповідає valid_bits")
    acc = int.from_bytes(payload, "big") if payload else 0
    # to_bytes добиває ЛІВОРУЧ (старші біти) — валідні біти сидять у МОЛОДШИХ.
    # Тому хвіст знімаємо МАСКОЮ, а не зсувом праворуч.
    acc &= (1 << valid_bits) - 1
    out: List[Word] = []
    for width in reversed(widths):
        mask = (1 << width) - 1
        out.append(Word(width, acc & mask))
        acc >>= width
    out.reverse()
    return out


# ---------------------------------------------------------------------------
# ДВІЙКОВЕ ДЖЕРЕЛО: рядок точних слів, розділених пробілом (як .lisp-джерело)
# ---------------------------------------------------------------------------

def parse_source(text: str) -> List[Word]:
    """Розбирає видиме бінарне джерело: послідовність бітових токенів.

    Кожен токен — точний бітовий рядок; ширина = довжина токена.
    Жодних імен, жодних літер — лише 0/1.
    """
    words: List[Word] = []
    for tok in text.split():
        if not tok or any(c not in "01" for c in tok):
            raise BinaryLanguageError(f"небінарний токен у джерелі: {tok!r}")
        words.append(Word(len(tok), int(tok, 2)))
    return words


def render_source(words: Iterable[Word]) -> str:
    return " ".join(w.bits() for w in words)


# ---------------------------------------------------------------------------
# ПРОГРАМА = бінарні слова + (окремо) доменні координати
# ---------------------------------------------------------------------------

@dataclass
class BinaryProgram:
    words: List[Word]
    coords: List[Coordinate]   # той самий порядок, той самий len

    def check(self) -> None:
        if len(self.words) != len(self.coords):
            raise BinaryLanguageError("кількість слів і координат не збігається")
        for w, c in zip(self.words, self.coords):
            if w.width != c.width:
                raise BinaryLanguageError(
                    f"ширина слова {w.width} != ширина координати {c.width} ({c.domain})"
                )

    def pack(self) -> Tuple[bytes, int]:
        self.check()
        return pack(self.words)

    def roundtrip(self) -> "BinaryProgram":
        self.check()
        payload, nbits = pack(self.words)
        widths = [w.width for w in self.words]
        back = unpack(payload, widths, nbits)
        return BinaryProgram(back, list(self.coords))


# ---------------------------------------------------------------------------
# SELF-TEST — доводить, що модель тримає контракт
# ---------------------------------------------------------------------------

def _self_test() -> int:
    fails = 0

    def ok(name: str, cond: bool) -> None:
        nonlocal fails
        print(f"  [{'OK' if cond else 'FAIL'}] {name}")
        if not cond:
            fails += 1

    # 1) слово завжди точне
    ok("width 0 відкидається", _raises(lambda: Word(0, 0)))
    ok("width 10 відкидається", _raises(lambda: Word(10, 0)))
    ok("значення за шириною відкидається", _raises(lambda: Word(3, 8)))

    # 2) пакування без вирівнювання: 3+5 біт = 8 біт, але слово перетинає байт
    words = [Word(3, 0b101), Word(5, 0b01101), Word(2, 0b10)]
    payload, nbits = pack(words)
    ok("valid_bits = сума ширин", nbits == 3 + 5 + 2)
    ok("payload мінімальної довжини", len(payload) == (nbits + 7) // 8)

    # 3) round-trip зберігає ТОЧНО слова
    back = unpack(payload, [w.width for w in words], nbits)
    ok("round-trip точний", back == words)

    # 4) межа слова перетинає межу байта (11 біт -> 2 байти, 1 слово на межі)
    w2 = [Word(5, 0b11111), Word(6, 0b000001)]
    p2, n2 = pack(w2)
    ok("перетин межі байта збережено", unpack(p2, [5, 6], n2) == w2)

    # 5) джерело: лише 0/1
    ok("бінарне джерело парситься", parse_source("101 01101 10") == words)
    ok("небінарний токен відкидається", _raises(lambda: parse_source("101 a10")))
    ok("render↔parse оборотні", parse_source(render_source(words)) == words)

    # 6) програма: координати окремо, ширина мусить збігатись
    coords = [Coordinate("D1", 3, 0), Coordinate("D3", 5, 1), Coordinate("D2", 2, 2)]
    prog = BinaryProgram(words, coords)
    prog.check()
    ok("програма round-trip з координатами", prog.roundtrip().words == words)
    bad = BinaryProgram(words, [Coordinate("D1", 9, 0)] + coords[1:])
    ok("розбіжність ширин координат відкидається", _raises(bad.check))

    # 7) fail-closed на неузгоджених width/valid_bits
    ok("невідповідність valid_bits відкидається",
       _raises(lambda: unpack(payload, [3, 5, 3], nbits)))

    print(f"\nSELF-TEST: {'PASS' if fails == 0 else 'FAIL'} ({fails} fail)")
    return 1 if fails else 0


def _raises(fn) -> bool:
    try:
        fn()
    except BinaryLanguageError:
        return True
    except Exception:
        return False
    return False


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    # демонстрація: бінарна програма -> бітопотік -> назад
    demo = parse_source("00000111 10011100 00000011")
    print("джерело :", render_source(demo))
    payload, nbits = pack(demo)
    print(f"payload : {payload.hex()}  ({nbits} бітів, {len(payload)} байтів)")
    back = unpack(payload, [w.width for w in demo], nbits)
    print("назад   :", render_source(back))
    print("точність:", back == demo)
