"""Точні комбінаторні свідки дослідного Tb-33, не файловий кодер SENS.

Доказ для всіх потоків із алфавіту {0,1,2} без підрядка 22.
Це ширший клас, ніж канонічні програми D2; не підмінює parser/T5.
"""

import itertools
import math
import unittest
from functools import lru_cache


@lru_cache(maxsize=None)
def ways(remaining: int, previous: int = -1) -> int:
    """Кількість допустимих продовжень за відомого попереднього трита."""
    if remaining == 0:
        return 1
    return sum(
        ways(remaining - 1, digit)
        for digit in (0, 1, 2)
        if not (previous == digit == 2)
    )


def rank(trits: tuple[int, ...]) -> int:
    """Лексикографічний номер у множині з відомою довжиною."""
    result, previous = 0, -1
    for position, digit in enumerate(trits):
        if digit not in (0, 1, 2) or previous == digit == 2:
            raise ValueError("недопустимий трит або заборонене 22")
        for smaller in range(digit):
            if not (previous == smaller == 2):
                result += ways(len(trits) - position - 1, smaller)
        previous = digit
    return result


def unrank(length: int, number: int) -> tuple[int, ...]:
    """Обернення можливе лише коли довжина відома окремо."""
    if not 0 <= number < ways(length):
        raise ValueError("номер поза ємністю довжини")
    result, previous = [], -1
    for remaining in range(length - 1, -1, -1):
        for digit in (0, 1, 2):
            if previous == digit == 2:
                continue
            count = ways(remaining, digit)
            if number < count:
                result.append(digit)
                previous = digit
                break
            number -= count
        else:
            raise ValueError("неможливо відновити номер")
    return tuple(result)


class Tb33CapacityEvidence(unittest.TestCase):
    def test_small_exhaustive_roundtrip(self) -> None:
        """Усі припустимі рядки n=0..8, незалежно від D2-синтаксису."""
        for length in range(9):
            accepted = [
                s for s in itertools.product((0, 1, 2), repeat=length)
                if all(a != 2 or b != 2 for a, b in zip(s, s[1:]))
            ]
            self.assertEqual(len(accepted), ways(length))
            self.assertEqual([rank(s) for s in accepted], list(range(len(accepted))))
            for index, item in enumerate(accepted):
                self.assertEqual(unrank(length, index), item)

    def test_exact_48_bit_capacity(self) -> None:
        """33 трити вміщуються, 34 — ні. Заповнення кодів і rate різні."""
        self.assertEqual(ways(0), 1)
        self.assertEqual(ways(1), 3)
        self.assertEqual(ways(33), 273203580829696)
        self.assertEqual(ways(34), 746406063636480)
        self.assertLess(ways(33), 1 << 48)
        self.assertGreater(ways(34), 1 << 48)
        self.assertAlmostEqual(math.log2(ways(33)) / 48, 0.9991035358607662)

    def test_unmarked_final_length_collision(self) -> None:
        """Два допустимі суфікси з кінцевим D2 01 мають той самий rank."""
        short = (0, 1)
        long = (0, 0, 1)
        self.assertNotEqual(short, long)
        self.assertEqual(rank(short), 1)
        self.assertEqual(rank(long), 1)
        self.assertEqual(unrank(2, 1), short)
        self.assertEqual(unrank(3, 1), long)
        # Шестибайтні слоти однакові без додаткового поля довжини.
        self.assertEqual(rank(short).to_bytes(6, "big"), rank(long).to_bytes(6, "big"))

    def test_all_variable_lengths_cannot_fit_one_48_bit_slot(self) -> None:
        """Строга межа для всіх потоків no-22 довжини 0..33."""
        count = sum(ways(n) for n in range(34))
        self.assertEqual(count, 430937741765290)
        self.assertGreater(count, 1 << 48)
        self.assertEqual((1 << 48) - ways(33), 8271395880960)

    def test_repeated_pad_two_breaks_transport_law(self) -> None:
        """Ніякого універсального доповнення лише 2 до 33 тритів."""
        stream = (1, 0, 1)
        padding = (2,) * (33 - len(stream))
        padded = stream + padding
        self.assertIn((2, 2), list(zip(padded, padded[1:])))


if __name__ == "__main__":
    unittest.main()
