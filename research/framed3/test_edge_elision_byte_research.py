"""Незалежні негативні й оборотні свідки вилучення першого та кінцевих D2."""
from itertools import product
import unittest

import adaptive_byte_research as base
import edge_elision_byte_research as edge
import trailing_closers_research as d2


class КраїРамки(unittest.TestCase):
    def roundtrip(self, words):
        raw = edge.кодувати(words)
        self.assertEqual(edge.декодувати(raw), tuple(words))
        self.assertEqual(edge.кодувати(edge.декодувати(raw)), raw)
        plan = edge.планувати(words)
        self.assertEqual(plan.байтів_після, len(raw))
        self.assertLessEqual(len(raw), plan.байтів_без_скорочення)
        return plan

    def test_обидва_краї_та_нульова_середина(self):
        for words in (
            ("10", "01"),
            ("10", "10", "111", "01", "01"),
            ("10", "10", "10", "0", "01", "01", "01"),
            ("10", "0", "11", "1", "01"),
            ("10", "00", "01"),
            ("10", "0", "00", "1", "01"),
            ("10", "001", "00", "000", "01"),
        ):
            with self.subTest(words=words):
                self.assertEqual(edge._відновити(2, d2.trim(words)[1:]), words)
                self.roundtrip(words)

    def test_багато_коренів_не_видаляти_перший_open(self):
        for words in (
            ("10", "01", "10", "01"),
            ("000", "10", "1", "01"),
            ("10", "0", "01", "10", "1", "01"),
            ("10", "01", "000"),
        ):
            with self.subTest(words=words):
                d2.validate(words)
                self.assertFalse(edge._одна_зовнішня(words))
                self.assertTrue(all(mode != edge.БЕЗ_КРАЇВ
                                    for mode, _ in edge._скорочення(words)))
                self.roundtrip(words)

    def test_тільки_кінцеві_закриття_і_атоми(self):
        for words in (
            ("000",),
            ("1",),
            ("01",),  # invalid D2, але lossless raw bytes допускають exact words
            ("10", "1", "01", "000"),
            ("000000000", "10", "0", "01"),
            (),
        ):
            with self.subTest(words=words):
                self.roundtrip(words)

    def test_глибокі_рамки_та_всі_ширини(self):
        for depth in (1, 2, 3, 16, 64, 100):
            words = ("10",) * depth + ("000000000",) + ("01",) * depth
            short = d2.trim(words)
            self.assertEqual(short, ("10",) * depth + ("000000000",))
            self.assertEqual(edge._відновити(2, short[1:]), words)
            plan = self.roundtrip(words)
            # На глибокому корпусі необхідно вимірювати реальні байти,
            # не підсумовувати "виграні біти" із граматичним ранжуванням.
            self.assertLessEqual(plan.байтів_після, plan.байтів_без_скорочення)

    def test_короткий_вичерпний_корпус(self):
        alphabet = ("0", "1", "00", "01", "10", "11", "000")
        count = 0
        for n in range(1, 4):
            for words in product(alphabet, repeat=n):
                try:
                    d2.validate(words)
                except d2.SuffixError:
                    continue
                for mode, reduced in edge._скорочення(words):
                    if mode == 1:
                        self.assertEqual(d2.restore(reduced), words)
                    if mode == 2:
                        self.assertEqual(edge._відновити(mode, reduced), words)
                self.roundtrip(words)
                count += 1
        self.assertGreater(count, 15)

    def test_пошкодження_сумі_довжини_режиму_і_eof(self):
        raw = edge.кодувати(("10", "10", "111", "01", "01"))
        invalid = [
            b"", raw[:2], raw[:-1], raw + b"\x00",
            b"ABC" + raw[3:],
            raw[:3] + b"\x07" + raw[4:],
            raw[:4] + b"\x82\x00" + raw[5:],
            raw[:5] + bytes((raw[5] ^ 0xFF,)) + raw[6:],
        ]
        for data in invalid:
            with self.subTest(raw=data[:9].hex()):
                with self.assertRaises(edge.ПомилкаСкорочення):
                    edge.декодувати(data)

    def test_контрприклад_префіксів_обовязкова_рамка(self):
        outer1 = ("10", "01")
        outer2 = ("10", "10", "01", "01")
        self.assertEqual(d2.trim(outer1), ("10",))
        self.assertEqual(d2.trim(outer2), ("10", "10"))
        # "10" — префікс "10 10", обидва можуть бути доповнені до
        # іншої правильної програми. Декодер покладається на exact
        # physical payload length + CRC, а не на EOF як доказ.
        one = edge.кодувати(outer1)
        two = edge.кодувати(outer2)
        self.assertNotEqual(one, two)
        self.assertEqual(edge.декодувати(one), outer1)
        self.assertEqual(edge.декодувати(two), outer2)
        with self.assertRaises(edge.ПомилкаСкорочення):
            edge.декодувати(two[:-1])


if __name__ == "__main__":
    unittest.main()
