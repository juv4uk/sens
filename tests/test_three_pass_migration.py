#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import inspect
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

FOUNDATION=ROOT/"knowledge"/"d1-d11-foundation.json"
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
        self.assertEqual(vocabulary["status"], "UNRATIFIED_REVIEW")
        self.assertIs(vocabulary["ratified"], False)
        self.assertIsNone(vocabulary["ratified_by"])
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
        self.assertEqual(
            {name: routed[name] for name in preserved_lower},
            {
                "READ-FILE": ("110110111", "D9"),
                "LENGTH": ("000000", "D6"),
                "TAKE": ("110000", "D6"),
                "DROP": ("110001", "D6"),
                "IF": ("0000000110", "D10"),
                "NOT": ("0100", "D4"),
            },
        )
        self.assertEqual(len(testing_only), 37)
        self.assertEqual(routed["NOT"], ("0100", "D4"))
        self.assertEqual(routed["LENGTH"], ("000000", "D6"))
        self.assertNotIn("TEST-PASS", routed)

    def test_no_d11_test_identity_enters_any_three_pass_successor_map(self):
        # Inspect all three REAL migration maps, not just current_residents().
        # Historical name and generated-surface imports must not accidentally
        # promote the unratified *test fixture* D11 to callable SENS identities.
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
    """Domain identities stay separate from named source projections/calls."""

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
                # Bare machine words do not supply a named current projection.
                blocked_width = (
                    width in (2, 7, 8, 9, 10)
                    or (width == 3 and n == 0)
                )

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
        self.assertEqual(admitted + rejected, 2046)
        # Raw D9/D10 coordinate tokens stay blocked: the name/projection,
        # not width alone, supplies current domain identity.
        self.assertEqual(sum(w * (1 << w) for w in range(1, 11)), 18434)

    def test_directory_scan_does_not_import_nested_agent_worktree_sources(self):
        with tempfile.TemporaryDirectory(prefix="sens-source-scope-") as td:
            root = Path(td)
            (root / "основний.lisp").write_text("()\n", encoding="utf-8")
            nested = root / ".worktrees" / "інша-гілка"
            nested.mkdir(parents=True)
            (nested / "чужий-знімок.lisp").write_text("()\n", encoding="utf-8")
            self.assertEqual(
                [path.relative_to(root).as_posix() for path in mod.source_files(root)],
                ["основний.lisp"],
            )

    def test_raw_d8_stays_sid8_ambiguous_and_bridge_is_rejected(self):
        for word in ("00001111", "00010110", "00100010"):
            with self.subTest(word=word), self.assertRaisesRegex(
                mod.MigrationError, "ambiguous eight-bit SID8/Sens8-or-D8"
            ):
                mod.Resolver({}, {}).head(mod.Tok("ATOM", word, 0))
        with self.assertRaisesRegex(mod.MigrationError, "unratified SID8 bridge"):
            mod.Resolver({}, {}, bridge_by_sid={"00010110": ("D9", "110111010")})

    def test_structural_empty_and_text_can_be_data_but_not_calls(self):
        resolver = mod.Resolver({}, {})
        for code in ("000", "0000000", "1111111",
                     "111111111", "0000000000",
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

    def test_repl_core_uses_ratified_ukr_d9_string_predicate_projection(self):
        source = (ROOT / "lib/repl-core.lisp").read_text(encoding="utf-8")
        self.assertNotIn("текст?", source)
        self.assertIn("рядок?", source)
        self.assertEqual(self.my.get("рядок?"), ("110100110", "D9"))
        projection, resolver = self.migrate('(рядок? "x")')
        self.assertNotIn("110100110", projection.split())
        words, origin = resolver.head(mod.Tok("ATOM", "рядок?", 0), self.text7)
        self.assertEqual(origin, "d7-resident-head")
        self.assertNotIn("110100110", words)
        with self.assertRaisesRegex(mod.MigrationError, "legacy-unmapped"):
            self.migrate('(текст? "x")')

    def test_ukrainian_apostrophe_is_identifier_data_not_a_quote(self):
        # lib/forward.lisp uses робоча-пам'ять; splitting the
        # apostrophe invents a QUOTE node and destroys program identity.
        source = "(визначити робоча-пам'ять (як-є ()))"
        parsed = mod.Parser(mod.tokenize(source)).parse_program()
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0].items[1].tok.text, "робоча-пам'ять")
        self.assertEqual(
            [t.kind for t in mod.tokenize("(функція (ім'я) ім'я)")],
            ["LP", "ATOM", "LP", "ATOM", "RP", "ATOM", "RP"],
        )
        self.assertEqual(
            [t.text for t in mod.tokenize("'ім'я")],
            ["'", "ім'я"],
        )
        self.assertEqual(
            [t.kind for t in mod.tokenize("'ім'я")],
            ["QUOTE", "ATOM"],
        )
        projection, _ = self.migrate("(функція (ім'я) ім'я)")
        self.assertTrue(projection.startswith("10 0010 00 "))
        self.assertEqual(projection.split()[-1], mod.D2_CLOSE)

    def test_lambda_parameter_shape_is_real_program_identity(self):
        # D4: variadic atom != one-element fixed binder list.
        # Proper, dotted and empty binders have different machine syntax.
        def binder(source):
            return mod.Parser(mod.tokenize(source)).parse_program()[0]

        bare = mod.encode_text7_identifier(
            "аргументи", self.text7, mod.Tok("ATOM", "аргументи", 0),
        )
        first = mod.encode_text7_identifier(
            "перший", self.text7, mod.Tok("ATOM", "перший", 0),
        )
        rest = mod.encode_text7_identifier(
            "решта", self.text7, mod.Tok("ATOM", "решта", 0),
        )
        self.assertEqual(
            mod.encode_lambda_params(binder("аргументи"), self.text7), bare,
        )
        self.assertEqual(
            mod.encode_lambda_params(binder("(аргументи)"), self.text7),
            [mod.D2_OPEN, *bare, mod.D2_CLOSE],
        )
        self.assertEqual(
            mod.encode_lambda_params(binder("(перший . решта)"), self.text7),
            [mod.D2_OPEN, *first, mod.D2_DOT, *rest, mod.D2_CLOSE],
        )
        self.assertEqual(
            mod.encode_lambda_params(binder("(перший решта)"), self.text7),
            [mod.D2_OPEN, *first, mod.D2_SEP, *rest, mod.D2_CLOSE],
        )
        self.assertEqual(
            mod.encode_lambda_params(binder("()"), self.text7),
            [mod.D3_EMPTY],
        )
        # Д4:1110 список є ратифікованим і не перевизначається у core/core4.
        # Синтаксис variadic binder все одно тестуємо на автономній
        # пробній формі: не прив'язуємо граматику до старого DEFINE.
        for source_name in ("lib/core.lisp", "lib/core4.lisp"):
            source = (ROOT / source_name).read_text(encoding="utf-8")
            self.assertNotIn("(визначити список (функція", source)
        program = "(визначити проба (функція аргументи аргументи))"
        projection, _ = self.migrate(program)
        words = projection.split()
        binder_words = mod.encode_text7_identifier(
            "аргументи", self.text7, mod.Tok("ATOM", "аргументи", 0),
        )
        # Точна D4 форма бере D7-атом параметра без D2-обгортки.
        self.assertIn(
            ["0010", mod.D2_SEP, *binder_words, mod.D2_SEP],
            [words[i:i + len(binder_words) + 3]
             for i in range(len(words) - len(binder_words) - 2)],
        )


        # Один машинний Lisp-атом із апострофом не має перетворитися
        # на два вузли та оператор QUOTE у параметрах реальної програми.
        observed = mod.tokenize("(функція (ім'я) ім'я)")
        self.assertEqual(
            [(tok.kind, tok.text) for tok in observed if tok.kind == "ATOM"],
            [("ATOM", "функція"), ("ATOM", "ім'я"), ("ATOM", "ім'я")],
        )
        self.assertEqual(
            [(tok.kind, tok.text) for tok in mod.tokenize("'ім'я")],
            [("QUOTE", "'"), ("ATOM", "ім'я")],
        )

    def test_full_d4_lambda_keeps_variadic_and_dotted_semantics(self):
        samples = (
            "(функція аргументи аргументи)",
            "(функція (аргументи) аргументи)",
            "(функція (перший . решта) решта)",
            "(функція (перший решта) решта)",
            "(функція () (як-є ()))",
        )
        projections = []
        for source in samples:
            with self.subTest(source=source):
                projection, _ = self.migrate(source)
                words = projection.split()
                self.assertEqual(words[0], mod.D2_OPEN)
                self.assertEqual(words[1], "0010")
                self.assertEqual(words[-1], mod.D2_CLOSE)
                projections.append(tuple(words))
        self.assertEqual(len(set(projections)), len(samples))
        self.assertIn(mod.D2_DOT, projections[2])
        # The strict parameter list cannot acquire a REST tail implicitly.
        self.assertNotIn(mod.D2_DOT, projections[3])

    def test_migrate_file_defaults_to_t5m(self):
        self.assertEqual(
            inspect.signature(mod.migrate_file).parameters["codec"].default,
            "t5m",
        )

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

    def test_exact_core_callable_d8_name_maps_inside_d1_24_plus_frame(self):
        out,resolver=self.migrate("(string->symbol x)\n")
        self.assertIn("11101101", out.split())
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_ukrainian_d8_resident_without_mechanism_keeps_d7_call_name(self):
        from domain_tables import read_domain_table
        resolver = mod.Resolver(self.my, self.upper)
        candidate = next(
            row for row in read_domain_table(ROOT / "lib/domains/d8.lisp")
            if row.bits not in mod.CORE_OPERATION_D8
            and row.uk and self.my.get(row.uk) == (row.bits, "D8")
        )
        words, origin = resolver.head(mod.Tok("ATOM", candidate.uk, 0), self.text7)
        self.assertEqual(words[0], "10")
        self.assertEqual(words[-1], "01")
        self.assertNotIn(candidate.bits, words)
        self.assertEqual(origin, "d7-resident-head")
        self.assertEqual(self.my[candidate.uk], (candidate.bits, "D8"))

    def test_d10_resident_names_keep_identity_but_not_unproved_callability(self):
        foundation = mod.load_foundation(FOUNDATION)
        my, upper, _bridge = mod.build_three_pass_maps(
            foundation, DOMAIN_SURFACES, SEMANTIC_GENERATED,
            SEMANTIC_REGISTRY, NECESSARY,
        )
        resolver = mod.Resolver(my, upper)
        text7 = mod.build_text7(foundation, TEXT7)
        expected = {
            "входження-тотожність": "0001100010",
            "асоціація-тотожність": "0001011001",
        }
        for spelling, bits in expected.items():
            with self.subTest(spelling=spelling):
                self.assertEqual(my.get(spelling), (bits, "D10"))
                self.assertFalse(resolver._has_concrete_callable((bits, "D10")),
                                 "D10 Lisp DEFINE не є native machine opcode")
                words, origin = resolver.head(mod.Tok("ATOM", spelling, 0), text7)
                self.assertEqual(origin, "d7-resident-head")
                self.assertEqual(words[0], "10")
                self.assertEqual(words[-1], "01")
                self.assertNotIn(bits, words)
                with self.assertRaisesRegex(
                    mod.MigrationError, r"D10 .*потрібна названа чинна проєкція"
                ):
                    resolver.head(mod.Tok("ATOM", bits, 0))

    def test_pass3_lisp15_car(self):
        out,resolver=self.migrate("(CAR x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_pass3_lisp15_arithmetic(self):
        out,resolver=self.migrate("(PLUS x y)\n")
        self.assertTrue(out.startswith("10 01010 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_quoted_strings_are_distinct_d7_text_data(self):
        alpha, _ = self.migrate('(сполучити "alpha")\n')
        beta, _ = self.migrate('(сполучити "beta")\n')
        self.assertNotEqual(alpha, beta)
        for encoded in (alpha, beta):
            words = encoded.split()
            self.assertIn(mod.D2_OPEN, words)
            self.assertIn(mod.D2_CLOSE, words)
            self.assertTrue(all(set(word) <= {"0", "1"} for word in words))

    def test_string_escapes_preserve_d7_control_words(self):
        # Source lowering follows the SENS reader rather than silently
        # replacing \n, \t or \r with the printable n, t or r glyph.
        for escape, scalar, exact_word in (
            (r"\n", "\n", "0001010"),
            (r"\t", "\t", "0001001"),
            (r"\r", "\r", "0001101"),
        ):
            with self.subTest(escape=escape):
                escaped, _ = self.migrate('(сполучити "a' + escape + 'b")')
                literal_control, _ = self.migrate('(сполучити "a' + scalar + 'b")')
                wrong_printable, _ = self.migrate('(сполучити "a' + escape[-1] + 'b")')
                self.assertEqual(escaped, literal_control)
                self.assertNotEqual(escaped, wrong_printable)
                self.assertIn(exact_word, escaped.split())

    def test_string_literals_never_fold_identifier_glyphs(self):
        # Лише імена допускають клавіатурне скорочення; рядки — дані.
        for raw, folded in (("a—b", "a-b"), ("a–b", "a-b"),
                            ("a─b", "a-b"), ("a═b", "a=b")):
            with self.subTest(raw=raw):
                token = mod.Tok("ATOM", raw, 0)
                self.assertEqual(
                    mod.text7_encode(raw, self.text7, token),
                    mod.text7_encode(folded, self.text7, token),
                )
                # Без захисту literal ставав a-b/a=b без жодної помилки.
                with self.assertRaisesRegex(mod.MigrationError, "cannot encode"):
                    self.migrate('(сполучити "' + raw + '")')

    def test_quoted_sanskrit_text_is_not_transliterated_as_identifier(self):
        # Сама IAST->деванагарі транслітерація змінює рядковий літерал.
        with self.assertRaisesRegex(mod.MigrationError, "cannot encode"):
            self.migrate('(сполучити "śūnya")')

    def test_sid8_bridge_cannot_authorize_any_executable_head(self):
        with self.assertRaisesRegex(mod.MigrationError, "unratified SID8 bridge"):
            mod.Resolver(self.my, self.upper,
                         bridge_by_sid={"01001011": ("D9", "110101001")})

    def test_d9_unifier_resident_is_not_implicitly_executable(self):
        identity = self.my["уніфікувати"]
        self.assertEqual(identity, ("101010000", "D9"))
        resolver = mod.Resolver(self.my, self.upper)
        self.assertNotIn(identity[0], resolver.d9_callable_bits,
                         "unify Lisp definition != Core4 native D9 opcode")
        words, origin = resolver.head(
            mod.Tok("ATOM", "уніфікувати", 0), self.text7,
        )
        self.assertEqual(origin, "d7-resident-head")
        self.assertEqual(words[0], "10")
        self.assertNotIn(identity[0], words)
        self.assertEqual(words[-1], "01")

    def test_core4_defined_d9_closure_preserves_lexical_d7_not_native_opcode(self):
        resolver = mod.Resolver(self.my, self.upper)
        spelling, bits = "додати-нові", "001000101"
        self.assertEqual(self.my[spelling], (bits, "D9"))
        self.assertFalse(resolver._has_concrete_callable((bits, "D9")))
        words, origin = resolver.head(mod.Tok("ATOM", spelling, 0), self.text7)
        self.assertEqual(origin, "d7-resident-head")
        self.assertEqual(words[0], "10")
        self.assertEqual(words[-1], "01")
        self.assertNotIn(bits, words)
        projection = mod.migrate_file("(додати-нові x)\n", resolver, self.text7)
        self.assertNotIn(bits, projection.split())
        self.assertTrue(projection.startswith("10 10 "))
        with self.assertRaisesRegex(mod.MigrationError, "D9 .*потрібна названа чинна проєкція"):
            resolver.head(mod.Tok("ATOM", "111111111", 0))

    def test_comments_disappear(self):
        a,_=self.migrate("; top\n(CAR #| nested #| inner |# body |# x)\n")
        b,_=self.migrate("(CAR x)\n")
        self.assertEqual(a,b)

    def test_block_comment_keeps_executable_atoms_separate(self):
        # Раніше x#|...|#y ставав одним атомом xy, змінюючи програму.
        a, _ = self.migrate("(CONS x#| вкладений #| фрагмент |# текст |#y)\n")
        b, _ = self.migrate("(CONS x y)\n")
        self.assertEqual(a, b)
        # Символи коментаря в лапках належать рядку даних.
        self.assertEqual(
            mod.strip_comments('"x#|не-коментар|#y"'),
            '"x#|не-коментар|#y"',
        )

    def test_unknown_ukrainian_name_is_carried_as_opaque_text7_data(self):
        out,resolver=self.migrate("(невідома-функція ікс)\n")
        self.assertTrue(all(set(word) <= {"0", "1"} for word in out.split()))
        self.assertNotIn("невідома-функція", out)
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

    def test_decimal_number_in_call_head_is_not_reclassified_as_d2(self):
        for number in ("1", "10"):
            with self.subTest(number=number), self.assertRaisesRegex(
                mod.MigrationError, "D24\\+ numeric value.*not callable"
            ):
                self.migrate(f"({number} x)\n")

    def test_d7_data_and_unnamed_d9_bits_are_not_projected_as_call_heads(self):
        # Numeric-looking source atoms are decimal D24+ data. Test physical
        # domain coordinates at the resolver boundary, not as Lisp source.
        resolver = mod.Resolver(self.my, self.upper)
        for word in ("0000000", "1111111"):
            with self.subTest(domain="D7", word=word):
                with self.assertRaisesRegex(
                    mod.MigrationError, "фонемна/текстова ідентичність"
                ):
                    resolver.head(mod.Tok("ATOM", word, 0))
        for word in ("111111111",):
            with self.subTest(domain="D9", word=word):
                with self.assertRaisesRegex(
                    mod.MigrationError, "D9 .*потрібна названа чинна проєкція"
                ):
                    resolver.head(mod.Tok("ATOM", word, 0))

    def test_d9_ukrainian_projection_keeps_all_residents_as_identity_not_admission(self):
        from domain_tables import read_domain_table
        foundation = mod.load_foundation(FOUNDATION)
        residents = set(foundation["domains"]["D9"]["residents"])
        self.assertEqual(len(residents), 512)
        rows = read_domain_table(ROOT / "lib/domains/d9.lisp")
        covered = {
            row.bits for row in rows
            if (row.uk and self.my.get(row.uk) == (row.bits, "D9"))
            or (row.ukr and self.my.get(row.ukr) == (row.bits, "D9"))
        }
        self.assertEqual(covered, residents)
        # The domain table is still an authority for quoted data and
        # surface lookup, but never a free callable D9 mechanism.
        resolver = mod.Resolver(self.my, self.upper, d9_residents=residents)
        self.assertFalse(resolver._has_concrete_callable(("000100001", "D9")),
                         "FS closure not a native D9 opcode")
        for spelling, bits in [("порожній-вміст-сховище", "000100001")]:
            with self.subTest(spelling=spelling):
                self.assertEqual(self.my[spelling], (bits, "D9"))
                words, origin = resolver.head(
                    mod.Tok("ATOM", spelling, 0), self.text7,
                )
                self.assertEqual(origin, "d7-resident-head")
                self.assertEqual(words[0], "10")
                self.assertEqual(words[-1], "01")
                self.assertNotIn(bits, words)
        # An admitted runtime-native D9 string operation retains exact bits.
        admitted, origin = resolver.head(
            mod.Tok("ATOM", "рядок-перший", 0), self.text7,
        )
        self.assertEqual(admitted, ["110101011"])
        self.assertEqual(origin, "pass2-my-lisp")

    def test_decimal_digit_sequences_in_lisp_data_are_not_domain_addresses(self):
        # Human Lisp numbers are decimal D24+ values; their spelling length
        # must not turn them into D7/D9 coordinates.
        zero = "0" * 24
        out, _ = self.migrate("(сполучити 0000000 000000000)\n")
        self.assertEqual(out, f"10 111 00 {zero} 00 {zero} 01\n")

    def test_decimal_human_projection_never_confuses_numbers_with_binary_domain_words(self):
        # .lisp is the human projection: decimal glyphs are numbers, while
        # structural D2 controls are generated from Lisp punctuation.
        for spelling, expected in (("00", 0), ("01", 1), ("10", 10),
                                   ("11", 11)):
            with self.subTest(spelling=spelling):
                projection = mod.migrate_file(
                    f"(CONS {spelling} x)\n", mod.Resolver(self.my, self.upper),
                    self.text7,
                )
                self.assertIn(f"{expected:024b}", projection.split())

    def test_human_decimal_integer_lowers_as_exact_d24_word(self):
        resolver = mod.Resolver({}, {})
        def expected_word(value):
            width = 24
            while not (-(1 << (width - 1)) <= value < (1 << (width - 1))):
                width *= 2
            return width, f"{value % (1 << width):0{width}b}"

        for value in (0, 1, 10, 1564, (1 << 23) - 1, 1 << 23, -1, -(1 << 23), -(1 << 23) - 1):
            width, expected = expected_word(value)
            low = mod.migrate_file(
                f"(CAR {value})\n", resolver, self.text7, codec="t5m",
            )
            self.assertIn(expected, low.split())
            self.assertEqual(len(expected), width)

    def test_numeric_admission_is_independent_of_physical_codec_and_decode(self):
        source = "(CAR 10)\n"
        t5_projection = mod.migrate_file(
            source, mod.Resolver({}, {}), self.text7, codec="t5",
            source_surface="укр",
        )
        t5m_projection = mod.migrate_file(
            source, mod.Resolver({}, {}), self.text7, codec="t5m",
            source_surface="укр",
        )
        self.assertEqual(t5_projection, t5m_projection)

        expected_ten = "000000000000000000001010"
        self.assertIn(expected_ten, t5m_projection.split())
        # Physical decode returns the exact semantic words, without assigning
        # D24+ meaning or re-running decimal-literal lowering.
        words = t5m_projection.split()
        decoded_words = mod.decode_t5m_bytes(
            mod.encode_t5m_projection(t5m_projection)
        )
        self.assertEqual(decoded_words, words)
        self.assertIn(expected_ten, decoded_words)

    def test_human_decimal_fraction_reduces_exactly(self):
        cases = {
            "1.5": (3, 2),
            "+1.5": (3, 2),
            "2.1564": (5391, 2500),
            "2.15648": (6739, 3125),
            "-2.1564": (-5391, 2500),
            "-0.5": (-1, 2),
            "0.125": (1, 8),
            "1.50": (3, 2),
            "1.0": (1, 1),
            "0.000": (0, 1),
            "-0.000": (0, 1),
        }
        for spelling, (numerator, denominator) in cases.items():
            with self.subTest(spelling=spelling):
                resolver = mod.Resolver({}, {})
                projection = mod.migrate_file(
                    f"(CAR {spelling})\n", resolver, self.text7, codec="t5m",
                )
                width = 24
                while not (-(1 << (width - 1)) <= numerator < (1 << (width - 1))):
                    width *= 2
                expected = [f"{numerator % (1 << width):0{width}b}"]
                if denominator != 1:
                    expected.append(f"{denominator:0{width}b}")
                words = projection.split()
                start = next(
                    index for index, word in enumerate(words)
                    if word == expected[0]
                )
                self.assertEqual(words[start:start + len(expected)], expected)
                packed = mod.encode_t5m_projection(projection)
                self.assertEqual(mod.decode_t5m_bytes(packed), words)

    def test_t5m_fraction_uses_adjacent_words_and_distinct_numbers_use_d2(self):
        # 2.15648 is finite decimal input, reduced exactly to 6739/3125.
        # These literal 24-bit words are independently checked fixtures; T5M
        # must transport them unchanged rather than reinterpret their meaning.
        resolver = mod.Resolver({}, {})
        projection = mod.migrate_file(
            "(CAR 2.15648)\n", resolver, self.text7, codec="t5m",
        )
        expected = [
            "000000000001101001010011",  # D24 +6739
            "000000000000110000110101",  # D24 +3125
        ]
        words = projection.split()
        start = next(i for i, word in enumerate(words) if word == expected[0])
        self.assertEqual(words[start:start + 2], expected)
        packed = mod.encode_t5m_projection(projection)
        self.assertEqual(mod.decode_t5m_bytes(packed), words)

        # The ratio 1546/8464 is represented by adjacent D24+ component
        # words, not by passing a slash token to T5M. Two distinct integers
        # instead get the structural D2 separator in a Lisp list.
        numerator = "000000000000011000001010"  # D24 1546
        denominator = "000000000010000100010000"  # D24 8464
        ratio_words = [numerator, denominator]
        self.assertEqual(
            mod.decode_t5m_bytes(
                mod.encode_t5m_projection(" ".join(ratio_words))
            ),
            ratio_words,
        )
        separate_numbers = mod.migrate_file(
            "(CAR '(1546 8464))\n", mod.Resolver({}, {}),
            self.text7, codec="t5m",
        ).split()
        start = next(i for i, word in enumerate(separate_numbers)
                     if word == numerator)
        self.assertEqual(separate_numbers[start:start + 3],
                         [numerator, "00", denominator])

        # Without an explicit Ukrainian source surface, comma keeps the
        # Lisp reader's unquote meaning and is not treated as a decimal mark.
        with self.assertRaisesRegex(
            mod.MigrationError, "comma/unquote syntax has no admitted migration law"
        ):
            mod.migrate_file(
                "(CAR 2,15648)\n", mod.Resolver({}, {}),
                self.text7, codec="t5m",
            )

    def test_t5m_ukrainian_decimal_comma_lowers_exactly_without_changing_unquote(self):
        expected = [
            "000000000000100110100011",  # D24 +2467
            "000000000000001111101000",  # D24 +1000
        ]
        for source_surface in ("ук", "укр"):
            with self.subTest(source_surface=source_surface):
                projection = mod.migrate_file(
                    "(CAR 2,467)\n", mod.Resolver({}, {}), self.text7,
                    codec="t5m", source_surface=source_surface,
                )
                words = projection.split()
                start = next(i for i, word in enumerate(words)
                             if word == expected[0])
                self.assertEqual(words[start:start + 2], expected)
                self.assertEqual(
                    mod.decode_t5m_bytes(
                        mod.encode_t5m_projection(projection)
                    ),
                    words,
                )

        # Only an explicitly selected Ukrainian surface gives decimal meaning
        # to comma-between-digits. Other commas keep the Lisp reader's law.
        with self.assertRaisesRegex(
            mod.MigrationError, "comma/unquote syntax has no admitted migration law"
        ):
            mod.migrate_file(
                "(CAR ,x)\n", mod.Resolver({}, {}), self.text7,
                codec="t5m", source_surface="укр",
            )
        with self.assertRaisesRegex(
            mod.MigrationError, "comma/unquote syntax has no admitted migration law"
        ):
            mod.migrate_file(
                "(CAR 2,467)\n", mod.Resolver({}, {}), self.text7, codec="t5m"
            )

    def test_t5m_decimal_fraction_does_not_accept_unsupported_numeric_syntax(self):
        resolver = mod.Resolver({}, {})
        for literal in ("1/2", "2e3", "#d3"):
            with self.subTest(literal=literal), self.assertRaisesRegex(
                mod.MigrationError, "ratios, exponents, and explicit numeric spellings"
            ):
                mod.migrate_file(
                    f"(CAR {literal})\n", resolver, self.text7, codec="t5m",
                )

    def test_ukr_source_rejects_nonkeyboard_decimal_digits(self):
        # No Unicode \d shortcut: mathematical digits in Ukrainian Lisp are 0–9.
        for spelling in ("١", "١,٢", "２", "५"):
            with self.subTest(spelling=spelling), self.assertRaisesRegex(
                mod.MigrationError, "non-keyboard decimal digit"
            ):
                mod.migrate_file(
                    f"(CAR {spelling})\n", mod.Resolver({}, {}), self.text7,
                    codec="t5m", source_surface="укр",
                )

    def test_ukr_comments_and_strings_do_not_act_as_numeric_program_atoms(self):
        original = mod.migrate_file(
            "(перше ())\n", mod.Resolver(self.my, self.upper), self.text7,
            codec="t5m", source_surface="укр",
        )
        for note in (
            "; тут ١٢٣ не операнди\n(перше ())\n",
            "#| інертний запис ५ #| вкладений ２ |# |#\n(перше ())\n",
            "(перше ()) ; значення ١,٢ належить коментареві",
        ):
            with self.subTest(note=note):
                actual = mod.migrate_file(
                    note, mod.Resolver(self.my, self.upper), self.text7,
                    codec="t5m", source_surface="укр",
                )
                self.assertEqual(actual, original)

    def test_decimal_zero_is_not_guessed_from_token_width(self):
        for width in (24, 48, 96):
            with self.subTest(width=width):
                projection = mod.migrate_file(
                    f"(CAR {'0' * width})\n", mod.Resolver(self.my, self.upper),
                    self.text7,
                )
                self.assertIn("0" * 24, projection.split())

    def test_numeric_zero_one_and_101_are_d24_values_in_human_projection(self):
        for spelling, value in (("0", 0), ("1", 1), ("101", 101)):
            with self.subTest(spelling=spelling):
                projection = mod.migrate_file(
                    f"(CAR {spelling})\n", mod.Resolver(self.my, self.upper),
                    self.text7,
                )
                self.assertIn(f"{value:024b}", projection.split())

        for spelling, bits in (("ні", "0"), ("так", "1")):
            projection = mod.migrate_file(
                f"(CAR {spelling})\n", mod.Resolver(self.my, self.upper),
                self.text7, source_surface="укр",
            )
            self.assertIn(bits, projection.split())

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
        out,_=self.migrate("(сполучити ікс ігрек)\n")
        x = mod.frame_text7(
            mod.text7_encode("ікс", self.text7, mod.Tok("ATOM", "ікс", 0)),
            mod.Tok("ATOM", "ікс", 0),
        )
        y = mod.frame_text7(
            mod.text7_encode("ігрек", self.text7, mod.Tok("ATOM", "ігрек", 0)),
            mod.Tok("ATOM", "ігрек", 0),
        )
        self.assertEqual(out, " ".join(["10", "111", "00", *x, "00", *y, "01"]) + "\n")

    def test_all_emitted_structural_control_is_d2_and_empty_is_d3_value(self):
        out,_=self.migrate("(CONS () 1)\n")
        words=out.split()
        controls=[word for word in words if len(word)==2]
        self.assertTrue(controls)
        self.assertTrue(all(word in {"00","01","10","11"} for word in controls))
        self.assertIn("000",words)
        self.assertEqual(words.count("000"),1)

    def test_same_basename_gets_sens_extension_without_directory_collision(self):
        self.assertEqual(str(mod.sens_destination(Path("tasks.lisp"))), "tasks.sens")
        self.assertEqual(str(mod.sens_destination(Path("tasks/pending.lisp"))),
                         "tasks/pending.sens")
        self.assertEqual(str(mod.sens_destination(Path("lib/sse4.1.lisp"))),
                         "lib/sse4.1.sens")
        self.assertEqual(str(mod.sens_destination(Path("foo.lisp"))), "foo.sens")

    def test_opaque_unknown_name_has_valid_t5_physical_roundtrip(self):
        projection,_ = self.migrate("(невідома-функція ікс)\n")
        physical = mod.encode_projection(projection)
        self.assertEqual(mod.decode_bytes(physical), projection.split())
        self.assertEqual(mod.decode_bytes(mod.encode_projection("000\n")), ["000"])

    def test_main_writes_binary_carriers_for_opaque_ukrainian_names(self):
        with tempfile.TemporaryDirectory() as td:
            temp = Path(td)
            root = temp / "inputs"
            root.mkdir()
            (root / "good.lisp").write_text("()\n", encoding="utf-8")
            (root / "tasks-root.lisp").write_text("()\n", encoding="utf-8")
            (root / "tasks").mkdir()
            (root / "tasks" / "more.lisp").write_text("()\n", encoding="utf-8")
            (root / "unresolved.lisp").write_text(
                "(невідома-функція ікс)\n", encoding="utf-8"
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
                "--codec", "t5",
            ]
            subprocess.run(args, check=True, capture_output=True, text=True)
            self.assertTrue((out / "good.sens").is_file())
            self.assertTrue((out / "tasks-root.sens").is_file())
            self.assertTrue((out / "tasks" / "more.sens").is_file())
            self.assertTrue((out / "unresolved.sens").is_file())
            self.assertEqual((out / "good").read_bytes(), b"000\n")
            self.assertFalse((out / "good.lisp").exists())
            self.assertEqual(mod.decode_bytes((out / "good.sens").read_bytes()),
                             ["000"])
            self.assertEqual((root / "good.lisp").read_text(), "()\n")
            result = json.loads(report.read_text())
            self.assertEqual(result["summary"]["files_written"], 4)
            self.assertEqual(result["summary"]["files_blocked"], 0)
            unresolved = next(row for row in result["files"]
                              if row["path"] == "unresolved.lisp")
            self.assertFalse(unresolved["semantic_admitted"])
            self.assertTrue(result["file_format"]["physical"].startswith("binary"))
            self.assertEqual(result["naming_law"].split(" -> ")[1].split(";")[0],
                             "OUT/name.sens")
            # Never silently overwrite the exact .sens target on rerun.
            again = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertEqual((out / "good.sens").read_bytes(),
                             mod.encode_projection("000\n"))
            # Explicitly return to source/manifest workflow before a rerun.
            self.assertTrue((root / "tasks-root.lisp").exists())

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

    def test_partial_t5m_preview_reports_blocked_without_hiding_valid_program(self):
        # Пакет з коректною і некоректною формою не може заявити
        # повне завершення міграції за успішним елементом.
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "in"
            src.mkdir()
            (src / "справне.lisp").write_text(
                "; коментар поза програмою\n()\n", encoding="utf-8",
            )
            (src / "несправне.lisp").write_text(
                "(незавершене\n", encoding="utf-8",
            )
            out = base / "out"
            report = base / "report.json"
            run = subprocess.run([
                sys.executable, str(SCRIPT), str(src),
                "--out", str(out), "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--text7", str(TEXT7), "--report", str(report),
                "--dry-run", "--codec", "t5m", "--source-surface", "укр",
            ], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            evidence = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(evidence["summary"]["files_would_write"], 1)
            self.assertEqual(evidence["summary"]["files_blocked"], 1)
            self.assertEqual(evidence["summary"]["files_not_program"], 0)
            self.assertFalse(evidence["physical_batch_complete"])
            self.assertFalse(evidence["migration_complete"])
            self.assertFalse(evidence["semantic_admitted"])
            self.assertFalse(out.exists())
            self.assertIn(
                "несправне.lisp",
                [row["path"] for row in evidence["files"]
                 if row["status"] == "blocked"],
            )


    def test_cli_dry_run_accepts_ukr_decimal_comma(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "in"
            src.mkdir()
            (src / "fraction.lisp").write_text("(CAR 2,467)\n", encoding="utf-8")
            out = base / "out"
            report = base / "report.json"
            process = subprocess.run([
                sys.executable, str(SCRIPT), str(src), "--out", str(out),
                "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY), "--text7", str(TEXT7),
                "--report", str(report), "--dry-run", "--codec", "t5m",
                "--source-surface", "укр",
            ], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            state = json.loads(report.read_text())
            self.assertEqual(state["summary"]["files_would_write"], 1)
            self.assertEqual(state["summary"]["files_blocked"], 0)
            self.assertEqual(state["file_format"]["source_surface"], "укр")
            self.assertFalse(out.exists())

    def test_main_t5m_mints_ukrainian_decimal_comma_fraction_through_zig(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "in"
            src.mkdir()
            (src / "fraction.lisp").write_text("(CAR 2,467)\n", encoding="utf-8")
            out = base / "out"
            report = base / "report.json"
            args = [
                sys.executable, str(SCRIPT), str(src), "--out", str(out),
                "--foundation", str(FOUNDATION),
                "--domain-surfaces", str(DOMAIN_SURFACES),
                "--semantic-generated", str(SEMANTIC_GENERATED),
                "--semantic-registry", str(SEMANTIC_REGISTRY),
                "--necessary-forms", str(NECESSARY),
                "--text7", str(TEXT7), "--report", str(report),
                "--codec", "t5m", "--source-surface", "укр",
            ]
            process = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            projection = (out / "fraction").read_text(encoding="ascii")
            payload = (out / "fraction.sens").read_bytes()
            words = projection.split()
            expected_pair = [f"{2467:024b}", f"{1000:024b}"]
            pair_start = next(
                index for index, word in enumerate(words)
                if word == expected_pair[0]
            )
            self.assertEqual(words[pair_start:pair_start + 2], expected_pair)
            self.assertEqual(mod.decode_t5m_bytes(payload), words)
            result = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(result["summary"]["files_written"], 1)
            self.assertEqual(result["summary"]["files_blocked"], 0)
            self.assertEqual(result["physical_producer"], "PINNED_ZIG_T5M_CARRY")

    def test_unpaired_only_ignores_preexisting_sens_pairs(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "src"
            source.mkdir()
            (source / "old.lisp").write_text("()\\n".replace("\\n", "\n"), encoding="utf-8")
            (source / "paired.lisp").write_text("()\\n".replace("\\n", "\n"), encoding="utf-8")
            already = mod.encode_t5m_projection("000")
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


    def test_unpaired_only_already_paired_is_noop_without_zig(self):
        # A second migration sweep must not build Zig or fail merely because
        # no new source remains. It must not promote parity to semantic GO.
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src = base / "src"
            src.mkdir()
            lisp = src / "готове.lisp"
            sens = src / "готове.sens"
            lisp.write_text("(як-є ())\\n".replace("\\n", "\n"), encoding="utf-8")
            original = mod.encode_t5m_projection("10 001 00 000 01")
            sens.write_bytes(original)
            output = base / "mirror"
            receipt = base / "report.json"
            run = subprocess.run([
                sys.executable, str(SCRIPT), str(src),
                "--out", str(output), "--report", str(receipt),
                "--unpaired-only", "--source-surface", "укр", "--codec", "t5m",
            ], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            result = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result["summary"]["files_seen"], 0)
            self.assertEqual(result["summary"]["files_skipped_paired"], 1)
            self.assertEqual(result["summary"]["files_written"], 0)
            self.assertEqual(result["summary"]["files_blocked"], 0)
            self.assertEqual(result["physical_producer"], "NOT_INVOKED_ALREADY_PAIRED")
            self.assertFalse(result["semantic_admitted"])
            self.assertEqual(result["skipped_paired_paths"], ["готове.lisp"])
            self.assertEqual(sens.read_bytes(), original)
            self.assertFalse(output.exists())


    def test_export_trigger_uses_pinned_zig_and_native_sens_writer(self):
        # CI packaging may use Python tests, but executable .sens MUST be
        # produced by native SENS -> Zig/T5M and executed by SENS itself.
        # A renamed historical Python/JSON exporter is no longer authority.
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        guards = workflow.split("  lisp-guards:", 1)[1]
        # Поточний native AST/T5M smoke завжди збирає SENS з pinned Zig.
        # Навіть якщо визначення змінених файлів упаде, не маскувати
        # первинний RED каскадом "Zig not found" через відсутній output.
        self.assertIn("echo 'needs_zig=true' >> \"$GITHUB_OUTPUT\"", guards)
        installer = guards.split("      - uses: ./.github/actions/install-zig", 1)[1]
        installer_tail = installer.split("      - name:", 1)[0]
        self.assertNotIn("        if:", installer_tail)
        section = guards.split(
            '      - name: "ONE-SHOT — нативні SENS/Zig T5M-пари', 1
        )[1].split('      - name: "ONE-SHOT — artifact', 1)[0]
        self.assertIn("MIGRATE-LIB-TRIPLETS:", section)
        self.assertIn("cargo build --locked -p sens-cli --bin sens --bin sens-trit", section)
        self.assertIn("scripts/refresh-verified-t5m-pair.sh", section)
        self.assertIn('target/debug/sens-trit "${bindings[@]}"', section)
        self.assertIn("NATIVE-RESULTS.tsv", section)
        self.assertIn("NATIVE_REJECTED", section)
        self.assertNotIn("python3 ", section)
        self.assertNotIn("migrate-three-pass.py", section)


    def test_current_nonprogram_sha_pins_are_real_and_d10_d11_are_data(self):
        # The owner-reviewed current manifests remain SHA-pinned, not a
        # permanent historical 2026-10-08 blocker for every live program.
        for _, name, count in mod.NONPROGRAM_MANIFESTS:
            content = (ROOT / name).read_bytes()
            sha = mod.hashlib.sha1(
                b"blob " + str(len(content)).encode("ascii") + b"\0" + content
            ).hexdigest()
            self.assertEqual(mod.NONPROGRAM_MANIFEST_BLOB_SHA[name], sha, name)
            record = json.loads(content)
            self.assertEqual(len(record["entries"]), count, name)
            self.assertIs(record["automatic_sens_companion"], False)
        for domain in ("d10", "d11"):
            with self.assertRaisesRegex(mod.SensT5Error, "NONPROGRAM_DATA_NOT_EXECUTABLE"):
                mod.reject_reviewed_nonprogram_source(ROOT / f"lib/domains/{domain}.lisp")


    def test_evolving_d11_table_is_data_without_historical_sha_lock(self):
        # Поточний D11 — тестовий словник, не виконуваний SENS і не
        # ратифікація. Старий запис blob у маніфесті не блокує дані.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "lib/domains/d11.lisp"
            source.parent.mkdir(parents=True)
            current = (ROOT / "lib/domains/d11.lisp").read_text(encoding="utf-8")
            source.write_text(current, encoding="utf-8")
            with self.assertRaisesRegex(mod.SensT5Error, "NONPROGRAM_DATA_NOT_EXECUTABLE"):
                mod.reject_reviewed_nonprogram_source(source, root)
            # Стороння програма не може сховатися після таблиці.
            source.write_text(current + "\n(визначити підміна так)\n", encoding="utf-8")
            with self.assertRaisesRegex(mod.SensT5Error, "NONPROGRAM_D11_TABLE_INVALID"):
                mod.reject_reviewed_nonprogram_source(source, root)

    def test_reviewed_data_and_comment_only_are_not_failed_programs(self):
        # Both are read-only positive classifications, not executable .sens.
        for name, reason in (("lib/domains/d4.lisp", "NONPROGRAM_DATA_NOT_EXECUTABLE"),
                             ("lib/surface/uk.lisp", "NONPROGRAM_COMMENT_ONLY")):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp:
                out = Path(temp)
                proc = subprocess.run([
                    sys.executable, str(SCRIPT), str(ROOT / name),
                    "--out", str(out / "pairs"), "--report", str(out / "report.json"),
                    "--dry-run", "--codec", "t5m",
                ], capture_output=True, text=True, check=False, timeout=30)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
                report = json.loads((out / "report.json").read_text(encoding="utf-8"))
                self.assertEqual(report["summary"]["files_not_program"], 1)
                self.assertEqual(report["summary"]["files_blocked"], 0)
                self.assertEqual(report["summary"]["files_would_write"], 0)
                self.assertEqual(report["files"][0]["status"], "not-program")
                self.assertIn(reason, report["files"][0]["reason"])
                self.assertIs(report["semantic_admitted"], False)
                self.assertIs(report["migration_complete"], False)
                self.assertFalse((out / "pairs").exists())


    def test_malformed_comment_is_a_real_error_not_nonprogram(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            src = base / "broken.lisp"
            src.write_text("#| коментар без завершення", encoding="utf-8")
            run = subprocess.run([
                sys.executable, str(SCRIPT), str(src), "--dry-run",
                "--out", str(base / "pairs"), "--report", str(base / "report.json"),
            ], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
            state = json.loads((base / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["files_blocked"], 1)
            self.assertEqual(state["summary"]["files_not_program"], 0)
            self.assertEqual(state["files"][0]["status"], "blocked")
            self.assertIn("unterminated block comment", state["files"][0]["reason"])


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
                             mod.encode_t5m_projection("000"))
            report = base / "mirror.report.json"
            self.assertTrue(report.is_file())
            state = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(state["summary"]["files_written"], 1)
            self.assertEqual(state["summary"]["files_seen"], 1)
            self.assertEqual(source.read_text(), "()\n")


    def test_global_define_shadows_builtin_surface_with_bound_text7_frame(self):
        # The Ukrainian source-defined name shadows the admitted D3 surface.
        source="(визначити перше (функція () 1))\n(перше)\n"
        projection,resolver=self.migrate(source)
        frame=mod.frame_text7(
            mod.text7_encode("перше",self.text7,mod.Tok("ATOM","перше",0)),
            mod.Tok("ATOM","перше",0),
        )
        self.assertGreaterEqual(projection.count(" ".join(frame)),2)
        self.assertEqual(resolver.counts["pass4-text7-global"],1)

    def test_global_text7_call_head_uses_same_frame_as_define_target(self):
        source="""\
(визначити власна-функція
  (функція ()
    ()))
(власна-функція)
"""
        projection,resolver=self.migrate(source)
        frame=mod.frame_text7(
            mod.text7_encode("власна-функція",self.text7,mod.Tok("ATOM","власна-функція",0)),
            mod.Tok("ATOM","власна-функція",0),
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
        # The Ukrainian source uses named admitted surfaces; it must not need
        # machine-bit heads in the Lisp projection.
        self.assertGreater(resolver.counts["pass2-my-lisp"], 0)
        self.assertEqual(source.count("(визначити "), 6)
        self.assertNotRegex(source, r"\(\s*[01]{2,}\s")

        for name in (
            "машинний-блок",
            "порожній-машинний-блок",
            "блок-з-однієї-форми",
            "додати-форму-до-блоку",
            "поєднати-машинні-блоки",
            "форми-машинного-блоку",
        ):
            frame=mod.frame_text7(
                mod.text7_encode(name,self.text7,mod.Tok("ATOM",name,0)),
                mod.Tok("ATOM",name,0),
            )
            self.assertIn(
                " ".join(frame),
                projection,
                f"missing exact current binding frame for {name}",
            )

        forms_frame=mod.frame_text7(
            mod.text7_encode("форми",self.text7,mod.Tok("ATOM","форми",0)),
            mod.Tok("ATOM","форми",0),
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
(визначити перша-функція
  (функція (перше)
    (перше)))
"""
        projection,resolver=self.migrate(source)
        words=projection.split()
        self.assertTrue(all(set(word) <= {"0","1"} for word in words))
        first_frame=mod.frame_text7(
            mod.text7_encode("перше",self.text7,mod.Tok("ATOM","перше",0)),
            mod.Tok("ATOM","перше",0),
        )
        self.assertGreaterEqual(projection.count(" ".join(first_frame)),2)


class ActiveContestSourceInventoryTests(unittest.TestCase):
    def test_migrator_never_reimports_superseded_lisp_as_executable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            winner = root / "benchmarks/contest-uk/winner.lisp"
            old = root / "benchmarks/contest-uk/superseded/older.lisp"
            winner.parent.mkdir(parents=True)
            old.parent.mkdir(parents=True)
            winner.write_text("(перше ())\n", encoding="utf-8")
            old.write_text("(перше ())\n", encoding="utf-8")
            self.assertEqual(list(mod.source_files(root)), [winner])


if __name__=="__main__":
    unittest.main()
