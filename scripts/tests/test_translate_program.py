#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "translate-program.py"
SPEC = importlib.util.spec_from_file_location("translate_program", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TranslateProgramTests(unittest.TestCase):
    def test_all_surface_directions_are_available(self):
        languages = sorted(MODULE.human_languages(MODULE.registry_rows()))
        for source in languages:
            for target in languages:
                if MODULE.LANGUAGE_FIELDS[source] != MODULE.LANGUAGE_FIELDS[target]:
                    self.assertTrue(MODULE.translation_map(source, target))

    def test_program_round_trip_preserves_source(self):
        english = "(car (cons 'cat (quote ())))\n"
        ukrainian = MODULE.translate_program(
            english, MODULE.translation_map("en", "ук")
        )
        self.assertEqual(ukrainian, "(перше (сполучити 'cat (як-є ())))\n")
        restored = MODULE.translate_program(
            ukrainian, MODULE.translation_map("ук", "en")
        )
        self.assertEqual(restored, english)

    def test_comments_strings_and_unknown_names_are_preserved(self):
        source = '(print "car atom") ; car atom\n(my-function об\'єкт)\n'
        result = MODULE.translate_program(
            source, MODULE.translation_map("en", "ук")
        )
        self.assertEqual(
            result,
            '(друкувати "car atom") ; car atom\n(my-function об\'єкт)\n',
        )

    def test_ukrainian_to_sanskrit_uses_the_shared_table(self):
        source = "(перше (сполучити 'кіт 'пес))"
        result = MODULE.translate_program(
            source, MODULE.translation_map("ук", "sa")
        )
        self.assertEqual(result, "(ādi (saṃyuj 'кіт 'пес))")


    def test_uk_and_ukr_are_distinct_table_namespaces_of_one_identity(self):
        compact = MODULE.translation_map("en", "ук")
        full = MODULE.translation_map("en", "укр")
        self.assertEqual(compact["utc-now"], "узгоджений-час-зараз")
        self.assertEqual(full["utc-now"], "узгоджений-час-зараз")
        self.assertEqual(
            MODULE.translation_map("ук", "укр")["узгоджений-час-зараз"],
            "узгоджений-час-зараз",
        )

    def test_d8_translation_uses_current_domain_row_not_historical_sid8(self):
        mapping = MODULE.translation_map("en", "укр")
        self.assertEqual(mapping["prog1"], "послідовність-повернути-перше")
        self.assertEqual(mapping["print"], "друкувати")
        self.assertEqual(
            MODULE.translate_program('(prog1 (print 1) 2)', mapping),
            '(послідовність-повернути-перше (друкувати 1) 2)',
        )

    def test_ambiguous_d6_d8_map_fails_only_for_ambiguous_token(self):
        mapping = MODULE.translation_map("en", "укр")
        self.assertIsNone(mapping["map"])
        self.assertEqual(
            MODULE.translate_program('(car x) ; map\\n"map"', mapping),
            '(перше x) ; map\\n"map"',
        )
        with self.assertRaisesRegex(ValueError, "неоднозначна"):
            MODULE.translate_program("(map f x)", mapping)

    def test_d7_text_not_misused_as_callable(self):
        self.assertNotIn("kh", MODULE.translation_map("san", "укр"))
        self.assertNotIn("open", MODULE.translation_map("en", "укр"))


if __name__ == "__main__":
    unittest.main()
