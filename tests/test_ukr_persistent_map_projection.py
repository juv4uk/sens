"""Exact-identity source migration of immutable persistent MAP into full укр.

Only D4 DEFINE, D3 QUOTE and exact D1:YES change their textual projection.
No host hashmap, new domain code, automatic aliasing or Python evaluation.
"""
from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/persistent-map.lisp"
PRE_MIGRATION_BLOB = "149d768862b8719d789297e53e80fad90c9fbfe7"

HISTORICAL_DEFS = (
    "map-empty", "map-insert", "map-get", "map-contains?", "map->list",
    "внутрішня-мапа-вставити", "внутрішня-мапа-отримати",
    "внутрішня-мапа-містить", "внутрішня-мапа-список",
    "внутрішня-мапа-порожній", "мапа-порожній", "мапа-отримати",
    "мапа-містить?", "мапа-список",
)
PEERS = {1: ("1", "так"), 3: ("001", "як-є"), 4: ("0011", "визначити")}


def restore_exact_previous(source: str) -> str:
    restored = []
    for line in source.splitlines(keepends=True):
        if line.lstrip().startswith(";"):
            restored.append(line)
            continue
        line = re.sub(r"\(визначити(?=\s)", "(0011", line)
        line = re.sub(r"\(так(?=\s|$)", "(#d1:1", line)
        # D3 QUOTE was present in the body of the unique map-empty declaration.
        line = line.replace("(0011 map-empty (як-є ()))",
                            "(0011 map-empty (001 ()))")
        restored.append(line)
    return "".join(restored)


def git_blob(source: str) -> str:
    encoded = source.encode("utf-8")
    return hashlib.sha1(
        b"blob " + str(len(encoded)).encode() + b"\0" + encoded
    ).hexdigest()


def verify(source: str) -> None:
    if git_blob(restore_exact_previous(source)) != PRE_MIGRATION_BLOB:
        raise AssertionError("MAP: змінено байти поза D1/D3/D4 peer проєкціями")
    heads = re.findall(r"(?m)^\(визначити\s+([^\s()]+)", source)
    if tuple(heads) != HISTORICAL_DEFS:
        raise AssertionError("MAP: визначення/порядок/імена порушено")
    if source.count("(так") != 2:
        raise AssertionError("MAP: мають бути два явні D1:YES fallback")
    if "(визначити map-empty (як-є ()))" not in source:
        raise AssertionError("MAP: D3:001 QUOTE не на повній укр-проєкції")


class PersistentMapUkrTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_domain_contract_exact_and_not_sid8(self):
        for width, (bits, expected) in PEERS.items():
            src = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            row = next((line for line in src.splitlines()
                        if line.lstrip().startswith(f"({bits} ")), None)
            self.assertIsNotNone(row)
            self.assertIn(f"(укр {expected})", row)
        self.assertEqual(len(set(PEERS)), 3)

    def test_original_blob_fully_recovered_no_semantic_substitution(self):
        verify(self.source)

    def test_all_fourteen_defs_and_d1_quote_are_ukr(self):
        self.assertEqual(self.source.count("(визначити "), 14)
        self.assertIn("(визначити map-empty (як-є ()))", self.source)
        code = "\n".join(s for s in self.source.splitlines()
                         if not s.lstrip().startswith(";"))
        self.assertNotRegex(code, r"\([01]{3,9}(?=\s|\))")
        self.assertNotIn("#d1:1", code)
        self.assertEqual(code.count("(так"), 2)

    def test_immutable_map_mechanism_and_aliases_unchanged(self):
        for form in (
            "(map-insert key value (решта entries))",
            "(map-get key (решта entries))",
            "(визначити внутрішня-мапа-вставити map-insert)",
            "(визначити мапа-порожній внутрішня-мапа-порожній)",
            "(визначити мапа-отримати внутрішня-мапа-отримати)",
        ):
            self.assertIn(form, self.source)
        verify(self.source)

    def test_fail_closed_for_wrong_op_bit_or_data(self):
        for mutation in (
            self.source.replace("(визначити map-empty", "(функція map-empty", 1),
            self.source.replace("(як-є ())", "(атом? ())", 1),
            self.source.replace("(так", "(ні", 1),
            self.source.replace("(сполучити key value)", "(сполучити value key)", 1),
            self.source.replace("мапа-отримати внутрішня-мапа-отримати",
                                "мапа-отримати внутрішня-мапа-містить", 1),
        ):
            with self.assertRaises(AssertionError):
                verify(mutation)

    def test_reversible_exact_projection_idempotence(self):
        previous = restore_exact_previous(self.source)
        again = previous.replace("(0011 map-empty (001 ()))",
                                 "(визначити map-empty (як-є ()))")
        again = re.sub(r"\(0011(?=\s)", "(визначити", again)
        again = re.sub(r"\(#d1:1(?=\s|$)", "(так", again, flags=re.M)
        self.assertEqual(again, self.source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
