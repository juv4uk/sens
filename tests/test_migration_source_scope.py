#!/usr/bin/env python3
"""Exact source provenance must not be manufactured by path normalization."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from migration_source_scope import archived_benchmark_source, scope


class ArchivedBenchmarkScopeTest(unittest.TestCase):
    def test_exact_archive_positive_and_noncanonical_aliases_negative(self):
        canonical = "benchmarks/sens-surface/results/20261015-archive/programs/proof.lisp"
        self.assertTrue(archived_benchmark_source(canonical))
        self.assertEqual(scope(canonical), "ARCHIVED_BENCHMARK_NONPROGRAM")
        mutants = {
            "double_separator": canonical.replace("/programs/", "//programs/"),
            "middle_double_separator": canonical.replace("/results/", "/results//"),
            "trailing_separator": canonical + "/",
            "dot_segment": canonical.replace("/programs/", "/programs/./"),
            "parent_segment": canonical.replace("/programs/", "/programs/../programs/"),
            "absolute": "/" + canonical,
            "backslash": canonical.replace("/programs/", "\\programs/"),
            "nul": canonical + "\0",
            "not_lisp": canonical.removesuffix(".lisp") + ".sens",
        }
        for label, path in mutants.items():
            with self.subTest(alias=label):
                self.assertFalse(archived_benchmark_source(path), label)
                self.assertEqual(scope(path), "UNCLASSIFIED_NEEDS_SOURCE_PROOF")


if __name__ == "__main__":
    unittest.main()
