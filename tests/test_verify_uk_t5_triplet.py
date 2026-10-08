#!/usr/bin/env python3
"""#4430 bounded reversible Ukrainian ↔ exact typed words ↔ physical/view proof."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/verify_uk_t5_triplet.py"
SPEC = importlib.util.spec_from_file_location("verify_uk_triplet", SOURCE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

F = ROOT / "tests/fixtures/migration-d1-cond-cohort"
WORDS = "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01"
UK = "(за-умовою (ні (перше ())) (так так))\n"


class BoundedUkTripletTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="uk-t5-triplet-")
        self.dir = Path(self.tmp.name)
        self.lisp, self.sens, self.view = (
            self.dir / "branch.lisp",
            self.dir / "branch.sens",
            self.dir / "branch",
        )
        for name in ("branch.lisp", "branch.sens", "branch"):
            shutil.copyfile(F / name, self.dir / name)

    def tearDown(self):
        self.tmp.cleanup()

    def verify(self):
        return mod.verify(self.lisp, self.sens, self.view)

    def test_real_existing_current_uk_canary_proves_three_way_bytes(self):
        original = (self.lisp.read_bytes(), self.sens.read_bytes(), self.view.read_bytes())
        record = self.verify()
        self.assertEqual(self.lisp.read_text(encoding="utf-8"), UK)
        self.assertEqual(self.view.read_text(encoding="ascii"), WORDS + "\n")
        self.assertEqual(self.sens.read_bytes().hex(), "67386515bf123b2dc4a9b1a1")
        self.assertEqual(record["physical_bytes"], 12)
        self.assertEqual(record["typed_word_count"], len(WORDS.split()))
        self.assertTrue(record["canonical_uk_roundtrip"])
        self.assertTrue(record["canonical_view_roundtrip"])
        self.assertFalse(record["runtime_oracle_admitted_by_this_audit"])
        self.assertEqual(record["old_originals_migrated_by_this_audit"], 0)
        self.assertEqual((self.lisp.read_bytes(), self.sens.read_bytes(),
                          self.view.read_bytes()), original)

    def test_exact_ratified_uk_surfaces_from_domain_tables(self):
        self.assertEqual(mod.uk_surface(1), {"0": "ні", "1": "так"})
        self.assertEqual(mod.uk_surface(3)["110"], "за-умовою")
        self.assertEqual(mod.uk_surface(3)["100"], "перше")
        self.assertEqual(mod.canonical_uk_from_words(WORDS.split()), UK)
        self.assertEqual(mod.project_current_uk(UK), WORDS.split())

    def test_single_atom_and_empty_list_are_distinct_from_d2_separator(self):
        self.assertEqual(mod.canonical_uk_from_words(["0"]), "ні\n")
        self.assertEqual(mod.canonical_uk_from_words(["1"]), "так\n")
        self.assertEqual(mod.canonical_uk_from_words(["000"]), "()\n")
        for word in (["00"], ["01"], ["10"], ["11"], ["00000000"]):
            with self.subTest(word=word):
                with self.assertRaises(mod.ProjectionBlocked):
                    mod.canonical_uk_from_words(word)

    def test_tampered_view_fails_even_if_t5_remains_canonical(self):
        original = self.view.read_bytes()
        for content in (
            b"", b" " + original, original[:-1], original+b"\n",
            original.replace(b" ", b"  ", 1), original.replace(b" ", b"\t", 1),
            original.replace(b"\n", b"\r\n"), original.replace(b"0", b"2", 1),
            original.replace(b"1", b"9", 1), b"D3:110\n", b"(110)\n",
            b"\xef\xbb\xbf" + original,
        ):
            with self.subTest(content=content[:35]):
                self.view.write_bytes(content)
                with self.assertRaisesRegex(mod.ProjectionBlocked, "view"):
                    self.verify()
        self.view.write_bytes(original)
        self.assertTrue(self.verify()["canonical_view_roundtrip"])

    def test_noncanonical_uk_aliases_english_and_whitespace_fail(self):
        original = self.lisp.read_bytes()
        for candidate in (
            UK.replace("за-умовою", "COND"),
            UK.replace("перше", "CAR"),
            UK.replace("так", "T"),
            UK.replace("ні", "NIL"),
            UK.replace("(так так)", "(так  так)"),
            UK.replace("\n", "\r\n"),
            UK.replace("\n", "\n\n"),
            " " + UK,
            UK.rstrip("\n"),
            UK.replace("так", "правда"),
        ):
            with self.subTest(source=candidate):
                self.lisp.write_bytes(candidate.encode("utf-8"))
                with self.assertRaisesRegex(mod.ProjectionBlocked, "noncanonical"):
                    self.verify()
        self.lisp.write_bytes(original)

    def test_physical_t5_corruption_and_noncanonical_tail_block(self):
        source = self.sens.read_bytes()
        for candidate in (
            b"", b"\xf3", source + bytes([242]),
            source + bytes([243]),
            source[:-1], bytes([242]) + source,
        ):
            with self.subTest(blob=candidate[:10].hex()):
                self.sens.write_bytes(candidate)
                with self.assertRaises(mod.ProjectionBlocked):
                    self.verify()
        self.sens.write_bytes(source)

    def test_missing_files_wrong_stem_and_symlink_block(self):
        with self.assertRaisesRegex(mod.ProjectionBlocked, "same-stem"):
            mod.verify(self.lisp, self.sens, self.dir/"different")
        self.view.unlink()
        with self.assertRaisesRegex(mod.ProjectionBlocked, "missing"):
            self.verify()
        self.view.symlink_to(F / "branch")
        with self.assertRaisesRegex(mod.ProjectionBlocked, "symlink"):
            self.verify()

    def test_nonadmitted_text_number_binding_and_bad_d2_block(self):
        for invalid_words in (
            ["10", "110", "01", "00"],
            ["10", "110", "00", "10", "0", "01", "01"],   # clause not pair
            ["10", "100", "01"],                         # CAR missing arg
            ["10", "110", "00", "10", "0", "00", "1", "01"], # unclosed outer
            ["10", "111", "00", "1", "01"],               # no CONS law here
            ["10", "0010", "00", "1", "01"],              # D4 binder
            ["10", "110", "00", "0000011", "01"],         # Text7 unknown
            ["10", "110", "00", "01010", "01"],           # D5 number/other
            ["10", "100", "00", "1", "00", "0", "01"],       # CAR arity
            ["0", "00", "1"],                             # multiple roots
            ["10", "1", "00", "1", "01"],                 # raw predicate call
        ):
            with self.subTest(words=invalid_words):
                with self.assertRaises(mod.ProjectionBlocked):
                    mod.canonical_uk_from_words(invalid_words)

    def test_cli_read_only_current_canary(self):
        cmd = [sys.executable, str(SOURCE), "--lisp", str(self.lisp),
               "--sens", str(self.sens), "--view", str(self.view)]
        ok = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=90)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("BOUNDED_TRIPLE_PARITY_ONLY_NOT_RELEASE_ADMISSION", ok.stdout)
        self.view.write_bytes(b"0\n")
        bad = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=90)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("BLOCKED", bad.stderr)


if __name__ == "__main__":
    unittest.main()
