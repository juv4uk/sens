"""Статична перевірка нової української поверхні добору механізмів.

Python НЕ обчислює семантику СЕНС: перевіряємо лише форму вихідного
файла, відсутність застарілих викличних назв і точність таблиць доменів.
Поведінку перевіряє справжній виконавець СЕНС, а не ця перевірка.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

КОРІНЬ = Path(__file__).resolve().parents[1]
ДЖЕРЕЛО = КОРІНЬ / "lib/mechanism-selector.lisp"
УКРАЇНСЬКІ_ВИЗНАЧЕННЯ = (
    "реєстр-вибору-механізму",
    "метадані-вибору-механізму",
    "рядки-реєстру-механізму",
    "механізм-однакові?",
    "механізм-знайти-секцію",
    "маршрути-вибору-механізму",
    "реєстр-містить-ідентичність?",
    "механізм-зіставити-маршрут",
    "механізм-знайти-маршрут",
    "механізм-оформити-вибір",
    "вибрати-механізм",
)
СТАРІ_ВИЗНАЧЕННЯ = (
    "mechanism-selector-find-section",
    "mechanism-selector-registry-has-sid?",
    "mechanism-selector-find-route",
    "mechanism-select",
    "mechanism-selector-registry",
    "mechanism-selector-metadata",
    "mechanism-selector-registry-rows",
    "mechanism-selector-routes",
)


def прибрати_коментарі_й_рядки(джерело: str) -> str:
    """Зберегти роздільники форм, не сприймаючи рядки й коментарі як код."""
    результат: list[str] = []
    рядок = False
    коментар = False
    екрановано = False
    for знак in джерело:
        if коментар:
            if знак == "\n":
                коментар = False
                результат.append("\n")
            continue
        if рядок:
            if екрановано:
                екрановано = False
            elif знак == "\\":
                екрановано = True
            elif знак == '"':
                рядок = False
            if знак == "\n":
                результат.append("\n")
            continue
        if знак == ";":
            коментар = True
        elif знак == '"':
            рядок = True
        else:
            результат.append(знак)
    if рядок:
        raise AssertionError("Незавершений рядковий літерал")
    return "".join(результат)


class УкраїнськийДобірМеханізмів(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.джерело = ДЖЕРЕЛО.read_text(encoding="utf-8")
        cls.код = прибрати_коментарі_й_рядки(cls.джерело)

    def test_лише_українські_визначення(self) -> None:
        визначення = re.findall(r"(?m)^\(визначити\s+([^\s()]+)", self.код)
        self.assertEqual(tuple(визначення), УКРАЇНСЬКІ_ВИЗНАЧЕННЯ)
        for назва in СТАРІ_ВИЗНАЧЕННЯ:
            self.assertNotRegex(self.код, rf"\({re.escape(назва)}(?=[\s)])")

    def test_точні_дужки_та_відсутність_старих_голів(self) -> None:
        глибина = 0
        for знак in self.код:
            if знак == "(":
                глибина += 1
            elif знак == ")":
                глибина -= 1
                self.assertGreaterEqual(глибина, 0, "Зайва закривальна дужка")
        self.assertEqual(глибина, 0, "Незакрита форма")
        self.assertNotRegex(self.код, r"\([01]{3,10}(?=[\s(])")
        self.assertNotRegex(self.код, r"\((?:defun|define|lambda)\s")
        self.assertNotRegex(self.код, r"\(\s*\(\s*функція\s*\(")
        self.assertIn("(механізм-зіставити-маршрут", self.код)
        self.assertIn("(механізм-оформити-вибір", self.код)

    def test_чинний_протокол_не_містить_sid8_статусу(self) -> None:
        for фрагмент in (
            "(як-є rows)",
            "(як-є mechanism-selected)",
            "(як-є mechanism-unavailable)",
            "(як-є mechanism-selection-failure)",
            "(як-є доменного-коду-немає-в-таблиці)",
        ):
            self.assertIn(фрагмент, self.джерело)
        self.assertNotIn("(як-є sid-not-in-function-table)", self.код)

    def test_чинні_споживачі_викликають_українську_поверхню(self) -> None:
        for шлях in ("lib/core3.lisp", "lib/island-lowering.lisp"):
            код = прибрати_коментарі_й_рядки(
                (КОРІНЬ / шлях).read_text(encoding="utf-8")
            )
            self.assertIn("(вибрати-механізм ", код, шлях)
            self.assertNotIn("(mechanism-select ", код, шлях)

    def test_домени_мають_точні_адреси(self) -> None:
        for ширина in range(1, 11):
            with self.subTest(домен=ширина):
                таблиця = (КОРІНЬ / f"lib/domains/d{ширина}.lisp").read_text(
                    encoding="utf-8"
                )
                слова = re.findall(r"(?m)^  \(([01]+)\s", таблиця)
                очікувані = [
                    format(індекс, f"0{ширина}b") for індекс in range(1 << ширина)
                ]
                self.assertEqual(слова, очікувані)


if __name__ == "__main__":
    unittest.main(verbosity=2)
