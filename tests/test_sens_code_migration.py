#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest
import tempfile
import subprocess
import json

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT = SCRIPTS / "migrate-to-sens-codes.py"
SPEC = importlib.util.spec_from_file_location("sens_migrator", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

from sens_source_resolver import build_resolver

FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"
NUMBER_WIDTHS = ROOT / "knowledge" / "number-width-ratified.json"
TEXT7 = ROOT / "crates" / "sens" / "src" / "text7_projection_generated.rs"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
HISTORICAL = ROOT / "contracts" / "core1-historical-sid-map.lisp"
DOMAIN_SURFACES = [
    ROOT / "lib" / "domains" / f"d{width}.lisp"
    for width in range(1, 7)
]


class SensCodeMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data, _ = mod.load_foundation(FOUNDATION)
        cls.data = data
        cls.code_map = mod.build_map(data, ["D3", "D4", "D5", "D6"])
        cls.code_map = mod.augment_code_map_with_domain_surfaces(
            cls.code_map, DOMAIN_SURFACES
        )
        cls.code_map = mod.augment_code_map_with_registry_aliases(
            cls.code_map, REGISTRY
        )
        cls.text7 = mod.build_text7_encoder(data, TEXT7)
        cls.legacy = mod.build_legacy_sid_map(REGISTRY, cls.code_map)
        cls.registry_surfaces = mod.build_registry_surface_sid_map(REGISTRY)
        cls.resolver = build_resolver(
            historical_map=HISTORICAL,
            foundation=FOUNDATION,
            registry=REGISTRY,
            domain_surfaces=DOMAIN_SURFACES,
        )

    def binary(self, source: str):
        return mod.binary_rewrite(
            source,
            self.code_map,
            self.text7,
            self.legacy,
            self.registry_surfaces,
            self.resolver,
        )

    def test_current_d3_authority_is_used(self):
        self.assertEqual(self.code_map["CAR"].bits, "100")
        self.assertEqual(self.code_map["CDR"].bits, "011")
        self.assertEqual(self.code_map["EQ"].bits, "101")
        self.assertEqual(self.code_map["COND"].bits, "110")

    def test_legacy_mirror_still_rewrites_only_call_heads(self):
        source = "(CONS (CAR x) (CDR y))\n"
        converted, hits, blocked = mod.rewrite(source, self.code_map)
        self.assertEqual(converted, "(111 (100 x) (011 y))\n")
        self.assertEqual(len(hits), 3)
        self.assertFalse(blocked)

    def test_empty_list_is_d3_empty_not_open_close(self):
        for source in ["()\n", "(   )\n"]:
            converted, hits, shadowed = self.binary(source)
            self.assertEqual(converted, "000\n")
            self.assertFalse(hits)
            self.assertFalse(shadowed)

    def test_nested_empty_list_uses_000(self):
        converted, _, _ = self.binary("(CONS () ())\n")
        self.assertEqual(converted, "10 111 00 000 00 000 01\n")
        self.assertNotIn("10 01", converted)

    def test_all_three_historical_function_notations_resolve_before_text7(self):
        cases = {
            "(00000101 ())\n": ("100", "CAR"),
            "(car ())\n": ("100", "CAR"),
            "(CAR ())\n": ("100", "CAR"),
            "(00001100 () ())\n": ("01010", "PLUS"),
            "(+ () ())\n": ("01010", "PLUS"),
            "(PLUS () ())\n": ("01010", "PLUS"),
        }
        for source, (bits, label) in cases.items():
            converted, hits, _ = self.binary(source)
            self.assertTrue(converted.startswith(f"10 {bits} 00 "), (source, converted))
            self.assertEqual(hits[0].label, label, source)

    def test_admitted_non_english_surface_resolves_before_text7(self):
        for surface, bits in [
            ("атом?", "010"),
            ("сполучити", "111"),
            ("aṇu", "010"),
            ("додати", "01010"),
        ]:
            converted, hits, _ = self.binary(f"({surface} ())\n")
            self.assertTrue(converted.startswith(f"10 {bits} 00 "), (surface, converted))
            self.assertTrue(hits, surface)

    def test_unframed_lexical_binder_blocks_old_false_binary_success(self):
        source = "(00001001 machine-block (00001000 (forms) forms))\n"
        with self.assertRaisesRegex(mod.BinaryMigrationError, "UNFRAMED_TEXT7_ATOM"):
            self.binary(source)
        # A true original lib source, not a synthetic canary, must not be
        # advertised as an executable packed SENS until a D7 binder term law.
        original = (ROOT / "lib/machine/block.lisp").read_text(encoding="utf-8")
        with self.assertRaisesRegex(
            mod.BinaryMigrationError, r"UNFRAMED_TEXT7_ATOM 'machine-block'"
        ):
            self.binary(original)

    def test_single_cell_text7_atom_is_not_a_bare_d7_codepoint(self):
        # A bare one-cell W7 value is D7 data, not a Lisp identifier.
        # No D2 Text7 atom/binder framing law has been ratified yet.
        with self.assertRaisesRegex(mod.BinaryMigrationError, "UNFRAMED_TEXT7_ATOM"):
            self.binary("(CONS a ())\n")

    def test_binary_source_uses_d2_structure_and_exact_function_words(self):
        converted, hits, shadowed = self.binary("(CONS (CAR ()) (CDR ()))\n")
        # Only D3 EMPTY is admitted as an operand here.
        self.assertEqual(
            converted,
            "10 111 00 10 100 00 000 01 00 "
            "10 011 00 000 01 01\n",
        )
        self.assertEqual([hit.label for hit in hits], ["CONS", "CAR", "CDR"])
        self.assertFalse(shadowed)

    def test_registry_only_old_sid_map_reaches_current_d6_map(self):
        converted, hits, _ = self.binary("(00110111 () ())\n")
        self.assertTrue(converted.startswith("10 101000 00 "), converted)
        self.assertEqual((hits[0].label, hits[0].domain), ("MAP", "D6"))

    def test_unresolved_legacy_sid8_fails_closed_instead_of_surviving_as_w8(self):
        with self.assertRaisesRegex(mod.BinaryMigrationError, "unresolved executable head"):
            self.binary("(11111111 x)\n")

    def test_unresolved_named_legacy_function_fails_instead_of_becoming_text(self):
        # PRINT still exists in the old flat registry, but has no proved current
        # D3-D6 identity.  It must not become either W8 compatibility or Text7.
        with self.assertRaisesRegex(mod.BinaryMigrationError, "unresolved executable head"):
            self.binary("(print x)\n")

    def test_current_exact_width_head_is_preserved(self):
        converted, hits, _ = self.binary("(100 ())\n")
        self.assertTrue(converted.startswith("10 100 00 "))
        self.assertEqual(hits[0].label, "CAR")

    def test_unknown_user_call_head_is_blocker_not_text7(self):
        with self.assertRaisesRegex(mod.BinaryMigrationError, "dynamic-symbol-head"):
            self.binary("(sqrt-iter x n)\n")

    def test_number_width_ladder_is_owner_ratified_24_48_96(self):
        import json
        policy = json.loads(NUMBER_WIDTHS.read_text(encoding="utf-8"))
        self.assertEqual(policy["status"], "owner-ratified")
        self.assertEqual(policy["first_width_bits"], 24)
        self.assertEqual(policy["growth_law"], "width(n) = 24 * 2^n")
        self.assertEqual(policy["ratified_prefix_bits"][:3], [24, 48, 96])

    def test_numeric_literal_is_number_blocker_not_text7_digits(self):
        with self.assertRaisesRegex(
            mod.BinaryMigrationError,
            "ratified Number widths are 24 -> 48 -> 96"
        ):
            self.binary("(LIST 25)\n")

    def test_comments_are_absent_and_do_not_change_binary_output(self):
        commented = """; outside
(CAR ; inline
  #| outer #| nested |# block |#
  ())
"""
        plain = "(CAR ())\n"
        a, _, _ = self.binary(commented)
        b, _, _ = self.binary(plain)
        self.assertEqual(a, b)
        self.assertNotIn(";", a)
        self.assertNotIn("#", a)

    def test_comment_markers_inside_string_remain_data_but_need_atom_framing(self):
        source = '(LIST ";not-comment" "#|not-comment|#")\n'
        cleaned = mod.strip_comments(source)
        self.assertIn('";not-comment"', cleaned)
        self.assertIn('"#|not-comment|#"', cleaned)
        with self.assertRaisesRegex(mod.BinaryMigrationError, "UNFRAMED_TEXT7_ATOM"):
            self.binary(source)

    def test_quoted_multicell_function_name_cannot_impersonate_one_atom(self):
        # No current atom framing law means quoted CAR is three D7 cells,
        # NOT a canonical standalone Lisp atom or executable head.
        with self.assertRaisesRegex(mod.BinaryMigrationError, "UNFRAMED_TEXT7_ATOM"):
            self.binary("'(CAR x)\n")

    def test_dot_is_d2_only_when_standalone_multi_cell_symbol_blocks(self):
        dotted, _, _ = self.binary("(LIST () . ())\n")
        self.assertIn(" 11 ", dotted)
        with self.assertRaisesRegex(mod.BinaryMigrationError, "UNFRAMED_TEXT7_ATOM"):
            self.binary("(LIST a.b)\n")

    def test_unencodable_data_character_fails_closed(self):
        with self.assertRaises(mod.BinaryMigrationError):
            self.binary("(LIST 🙂)\n")

    def test_binary_output_is_ascii_bits_only(self):
        converted, _, _ = self.binary("(CONS (CAR ()) (CDR ()))\n")
        self.assertRegex(converted, r"^[01\s]+$")
        converted.encode("ascii")

    def test_multi_cell_ukrainian_and_english_strings_require_ratified_term(self):
        for source in (
            '(CONS "привіт" x)\n',
            '(CONS test-name x)\n',
            '(CONS ім’я x)\n',
        ):
            with self.subTest(source=source):
                with self.assertRaisesRegex(
                    mod.BinaryMigrationError, "UNFRAMED_TEXT7_ATOM"
                ):
                    self.binary(source)

    def test_new_sens_mirror_is_actual_physical_file_and_no_extensionless(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'source'
            root.mkdir()
            (root / 'hello.lisp').write_text('()\n', encoding='utf-8')
            out = Path(td) / 'out'
            report = Path(td) / 'report.json'
            args = [
                sys.executable, str(SCRIPT), str(root),
                '--foundation', str(FOUNDATION),
                '--sens-mirror', str(out),
                '--text7-projection', str(TEXT7),
                '--historical-map', str(HISTORICAL),
                '--semantic-registry', str(REGISTRY),
                '--report', str(report),
                '--domain-surfaces', *[str(x) for x in DOMAIN_SURFACES],
            ]
            first = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            from sens_t5_codec import decode_bytes, encode_projection
            target = out / 'hello.sens'
            self.assertTrue(target.is_file())
            self.assertFalse((out / 'hello').exists())
            self.assertFalse((out / 'hello.lisp').exists())
            self.assertEqual(target.read_bytes(), encode_projection('000'))
            self.assertEqual(decode_bytes(target.read_bytes()), ['000'])
            self.assertEqual((root / 'hello.lisp').read_text(), '()\n')
            state=json.loads(report.read_text())
            self.assertEqual(state['mode'], 'sens-mirror')
            self.assertEqual(state['files'][0]['status'], 'sens-written')
            second=subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2, second.stderr)
            self.assertEqual(target.read_bytes(), encode_projection('000'))


if __name__ == "__main__":
    unittest.main()
