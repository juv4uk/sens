"""Proof of exact source-only SID8 replacement in 11 live Lisp witness fixtures.

Immutable Git blobs preserve the pre-migration inputs; the production three-pass
parser and existing migration auditor independently enforce no edits to quoted
data, strings, lists, binders or argument counts. Runtime parity is NOT claimed.
"""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = ROOT / "scripts" / "audit_lisp_migration_edits.py"
spec = importlib.util.spec_from_file_location("sens_sid8_witness_auditor", AUDIT_PATH)
assert spec and spec.loader
auditor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = auditor
spec.loader.exec_module(auditor)

COHORT = {
    "tests/fixtures/content-store-authority-witness.lisp": ("f2525c2f6a96706cca46c00b807095bfa357e24f", 31),
    "tests/fixtures/life-1-contract-witness.lisp": ("4be1012540aa630058ca4017828535edb15f30af", 134),
    "tests/fixtures/life-1-scheduler-witness.lisp": ("4e7d416bd69371bdefb88ab3ca38b45f8e8ff63d", 72),
    "tests/fixtures/meta-semantic-registry-witness.lisp": ("9efc1b4e755b1e3abe109f3d0f4be21e42d6d21b", 113),
    "tests/fixtures/narrate-outcome-authority-witness.lisp": ("52dc37bc7a9511bf8681947e0b698e347da4be94", 56),
    "tests/fixtures/persistent-vector-balance-witness.lisp": ("d8deef1b93f52db2b4f8b7377df835bc11e7df05", 23),
    "tests/fixtures/prolog-datalog-bridge-witness.lisp": ("afd0019a1fcb981ce848e2b25ae381f776d374b5", 11),
    "tests/fixtures/reason-index-authority-witness.lisp": ("a83b8466f1afa19eecb314ccc9494c0ceb9c1451", 51),
    "tests/fixtures/scientific-constant-knowledge-projection-witness.lisp": ("da0b0d886182c04dd2ce7c8046d8667580fb4070", 21),
    "tests/fixtures/world-transition-witness.lisp": ("f372930f83161653f5379a1689fc93e9b4f12c7d", 38),
}


class WitnessSourceMigration(unittest.TestCase):
    def test_exact_source_only_substitutions_and_identity_counts(self):
        total = 0
        for path, (old_blob, expected) in COHORT.items():
            with self.subTest(path=path):
                before = subprocess.check_output(
                    ["git", "cat-file", "blob", old_blob], cwd=ROOT
                ).decode("utf-8")
                after = (ROOT / path).read_text(encoding="utf-8")
                result = auditor.audit_edit(before, after)
                self.assertEqual(result["status"], "LEXICAL_CONTEXT_ONLY")
                self.assertEqual(result["semantic_parity"], "NOT_CHECKED")
                lexer = auditor.parser
                prior = [t.text for t in lexer.tokenize(lexer.strip_comments(before))]
                current = [t.text for t in lexer.tokenize(lexer.strip_comments(after))]
                self.assertEqual(len(prior), len(current))
                changes = sum(a != b for a, b in zip(prior, current))
                self.assertEqual(changes, expected)
                total += changes
        self.assertEqual(len(COHORT), 10)
        self.assertEqual(total, 550)

    def test_process_witness_executes_current_ukrainian_function(self):
        # Старий точний Git-знімок зберігається в історії, а не в чинному API.
        source = (ROOT / "tests/fixtures/process-load-witness.lisp").read_text(
            encoding="utf-8")
        self.assertEqual(source.count("(процес-публічний-вихід-код "), 2)
        self.assertNotIn("(тотожне? process-run запустити-процес)", source)
        self.assertNotIn("(визначити process-run ", source)
        self.assertIn("(status pass)", source)
        self.assertIn("(status fail)", source)
        self.assertIn("(за-умовою", source)

    def test_old_binary_call_heads_not_reintroduced(self):
        for path in COHORT:
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                self.assertNotIn("(00001001 ", source)
                self.assertIn("(0011 ", source)


if __name__ == "__main__":
    unittest.main()
