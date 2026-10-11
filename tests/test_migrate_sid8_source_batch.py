"""Regressions for source-only, all-live-files SID8 bulk intake."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "migrate-sid8-source-batch.py"
SPEC = importlib.util.spec_from_file_location("sens_sid8_source_batch", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

class BatchSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping, cls.blocked = MOD.authority(ROOT)
        cls.guard = MOD.guard_module(ROOT)

    def test_ratified_map_exact_and_ambiguous_blocked(self):
        self.assertEqual(len(self.mapping), 171)
        self.assertEqual(self.mapping["00001001"], "0011")
        self.assertEqual(self.mapping["00000011"], "101")
        for code in ("00001010", "00110111", "01011010"):
            self.assertNotIn(code, self.mapping)
            self.assertIn(code, self.blocked)

    def test_nested_quoted_data_and_comments_preserved(self):
        old = ";(00000100 ignored)\n(00001001 f (00001000 (x) (00000100 (00000001 00000011) x)))\n"
        new, n, blockers = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(n, 4)
        self.assertFalse(blockers)
        self.assertIn("(0011 f (0010 (x) (111 (001 00000011) x)))", new)
        self.assertIn(";(00000100 ignored)", new)

    def test_ambiguous_head_blocks_entire_file(self):
        old = "(00001001 f (00001000 () (00110111 fun values)))"
        new, n, blockers = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(new, old)
        self.assertEqual(n, 2)
        self.assertTrue(any("00110111" in b for b in blockers))

    def test_cond_three_fields_requires_semantic_translation(self):
        old = "(00001001 f (00001000 (x) (00000111 ((00000010 x) 0 1))))"
        new, n, blockers = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(n, 4)
        self.assertFalse(blockers)
        findings = self.guard.scan_lisp(new, "lib/f.lisp")
        self.assertIn("COND_NOT_TWO_FIELDS", {f.rule for f in findings})

    def test_generated_and_current_domain_data_are_never_mass_rewritten(self):
        names = {
            "lib/machine/encoding/admitted-iclass-index.lisp",
            "lib/machine/cpu/intel-core-i5-6400-inventory.lisp",
            "lib/machine/dispatch/native-first-execute.lisp",
            "lib/island-math-evidence.lisp",
            "knowledge/language-detection-probe.lisp",
        }
        census = MOD.run(ROOT, False, names)
        self.assertEqual(census["summary"]["admitted_heads"], 0)
        self.assertEqual(census["summary"]["admitted_files"], 0)
        self.assertEqual(len(census["files"]), len(names))
        for row in census["files"]:
            with self.subTest(path=row["path"]):
                self.assertEqual(row["status"], "source-era-unproved")

    def test_immutable_guard_reference_not_rewritten_until_cond_law(self):
        report = MOD.run(ROOT, False, {"knowledge/guard-reference.lisp"})
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertGreaterEqual(report["summary"]["blocked_files"], 1)
        self.assertEqual(report["files"][0]["status"], "blocked")

if __name__ == "__main__":
    unittest.main()
