"""Exact bytes, global plans, corruption and independent Round-Trip tests."""
import itertools
import random
import unittest

import adaptive_width_research as кодек


class ТестиАдаптивногоПланувальника(unittest.TestCase):
    def перевірити(self, words):
        wire = кодек.кодувати(words)
        self.assertEqual(кодек.декодувати(wire), tuple(words))
        self.assertEqual(кодек.кодувати(кодек.декодувати(wire)), wire)
        plan = кодек.планувати(words)
        self.assertEqual(len(wire), plan.усього_байтів)
        self.assertLessEqual(plan.усього_байтів, plan.простий_базис_байтів)
        return wire, plan

    def test_атоми_порожня_кілька_коренів(self):
        for words in ((), ("0",), ("1",), ("000000000",), ("111111111",),
                      ("10", "01"), ("10", "01", "10", "01"),
                      ("10", "001", "00", "000", "01")):
            with self.subTest(words=words):
                self.перевірити(words)

    def test_вичерпно_короткі_послідовності(self):
        alphabet = ("0", "1", "01", "10", "000")
        for n in range(4):
            for words in itertools.product(alphabet, repeat=n):
                self.перевірити(words)

    def test_всі_ширини_з_нулями(self):
        for width in range(1, 10):
            self.перевірити(("0" * width, "1" * width, "0" * (width - 1) + "1"))
            words = ("0" * width,) * 128
            wire, plan = self.перевірити(words)
            self.assertEqual(plan.блоки[0].режим, width)

    def test_розумні_комбінації_ширин(self):
        for sizes in ((1, 2), (1, 2, 3), (9, 1, 4, 2), (3, 6, 2, 9, 1, 8, 5, 7)):
            words = tuple("1" * w for w in sizes) * 32
            wire, plan = self.перевірити(words)
            self.assertTrue(any(0x22 <= b.режим <= 0x28 for b in plan.блоки),
                            (sizes, plan))
            self.assertLess(len(wire), plan.простий_базис_байтів)

    def test_однорідні_й_циклічні_блоки_в_одній_програмі(self):
        words = ("0",) * 50 + ("00",) * 50 + ("111", "0", "10") * 50
        wire, plan = self.перевірити(words)
        self.assertTrue(any(b.режим == 1 for b in plan.блоки))
        self.assertTrue(any(b.режим == 2 for b in plan.блоки))
        self.assertTrue(any(b.режим >= 0x20 for b in plan.блоки))

    def test_довгі_випадкові_послідовності(self):
        rng = random.Random(20261011)
        for n in (8, 30, 129, 257):
            words = []
            for _ in range(n):
                width = rng.randrange(1, 10)
                words.append(format(rng.randrange(1 << width), f"0{width}b"))
            self.перевірити(tuple(words))

    def test_пошкоджені_записи_й_версії(self):
        wire = кодек.кодувати(("0", "10", "111") * 16)
        bad_records = (
            b"", b"R3A", wire[:-1], wire + b"\xff", b"\x00" + wire[1:],
            wire[:3] + b"\x81\x00" + wire[4:],
            wire[:5] + b"\xff" + wire[6:],
        )
        for raw in bad_records:
            with self.subTest(raw=raw[:12]):
                with self.assertRaises(кодек.ПомилкаПакування):
                    кодек.декодувати(raw)
        for words in (("",), ("3",), ("1010101010",), ("1", 2)):
            with self.assertRaises(кодек.ПомилкаПакування):
                кодек.кодувати(words)

    def test_доповнення_байта_мусить_бути_нульовим(self):
        wire = кодек.кодувати(("1",))
        with self.assertRaises(кодек.ПомилкаПакування):
            кодек.декодувати(wire[:-1] + bytes((wire[-1] | 1,)))


    def test_незалежний_повний_перебір_мінімального_плану(self):
        # 1093 незалежних маленьких задач (довжини 0..6, ширини 1/2/3).
        # Оракул сам перебирає всі розбиття, а не викликає DP кодека.
        from functools import lru_cache
        for count in range(7):
            for widths in itertools.product((1, 2, 3), repeat=count):
                @lru_cache(None)
                def мінімум(i):
                    if i == count:
                        return 0
                    best = 10 ** 30
                    for j in range(i + 1, count + 1):
                        segment = widths[i:j]
                        n, payload = len(segment), (sum(segment) + 7) // 8
                        costs = [2 + (n + 1) // 2 + payload]
                        if len(set(segment)) == 1:
                            costs.append(2 + payload)
                        for period in range(2, 9):
                            if (n >= 2 * period
                                    and all(segment[t] == segment[t % period]
                                            for t in range(n))):
                                costs.append(2 + (period + 1) // 2 + payload)
                        best = min(best, min(costs) + мінімум(j))
                    return best

                words = tuple("0" * width for width in widths)
                plan = кодек.планувати(words)
                # magic 3B + ULEB count 1B + u16 block count 2B
                self.assertEqual(plan.усього_байтів, 6 + мінімум(0),
                                 (widths, plan))

if __name__ == "__main__":
    unittest.main()
