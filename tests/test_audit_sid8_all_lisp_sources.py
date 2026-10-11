"""Non-destructive census of all active, archival and data-only Lisp originals."""
from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "scripts" / "audit_sid8_all_lisp_sources.py"
spec = importlib.util.spec_from_file_location("_test_sid8_all_lisp", P)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
assert spec and spec.loader
spec.loader.exec_module(module)


class AuditAllLispSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = module.d3_reader()
        cls.authority = module.authority()

    def test_all_old_codes_covered_exactly_once(self):
        self.assertEqual(len(self.authority), 256)
        self.assertEqual(self.authority["00001001"]["legacy_name"], "define")

    def test_historical_archive_and_evidence_never_migrated(self):
        for path in (
            "research/domain-archive/20261011/donor.lisp",
            "knowledge/d10-source-snapshots/sha.lisp",
            "benchmarks/sens-surface/results/20260925/program.lisp",
        ):
            self.assertEqual(module.scope(path), "PRESERVE_HISTORICAL")
        self.assertEqual(module.scope("tests/fixtures/cond-original.lisp"),
                         "PRESERVE_TEST_OR_EVIDENCE")
        self.assertEqual(module.scope("lib/domains/d3.lisp"),
                         "CONTRACT_OR_DATA_REVIEW")
        self.assertEqual(module.scope("lib/reason.lisp"), "LIVE_CANDIDATE")

    def test_old_executable_vs_quoted_data_and_comments(self):
        src = (
            "; (00000111 ((t x y)))\n"
            "(00001001 f (00001000 (x) (00000111 ((00000010 x) x))))\n"
            '(00000001 (00000011 a b))\n'
            '"(00001001 not code)"\n'
        )
        x = module.inspect(src, "lib/example.lisp", self.reader, self.authority)
        self.assertTrue(x["legacy_source_anchor"])
        self.assertEqual(x["legacy_word_sites"]["00001001"], 1)
        self.assertEqual(x["legacy_word_sites"]["00001000"], 1)
        self.assertEqual(x["legacy_word_sites"]["00000111"], 1)
        self.assertEqual(x["legacy_word_sites"]["00000010"], 1)
        self.assertNotIn("00000011", x["legacy_word_sites"])
        self.assertEqual(x["action"], "POSSIBLE_HISTORICAL_SOURCE_REVIEW")

    def test_ambiguous_map_not_misrepresented_as_unique(self):
        src = "(00001001 m (00001000 (xs) (00110111 f xs)))"
        x = module.inspect(src, "lib/example.lisp", self.reader, self.authority)
        self.assertIn("00110111", x["ambiguous_old_words"])

    def test_full_manifest_scans_all_tracked_lisp_not_only_one_library(self):
        output = module.census()
        self.assertGreaterEqual(output["summary"]["tracked_lisp_files"], 600)
        file_paths = {row["path"] for row in output["files"]}
        self.assertIn("lib/world.lisp", file_paths)
        self.assertIn("scripts/check-island-math-evidence.lisp", file_paths)
        self.assertIn("benchmarks/arithmetic.lisp", file_paths)
        self.assertIn("tests/fixtures/world-d3-before.lisp", file_paths)
        self.assertTrue(all(row["scope"] != "PRESERVE_HISTORICAL" or
                            row["action"] == "PRESERVE_ORIGINAL_BYTES"
                            for row in output["files"]))
        self.assertEqual(len(file_paths), len(output["files"]))
        self.assertEqual(output["summary"]["unscannable"],
                         output["summary"]["by_action"].get("UNSCANNABLE_FAIL_CLOSED", 0))


if __name__ == "__main__":
    unittest.main()
