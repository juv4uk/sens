#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

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
CONTRACT_FOUNDATION = ROOT / "knowledge" / "d1-d9-foundation.json"
NUMBER_WIDTHS = ROOT / "knowledge" / "number-width-ratified.json"
TEXT7 = ROOT / "crates" / "sens" / "src" / "text7_projection_generated.rs"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
HISTORICAL = ROOT / "contracts" / "core1-historical-sid-map.lisp"
DOMAIN_SURFACES = [
    ROOT / "lib" / "domains" / f"d{width}.lisp"
    for width in range(1, 7)
]
CONTRACT_DOMAIN_SURFACES = [
    ROOT / "lib" / "domains" / f"d{width}.lisp"
    for width in (*range(1, 7), 8, 9)
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

    @classmethod
    def contract_setup(cls):
        data, _ = mod.load_foundation(CONTRACT_FOUNDATION)
        callable_domains = list(mod.CONTRACT_CALL_DOMAINS)
        # The executable migration map is deliberately only D3-D6.
        # D8/D9 residents participate through exact-domain authority and
        # resolver evidence, never by a global human-label identity map.
        code_map = mod.build_map(data, callable_domains)
        code_map = mod.augment_code_map_with_domain_surfaces(
            code_map,
            CONTRACT_DOMAIN_SURFACES,
        )
        resolver = build_resolver(
            historical_map=HISTORICAL,
            foundation=CONTRACT_FOUNDATION,
            registry=REGISTRY,
            domain_surfaces=CONTRACT_DOMAIN_SURFACES,
            prefer_current_surface=True,
        )
        authority = mod.build_binary_authority(data, mod.CONTRACT_DOMAINS)
        return (
            data,
            code_map,
            mod.build_text7_encoder(data, TEXT7),
            resolver,
            authority,
        )

    def contract_binary(self, source: str):
        _, code_map, text7, resolver, authority = self.contract_setup()
        return mod.binary_rewrite(
            source,
            code_map,
            text7,
            resolver=resolver,
            contract_authority=True,
            binary_authority=authority,
            d1_enabled=True,
            d9_enabled=True,
        )

    def test_contract_authority_preserves_exact_d8_word_as_data(self):
        converted, _, _ = self.contract_binary("(LIST 11111111)\n")
        self.assertTrue(converted.startswith("10 1110 00 11111111 01\n"), converted)
        self.assertNotIn("1100001 1100001 1100001", converted)

    def test_contract_authority_rejects_d8_head_as_non_callable(self):
        with self.assertRaisesRegex(
            mod.BinaryMigrationError,
            "non-callable authority resident used as executable head",
        ):
            self.contract_binary("(ROUND x)\n")

    def test_contract_authority_rejects_human_alist_head_instead_of_serializing_prose_authority(self):
        with self.assertRaisesRegex(
            mod.BinaryMigrationError,
            "dynamic-symbol-head",
        ):
            self.contract_binary("((major . contract-version))\n")

    def test_contract_authority_call_map_excludes_d8_d9_but_resolver_keeps_evidence(self):
        _, code_map, _, resolver, authority = self.contract_setup()
        self.assertTrue(
            all(entry.domain in mod.CONTRACT_CALL_DOMAINS for entry in code_map.values())
        )
        self.assertEqual(mod.CONTRACT_CALL_DOMAINS, ("D3", "D4", "D5", "D6"))
        self.assertIn((8, "10101000"), authority)
        self.assertIn((9, "100000001"), authority)
        self.assertNotIn("ROUND", code_map)

        resolution = resolver.resolve_head("ROUND")
        self.assertTrue(resolution.resolved)
        self.assertEqual(resolution.current.domain, "D8")
        self.assertEqual(resolution.current.bits, "10101000")

        # A reused human label cannot select one domain globally.
        self.assertNotIn("MAP", resolver.current_by_label)


    def test_contract_authority_preserves_bare_d7_word_instead_of_spelling_digits(self):
        converted, _, _ = self.contract_binary("(LIST 0011001)\n")
        self.assertIn("0011001", converted)
        self.assertNotIn("1100001 1100001 1100001", converted)

    def test_contract_authority_preserves_exact_d1_source_cell(self):
        converted, _, _ = self.contract_binary("(LIST 1)\n")
        self.assertTrue(converted.startswith("10 1110 00 1 01\n"), converted)
        self.assertIn("1", converted.split())

    def test_contract_authority_rejects_hash_b_wrapper(self):
        with self.assertRaisesRegex(
            mod.BinaryMigrationError,
            "legacy #b binary wrapper",
        ):
            self.contract_binary("(LIST #b101)\n")

    def test_contract_authority_digit_only_string_is_text7_data(self):
        converted, hits, _ = self.contract_binary('(LIST "101")\n')
        self.assertTrue(converted.startswith("10 1110 00 "), converted)
        self.assertNotIn("101", converted.split())
        self.assertRegex(converted, r"^[01\s]+$")
        self.assertEqual([hit.label for hit in hits], ["LIST"])

    def test_contract_authority_rejects_noncanonical_d2_data_word(self):
        with self.assertRaisesRegex(
            mod.BinaryMigrationError,
            "D2 word '10' is structural control only",
        ):
            self.contract_binary("(LIST 10)\n")

    def test_contract_authority_preserves_exact_w9_source_cell(self):
        converted, _, _ = self.contract_binary("(LIST 100000001)\n")
        self.assertIn("100000001", converted.split())

    def test_contract_authority_keeps_w8_even_when_legacy_sid8_evidence_exists(self):
        converted, _, _ = self.contract_binary("(LIST 00000101)\n")
        self.assertIn("00000101", converted.split())
        self.assertNotIn("100", converted.split())

    def test_contract_authority_validator_accepts_exact_d8_value(self):
        _, _, _, _, authority = self.contract_setup()
        mod.validate_contract_binary_output(
            "10 1110 00 00000101 01\n",
            authority,
            d1_enabled=False,
            d9_enabled=False,
        )

    def test_contract_authority_validator_rejects_unadmitted_binary_word(self):
        _, _, _, _, authority = self.contract_setup()
        with self.assertRaisesRegex(
            mod.BinaryMigrationError,
            "unadmitted exact binary word",
        ):
            mod.validate_contract_binary_output(
                "10 111 00 0100001 01\n",
                authority,
                d1_enabled=True,
                d9_enabled=True,
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
            "(00000101 x)\n": ("100", "CAR"),
            "(car x)\n": ("100", "CAR"),
            "(CAR x)\n": ("100", "CAR"),
            "(00001100 a b)\n": ("01010", "PLUS"),
            "(+ a b)\n": ("01010", "PLUS"),
            "(PLUS a b)\n": ("01010", "PLUS"),
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
            converted, hits, _ = self.binary(f"({surface} x)\n")
            self.assertTrue(converted.startswith(f"10 {bits} 00 "), (surface, converted))
            self.assertTrue(hits, surface)

    def test_binary_source_uses_d2_structure_and_exact_function_words(self):
        converted, hits, shadowed = self.binary("(CONS (CAR x) (CDR y))\n")
        # x = SLP1 0x50, y = SLP1 0x26.
        self.assertEqual(
            converted,
            "10 111 00 10 100 00 1010000 01 00 "
            "10 011 00 0100110 01 01\n",
        )
        self.assertEqual([hit.label for hit in hits], ["CONS", "CAR", "CDR"])
        self.assertFalse(shadowed)

    def test_registry_only_old_sid_map_reaches_current_d6_map(self):
        converted, hits, _ = self.binary("(00110111 f xs)\n")
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
        converted, hits, _ = self.binary("(100 x)\n")
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
  x)
"""
        plain = "(CAR x)\n"
        a, _, _ = self.binary(commented)
        b, _, _ = self.binary(plain)
        self.assertEqual(a, b)
        self.assertNotIn(";", a)
        self.assertNotIn("#", a)

    def test_comment_markers_inside_string_are_data_not_comments(self):
        source = '(LIST ";not-comment" "#|not-comment|#")\n'
        converted, hits, _ = self.binary(source)
        self.assertTrue(converted.startswith("10 1110 "))
        self.assertEqual([hit.label for hit in hits], ["LIST"])
        self.assertRegex(converted, r"^[01\s]+$")

    def test_quoted_function_name_is_data_not_callable_identity(self):
        converted, hits, _ = self.binary("'(CAR x)\n")
        self.assertFalse(hits)
        words = converted.split()
        self.assertNotEqual(words[words.index("10") + 1], "100")
        self.assertRegex(converted, r"^[01\s]+$")

    def test_standalone_dot_is_d2_dot_but_dot_inside_data_symbol_is_text7(self):
        dotted, _, _ = self.binary("(LIST a . b)\n")
        self.assertIn(" 11 ", dotted)
        symbol, _, _ = self.binary("(LIST a.b)\n")
        self.assertIn("1111010", symbol)  # Text7 sign.dot

    def test_unencodable_data_character_fails_closed(self):
        with self.assertRaises(mod.BinaryMigrationError):
            self.binary("(LIST 🙂)\n")

    def test_binary_output_is_ascii_bits_only(self):
        converted, _, _ = self.binary('(CONS "привіт" test-name)\n')
        self.assertRegex(converted, r"^[01\s]+$")
        converted.encode("ascii")


if __name__ == "__main__":
    unittest.main()