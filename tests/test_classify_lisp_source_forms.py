#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT = SCRIPTS / "classify-lisp-source-forms.py"
SPEC = importlib.util.spec_from_file_location("classify_forms", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

from sens_source_resolver import build_resolver

HIST = ROOT / "contracts" / "core1-historical-sid-map.lisp"
FOUNDATION = ROOT / "knowledge" / "d1-d11-foundation.json"
REGISTRY = ROOT / "lib" / "surface" / "semantic-registry.lisp"
SURFACES = [
    ROOT / "lib" / "domains" / f"d{width}.lisp"
    for width in (3, 4, 5, 6, 8, 9, 10)
]


class ThreePassClassifierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = build_resolver(
            historical_map=HIST,
            foundation=FOUNDATION,
            registry=REGISTRY,
            domain_surfaces=SURFACES,
        )

    def classify(self, source: str, *, source_era: str = "current"):
        heads = mod.scan_heads("sample.lisp", source, source_era=source_era)
        return mod.classify_heads(
            heads, self.resolver, source_era=source_era,
        )

    def test_physical_t5m_never_enters_text_source_inventory(self):
        # Навіть UTF-8-подібний .sens не є джерелом чи дозволом
        # трактувати історичний SID8 як поточний код Д8.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "дійсний.lisp").write_text("(атом? (як-є ()))\n", encoding="utf-8")
            (root / "дійсний.sens").write_bytes(b"\x00\xff\x02")
            (root / "старий.sens").write_text("(00000101 x)\n", encoding="utf-8")
            self.assertEqual(
                {p.name for p in mod.source_files(root)}, {"дійсний.lisp"}
            )
            _, _, _, _, summary = mod.scan_tree(root, self.resolver)
            self.assertEqual(summary["files_seen"], 1)

    def test_current_sid8_lookalike_is_rejected_not_assumed_d8_or_legacy(self):
        for old_word in ("00000101", "00000001", "00001100", "11111111"):
            with self.subTest(old_word=old_word):
                with self.assertRaisesRegex(ValueError, "retired SID8-era head"):
                    self.classify(f"({old_word} x)\\n")

    def test_explicit_legacy_quote_candidate_does_not_authorize_modern_d8(self):
        historical, _, _, _ = self.classify(
            "(00000001 (00000101 x))\\n", source_era="legacy",
        )
        self.assertEqual(len(historical), 1)
        self.assertEqual(historical[0].current_domain, "D3")
        self.assertEqual(historical[0].current_bits, "001")
        self.assertIn("execution not certified", historical[0].evidence)

    def test_wide_current_ukr_heads_resolve_without_promoting_sid8(self):
        # Власницькі людські проєкції D8–D10, не доказ виконання.
        src = (
            "(символ-за-кодом 65)\n"
            "(пояснити-відповідь x)\n"
            "(відсутня-можливість-виконання x)\n"
        )
        historical, current, dynamic, empty = self.classify(src)
        self.assertFalse(dynamic)
        self.assertFalse(current)
        self.assertFalse(empty)
        self.assertEqual(
            [(x.current_domain, x.current_bits) for x in historical],
            [("D8", "00000000"), ("D9", "000000001"),
             ("D10", "0000000000")],
        )
        with self.assertRaisesRegex(ValueError, "retired SID8-era head"):
            self.classify("(00000000 x)\n")

    def test_pass1_detects_legacy_sid8_and_resolves_current_car(self):
        historical, current, dynamic, empty = self.classify("(00000101 x)\n", source_era="legacy")
        self.assertFalse(current)
        self.assertFalse(dynamic)
        self.assertFalse(empty)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual((hit.pass_number, hit.representation), (1, "sid8-sens8"))
        self.assertEqual(hit.legacy_sid8, "00000101")
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D3", "100", "CAR"))

    def test_pass1_uses_named_registry_role_not_bit_shape_for_map(self):
        historical, _, _, _ = self.classify("(00110111 f xs)\n", source_era="legacy")
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 1)
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D6", "101000", "MAP"))

    def test_pass2_detects_known_my_lisp_surface(self):
        historical, _, dynamic, _ = self.classify("(car x)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual((hit.pass_number, hit.representation), (2, "my-lisp-surface"))
        self.assertEqual((hit.current_domain, hit.current_bits), ("D3", "100"))

    def test_pass2_detects_symbolic_and_ukrainian_surfaces(self):
        for source, bits in [
            ("(+ a b)\n", "01010"),
            ("(додати a b)\n", "01010"),
            ("(атом? x)\n", "010"),
        ]:
            historical, _, dynamic, _ = self.classify(source)
            self.assertFalse(dynamic, source)
            self.assertEqual(len(historical), 1, source)
            self.assertEqual(historical[0].pass_number, 2, source)
            self.assertEqual(historical[0].current_bits, bits, source)

    def test_pass3_detects_uppercase_lisp_1_5(self):
        historical, _, dynamic, _ = self.classify("(PLUS a b)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual((hit.pass_number, hit.representation), (3, "lisp1-1.5-uppercase"))
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D5", "01010", "PLUS"))

    def test_current_exact_head_is_not_reclassified_as_historical(self):
        historical, current, dynamic, _ = self.classify("(100 x)\n")
        self.assertFalse(historical)
        self.assertFalse(dynamic)
        self.assertEqual(len(current), 1)
        self.assertEqual((current[0].current_domain, current[0].current_label), ("D3", "CAR"))

    def test_empty_list_is_structural_inventory_not_function_pass(self):
        historical, current, dynamic, empty = self.classify("(cons x ())\n")
        self.assertEqual([(h.pass_number, h.token) for h in historical], [(2, "cons")])
        self.assertFalse(current)
        self.assertFalse(dynamic)
        self.assertEqual([h.token for h in empty], ["()"])

    def test_unknown_user_call_head_is_dynamic_not_fake_my_lisp(self):
        historical, current, dynamic, empty = self.classify("(sqrt-iter x n)\n")
        self.assertFalse(historical)
        self.assertFalse(current)
        self.assertFalse(empty)
        self.assertEqual([h.token for h in dynamic], ["sqrt-iter"])

    def test_three_real_generations_are_separated_and_clause_symbols_are_not_pass2(self):
        source = """
(00000100 a b)
(car x)
(COND (p a) (T b))
"""
        historical, _, dynamic, _ = self.classify(source, source_era="legacy")
        self.assertEqual(
            [(hit.pass_number, hit.token) for hit in historical],
            [(1, "00000100"), (2, "car"), (3, "COND")],
        )
        # The lexical scanner still sees p/T as list heads inside old COND
        # clause containers, but crucially they are NOT mislabeled as pass 2.
        self.assertEqual([head.token for head in dynamic], ["p", "T"])

    def test_comments_strings_and_reader_quoted_data_do_not_count(self):
        source = """
; (00000101 x)
'(CAR x)
#| (PLUS a b) |#
(car "CAR")
"""
        historical, current, dynamic, empty = self.classify(source)
        self.assertEqual([(hit.pass_number, hit.token) for hit in historical], [(2, "car")])
        self.assertFalse(current)
        self.assertFalse(dynamic)
        self.assertFalse(empty)

    def test_explicit_quote_data_is_not_counted_as_executable_calls(self):
        source = """(quote (car x))
(001 (00000101 x))
(QUOTE ((PLUS a b) (CAR c)))
(00000001 (00110111 f xs))
(car x)
"""
        heads = mod.scan_heads("sample.lisp", source, source_era="legacy")
        self.assertEqual(
            [head.token for head in heads if not head.empty_list],
            ["quote", "001", "QUOTE", "00000001", "car"],
        )
        historical, current, dynamic, empty = mod.classify_heads(
            heads, self.resolver, source_era="legacy",
        )
        self.assertEqual([hit.token for hit in historical],
                         ["quote", "QUOTE", "00000001", "car"])
        self.assertEqual([hit.token for hit in current], ["001"])
        self.assertFalse(dynamic)
        self.assertFalse(empty)

    def test_modern_d8_doseq_is_not_confused_with_legacy_sid8_quote(self):
        # D8:00000001 у чинній драбині = для-кожного-елемента (DOSEQ),
        # а НЕ старе SID8:00000001 QUOTE. Вкладені голови слід бачити.
        src = "(00000001 (додати 2 3))\n"
        current = mod.scan_heads("current.lisp", src)
        self.assertEqual([x.token for x in current], ["00000001", "додати"])
        legacy = mod.scan_heads("legacy.lisp", src, source_era="legacy")
        self.assertEqual([x.token for x in legacy], ["00000001"])
        with self.assertRaises(ValueError):
            mod.scan_heads("unknown.lisp", src, source_era="auto")


    def test_legacy_lambda_sid8_cannot_hide_modern_d8_arguments(self):
        # D8:00001000 = ТОТОЖНЕ-ЗНАЧЕННЯ?, не історична LAMBDA.
        src = "(00001000 (додати 2 3))\n"
        modern = mod.scan_heads("modern.lisp", src)
        self.assertEqual([h.token for h in modern], ["00001000", "додати"])
        historic = mod.scan_heads("historic.lisp", src, source_era="legacy")
        self.assertEqual([h.token for h in historic], ["00001000"])

    def test_nested_executable_operator_does_not_create_second_head(self):
        source = """((car f) car)
((0010 (x) (car x)) value)
('car x)
("car" car)
(car x)
"""
        heads = mod.scan_heads("sample.lisp", source)
        self.assertEqual(
            [head.token for head in heads if not head.empty_list],
            ["car", "0010", "car", "car"],
        )
        # The atom following the nested operator, or a quoted operator atom,
        # is never a new executable head.
        self.assertFalse(any(head.token == "value" for head in heads))

    def test_lambda_and_definition_binders_are_not_function_heads(self):
        source = """(0010 (CAR CDR) (car CAR))
(функція (перше) (car перше))
(define (car x) (atom? x))
(визначити (CAR x) (cdr x))
"""
        heads = mod.scan_heads("sample.lisp", source)
        self.assertEqual(
            [head.token for head in heads if not head.empty_list],
            ["0010", "car", "функція", "car",
             "define", "atom?", "визначити", "cdr"],
        )

    def test_variadic_lambda_binder_atom_does_not_hide_body(self):
        heads = mod.scan_heads("sample.lisp", "(lambda args (car args))")
        self.assertEqual([head.token for head in heads], ["lambda", "car"])

    def test_nested_quoted_and_structural_empty_lists_remain_data(self):
        source = """(quote (()))
'(car ())
(())
(car ())
"""
        heads = mod.scan_heads("sample.lisp", source)
        self.assertEqual([head.token for head in heads if not head.empty_list],
                         ["quote", "car"])
        self.assertEqual([head.token for head in heads if head.empty_list],
                         ["()", "()"])

    def test_uppercase_define_collapses_two_legacy_candidates_to_one_current_identity(self):
        historical, _, dynamic, _ = self.classify("(DEFINE foo x)\n")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 3)
        self.assertEqual((hit.current_domain, hit.current_bits, hit.current_label), ("D4", "0011", "DEFINE"))
        self.assertEqual(hit.resolution, "resolved")

    def test_unknown_eight_bit_head_is_pass1_but_unresolved(self):
        historical, _, dynamic, _ = self.classify("(11111111 x)\n", source_era="legacy")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 1)
        self.assertEqual(hit.resolution, "legacy-unmapped")
        self.assertEqual(hit.legacy_sid8, "11111111")

    def test_old_registry_function_without_current_domain_is_legacy_unmapped(self):
        historical, _, dynamic, _ = self.classify("(01001000 x)\n", source_era="legacy")
        self.assertFalse(dynamic)
        self.assertEqual(len(historical), 1)
        hit = historical[0]
        self.assertEqual(hit.pass_number, 1)
        self.assertEqual(hit.legacy_sid8, "01001000")
        self.assertEqual(hit.resolution, "legacy-unmapped")
        self.assertEqual(hit.current_domain, "")


if __name__ == "__main__":
    unittest.main()
