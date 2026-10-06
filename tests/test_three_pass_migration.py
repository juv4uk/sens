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
TEXT7=ROOT/"crates"/"sens"/"src"/"text7_projection_generated.rs"

class ThreePassMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=mod.load_foundation(FOUNDATION)
        cls.legacy,cls.my,cls.upper=mod.build_three_pass_maps(
            data,DOMAIN_SURFACES,SEMANTIC_GENERATED,SEMANTIC_REGISTRY,NECESSARY
        )
        cls.text7=mod.build_text7(data,TEXT7)

    def migrate(self,source):
        resolver=mod.Resolver(self.legacy,self.my,self.upper)
        return mod.migrate_file(source,resolver,self.text7),resolver

    def test_empty_list_is_compact_d3_empty(self):
        out,_=self.migrate("()\n")
        self.assertEqual(out,"000\n")

    def test_nonempty_list_uses_d2_structure(self):
        out,_=self.migrate("(CAR x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertTrue(out.endswith(" 01\n"))

    def test_pass1_legacy_sid8_car(self):
        out,resolver=self.migrate("(00000101 x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass1-sens8"],1)

    def test_pass2_my_lisp_car(self):
        out,resolver=self.migrate("(car x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass2_my_lisp_predicate_alias(self):
        out,resolver=self.migrate("(atom? x)\n")
        self.assertTrue(out.startswith("10 010 00 "))
        self.assertEqual(resolver.counts["pass2-my-lisp"],1)

    def test_pass2_def_normalizes_to_define(self):
        out,resolver=self.migrate("(def f (lambda (x) x))\n")
        self.assertTrue(out.startswith("10 0011 00 "))
        self.assertGreaterEqual(resolver.counts["pass2-my-lisp"],2)

    def test_pass3_lisp15_car(self):
        out,resolver=self.migrate("(CAR x)\n")
        self.assertTrue(out.startswith("10 100 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_pass3_lisp15_arithmetic(self):
        out,resolver=self.migrate("(PLUS x y)\n")
        self.assertTrue(out.startswith("10 01010 00 "))
        self.assertEqual(resolver.counts["pass3-lisp15"],1)

    def test_comments_disappear(self):
        a,_=self.migrate("; top\n(CAR #| nested #| inner |# body |# x)\n")
        b,_=self.migrate("(CAR x)\n")
        self.assertEqual(a,b)

    def test_unknown_function_passes_through_verbatim(self):
        out,resolver=self.migrate("(totally-unknown-function x)\n")
        self.assertEqual(out,"10 totally-unknown-function 00 x 01\n")
        self.assertEqual(resolver.counts["passthrough-head"],1)

    def test_unresolved_sid8_passes_through_verbatim(self):
        out,resolver=self.migrate("(11111111 x)\n")
        self.assertEqual(out,"10 11111111 00 x 01\n")
        self.assertEqual(resolver.counts["passthrough-head"],1)

    def test_d1_d2_head_words_pass_through_verbatim(self):
        out1,resolver1=self.migrate("(1 x)\n")
        out2,resolver2=self.migrate("(10 x)\n")
        self.assertEqual(out1,"10 1 00 x 01\n")
        self.assertEqual(out2,"10 10 00 x 01\n")
        self.assertEqual(resolver1.counts["passthrough-head"],1)
        self.assertEqual(resolver2.counts["passthrough-head"],1)

    def test_numeric_literal_passes_through_verbatim(self):
        out,_=self.migrate("(CAR 25)\n")
        self.assertEqual(out,"10 100 00 25 01\n")

    def test_quote_of_empty_is_quote_plus_000(self):
        out,_=self.migrate("'()\n")
        self.assertEqual(out,"10 001 00 000 01\n")

    def test_dotted_pair_uses_d2_dot(self):
        out,_=self.migrate("'(a . b)\n")
        self.assertIn(" 11 ",out)
        self.assertRegex(out,r"^[01\s]+$")

    def test_known_structure_and_function_convert_while_unknown_data_stays_visible(self):
        out,_=self.migrate("(CONS x y)\n")
        self.assertEqual(out,"10 111 00 x 00 y 01\n")

    def test_extensionless_output_name(self):
        self.assertEqual(str(mod.extensionless(Path("lib/foo.lisp"))),"lib/foo")
        self.assertEqual(str(mod.extensionless(Path("lib/sse4.1.lisp"))),"lib/sse4.1")

if __name__=="__main__":
    unittest.main()
