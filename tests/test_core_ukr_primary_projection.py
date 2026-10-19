"""Точкова перевірка повної української проєкції основних Core-файлів.

Перевіряє напрямок primary → сумісний alias та exact-width таблиці.
Назви з таблиць є проєкціями; цей тест не надає координатам викличності.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class CoreUkrPrimaryProjectionTests(unittest.TestCase):
    def test_core_sources_follow_full_ukrainian_projection_without_changing_domain_identity(self):
        core = source("lib/core.lisp")
        core4 = source("lib/core4.lisp")
        surface = source("lib/surface/uk.lisp")

        with self.subTest(file="lib/core.lisp"):
            self.assertIn(
                "(визначити друге\n"
                "  (функція (значення-функції)\n"
                "    (перше (решта значення-функції))))\n"
                "(визначити second друге)",
                core,
            )
            self.assertIn("(визначити third третє)", core)
            self.assertIn(
                "(визначити четверте\n"
                "  (функція (значення-функції)\n"
                "    (третє (решта значення-функції))))\n"
                "(визначити fourth четверте)",
                core,
            )
            self.assertNotIn("(визначити друге second)", core)
            self.assertNotIn("(визначити четверте fourth)", core)

        with self.subTest(file="lib/core4.lisp"):
            self.assertIn("(визначити pair пара)", core4)
            self.assertIn("(визначити second друге)", core4)
            self.assertIn("(визначити third третє)", core4)
            self.assertIn(
                "(визначити четверте\n"
                "  (функція (значення-аргументів)\n"
                "    (третє (решта значення-аргументів))))\n"
                "(визначити fourth четверте)",
                core4,
            )
            self.assertNotIn("(визначити четверте fourth)", core4)

        with self.subTest(file="lib/surface/uk.lisp"):
            for alias in (
                "(визначити pair пара)",
                "(визначити second друге)",
                "(визначити third третє)",
                "(визначити fourth четверте)",
            ):
                with self.subTest(alias=alias):
                    self.assertIn(alias, surface)

        # Exact keys and full Ukrainian labels come from their owning domains.
        # In particular, D6:100111's label "четверте" is only a projection;
        # this test does not admit direct D6 execution.
        for path, bits, label in (
            ("lib/domains/d4.lisp", "1001", "друге"),
            ("lib/domains/d5.lisp", "10011", "третє"),
            ("lib/domains/d6.lisp", "100111", "четверте"),
        ):
            with self.subTest(domain=path, bits=bits):
                matching = [
                    line for line in source(path).splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(
                    len(matching), 1,
                    f"{path}: очікував єдиний точний ключ ширини {len(bits)}: {bits}",
                )
                self.assertRegex(
                    matching[0], rf"\(укр\s+{re.escape(label)}\)"
                )
                self.assertEqual(len(bits), len(re.sub(r"[^01]", "", bits)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
