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
            # Допоміжний двоелементний список і D8 «пара» — різні закони.
            self.assertIn(
                "(визначити створити-список-із-двох-значень\n  (функція (лівий-аргумент правий-аргумент)",
                core4,
            )
            self.assertIn(
                "(визначити пара\n  (функція (ліві праві)\n    (спарувати-послідовності ліві праві)))",
                core4,
            )
            self.assertNotIn("(визначити pair\n  (функція", core4)
            self.assertNotIn("(визначити pair пара)", core4)
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

        # Internal helpers remain internal; their executable names are Ukrainian
        # in both bootstrap/core4 copies and every live caller. No alias or new
        # domain resident is introduced by this lexical migration.
        helpers = (
            ("класифікувати-рядкове-значення", "string-membership-helper"),
            ("порівняти-рядки-за-кодовими-точками", "string-order-helper"),
            ("класифікувати-непорожність-рядка", "nonempty-string-membership-helper"),
            ("знайти-пару-підстановки", "sublis-pair"),
            ("підготувати-цитовані-аргументи", "apply-quote-args"),
            ("уточнити-корінь-ітерацією", "sqrt-iter"),
            ("крок-цілого-кореня", "isqrt-step"),
            ("знайти-найбільший-блок-частки", "largest-chunk"),
            ("перевірити-неспадання-значень?", "nondecreasing-from?"),
            ("перевірити-незростання-значень?", "nonincreasing-from?"),
        )
        # Core4 owns these remaining internal helper definitions. The smaller
        # Ukrainian core.lisp no longer carries duplicate number-rendering code.
        for ukrainian, legacy in helpers:
            with self.subTest(file="lib/core4.lisp", helper=ukrainian):
                self.assertIn(f"(визначити {ukrainian}", core4)
                self.assertNotIn(f"({legacy} ", core4)
        self.assertNotIn("взяти-десятковий-символ", core4)
        self.assertNotIn("number->string-onto", core4)
        live_callers = (
            "lib/yantra.lisp",
            "lib/translation.lisp",
            "scripts/generate-rust-semantic-registry.lisp",
            "scripts/generate-function-table.lisp",
        )
        for filename in live_callers:
            code = source(filename)
            with self.subTest(file=filename, migration="string classification"):
                self.assertIn("класифікувати-рядкове-значення", code)
                self.assertNotIn("(string-membership-helper ", code)
        inventory = source("lib/surface/uk-inventory.lisp")
        for ukrainian, legacy in helpers:
            with self.subTest(inventory=legacy):
                self.assertIn(ukrainian, inventory)
                self.assertNotIn(legacy, inventory)

        # These three helpers deliberately have no D-domain resident names:
        # keep them internal, Ukrainian, and exactly reversible at the callsite.
        for ukrainian, legacy in (
            ("уточнити-корінь-ітерацією", "sqrt-iter"),
            ("крок-цілого-кореня", "isqrt-step"),
        ):
            self.assertIn(f"(визначити {ukrainian}", core4)
            self.assertNotIn(f"({legacy} ", core4)
        inventory = source("lib/surface/uk-inventory.lisp")
        for ukrainian, legacy in helpers[-3:]:
            with self.subTest(inventory=legacy):
                self.assertIn(ukrainian, inventory)
                self.assertNotIn(legacy, inventory)

        with self.subTest(file="racket/boot/core.lisp", migration="canonical decimal rendering"):
            racket_core = source("racket/boot/core.lisp")
            self.assertIn("(визначити число-рядок", racket_core)
            self.assertIn("(значення-у-текст число-аргумент)", racket_core)
            self.assertNotIn("взяти-десятковий-символ", racket_core)
            self.assertNotIn("number->string-onto", racket_core)
            start = racket_core.index("(визначити число-рядок")
            end = racket_core.index("; -> / ->> (thread-first / thread-last macros)", start)
            renderer = racket_core[start:end]
            self.assertNotRegex(renderer, r"\([01]{3,9}(?=\s|\))")

        dependency_classifier = source("scripts/build-dependency-classification.lisp")
        with self.subTest(file="scripts/build-dependency-classification.lisp", migration="canonical decimal rendering"):
            self.assertIn("number->string", dependency_classifier)
            self.assertNotIn("взяти-десятковий-символ", dependency_classifier)
            self.assertNotIn("number->string-onto", dependency_classifier)

        # Numeric iteration workers remain ordinary Ukrainian library helpers.
        for ukrainian, legacy in (
            ("уточнити-корінь-ітерацією", "sqrt-iter"),
            ("крок-цілого-кореня", "isqrt-step"),
        ):
            self.assertIn(f"(визначити {ukrainian}", core4)
            self.assertNotIn(f"({legacy} ", core4)

        # Exact keys and full Ukrainian labels come from their owning domains.
        # In particular, D6:100111's label "четверте" is only a projection;
        # this test does not admit direct D6 execution.
        for path, width, bits, label in (
            ("lib/domains/d4.lisp", 4, "1001", "друге"),
            ("lib/domains/d5.lisp", 5, "10011", "третє"),
            ("lib/domains/d6.lisp", 6, "100111", "четверте"),
        ):
            with self.subTest(domain=path, bits=bits):
                self.assertEqual(
                    len(bits), width,
                    f"{path}: ширина ключа має належати своєму домену D{width}",
                )
                matching = [
                    line for line in source(path).splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(
                    len(matching), 1,
                    f"{path}: очікував єдиний точний ключ {width}-бітової ширини: {bits}",
                )
                self.assertRegex(
                    matching[0], rf"\(укр\s+{re.escape(label)}\)"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
