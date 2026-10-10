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
PAIR = ROOT / "tests/fixtures/migration-pair-cohort-main"
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

    def test_existing_real_uk_pair_cons_triple_is_reversible_without_rewriting(self):
        # Previously BLOCKED by bounded CAR/COND-only renderer despite an
        # owner-reviewed Ukrainian source and unchanged current D3 T5 bytes.
        lisp = PAIR / "pair-cons.lisp"
        sens = PAIR / "pair-cons.sens"
        view = PAIR / "pair-cons"
        original = (lisp.read_bytes(), sens.read_bytes(), view.read_bytes())
        self.assertEqual(lisp.read_text(encoding="utf-8"),
                         "(сполучити (як-є ()) (як-є ()))\n")
        expected = "10 111 00 10 001 00 000 01 00 10 001 00 000 01 01"
        self.assertEqual(view.read_text(encoding="ascii"), expected + "\n")
        report = mod.verify(lisp, sens, view)
        self.assertEqual(report["physical_bytes"], 10)
        self.assertEqual(report["typed_word_count"], len(expected.split()))
        self.assertTrue(report["canonical_uk_roundtrip"])
        self.assertTrue(report["canonical_view_roundtrip"])
        self.assertFalse(report["runtime_oracle_admitted_by_this_audit"])
        self.assertEqual(report["old_originals_migrated_by_this_audit"], 0)
        self.assertEqual((lisp.read_bytes(), sens.read_bytes(),
                          view.read_bytes()), original)

    def test_ratifed_d3_call_arities_and_atomic_quote_roundtrip(self):
        # D3 callable spellings are always owner uk surfaces; 000 is literal
        # (), not NIL, a missing alias or a D2 empty-list special case.
        rows = [
            ("10 001 00 000 01", "(як-є ())\n"),
            ("10 010 00 000 01", "(атом? ())\n"),
            ("10 011 00 000 01", "(решта ())\n"),
            ("10 100 00 000 01", "(перше ())\n"),
            ("10 101 00 10 001 00 1 01 00 10 001 00 1 01 01",
             "(тотожне? (як-є так) (як-є так))\n"),
            ("10 111 00 10 001 00 000 01 00 10 001 00 000 01 01",
             "(сполучити (як-є ()) (як-є ()))\n"),
        ]
        for visible, uk in rows:
            words = visible.split()
            with self.subTest(visible=visible):
                self.assertEqual(mod.canonical_uk_from_words(words), uk)
                self.assertEqual(mod.project_current_uk(uk), words)
                physical = mod.encode_words(words)
                self.assertEqual(mod.decode_bytes(physical), words)
        self.assertEqual(mod.uk_surface(3)["000"], "()")

    def test_quote_rejects_structural_data_without_a_proven_d7_law(self):
        for words in (
            ["10", "001", "00", "10", "000", "01", "01"],
            ["10", "001", "00", "10", "001", "00", "000", "01", "01"],
            ["10", "001", "00", "101", "01"],
            ["10", "101", "00", "0", "01"],
            ["10", "010", "00", "000", "00", "1", "01"],
            ["10", "011", "01"],
            ["10", "111", "00", "0", "00", "1", "00", "0", "01"],
        ):
            with self.subTest(words=words):
                with self.assertRaises(mod.ProjectionBlocked):
                    mod.canonical_uk_from_words(words)

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
            ["10", "111", "00", "1", "01"],               # CONS wrong arity
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

    def test_caar_real_uk_source_against_original_unmodified_physical_t5(self):
        source_dir = ROOT / "tests/fixtures/migration-d4-selector-cohort"
        self.assertEqual(mod.uk_surface(4)["1000"], "п-п")
        with tempfile.TemporaryDirectory(prefix="sens-d4-uk-triple-") as td:
            stage = Path(td)
            for suffix in (".lisp", ".sens", ""):
                shutil.copyfile(source_dir / ("caar" + suffix),
                                stage / ("caar" + suffix))
            lisp, sens, view = stage / "caar.lisp", stage / "caar.sens", stage / "caar"
            original = (lisp.read_bytes(), sens.read_bytes(), view.read_bytes())
            self.assertEqual(lisp.read_text(encoding="utf-8"),
                "(п-п (сполучити (сполучити (як-є ()) (як-є ())) (як-є ())))\n")
            words = mod.decode_bytes(original[1])
            self.assertEqual(words[0:2], ["10", "1000"])
            self.assertEqual(mod.canonical_uk_from_words(words), lisp.read_text(encoding="utf-8"))
            self.assertEqual(mod.project_current_uk(lisp.read_text(encoding="utf-8")), words)
            receipt = mod.verify(lisp, sens, view)
            self.assertEqual(receipt["physical_bytes"], 20)
            self.assertTrue(receipt["canonical_uk_roundtrip"])
            self.assertTrue(receipt["canonical_view_roundtrip"])
            self.assertFalse(receipt["runtime_oracle_admitted_by_this_audit"])
            self.assertEqual(receipt["old_originals_migrated_by_this_audit"], 0)
            self.assertEqual(original,
                             (lisp.read_bytes(), sens.read_bytes(), view.read_bytes()))
            forged = words.copy()
            forged[1] = "100"  # D3 CAR is NOT D4 CAAR!
            sens.write_bytes(mod.encode_words(forged))
            view.write_text(" ".join(forged) + "\n", encoding="ascii")
            with self.assertRaises(mod.ProjectionBlocked):
                mod.verify(lisp, sens, view)

    def test_caar_only_accepts_proven_cons_with_nested_cons_car(self):
        for invalid in (
            ["10", "1000", "01"],                     # no argument
            ["10", "1000", "00", "000", "01"],        # empty not a pair
            ["10", "1000", "00", "10", "001", "00", "000", "01", "01"],  # quoted nil
            ["10", "1000", "00", "10", "111", "00", "10",
             "001", "00", "000", "01", "00", "10", "001",
             "00", "000", "01", "01", "01"],          # CONS but CAR not CONS
            ["10", "1000", "00", "10", "111", "00", "10",
             "111", "00", "10", "001", "00", "1", "01",
             "00", "10", "001", "00", "000", "01", "01",
             "00", "10", "001", "00", "000", "01", "01",
             "01"],                                # quoted D1 not nil-pair
            ["10", "1001", "00", "000", "01"],        # unproved D4 CADR
            ["10", "0010", "00", "000", "01"],        # D4 binder not callable
        ):
            with self.subTest(words=invalid):
                with self.assertRaises(mod.ProjectionBlocked):
                    mod.canonical_uk_from_words(invalid)

    def test_bounded_d4_cadr_two_cell_chain_and_negative_shapes(self):
        # D4:1001 is CADR, not a D3:100 CAR or D4:1000 CAAR alias.
        from sens_t5_codec import decode_bytes, encode_words
        fixture = ROOT / "tests/fixtures/migration-d4-cadr-cohort"
        source = (fixture / "cadr.lisp").read_text(encoding="utf-8")
        binary = (fixture / "cadr.sens").read_bytes()
        visible = (fixture / "cadr").read_text(encoding="ascii")
        self.assertEqual(mod.uk_surface(4)["1001"], "п-р")
        self.assertEqual(source, "(п-р (сполучити (як-є ()) (сполучити (як-є ()) (як-є ()))))\n")
        self.assertEqual(len(binary), 20)
        self.assertEqual(binary.hex(), "662dc47ec32da42dc47ec32da42dc32da42eb1a1")
        self.assertEqual(decode_bytes(binary), visible.split())
        self.assertEqual(encode_words(visible.split()), binary)
        self.assertEqual(mod.canonical_uk_from_words(visible.split()), source)
        self.assertEqual(mod.project_current_uk(source), visible.split())
        attestation = mod.verify(fixture / "cadr.lisp", fixture / "cadr.sens", fixture / "cadr")
        self.assertTrue(attestation["canonical_uk_roundtrip"])
        self.assertFalse(attestation["runtime_oracle_admitted_by_this_audit"])
        for invalid in (
            "10 1001 00 000 01", # no pair to take CDR
            "10 1001 00 10 001 00 000 01 01", # quoted empty is not two cells
            "10 1001 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 01", # CDR is not CONS
            "10 1001 00 10 111 00 10 001 00 1 01 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 01 01", # unproved quoted D1
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(mod.ProjectionBlocked):
                    mod.canonical_uk_from_words(invalid.split())

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
