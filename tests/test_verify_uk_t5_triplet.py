#!/usr/bin/env python3
"""#4430 bounded reversible Ukrainian ↔ exact typed words ↔ physical/view proof."""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from scripts.sens_t5_codec import encode_t5m_projection

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/verify_uk_t5_triplet.py"
SPEC = importlib.util.spec_from_file_location("verify_uk_triplet", SOURCE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

F = ROOT / "tests/semantic/native-t5"
PAIR = ROOT / "tests/fixtures/migration-pair-cohort-main"
WORDS = "10 110 00 10 10 010 00 10 111 00 10 001 00 000 01 00 10 001 00 000 01 01 01 00 10 100 00 000 01 01 00 10 10 010 00 10 001 00 000 01 01 00 10 010 00 10 001 00 000 01 01 01 01"
UK = "(за-умовою ((атом? (сполучити (як-є ()) (як-є ()))) (перше ())) ((атом? (як-є ())) (атом? (як-є ()))))\n"


class BoundedUkTripletTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="uk-t5-triplet-")
        self.dir = Path(self.tmp.name)
        self.lisp, self.sens, self.view = (
            self.dir / "branch.lisp",
            self.dir / "branch.sens",
            self.dir / "branch",
        )
        for suffix in (".lisp", ".sens", ""):
            shutil.copyfile(F / ("cond-short-circuit" + suffix),
                            self.dir / ("branch" + suffix))
        # Джерело й канонічна проєкція відрізняються лише зайвим LF.
        self.lisp.write_text(UK, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def verify(self):
        return mod.verify(self.lisp, self.sens, self.view)

    def test_real_existing_current_uk_canary_proves_three_way_bytes(self):
        original = (self.lisp.read_bytes(), self.sens.read_bytes(), self.view.read_bytes())
        record = self.verify()
        self.assertEqual(self.lisp.read_text(encoding="utf-8"), UK)
        self.assertEqual(self.view.read_text(encoding="ascii"), WORDS + "\n")
        self.assertEqual(self.sens.read_bytes(), encode_t5m_projection(WORDS))
        self.assertEqual(record["physical_bytes"], 35)
        self.assertEqual(record["typed_word_count"], len(WORDS.split()))
        self.assertTrue(record["canonical_uk_roundtrip"])
        self.assertTrue(record["canonical_view_roundtrip"])
        self.assertFalse(record["runtime_oracle_admitted_by_this_audit"])
        self.assertEqual(record["old_originals_migrated_by_this_audit"], 0)
        self.assertEqual((self.lisp.read_bytes(), self.sens.read_bytes(),
                          self.view.read_bytes()), original)

    def test_current_t5m_ukr_source_and_reverse_are_byte_identical(self):
        # Keep the historic fixture read-only: modern T5M is checked in temp.
        physical = encode_t5m_projection(WORDS)
        self.sens.write_bytes(physical)
        report = mod.verify(self.lisp, self.sens, self.view, codec="t5m")
        self.assertEqual(report["physical_codec"], "t5m")
        self.assertTrue(report["physical_T5M_roundtrip"])
        self.assertFalse(report["physical_T5_roundtrip"])
        self.assertTrue(report["canonical_uk_roundtrip"])
        self.assertEqual(self.sens.read_bytes(), physical)
        self.assertEqual(self.view.read_text(encoding="ascii"), WORDS + "\n")
        self.assertEqual(mod.verify(self.lisp, self.sens, self.view)["physical_codec"], "t5m")
        self.view.write_text("0\n", encoding="ascii")
        with self.assertRaisesRegex(mod.ProjectionBlocked, "view"):
            mod.verify(self.lisp, self.sens, self.view, codec="t5m")

    def test_programmatic_verifier_defaults_to_t5m_not_legacy_auto(self):
        # CLI і Python-виклики мають один чинний фізичний режим.
        # Історичні t5/auto перевіряються лише за явним запитом.
        signature = inspect.signature(mod.verify)
        self.assertEqual(signature.parameters["codec"].default, "t5m")
        self.sens.write_bytes(encode_t5m_projection(WORDS))
        receipt = mod.verify(self.lisp, self.sens, self.view)
        self.assertEqual(receipt["physical_codec"], "t5m")
        self.assertTrue(receipt["program_identity_roundtrip"])
        self.assertFalse(receipt["runtime_oracle_admitted_by_this_audit"])

    def test_exact_ratified_uk_surfaces_from_domain_tables(self):
        self.assertEqual(mod.uk_surface(1), {"0": "ні", "1": "так"})
        self.assertEqual(mod.uk_surface(3)["110"], "за-умовою")
        self.assertEqual(mod.uk_surface(3)["100"], "перше")
        self.assertEqual(mod.canonical_uk_from_words(WORDS.split()), UK)
        self.assertEqual(mod.project_current_uk(UK), WORDS.split())

    def test_text7_authority_is_ratified_d7_keyboard_v2_not_the_retired_donor(self):
        # Retirement of the historical .rs donor must not silently degrade the
        # gate to an empty projection: the gate consumes the ratified D7
        # keyboard/v2 table (width 7, 128/128) and fails closed on the donor.
        import json
        foundation = mod.three_pass.load_foundation(
            ROOT / "knowledge/d1-d11-foundation.json")
        self.assertIn("D11", foundation["current_domains"])
        donor = ROOT / "crates/sens/src/text7_projection_generated.rs"
        self.assertIn("No executable or display mapping",
                      donor.read_text(encoding="utf-8"))
        with self.assertRaises(mod.three_pass.MigrationError):
            mod.three_pass.build_text7(foundation, donor)
        ratified = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
        payload = json.loads(ratified.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "sens.d7.keyboard/v2")
        self.assertEqual(
            (payload["width"], payload["capacity"], payload["occupancy"]),
            (7, 128, 128))
        self.assertIn("keyboard-v2", mod.three_pass.build_text7(foundation, ratified))
        self.assertTrue(self.verify()["canonical_uk_roundtrip"])

    def test_native_multiform_t5m_fixture_has_exact_ukr_inverse(self):
        # Реальна двоформова фізична програма вже виконується у
        # crates/sens/tests/physical_t5m_execution.rs, а не у Python.
        # Тут доводимо лише механічну укр ↔ точні D2 слова ↔ Zig/T5M.
        fixture = ROOT / "tests/fixtures/migration-multiform-cohort-main"
        lisp = fixture / "two-forms.lisp"
        sens = fixture / "two-forms.sens"
        view = fixture / "two-forms"
        original = (lisp.read_bytes(), sens.read_bytes(), view.read_bytes())
        words = view.read_text(encoding="ascii").split()
        self.assertEqual(
            mod.canonical_uk_from_words(words),
            "(як-є ())\\n(сполучити (як-є ()) (як-є ()))\\n",
        )
        self.assertEqual(mod.project_current_uk(lisp.read_text(encoding="utf-8")), words)
        record = mod.verify(lisp, sens, view)
        self.assertTrue(record["program_identity_roundtrip"])
        self.assertTrue(record["canonical_view_roundtrip"])
        self.assertFalse(record["runtime_oracle_admitted_by_this_audit"])
        self.assertEqual(
            (lisp.read_bytes(), sens.read_bytes(), view.read_bytes()), original
        )

    def test_multiform_bad_separators_and_reader_depth_are_rejected(self):
        forms = ["10", "001", "00", "000", "01"]
        for bad in (
            ["00", *forms],
            [*forms, "00"],
            [*forms, "00", "00", *forms],
            [*forms, "01", *forms],
        ):
            with self.subTest(words=bad), self.assertRaises(mod.ProjectionBlocked):
                mod.canonical_uk_from_words(bad)
        # Реальний SENS reader має межу 128: ширша Python-рекурсія
        # не може породжувати хибного сертифіката оберненості.
        too_deep = ["10"] * 130 + ["000"] + ["01"] * 130
        with self.assertRaisesRegex(mod.ProjectionBlocked, "128"):
            mod.canonical_uk_from_words(too_deep)

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

    def test_comments_whitespace_and_line_endings_do_not_change_program(self):
        # The machine must preserve the D1/D2/D3 program, NOT comments or
        # byte-identical human formatting. Even non-keyboard digits in a
        # comment are inert, while those in an executable atom are not.
        variants = (
            "   " + UK,
            UK.replace(" ", "\t"),
            UK.rstrip("\n"),
            UK.rstrip("\n") + "\n\n",
            UK.replace("\n", "\r\n"),
            "; Коментар із чужою цифрою ٢\n" + UK,
            "#| коментар #| вкладений ५ |# завершено |#\n" + UK,
            UK.replace("(атом? (як-є ()))",
                       "#| інертний |# (атом? (як-є ()))", 1) +
                "; наприкінці",
        )
        for source in variants:
            with self.subTest(source=source):
                self.lisp.write_text(source, encoding="utf-8")
                original = self.lisp.read_bytes()
                report = self.verify()
                self.assertTrue(report["canonical_uk_roundtrip"])
                self.assertTrue(report["program_identity_roundtrip"])
                self.assertEqual(self.lisp.read_bytes(), original)
                self.assertEqual(mod.project_current_uk(source), WORDS.split())
        self.lisp.write_text(UK, encoding="utf-8")

    def test_english_aliases_and_changed_program_fail(self):
        # Changed domain identity or a different operation is a real
        # regression even when .sens and its canonical view remain intact.
        original = self.lisp.read_bytes()
        for candidate in (
            UK.replace("за-умовою", "COND"),
            UK.replace("перше", "CAR"),
            UK.replace("атом?", "ATOM"),
            UK.replace("сполучити", "CONS"),
            UK.replace("(як-є ())", "(як-є так)", 1),
            UK.replace("(перше ())", "(решта ())"),
            UK.replace("(атом? (як-є ()))", "(атом? (сполучити (як-є ()) (як-є ())))", 1),
        ):
            with self.subTest(source=candidate):
                self.lisp.write_bytes(candidate.encode("utf-8"))
                with self.assertRaises(mod.ProjectionBlocked):
                    self.verify()
        self.lisp.write_bytes(original)

    def test_english_heads_rejected_only_when_executable_not_quoted_data(self):
        # AST reader sees quote context; Python does not evaluate SENS.
        source = "(за-умовою (так (як-є (CAR payload))) (ні (CAR ())))"
        tokens = mod.three_pass.tokenize(
            mod.three_pass.strip_comments(source), source_surface="укр"
        )
        ast = mod.three_pass.Parser(tokens).parse_program()
        self.assertEqual(len(ast), 1)
        # A real unquoted English head must still be rejected.
        with self.assertRaisesRegex(mod.ProjectionBlocked, "Latin executable head"):
            mod.project_current_uk(source)
        quoted_source = "(як-є (CAR payload))"
        # The remaining migrator may reject unsupported quoted data for a
        # separate exact-domain reason; never reject it as an English CALL.
        try:
            mod.project_current_uk(quoted_source)
        except (mod.ProjectionBlocked, mod.three_pass.MigrationError) as err:
            self.assertNotIn("Latin executable head", str(err))
        for plain in ("(CAR ())", "(COND (так ні))", "(QUOTE ())"):
            with self.subTest(plain=plain):
                with self.assertRaisesRegex(
                    mod.ProjectionBlocked, "Latin executable head"
                ):
                    mod.project_current_uk(plain)

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
        self.view.symlink_to(F / "cond-short-circuit")
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
        self.assertEqual(mod.uk_surface(4)["1000"], "перше-першого")
        with tempfile.TemporaryDirectory(prefix="sens-d4-uk-triple-") as td:
            stage = Path(td)
            for suffix in (".lisp", ".sens", ""):
                shutil.copyfile(source_dir / ("caar" + suffix),
                                stage / ("caar" + suffix))
            lisp, sens, view = stage / "caar.lisp", stage / "caar.sens", stage / "caar"
            original = (lisp.read_bytes(), sens.read_bytes(), view.read_bytes())
            self.assertEqual(lisp.read_text(encoding="utf-8"),
                "(перше-першого (сполучити (сполучити (як-є ()) (як-є ())) (як-є ())))\n")
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

    def test_four_d4_selectors_preserve_program_identity_over_t5m(self):
        # Чотири селектори Д4 — тільки для доведених вкладених D3 CONS.
        # Фізична тотожність не видається за доказ виконання SENS.
        empty = ["10", "001", "00", "000", "01"]

        def pair(left, right):
            return ["10", "111", "00", *left, "00", *right, "01"]

        inner_left = pair(pair(empty, empty), empty)
        inner_right = pair(empty, pair(empty, empty))
        for opcode, name, program_tree in (
            ("1000", "перше-першого", inner_left),
            ("0110", "решта-першого", inner_left),
            ("1001", "друге", inner_right),
            ("0111", "решта-решти", inner_right),
        ):
            words = ["10", opcode, "00", *program_tree, "01"]
            source = (
                f"({name} " + mod.canonical_uk_from_words(program_tree).strip() + ")\n"
            )
            with self.subTest(opcode=opcode):
                self.assertEqual(mod.canonical_uk_from_words(words), source)
                self.assertEqual(mod.project_current_uk(source), words)
                lisp, sens, view = (
                    self.dir / "вибірка.lisp",
                    self.dir / "вибірка.sens",
                    self.dir / "вибірка",
                )
                lisp.write_text(source, encoding="utf-8")
                sens.write_bytes(encode_t5m_projection(" ".join(words)))
                view.write_text(" ".join(words) + "\n", encoding="ascii")
                receipt = mod.verify(lisp, sens, view, codec="t5m")
                self.assertTrue(receipt["program_identity_roundtrip"])
                self.assertTrue(receipt["physical_T5M_roundtrip"])
                self.assertFalse(receipt["runtime_oracle_admitted_by_this_audit"])

                bad_tree = inner_right if opcode in ("1000", "0110") else inner_left
                with self.assertRaisesRegex(mod.ProjectionBlocked, "proved nested"):
                    mod.canonical_uk_from_words(["10", opcode, "00", *bad_tree, "01"])
                with self.assertRaises(mod.ProjectionBlocked):
                    mod.canonical_uk_from_words(["10", opcode, "00", "000", "01"])

    def test_cli_read_only_current_canary(self):
        cmd = [sys.executable, str(SOURCE), "--lisp", str(self.lisp),
               "--sens", str(self.sens), "--view", str(self.view)]
        old_default = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=90)
        # Одні байти можуть одночасно бути канонічним T5M.
        self.assertEqual(old_default.returncode, 0, old_default.stderr)
        self.assertIn('"physical_codec": "t5m"', old_default.stdout)
        # Лише явний legacy T5 у тимчасовій копії, без auto fallback.
        self.sens.write_bytes(mod.encode_words(WORDS.split()))
        legacy = subprocess.run([*cmd, "--codec", "t5"], cwd=ROOT, text=True,
                                capture_output=True, timeout=90)
        self.assertEqual(legacy.returncode, 0, legacy.stderr)
        self.sens.write_bytes(encode_t5m_projection(WORDS))
        ok = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=90)
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertIn("BOUNDED_TRIPLE_PARITY_ONLY_NOT_RELEASE_ADMISSION", ok.stdout)
        self.assertIn('"physical_codec": "t5m"', ok.stdout)
        self.view.write_bytes(b"0\n")
        bad = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=90)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("BLOCKED", bad.stderr)


if __name__ == "__main__":
    unittest.main()
