"""Захист точного Lisp-переписування, не Python-емуляція семантики SENS."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SCRIPT = ROOT / "scripts/migrate-english-predicates-question-mark.py"
spec = importlib.util.spec_from_file_location("sens_ukr_predicate_migration", SCRIPT)
assert spec is not None and spec.loader is not None
migration = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = migration
spec.loader.exec_module(migration)


class ExactUkrPredicateSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping = migration.predicates()

    def test_only_ratified_d3_d4_full_names(self):
        for old, current in {
            "atom": "атом?", "ATOM": "атом?",
            "eq": "тотожне?", "EQ": "тотожне?",
            "not": "хибне?", "NOT": "хибне?",
            "null": "порожній?", "NULL": "порожній?",
        }.items():
            with self.subTest(old=old):
                self.assertEqual(self.mapping[old], current)
        self.assertNotIn("quote", self.mapping)
        self.assertNotIn("cons", self.mapping)

    def test_rewrites_only_live_heads_not_quotes_comments_or_strings(self):
        old = (
            "(eq перший другий)\n"
            "(ATOM (як-є предмет))\n"
            "(not (null список))\n"
            "(як-є (eq дані не-виклик))\n"
            "'(atom цитата)\n"
            "; (not коментар)\n"
            '(визначити приклад "(eq рядок)")\n'
        )
        new = (
            "(тотожне? перший другий)\n"
            "(атом? (як-є предмет))\n"
            "(хибне? (порожній? список))\n"
            "(як-є (eq дані не-виклик))\n"
            "'(atom цитата)\n"
            "; (not коментар)\n"
            '(визначити приклад "(eq рядок)")\n'
        )
        result, edits = migration.rewrite_lisp(old, self.mapping)
        self.assertEqual(result, new)
        self.assertEqual(len(edits), 4)
        self.assertEqual(migration.rewrite_lisp(result, self.mapping)[1], [])

    def test_data_only_is_preserved(self):
        text = "(як-є ((eq a b) (not c)))\n"
        self.assertEqual(migration.rewrite_lisp(text, self.mapping), (text, []))

    def test_invalid_source_fails_closed(self):
        with self.assertRaises(ValueError):
            migration.rewrite_lisp("(eq перший другий", self.mapping)

    def test_never_rewrite_machine_or_domain_table_or_whole_directory(self):
        for filename in (
            "lib/core.sens", "lib/domains/d3.lisp",
            "lib/surface/semantic-registry.lisp",
            "research/історія.lisp", "../lib/core1.lisp",
        ):
            with self.subTest(filename=filename):
                with self.assertRaises(ValueError):
                    migration.selected([filename], apply=True)
        with self.assertRaises(ValueError):
            migration.selected(["lib"], apply=True)
        with self.assertRaises(ValueError):
            migration.selected([], apply=True)

    def test_readonly_default_excludes_nonprogram_domain_tables(self):
        paths = migration.selected([], apply=False)
        self.assertGreater(len(paths), 30)
        self.assertNotIn(ROOT / "lib/domains/d3.lisp", paths)


if __name__ == "__main__":
    unittest.main()
