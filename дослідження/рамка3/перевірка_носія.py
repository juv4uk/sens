"""Відтворювані позитивні й негативні свідки для дослідної рамки."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import носій as р


class ПеревіркаРамки(unittest.TestCase):
    def test_відомі_приклади(self):
        зразки = [
            ("10 01", "00", 1),
            ("10 001 01", "08", 2),
            ("10 001 00 000 01", "23d0", 4),
            ("10 100 00 10 111 00 1 00 0 01 01", "2109895eb5", 7),
            ("10 001 00 10 000 01 01", "3a38ed", 5),
        ]
        for текст, очікуване, байтів_т5 in зразки:
            with self.subTest(текст=текст):
                слова = текст.split()
                фізичні = р.упакувати(слова)
                self.assertEqual(фізичні.hex(), очікуване)
                self.assertEqual(р.розпакувати(фізичні), слова)
                self.assertEqual(р.байтів_т5(слова), байтів_т5)
                self.assertLessEqual(len(фізичні), байтів_т5)

    def test_місткість_до_трьох_байтів(self):
        self.assertEqual(р.групи()[:3],
            ((1, 5, 11, 139), (2, 12, 17, 57504), (3, 18, 22, 8716160)))
        for байтів, _перша, _остання, обсяг in р.групи():
            self.assertLessEqual(обсяг, 1 << (8 * байтів))

    def test_ранжування_незалежних_послідовностей(self):
        випадкові = random.Random(20261010)
        перевірок = 0
        for _, перша, остання, _ in р.групи():
            for довжина in range(перша, остання + 1):
                кількість = р.місткість(довжина)
                if кількість == 0:
                    continue  # Немає жодного допустимого слова цієї довжини.
                варіанти = {0, кількість // 2, кількість - 1}
                варіанти.update(випадкові.randrange(кількість) for _ in range(50))
                for число in варіанти:
                    трити = р.за_рангом(довжина, число)
                    self.assertEqual(р.ранг(трити), число)
                    self.assertNotIn((2, 2), list(zip(трити, трити[1:])))
                    перевірок += 1
        self.assertGreaterEqual(перевірок, 2000)

    def test_помилкові_рамки(self):
        for текст in ("10 001", "10 01 10 01", "10 001 01 01",
                      "01 10", "10 0000000000 01", "10 01 0"):
            with self.subTest(текст=текст), self.assertRaises(ValueError):
                р.упакувати(текст.split())

    def test_незайняті_коди(self):
        for дані in (b"\xff", b"\xff\xff", b"\xff\xff\xff", b""):
            with self.subTest(дані=дані), self.assertRaises(ValueError):
                р.розпакувати(дані)

    def test_послідовності_вкладених_рамок(self):
        випадкові = random.Random(1042026)
        for _ in range(1000):
            # Одна зовнішня форма, не більше трьох вкладених рамок.
            слова = ["10"]
            for _ in range(випадкові.randrange(4)):
                слова += ["00", "10", "00", "001", "01"]
            слова += ["00", "111", "01"]
            try:
                фізичні = р.упакувати(слова)
            except ValueError as e:
                if "межу дослідного носія" in str(e):
                    continue
                raise
            self.assertEqual(р.розпакувати(фізичні), слова)


if __name__ == "__main__":
    unittest.main()
