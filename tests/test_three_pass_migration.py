#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"migrate-three-pass.py"
SPEC=importlib.util.spec_from_file_location("three_pass",SCRIPT)
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=mod
SPEC.loader.exec_module(mod)

FOUNDATION=ROOT/"knowledge"/"d1-d7-foundation.json"
DOMAIN_SURFACES=ROOT/"crates"/"sens"/"src"/"domain_surface_registry_generated.rs"
SEMANTIC_GENERATED=ROOT/"crates"/"sens"/"src"/"semantic_registry_generated.rs"
SEMANTIC_REGISTRY=ROOT/"crates"/"sens"/"src"/"semantic_registry.rs"
NECESSARY=ROOT/"crates"/"sens"/"src"/"eval"/"necessary_forms_generated.rs"

class ThreePassMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=mod.load_foundation(FOUNDATION)
        cls.legacy,cls.my,cls.upper=mod.build_three_pass_maps(
            data,DOMAIN_SURFACES,SEMANTIC_GENERATED,SEMANTIC_REGISTRY,NECESSARY
        )

    def resolver(self):
        return mod.Resolver(self.legacy,self.my,self.upper)

    def migrate(self,source):
        resolver=self.resolver()
        return mod.migrate_file(source,resolver),resolver

    def test_empty_list_is_compact_d3_empty(self):
        out,_=self.migrate("()\n")
        self.assertEqual(out,"000\n")

    def test_nonempty_list_uses_d2_structure(self):
        out,_=self.migrate("(CAR ())\n")
        self.assertEqual(out,"10 100 00 000 01\n")

    def test_pass1_legacy_sid8_car(self):
        out,resolver=self.migrate("(00000101 ())\n")
        self.assertEqual(out,"10 100 00 000 01\n")
        self.assertEqual(resolver.counts["pass1-sens8"],1)

    def test_pass2_my_lisp_car(self):
        out,resolver=self.migrate("(car ())\n")
        self.assertEqual(out,"10 100 00 000 01\n")
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass2_my_lisp_predicate_alias(self):
        out,resolver=self.migrate("(atom? ())\n")
        self.assertEqual(out,"10 010 00 000 01\n")
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass2_def_and_lambda_resolve_as_heads_without_using_d7(self):
        resolver=self.resolver()
        def_bits,_=resolver.head(mod.Tok("ATOM","def",0))
        lambda_bits,_=resolver.head(mod.Tok("ATOM","lambda",0))
        self.assertEqual(def_bits,["0011"])
        self.assertEqual(lambda_bits,["0010"])
        self.assertEqual(resolver.counts["pass2-my-lisp"],2)

    def test_pass3_lisp15_car(self):
        out,resolver=self.migrate("(CAR ())\n")
        self.assertEqual(out,"10 100 00 000 01\n")
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_pass3_lisp15_arithmetic(self):
        out,resolver=self.migrate("(PLUS () ())\n")
        self.assertEqual(out,"10 01010 00 000 00 000 01\n")
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_comments_disappear(self):
        a,_=self.migrate("; top\n(CAR #| nested #| inner |# body |# ())\n")
        b,_=self.migrate("(CAR ())\n")
        self.assertEqual(a,b)

    def test_unknown_function_never_becomes_data(self):
        with self.assertRaisesRegex(mod.MigrationError,"unknown executable head"):
            self.migrate("(totally-unknown-function ())\n")

    def test_non_function_atom_blocks_until_d7_role_is_known(self):
        with self.assertRaisesRegex(mod.MigrationError,"D7/Text7 is deferred"):
            self.migrate("(CAR x)\n")

    def test_string_blocks_until_d7_role_is_known(self):
        with self.assertRaisesRegex(mod.MigrationError,"deferred D7/Text7"):
            self.migrate('(CAR "text")\n')

    def test_numeric_literal_blocks_for_number_framing(self):
        with self.assertRaisesRegex(mod.MigrationError,"Number framing"):
            self.migrate("(CAR 25)\n")

    def test_quote_of_empty_is_quote_plus_000(self):
        out,_=self.migrate("'()\n")
        self.assertEqual(out,"10 001 00 000 01\n")

    def test_dotted_pair_uses_d2_dot_without_d7(self):
        out,_=self.migrate("'(000 . 000)\n")
        self.assertIn(" 11 ",out)
        self.assertRegex(out,r"^[01\s]+$")

    def test_output_is_only_exact_width_binary_words(self):
        out,_=self.migrate("(CONS () ())\n")
        self.assertRegex(out,r"^[01\s]+$")
        self.assertTrue(all(1<=len(word)<=8 for word in out.split()))

    def test_extensionless_output_name(self):
        self.assertEqual(str(mod.extensionless(Path("lib/foo.lisp"))),"lib/foo")
        self.assertEqual(str(mod.extensionless(Path("lib/sse4.1.lisp"))),"lib/sse4.1")

    def test_three_pass_tool_contains_no_text7_encoder(self):
        source=SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("build_text7",source)
        self.assertNotIn("text7_encode",source)
        self.assertNotIn("--text7",source)

if __name__=="__main__":
    unittest.main()
