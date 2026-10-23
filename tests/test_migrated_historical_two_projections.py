"""Seven source-derived historical SENS views before the physical codec cutover."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_uk_t5_t5m_triplet import canonical_uk_from_words, project_current_uk, three_pass

ROWS = (
    ("historic-atom", "tests/fixtures/migration-atom-cohort/atom-empty.lisp", True),
    ("historic-eq-legacy", "tests/fixtures/migration-eq-cohort/eq-legacy-sid.lisp", False),
    ("historic-eq-lisp15", "tests/fixtures/migration-eq-cohort/eq-lisp15.lisp", False),
    ("historic-cons-legacy", "tests/fixtures/migration-pair-cohort/pair-cons.lisp", False),
    ("historic-quote-legacy", "tests/fixtures/migration-quote-cohort/quote-legacy.lisp", False),
    ("historic-quote-lisp15", "tests/fixtures/migration-quote-cohort/quote-lisp15.lisp", False),
    ("historic-quote-mylisp", "tests/fixtures/migration-quote-cohort/quote-mylisp.lisp", False),
)


class HistoricalTwoFileMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = three_pass.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
        cls.legacy, cls.my, cls.upper = three_pass.build_three_pass_maps(
            data,
            ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry.rs",
            ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
            ROOT / "contracts/core1-historical-sid-map.lisp",
            ROOT / "knowledge/sens8-current-coverage-v1.json",
        )
        # Ratified D7 keyboard/v2 is the current Text7 authority; the retired
        # .rs donor no longer carries an executable mapping.
        cls.text7 = three_pass.build_text7(
            data, ROOT / "knowledge/d7-keyboard-v2-ratified.json"
        )

    def test_source_to_canonical_uk_and_same_width_bits(self):
        for name, original, already_bits in ROWS:
            with self.subTest(name=name):
                source = (ROOT / original).read_text(encoding="utf-8")
                dest = ROOT / "examples/migrated/history" / name
                view = dest.read_text(encoding="ascii")
                uk = dest.with_suffix(".lisp").read_text(encoding="utf-8")
                self.assertFalse(dest.with_suffix(".sens").exists())
                if already_bits:
                    words = source.split()
                else:
                    resolver = three_pass.Resolver(
                        self.legacy, self.my, self.upper, source_era="legacy"
                    )
                    words = three_pass.migrate_file(
                        source, resolver, self.text7
                    ).split()
                self.assertEqual(view, " ".join(words) + "\n")
                self.assertEqual(uk, canonical_uk_from_words(words))
                self.assertEqual(project_current_uk(uk), words)


if __name__ == "__main__":
    unittest.main()
