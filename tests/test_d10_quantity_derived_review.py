#!/usr/bin/env python3
"""No D10 resident from an already-derived Lisp library expression."""
from pathlib import Path
import hashlib
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "knowledge/d10-quantity-derived-review-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
ARCHIVED_DONORS = ROOT / "research/domain-archive/20261011/d10-quantity-source-pins"
ALIASES = {"UNIT-PRODUCT", "UNIT-QUOTIENT", "QUANTITY-PRODUCT", "QUANTITY-QUOTIENT"}
DUPLICATES = {"SCIENCE-ADD-DIMENSION", "SCIENCE-MERGE-DIMENSIONS",
              "SCIENCE-NEGATE-DIMENSIONS", "TRANSLATION-ENVELOPE-VALID?",
              "TRANSLATION-REVIEW-CANDIDATE"}

def git_blob_id(content):
    return hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()

class D10QuantityDerivedReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(REVIEW.read_text(encoding="utf-8"))
        cls.inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
        cls.names = {r["semantic_name"] for r in cls.inv["rows"]}

    def test_review_is_proposal_only_and_does_not_mint_bit_identity(self):
        d = self.doc
        self.assertEqual(d["schema"], "sens-d10-quantity-derived-review/v1")
        self.assertEqual(d["status"], "RESEARCH-UNRATIFIED-HOLD")
        self.assertEqual(d["snapshot"]["ratified_residents"], 0)
        self.assertFalse(d["snapshot"]["existing_semantic_inventory_mutated"])
        self.assertTrue(d["anti_junk_drawer_rules"]["no_new_ten_bit_coordinates"])
        self.assertTrue(d["anti_junk_drawer_rules"]["no_physical_sens_publication"])
        self.assertTrue(d["anti_junk_drawer_rules"]["d2_sole_language_structure_authority"])

    def test_real_git_donor_bytes_are_pinned(self):
        # Досьє історичне. Порівнюємо з незмінним донором, а не з
        # поточною бібліотекою, яку законно змінює розробка SENS.
        for donor in self.doc["donors"]:
            live = ROOT / donor["path"]
            historical = ARCHIVED_DONORS / donor["path"]
            self.assertTrue(live.is_file(), live)
            self.assertFalse(live.is_symlink())
            self.assertTrue(historical.is_file(), historical)
            self.assertFalse(historical.is_symlink())
            self.assertEqual(
                git_blob_id(historical.read_bytes()), donor["git_blob_sha1"], historical
            )

    def test_hold_derived_names_are_not_duplicate_or_secret_new_inventory_slots(self):
        rows = self.doc["review_rows"]
        self.assertEqual({r["candidate"] for r in rows}, ALIASES)
        self.assertTrue(DUPLICATES <= set(self.doc["selected_duplicates_verified_in_main"]))
        self.assertTrue(DUPLICATES <= self.names)
        self.assertTrue(ALIASES.isdisjoint(self.names))
        for row in rows:
            self.assertEqual(row["status"], "HOLD-DERIVED-COMPOSITION")
            self.assertTrue(row["distinct_new_meaning_unproven"])
            self.assertTrue(row["derivable_from"])
            self.assertGreater(len(row["falsifier"]), 35)
            self.assertGreater(len(row["semantic_law"]), 30)
            self.assertNotIn("coordinate", row)

    def test_real_source_function_locations_not_guessed(self):
        for row in self.doc["review_rows"]:
            historical = (ARCHIVED_DONORS / row["source_path"]).read_text(
                encoding="utf-8"
            ).splitlines()
            expected = row["candidate"].lower()
            self.assertTrue(
                historical[row["line"] - 1].lstrip().startswith("(00001001 " + expected),
                f"historical {row['source_path']}:{row['line']} is not {expected}",
            )
            # Чинний код може додавати рядки, але не втрачати сам закон.
            live = (ROOT / row["source_path"]).read_text(encoding="utf-8")
            pattern = r"(?m)^\\s*\\(00001001\\s+" + re.escape(expected) + r"(?=\\s|\\))"
            self.assertRegex(live, pattern, f"current library lost {expected}")

if __name__ == "__main__":
    unittest.main()
