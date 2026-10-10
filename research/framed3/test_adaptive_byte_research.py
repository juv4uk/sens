"""Блоки саме у фізичних БАЙТАХ: незалежний oracle та негативні свідки."""
import itertools
import random
import unittest
from functools import lru_cache

import adaptive_byte_research as носій
import research_codec as рамка


def незалежний_мінімум(слова):
    """Перебір усіх коротких сегментацій; без DP із production-досліду."""
    buckets = {}
    for size, lo, hi in рамка._buckets():
        for n in range(lo, hi + 1):
            buckets[n] = size

    @lru_cache(None)
    def walk(i):
        if i == len(слова):
            return 0
        result = 1 << 40
        for j in range(i + 1, min(i + 128, len(слова)) + 1):
            chunk = слова[i:j]
            n, bits = len(chunk), sum(len(w) for w in chunk)
            costs = [1 + len(носій._число(n)) + (n + 1) // 2 + (bits + 7) // 8]
            virtual = 4 + bits + n - 1
            if virtual in buckets:
                costs.append(1 + buckets[virtual])
            try:
                рамка.transport(chunk)
            except рамка.FrameError:
                pass
            else:
                direct = bits + max(0, n - 3)
                if direct in buckets:
                    costs.append(1 + buckets[direct])
            result = min(result, min(costs) + walk(j))
        return result

    return 3 + len(носій._число(len(слова))) + walk(0)


class ТестиБайтовоїРамки(unittest.TestCase):
    def перевірити(self, words):
        raw = носій.кодувати(words)
        plan = носій.планувати(words)
        self.assertEqual(носій.декодувати(raw), tuple(words))
        self.assertEqual(len(raw), plan.фізичних_байтів)
        self.assertLessEqual(len(raw), plan.базовий_сирий_розмір)
        self.assertEqual(носій.кодувати(носій.декодувати(raw)), raw)
        return plan

    def test_один_два_три_фізичні_байти(self):
        cases = [
            (("0",), 1),
            (("111111111",), 2),
            (("111111", "111111"), 3),
        ]
        for words, expected in cases:
            with self.subTest(bytes=expected):
                plan = self.перевірити(words)
                self.assertEqual(plan.групи_байтів, (expected,))
                self.assertNotEqual(plan.фрагменти[0].режим, "сирий")

    def test_короткі_програми_включно_з_атомом(self):
        for words in [(), ("0",), ("1",), ("000000000",), ("10", "01"),
                      ("10", "01", "10", "01"), ("01", "10", "00"),
                      ("10", "001", "00", "000", "01")]:
            self.перевірити(words)

    def test_короткий_вичерпний_словник(self):
        alphabet = ("0", "1", "01", "10", "000")
        for n in range(4):
            for words in itertools.product(alphabet, repeat=n):
                self.перевірити(words)

    def test_незалежний_мінімум_для_кожної_комбінації_1_2_3_біт_слів(self):
        # Семантична ширина слів тут лише НАВАНТАЖЕННЯ.
        # Обирається оптимальна комбінація ФІЗИЧНИХ 1,2,3,... байтових кадрів.
        checked = 0
        for n in range(7):
            for widths in itertools.product((1, 2, 3), repeat=n):
                words = tuple("0" * w for w in widths)
                plan = носій.планувати(words)
                self.assertEqual(plan.фізичних_байтів, незалежний_мінімум(words),
                                 (widths, plan))
                checked += 1
        self.assertEqual(checked, 1093)

    def test_великі_та_змішані_програми(self):
        rng = random.Random(20261011)
        examples = [
            ("0",) * 128,
            ("00",) * 128,
            ("111111111",) * 150,
            (("0", "111111111", "011") * 75),
            tuple(format(rng.randrange(1 << w), f"0{w}b")
                  for w in (rng.randrange(1, 10) for _ in range(196))),
        ]
        for words in examples:
            self.перевірити(words)

    def test_комбінації_байтових_блоків(self):
        words = ("0", "111111111", "101") * 90
        plan = self.перевірити(words)
        self.assertGreater(len(plan.групи_байтів), 1)
        self.assertTrue(all(1 <= n <= 63 for n in plan.групи_байтів
                            if n != 0))
        self.assertEqual(plan.фізичних_байтів,
                         3 + len(носій._число(len(words))) +
                         sum(b.байтів_запис for b in plan.фрагменти))

    def test_неканонічні_потоки(self):
        wire = носій.кодувати(("0", "111111111", "10"))
        corrupt = [
            b"", wire[:2], b"ABC" + wire[3:],
            wire[:-1], wire + b"\x00",
            wire[:3] + b"\x83\x00" + wire[4:],  # nonminimal varint count
            wire[:4] + b"\xff" + wire[5:],       # невідомий блок
            носій.МАГІЯ + b"\x01\x00\x01\x10\x81",  # raw: 7 padding bits nonzero
            носій.МАГІЯ + b"\x01\x00\x01\x10\x00",  # валідний raw, але alias
        ]
        for raw in corrupt:
            with self.subTest(raw=raw.hex()):
                with self.assertRaises(носій.ПомилкаБайтовоїРамки):
                    носій.декодувати(raw)

    def test_недопустимі_слова_та_ресурси(self):
        for words in [("",), ("012",), ("1010101010",), ("3",), (42,)]:
            with self.assertRaises(носій.ПомилкаБайтовоїРамки):
                носій.кодувати(words)


if __name__ == "__main__":
    unittest.main()
