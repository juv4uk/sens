#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import subprocess
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"migrate-three-pass.py"
SPEC=importlib.util.spec_from_file_location("three_pass",SCRIPT)
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=mod
SPEC.loader.exec_module(mod)

FOUNDATION=ROOT/"knowledge"/"d1-d9-foundation.json"
DOMAIN_SURFACES=ROOT/"crates"/"sens"/"src"/"domain_surface_registry_generated.rs"
SEMANTIC_GENERATED=ROOT/"crates"/"sens"/"src"/"semantic_registry_generated.rs"
SEMANTIC_REGISTRY=ROOT/"crates"/"sens"/"src"/"semantic_registry.rs"
NECESSARY=ROOT/"crates"/"sens"/"src"/"eval"/"necessary_forms_generated.rs"
TEXT7=ROOT/"knowledge"/"d7-keyboard-v2-ratified.json"

class KeyboardV2Sid8MigrationTests(unittest.TestCase):
    """Fresh SID8 imports use the owner-ratified keyboard v2, not old SLP1."""

    @classmethod
    def setUpClass(cls):
        cls.keyboard = mod.build_text7(
            mod.load_foundation(FOUNDATION),
            ROOT / "knowledge/d7-keyboard-v2-ratified.json",
        )
        cls.table = json.loads((ROOT / "knowledge/d7-keyboard-v2-ratified.json").read_text(encoding="utf-8"))["table"]

    def test_all_128_coordinates_in_each_projection(self):
        for view, field in (("en", "ascii"), ("uk", "uk"), ("san", "san")):
            for number in range(128):
                glyph = self.table[number][field]
                if glyph.isalpha():
                    # A single glyph must restore its exact W7 coordinate.
                    self.assertEqual(
                        mod.text7_encode(glyph, self.keyboard, mod.Tok("ATOM", glyph, 0)),
                        [f"{number:07b}"],
                    ) if mod._keyboard_v2_mode(glyph, mod.Tok("ATOM", glyph, 0)) == view else None

    def test_ascii_d7_and_ukrainian_keyboard_roundtrip(self):
        for word, view in (("identity", "en"), ("value", "en"),
                           ("ім'я", "uk"), ("Привіт", "uk"), ("क", "san")):
            cells = mod.text7_encode(word, self.keyboard, mod.Tok("ATOM", word, 0))
            indexes = self.keyboard["keyboard-v2"][view]
            self.assertEqual(cells, [indexes[ch] for ch in word])
            glyphs = {coord: char for char, coord in indexes.items()}
            self.assertEqual("".join(glyphs[cell] for cell in cells), word)

    def test_mixed_scripts_and_unmappable_fail_closed(self):
        for word in ("aб", "кa", "🙂", "é"):
            with self.subTest(word=word), self.assertRaises(mod.MigrationError):
                mod.text7_encode(word, self.keyboard, mod.Tok("ATOM", word, 0))

    def test_all_d11_words_stay_testing_data_not_callable_names(self):
        foundation = json.loads(
            (ROOT / "knowledge/d1-d11-foundation.json").read_text(encoding="utf-8")
        )
        vocabulary = json.loads(
            (ROOT / "knowledge/d11-testing-vocabulary-ratified.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(vocabulary["status"], "owner-ratified")
        self.assertIn("not callable Core", vocabulary["semantic_scope"])
        rows = vocabulary["table"]
        self.assertEqual(len(rows), 43)
        self.assertEqual(
            {row["bits"]: row["lisp"] for row in rows},
            foundation["domains"]["D11"]["residents"],
        )
        routed = mod.current_residents(foundation)
        preserved_lower = []
        testing_only = []
        for row in rows:
            bits, name = row["bits"], row["lisp"].upper()
            self.assertEqual(len(bits), 11, name)
            self.assertEqual(set(bits) - {"0", "1"}, set(), name)
            target = routed.get(name)
            # Positive: original lower-domain identities remain stable;
            # negative: no test-only coordinate becomes a callable head.
            self.assertNotEqual(target, (bits, "D11"), name)
            if target is None:
                testing_only.append(name)
            else:
                self.assertIn(target[1], (
                    "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
                ))
                preserved_lower.append(name)
        self.assertEqual(len(preserved_lower), 9)
        self.assertEqual(len(testing_only), 34)
        self.assertEqual(routed["NOT"], ("0100", "D4"))
        self.assertEqual(routed["LENGTH"], ("000000", "D6"))
        self.assertNotIn("TEST-PASS", routed)

    def test_no_d11_test_identity_enters_any_three_pass_successor_map(self):
        # Inspect all three REAL migration maps, not just current_residents().
        # Historical name and generated-surface imports must not accidentally
        # promote the ratified *test data* D11 to callable SENS identities.
        foundation = mod.load_foundation(
            ROOT / "knowledge/d1-d11-foundation.json"
        )
        my, upper, _bs = mod.build_three_pass_maps(
            foundation, DOMAIN_SURFACES, SEMANTIC_GENERATED,
            SEMANTIC_REGISTRY, NECESSARY,
        )
        for stage, mapping in (("my", my), ("upper", upper)):
            for spelling, identity in mapping.items():
                if identity is not None:
                    self.assertNotEqual(
                        identity[1], "D11",
                        f"{stage}:{spelling!r} must not import testing-only D11",
                    )

        # Nine same-spelling D11 tests cannot erase the lower ratified identity.
        self.assertEqual(upper["NOT"], ("0100", "D4"))
        self.assertEqual(upper["LENGTH"], ("000000", "D6"))
        # Unique D11 test names are valid testing DATA, not implicit calls.
        for name in ("DECODE-T5", "TEST-WORDS", "TEST-PASS"):
            self.assertIsNone(upper.get(name), name)


class ExhaustiveExactCallHeadWidthTests(unittest.TestCase):
    """All 2046 D1–D10 typed coordinates; no SID8-by-payload alias."""

    def test_every_ratified_width_stays_exact_and_noncallable_domains_block(self):
        from domain_tables import read_domain_table

        current_d8 = {format(n, "08b") for n in range(256)}
        resolver = mod.Resolver({}, {})
        seen = set()
        admitted = 0
        rejected = 0
        for width in range(1, 11):
            path = ROOT / "lib" / "domains" / f"d{width}.lisp"
            rows = read_domain_table(path)
            self.assertEqual(len(rows), 1 << width)
            for n, row in enumerate(rows):
                bits = format(n, f"0{width}b")
                self.assertEqual((row.width, row.bits), (width, bits))
                ident = (width, bits)
                self.assertNotIn(ident, seen)
                seen.add(ident)
                tok = mod.Tok("ATOM", bits, 0)
                # Domain presence is NOT proof of callable admission.
                # D8 is owner-ratified as a domain, but its residents do not
                # become executable merely because eight-bit coordinates exist.
                blocked_width = width in (2, 7, 8, 9, 10) or (width == 3 and n == 0)
                if blocked_width:
                    with self.subTest(width=width, index=n):
                        with self.assertRaises(mod.MigrationError):
                            resolver.head(tok)
                    rejected += 1
                else:
                    out, origin = resolver.head(tok)
                    self.assertEqual(out, [bits])
                    self.assertEqual(len(out[0]), width)
                    admitted += 1
        self.assertEqual(len(seen), 2046)  # 2^1 + ... + 2^10
        self.assertEqual(rejected, 1669 + (1 << 8))
        self.assertEqual(admitted, 377 - (1 << 8))
        # D7 and D10 are counted as coordinates, NOT 1152 callable functions.
        self.assertEqual(sum(w * (1 << w) for w in range(1, 11)), 18434)

    def test_unratified_sid8_bridge_cannot_admit_d8_or_d9_calls(self):
        for word in ("00001111", "00010110", "00100010"):
            with self.subTest(word=word), self.assertRaisesRegex(
                mod.MigrationError, "retired SID8-era head"
            ):
                mod.Resolver({}, {}).head(mod.Tok("ATOM", word, 0))
        with self.assertRaisesRegex(mod.MigrationError, "unratified SID8 bridge"):
            mod.Resolver({}, {}, bridge_by_sid={"00010110": ("D9", "110111010")})

    def test_structural_empty_and_text_can_be_data_but_not_calls(self):
        resolver = mod.Resolver({}, {})
        for code in ("000", "0000000", "1111111",
                     "000000000", "111111111", "0000000000",
                     "1111111111", "00000000000"):
            with self.subTest(code=code), self.assertRaises(mod.MigrationError):
                resolver.head(mod.Tok("ATOM", code, 0))
        # The source D3 EMPTY value is still canonical data.
        self.assertEqual(mod.migrate_file("()", resolver, {}), "000\n")


class ThreePassMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=mod.load_foundation(FOUNDATION)
        cls.my,cls.upper,_bs=mod.build_three_pass_maps(
            data,DOMAIN_SURFACES,SEMANTIC_GENERATED,SEMANTIC_REGISTRY,NECESSARY
        )
        cls.text7=mod.build_text7(data,TEXT7)

    def migrate(self,source):
        resolver=mod.Resolver(self.my,self.upper)
        return mod.migrate_file(source,resolver,self.text7),resolver

    def test_empty_list_is_compact_d3_empty(self):
        out,_=self.migrate("()\n")
        self.assertEqual(out,"000\n")

    def test_nonempty_list_uses_d2_structure(self):
        out,_=self.migrate("(CAR x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertTrue(out.endswith(" 01\n"))

    def test_pass2_my_lisp_car(self):
        out,resolver=self.migrate("(car x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass2_my_lisp_predicate_alias(self):
        out,resolver=self.migrate("(atom? x)\n")
        self.assertTrue(out.startswith("10 010 00 "))
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass3_lisp15_car(self):
        out,resolver=self.migrate("(CAR x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_pass3_lisp15_arithmetic(self):
        out,resolver=self.migrate("(PLUS x y)\n")
        self.assertTrue(out.startswith("10 01010 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_string_literal_never_collapses_into_empty(self):
        for datum in ('"alpha"', '"beta"', '""'):
            with self.subTest(datum=datum):
                with self.assertRaisesRegex(mod.MigrationError, "STRING_LITERAL_UNADMITTED"):
                    self.migrate(f"(100 {datum})\n")

    def test_sid8_bridge_cannot_authorize_any_executable_head(self):
        with self.assertRaisesRegex(mod.MigrationError, "unratified SID8 bridge"):
            mod.Resolver(self.my, self.upper,
                         bridge_by_sid={"01001011": ("D9", "110101001")})

    def test_named_d9_resident_cannot_become_callable(self):
        resolver = mod.Resolver({"unproved-d9": ("110101001", "D9")}, {})
        with self.assertRaisesRegex(mod.MigrationError, "D9 .*callable"):
            mod.migrate_file("(unproved-d9 x)\n", resolver, self.text7)

    def test_comments_disappear(self):
        a,_=self.migrate("; top\n(CAR #| nested #| inner |# body |# x)\n")
        b,_=self.migrate("(CAR x)\n")
        self.assertEqual(a,b)

    def test_unknown_function_passes_through_verbatim(self):
        out,resolver=self.migrate("(totally-unknown-function x)\n")
        self.assertEqual(out,"10 totally-unknown-function 00 x 01\n")
        self.assertEqual(resolver.counts["passthrough-head"],1)

    def test_my_lisp_functions_with_current_successors_are_not_legacy_unmapped(self):
        for source,bits in [
            ("(not? x)\n","0100"),
            ("(length xs)\n","000000"),
            ("(map f xs)\n","101000"),
            ("(reduce f z xs)\n","101110"),
            ("(let ((x 1)) x)\n","001000"),
            ("(let* ((x 1)) x)\n","001001"),
        ]:
            out,resolver=self.migrate(source)
            self.assertTrue(out.startswith(f"10 {bits} "),source)
            self.assertEqual(resolver.counts["pass2-my-lisp"],1,source)

    def test_d1_head_may_pass_but_d2_head_is_reserved_for_structure(self):
        out1,resolver1=self.migrate("(1 x)\n")
        self.assertEqual(out1,"10 1 00 x 01\n")
        self.assertEqual(resolver1.counts["passthrough-head"],1)
        with self.assertRaisesRegex(mod.MigrationError,"D2 word 10 is structural control only"):
            self.migrate("(10 x)\n")

    def test_d7_d9_heads_without_callable_proof_are_blocked(self):
        # Ширина й наявність резидента не надають права виклику.
        for word in ("0000000", "1111111"):
            with self.subTest(domain="D7", word=word):
                with self.assertRaisesRegex(
                    mod.MigrationError, "фонемна/текстова ідентичність"
                ):
                    self.migrate(f"({word} x)\n")
        for word in ("000000000", "111111111"):
            with self.subTest(domain="D9", word=word):
                with self.assertRaisesRegex(
                    mod.MigrationError, "відсутній доказ допущеного механізму"
                ):
                    self.migrate(f"({word} x)\n")

    def test_d9_full_residency_is_data_not_implicit_callability(self):
        # Exact D9 residency: all 512 data coordinates are not executable mechanisms.
        foundation = mod.load_foundation(FOUNDATION)
        residents = set(foundation["domains"]["D9"]["residents"])
        self.assertEqual(len(residents), 512)
        resolver = mod.Resolver(self.my, self.upper, d9_residents=residents)
        for word in ("000000000", "111111111"):
            with self.subTest(word=word):
                self.assertIn(word, residents)
                with self.assertRaisesRegex(
                    mod.MigrationError, "D9 .*відсутній доказ допущеного механізму"
                ):
                    mod.migrate_file(f"({word} x)\n", resolver, self.text7)
                self.assertEqual(
                    mod.migrate_file(f"(100 {word})\n", resolver, self.text7),
                    f"10 100 00 {word} 01\n",
                )

    def test_d7_d9_data_words_remain_distinct_from_executable_heads(self):
        # Зміна стосується лише позиції виклику, не даних.
        for word in ("0000000", "000000000"):
            with self.subTest(word=word):
                out, _ = self.migrate(f"(100 {word})\n")
                self.assertEqual(out, f"10 100 00 {word} 01\n")

    def test_d2_words_cannot_survive_as_ordinary_data(self):
        for word in ("00","01","10","11"):
            with self.assertRaisesRegex(mod.MigrationError,"structural control only"):
                self.migrate(f"(CONS {word} x)\n")

    def test_numeric_literals_are_blocked_until_explicit_d24_admission(self):
        # Historic human spellings are not D1-D9 function/domain addresses.
        # An incomplete source cannot silently become physical executable T5.
        for literal in ("25", "#d25", "#b101", "#q2:1/10", "-3",
                        "1/2", "1.5", "2e3"):
            with self.subTest(literal=literal):
                with self.assertRaisesRegex(
                    mod.MigrationError, "requires explicit D24\\+ numeric-domain"
                ):
                    self.migrate(f"(CAR {literal})\n")

    def test_bare_d24_full_width_is_not_guessed_from_bits(self):
        for width in (24, 48, 96):
            with self.subTest(width=width):
                with self.assertRaisesRegex(
                    mod.MigrationError, "requires explicit D24\\+ numeric-domain"
                ):
                    self.migrate(f"(CAR {'0' * width})\n")

    def test_d1_predicates_and_binary_domain_codes_are_not_numeric_literals(self):
        for bit in ("0", "1"):
            projection, _=self.migrate(f"(CAR {bit})\n")
            self.assertEqual(projection, f"10 100 00 {bit} 01\n")
        # A binary D3 identity in a data slot does not infer a numeric 5.
        projection, _=self.migrate("(CAR 101)\n")
        self.assertEqual(projection, "10 100 00 101 01\n")

    def test_quote_of_empty_is_quote_plus_000(self):
        out,_=self.migrate("'()\n")
        self.assertEqual(out,"10 001 00 000 01\n")

    def test_dotted_pair_uses_d2_dot_without_unadmitted_quote_symbols(self):
        # D2 DOT is structural; quoted free symbols still have no ratified
        # reversible D7 datum transport. Use admitted D3 EMPTY instead.
        out,_=self.migrate("'(() . ())\n")
        self.assertEqual(out,"10 001 00 10 000 11 000 01 01\n")

    def test_quoted_symbol_datum_is_transported_as_ratified_d7_text(self):
        # Ratified quoted-datum law: a quoted free symbol with no place in the
        # callable D3-D10 ladder is transported as D7 Text/Data (D7 never
        # creates a callable), framed exactly and never silently dropped.
        out,_=self.migrate("'(a . b)\n")
        self.assertEqual(
            out,"10 001 00 10 10 1100001 01 11 10 1100010 01 01 01\n"
        )

    def test_known_structure_and_function_convert_while_unknown_data_stays_visible(self):
        out,_=self.migrate("(CONS x y)\n")
        self.assertEqual(out,"10 111 00 x 00 y 01\n")

    def test_all_emitted_structural_control_is_d2_and_empty_is_d3_value(self):
        out,_=self.migrate("(CONS () 1)\n")
        words=out.split()
        controls=[word for word in words if len(word)==2]
        self.assertTrue(controls)
        self.assertTrue(all(word in {"00","01","10","11"} for word in controls))
        self.assertIn("000",words)
        self.assertEqual(out.count("000"),1)

    def test_same_basename_gets_sens_extension_without_directory_collision(self):
        self.assertEqual(str(mod.sens_destination(Path("tasks.lisp"))), "tasks.sens")
        self.assertEqual(str(mod.sens_destination(Path("tasks/pending.lisp"))),
                         "tasks/pending.sens")
        self.assertEqual(str(mod.sens_destination(Path("lib/sse4.1.lisp"))),
                         "lib/sse4.1.sens")
        self.assertEqual(str(mod.sens_destination(Path("foo.lisp"))), "foo.sens")

    def test_legacy_unmapped_name_is_not_valid_t5_binary_output(self):
        projection,_ = self.migrate("(totally-unknown-function x)\n")
        with self.assertRaises(mod.SensT5Error):
            mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(mod.encode_projection("000\n")), ["000"])

    def test_main_writes_actual_sens_bytes_and_blocks_leftover_names(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            root = temp / "inputs"
            root.mkdir()
            (root / "tasks").mkdir()
            (root / "good.lisp").write_text("()\n", encoding="utf-8")
            (root / "tasks.lisp").write_text("()\n", encoding="utf-8")
            (root / "tasks" / "more.lisp").write_text("()\n", encoding="utf-8")
            (root / "unresolved.lisp").write_text(
                "(totally-unknown-function x)\n", encoding="utf-8"
            )
            out = temp / "artifacts"
            report = temp / "report.json"
            args = [
                sys.executable, str(SCRIPT), str(root), "--out", str(out),
                "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--text7", str(TEXT7),
                "--report", str(report),
            ]
            subprocess.run(args, check=True, capture_output=True, text=True)
            self.assertTrue((out / "good.sens").is_file())
            self.assertTrue((out / "tasks.sens").is_file())
            self.assertTrue((out / "tasks" / "more.sens").is_file())
            self.assertFalse((out / "unresolved.sens").exists())
            self.assertFalse((out / "good").exists())
            self.assertFalse((out / "good.lisp").exists())
            self.assertEqual(mod.decode_bytes((out / "good.sens").read_bytes()),
                             ["000"])
            self.assertEqual((root / "good.lisp").read_text(), "()\n")
            result = json.loads(report.read_text())
            self.assertEqual(result["summary"]["files_written"], 3)
            self.assertEqual(result["summary"]["files_blocked"], 1)
            self.assertTrue(result["file_format"]["physical"].startswith("binary"))
            self.assertEqual(result["naming_law"].split(" -> ")[1].split(";")[0],
                             "OUT/name.sens")
            # Never silently overwrite the exact .sens target on rerun.
            again = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertEqual((out / "good.sens").read_bytes(),
                             mod.encode_projection("000\n"))
            # Explicitly return to source/manifest workflow before a rerun.
            self.assertTrue((root / "tasks.lisp").exists())

    def test_dry_run_produces_report_without_any_binary_file(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "in"
            src.mkdir()
            (src / "one.lisp").write_text("()\n", encoding="utf-8")
            dst = base / "out"
            report = base / "report.json"
            process = subprocess.run([
                sys.executable, str(SCRIPT), str(src),
                "--out", str(dst), "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--text7", str(TEXT7), "--report", str(report), "--dry-run",
            ], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertFalse(dst.exists())
            state = json.loads(report.read_text())
            self.assertEqual(state["summary"]["files_would_write"], 1)
            self.assertEqual(state["summary"]["files_written"], 0)


    def test_unpaired_only_ignores_preexisting_sens_pairs(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "src"
            source.mkdir()
            (source / "old.lisp").write_text("()\\n".replace("\\n", "\n"), encoding="utf-8")
            (source / "paired.lisp").write_text("()\\n".replace("\\n", "\n"), encoding="utf-8")
            already = mod.encode_projection("000")
            (source / "paired.sens").write_bytes(already)
            out = base / "mirror"
            report = base / "report.json"
            result = subprocess.run([
                sys.executable, str(SCRIPT), str(source),
                "--out", str(out), "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--text7", str(TEXT7), "--report", str(report),
                "--unpaired-only",
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((out / "old.sens").read_bytes(), already)
            self.assertFalse((out / "paired.sens").exists())
            self.assertEqual((source / "paired.sens").read_bytes(), already)
            self.assertEqual((source / "old.lisp").read_text(), "()\n")
            summary = json.loads(report.read_text())
            self.assertTrue(summary["only_unpaired"])
            self.assertEqual(summary["skipped_paired_paths"], ["paired.lisp"])
            self.assertEqual(summary["summary"]["files_seen"], 1)
            self.assertEqual(summary["summary"]["files_skipped_paired"], 1)
            self.assertEqual(summary["summary"]["files_written"], 1)


    def test_minimal_cli_defaults_to_current_ratified_foundation(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "old.lisp"
            source.write_text("()\n", encoding="utf-8")
            out = base / "mirror"
            done = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--out", str(out)],
                cwd=base, text=True, capture_output=True,
            )
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual((out / "old.sens").read_bytes(),
                             mod.encode_projection("000"))
            report = base / "mirror.report.json"
            self.assertTrue(report.is_file())
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["files_written"], 1)
            self.assertEqual(state["summary"]["files_seen"], 1)
            self.assertEqual(source.read_text(), "()\n")


    def test_global_define_shadows_builtin_surface_with_bound_text7_frame(self):
        # Pass 2 knows 'car' as D3 CAR, but the source-defined callable must
        # win at its own call site without rewriting the literal D3 code.
        source="(0011 car (1000 () 1))\n(car)\n"
        projection,resolver=self.migrate(source)
        frame=mod.frame_text7(
            mod.text7_encode("car",self.text7,mod.Tok("ATOM","car",0)),
            mod.Tok("ATOM","car",0),
        )
        self.assertGreaterEqual(projection.count(" ".join(frame)),2)
        self.assertEqual(resolver.counts["pass4-text7-global"],1)

    def test_global_text7_call_head_uses_same_frame_as_define_target(self):
        source="""\
(0011 foo
  (1000 ()
    1))
(foo)
"""
        projection,resolver=self.migrate(source)
        frame=mod.frame_text7(
            mod.text7_encode("foo",self.text7,mod.Tok("ATOM","foo",0)),
            mod.Tok("ATOM","foo",0),
        )
        frame_text=" ".join(frame)
        self.assertGreaterEqual(projection.count(frame_text),2)
        self.assertEqual(resolver.counts["pass4-text7-global"],1)
        self.assertTrue(all(set(word) <= {"0","1"} for word in projection.split()))
        payload=mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(payload),projection.split())


    def test_real_machine_block_closes_all_global_and_local_symbolic_words(self):
        source=(ROOT/"lib"/"machine"/"block.lisp").read_text(encoding="utf-8")
        projection,resolver=self.migrate(source)
        words=projection.split()
        self.assertTrue(words)
        self.assertTrue(
            all(set(word) <= {"0","1"} for word in words),
            "the real machine-block source must reach an all-binary candidate",
        )
        # The original machine-block witness needed 17 historical W8 routes.
        # That source has since been migrated to exact D3/D4 code; requiring
        # 17 SID8 hits here would force a regression to retired semantics.
        self.assertGreater(resolver.counts["already-exact"], 0)
        self.assertEqual(source.count("(0011 "), 6)
        self.assertNotIn("(00001001 ", source)

        for name in (
            "machine-block",
            "machine-block-empty",
            "machine-block-one",
            "machine-block-append",
            "machine-block-concat",
            "machine-block-forms",
        ):
            frame=mod.frame_text7(
                mod.text7_encode(name,self.text7,mod.Tok("ATOM",name,0)),
                mod.Tok("ATOM",name,0),
            )
            self.assertIn(
                " ".join(frame),
                projection,
                f"missing canonical global Text7 frame for {name}",
            )

        forms_frame=mod.frame_text7(
            mod.text7_encode("forms",self.text7,mod.Tok("ATOM","forms",0)),
            mod.Tok("ATOM","forms",0),
        )
        self.assertGreaterEqual(
            projection.count(" ".join(forms_frame)),
            2,
            "lambda binder and local reference must share one Text7 binding frame",
        )

        payload=mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(payload),words)
        self.assertTrue(payload, "physical T5 candidate must contain bytes")


    def test_machine_block_local_callable_shadows_builtin_surface(self):
        source="""\
(0011 first
  (1000 (first)
    (first)))
"""
        projection,resolver=self.migrate(source)
        words=projection.split()
        self.assertTrue(all(set(word) <= {"0","1"} for word in words))
        first_frame=mod.frame_text7(
            mod.text7_encode("first",self.text7,mod.Tok("ATOM","first",0)),
            mod.Tok("ATOM","first",0),
        )
        self.assertGreaterEqual(projection.count(" ".join(first_frame)),2)


if __name__=="__main__":
    unittest.main()
