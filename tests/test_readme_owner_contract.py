#!/usr/bin/env python3
"""#4250/#4449: README is not a backdoor to stale triple or Rust-owner law."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
D3 = ROOT / "lib/domains/d3.lisp"


class ReadmeOwnerTripletContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = README.read_text(encoding="utf-8")

    def test_rust_reference_not_semantic_owner(self):
        self.assertTrue(any(needle in self.doc for needle in (
            "reference implementation", "референсна реалізація")))
        self.assertNotIn("canonical Rust implementation", self.doc)
        self.assertNotIn("канонічна реалізація на Rust", self.doc)
        self.assertIn("семантику SENS", self.doc)
        self.assertIn("docs/semantic-authority-map.md", self.doc)

    def test_exact_source_and_legacy_extensions(self):
        self.assertIn("Канонічне розширення вихідного коду — **\x60.lisp\x60**",
                      self.doc)
        self.assertIn("\x60.wsm\x60", self.doc)
        self.assertIn("\x60.my\x60", self.doc)
        self.assertIn("legacy aliases", self.doc)

    def test_actual_triple_not_old_prohibition(self):
        self.assertIn("каталог/назва.lisp", self.doc)
        self.assertIn("каталог/назва.sens", self.doc)
        self.assertIn("файл \x60каталог/назва\x60 без розширення", self.doc)
        self.assertNotIn("Не створювати файлів \x60каталог/назва\x60 без розширення", self.doc)
        self.assertIn("одним ASCII-пробілом", self.doc)
        self.assertIn("завершальним LF", self.doc)
        self.assertIn("не підтверджує семантичного допуску", self.doc)

    def test_literal_d3_nil_in_current_domain_and_readme(self):
        source = D3.read_text(encoding="utf-8")
        self.assertRegex(source, r"\(000 \(ук \(\)\)")
        self.assertIn("| 000 | порожня структура | \x60()\x60 |", self.doc)
        self.assertIn("(перше (сполучити () ()))", self.doc)
        self.assertNotIn("(перше (сполучити порожнє порожнє))", self.doc)

    def test_historical_compatibility_markdown_exactly_matches_reviewed_140(self):
        # This is a deprecated 8-bit API compatibility index, not the
        # ratified current exact-width D1-D9 authority.
        registry = (ROOT/"lib/surface/semantic-registry.lisp").read_text(encoding="utf-8")
        authority = (ROOT/"lib/surface/uk-docs.lisp").read_text(encoding="utf-8")
        markdown = (ROOT/"docs/ukrainian-api.md").read_text(encoding="utf-8")
        legacy = markdown.split("## Історичний Function8/SID8 індекс сумісності", 1)
        self.assertEqual(len(legacy), 2)
        indexed = dict(re.findall(r"^\| \x60([^|\x60]+)\x60 \| \x60([01]{8})\x60 \| [a-z-]+ \|$", legacy[1], re.M))
        by_id = dict(re.findall(
            r"^\s*\(([01]{8})\s+\(en [^)]+\)\s+\(ук ([^)]+)\)",
            registry, re.M,
        ))
        docs = re.findall(r"^\s*\(doc \S+ ([01]{8})\b", authority, re.M)
        self.assertEqual(len(docs), 140)
        self.assertEqual(len(indexed), 140)
        self.assertEqual({by_id[k]: k for k in docs}, indexed)
        self.assertIn("не** первинні коди сучасної мови", legacy[1])

    def test_contract_same_as_real_governance_script(self):
        owner = (ROOT/"scripts/verify-repo.lisp").read_text(encoding="utf-8")
        self.assertIn('": must describe Rust as a reference implementation"', owner)
        self.assertIn('(check-doc-identity "README.md")', owner)
        self.assertIn("legacy aliases", self.doc)
        self.assertIn("reference implementation", self.doc)


if __name__ == "__main__":
    unittest.main()
