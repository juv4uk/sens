"""Вичерпна валідація канонічної ємності проти незалежного оракула.

Порівнює DP канонічного підрахунку з повним переліком усіх програм малої довжини,
де кожна дерева перевіряється ДОВЕДЕНИМ оракулом `definitely_impossible`
і правилом власника `() = 000` (порожній D2-кадр не є програмою).
"""
from __future__ import annotations

import unittest
from dataclasses import dataclass
from functools import lru_cache

import canonical_capacity_research as cap
from canonical_d2_rank_research import count_inner, rank
from semantic_redundancy_research import Form, Word, definitely_impossible

OPEN, CLOSE, SEP, DOT = "10", "01", "00", "11"


@dataclass(frozen=True)
class WideWord(Word):
    """Payload-слово будь-якої ширини 1..9 (оракул приймає лише D1/D3)."""

    def __post_init__(self):
        if not (1 <= len(self.bits) <= 9 and all(c in "01" for c in self.bits)):
            raise ValueError("дослід підтримує exact D1–D9")


class Rejected(ValueError):
    pass


def parse_program(form: tuple[str, ...]):
    """Дерево цілої програми (`10 … 01`). Rejected — структурно недійсне."""
    pos = 0
    size = len(form)

    def separators():
        nonlocal pos
        while pos < size and form[pos] == SEP:
            pos += 1

    def expression(data: bool):
        nonlocal pos
        if pos >= size:
            raise Rejected("немає виразу")
        word = form[pos]
        if word == OPEN:
            return list_expr(data)
        if len(word) == 2:
            raise Rejected("структурне слово як вираз")
        pos += 1
        return WideWord(word)

    def list_expr(data: bool):
        nonlocal pos
        if form[pos] != OPEN:
            raise Rejected("список мусив починатися з OPEN")
        pos += 1
        heads = 0
        items = []
        while True:
            separators()
            if pos >= size:
                raise Rejected("незакритий список")
            if form[pos] == CLOSE:
                pos += 1
                return Form(tuple(items))
            if form[pos] == DOT:
                if heads == 0:
                    raise Rejected("крапка без голови")
                pos += 1
                separators()
                items.append(expression(data))
                separators()
                if pos >= size or form[pos] != CLOSE:
                    raise Rejected("після хвоста мусить бути CLOSE")
                pos += 1
                return Form(tuple(items))
            items.append(expression(data))
            heads += 1

    if not form or form[0] != OPEN:
        raise Rejected("програма мусить починатися з OPEN")
    tree = list_expr(False)
    if pos != size:
        raise Rejected("зайві слова")
    return tree


def empty_code_list(tree) -> bool:
    """Чи є в КОДОВОМУ контексті порожній D2-кадр (`() = 000`, не кадр)."""
    if isinstance(tree, Word):
        return False
    if not tree.items:
        return True
    # Аргументи QUOTE — дані: перевірка не застосовується.
    head = tree.items[0]
    if isinstance(head, Word) and head.bits == "001" and len(tree.items) == 2:
        return False
    return any(empty_code_list(item) for item in tree.items)


@lru_cache(maxsize=None)
def all_bodies(bits: int) -> tuple[tuple[str, ...], ...]:
    if bits == 0:
        return ((),)
    out = []
    for width in range(1, min(9, bits) + 1):
        for value in range(1 << width):
            word = format(value, f"0{width}b")
            for suffix in all_bodies(bits - width):
                out.append((word, *suffix))
    return tuple(out)


class ExhaustiveOracle(unittest.TestCase):
    """Повний перелік програм малої довжини проти оракула."""

    def test_counts_match_proved_oracle(self):
        for bits in range(0, 6):
            admissible = 0
            empty_frame = 0
            for body in all_bodies(bits):
                form = ("10", *body, "01")
                try:
                    rank(form)
                except Exception:
                    continue
                tree = parse_program(form)
                if empty_code_list(tree):
                    empty_frame += 1
                    continue
                if not definitely_impossible(tree):
                    admissible += 1
            dp = sum(v for (b, w), v in cap.counts(bits, "canonical").items()
                     if b == bits)
            self.assertEqual(dp, admissible,
                             f"біти={bits}: DP={dp} оракул={admissible}")
            print(f"  біти={bits}: DP={dp} оракул={admissible} "
                  f"(порожніх кадрів відкинуто: {empty_frame})")

    def test_dead_tree_is_named_rejected(self):
        dead = ("10", "10", "010", "01", "01")   # ((ATOM))
        quoted = ("10", "001", "10", "010", "01", "01")  # (QUOTE ((ATOM)))
        dead_tree = parse_program(dead)
        quoted_tree = parse_program(quoted)
        self.assertTrue(definitely_impossible(dead_tree))
        self.assertFalse(empty_code_list(dead_tree))
        self.assertFalse(definitely_impossible(quoted_tree))
        self.assertFalse(empty_code_list(quoted_tree))
        print(f"  мертве дерево {' '.join(dead)} → відкинуто (named fail)")
        print(f"  як дані {' '.join(quoted)} → збережено")


if __name__ == "__main__":
    unittest.main(verbosity=2)
