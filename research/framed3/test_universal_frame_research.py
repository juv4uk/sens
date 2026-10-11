"""Негативні та диференційні досліди віртуального продовження Рамки-3."""

import itertools
import random
import unittest

import research_codec as рамка
import virtual_frame_research as носій


class ВіртуальнаРамкаТести(unittest.TestCase):
    def перевірити(self, слова):
        код = носій.кодувати(слова)
        self.assertEqual(носій.декодувати(код), tuple(слова))
        self.assertEqual(носій.кодувати(носій.декодувати(код)), код)
        self.assertTrue(code_has_version(code=код))

    def test_порожні_атоми_структури(self):
        for слова in [
            (), ("0",), ("1",), ("00",), ("000",),
            ("000000000",), ("01",), ("10",), ("11",),
            ("10", "01"), ("10", "000", "01"),
            ("10", "100", "00", "10", "111", "00", "000", "00", "000", "01", "01"),
            ("01", "10", "01"),  # Два крайні маркери як точні слова даних.
            ("10", "01", "10", "01"),  # Декілька кореневих форм.
            ("001", "000", "01", "10", "101"),
        ]:
            with self.subTest(слова=слова):
                self.перевірити(слова)

    def test_вичерпні_короткі_послідовності(self):
        алфавіт = ("0", "1", "00", "01", "10")
        for довжина in range(4):
            for слова in itertools.product(алфавіт, repeat=довжина):
                self.перевірити(слова)

    def test_усі_ширини_і_провідні_нулі(self):
        for ширина in range(1, 10):
            self.перевірити(("0" * ширина, "1" * ширина, "0" * (ширина - 1) + "1"))
        rng = random.Random(20261011)
        for _ in range(35):
            count = rng.randrange(0, 48)
            words = tuple(
                format(rng.randrange(1 << w), f"0{w}b")
                for w in (rng.randrange(1, 10) for _ in range(count))
            )
            self.перевірити(words)

    def test_довгі_потоки_і_перетин_блоків(self):
        corpus = tuple(("10", "01", "000000000", "0", "11") * 48)
        wire = носій.кодувати(corpus)
        self.assertGreater(wire.count(bytes([носій.РЕЖИМ_ВІРТУАЛЬНИЙ])), 1)
        self.перевірити(corpus)

    def test_нативна_рамка_зберігає_свій_ранг(self):
        words = ("10", "001", "00", "000", "01")
        wire = носій.кодувати(words)
        self.assertEqual(wire[3], носій.РЕЖИМ_ПРЯМИЙ)
        size, off = носій._читати_довжину(wire, 4)
        self.assertEqual(wire[off:off + size], рамка.encode(words))
        self.перевірити(words)

    def test_неканонічні_контейнери_і_межі(self):
        valid = носій.кодувати(("0",))
        corrupted = [
            b"", valid[:2], b"oops" + valid,
            valid[:-1], valid + b"\x00", valid[:3] + b"\x07" + valid[4:],
            valid[:4] + b"\x81\x00" + valid[5:],  # Не мінімальна LEB128 довжина.
            valid[:4] + b"\x00" + valid[5:],
            valid[:4] + b"\xff" + valid[5:],
        ]
        for data in corrupted:
            with self.subTest(raw=data.hex()):
                with self.assertRaises(носій.ПомилкаРамки):
                    носій.декодувати(data)
        for words in [("",), ("012",), ("1010101010",), ("3",)]:
            with self.assertRaises(носій.ПомилкаРамки):
                носій.кодувати(words)

    def test_неприродне_подвійне_розбиття_заборонено(self):
        # Пара віртуальних записів має еквівалент одному; тільки один канонічний.
        body = носій._байти_за_тритами(носій._віртуальні_трити(("0",)))
        record = bytes((носій.РЕЖИМ_ВІРТУАЛЬНИЙ, len(body))) + body
        invalid = носій.МАГІЯ + record + record + bytes((носій.КІНЕЦЬ,))
        with self.assertRaises(носій.ПомилкаРамки):
            носій.декодувати(invalid)


def code_has_version(*, code):
    return code.startswith(носій.МАГІЯ) and code.endswith(bytes((носій.КІНЕЦЬ,)))


if __name__ == "__main__":
    unittest.main()
