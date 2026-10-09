#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE.parent / "memory_runner.py"

spec = importlib.util.spec_from_file_location("memory_runner_under_test", MODULE_PATH)
assert spec is not None and spec.loader is not None
memory = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = memory
spec.loader.exec_module(memory)


class MemoryRunnerTests(unittest.TestCase):
    def test_summary_reports_median_min_max_and_keeps_allocations_unknown(self) -> None:
        rows = []
        for rep, rss in enumerate([120, 100, 140]):
            rows.append(
                {
                    "candidate": "english-surface",
                    "phase": "full",
                    "metrics": {"peak_rss_kb": rss},
                }
            )
        summary = memory.summarize(rows)
        self.assertEqual(summary["schema"], memory.SUMMARY_SCHEMA)
        only = summary["rows"][0]
        self.assertEqual(only["samples"], 3)
        self.assertEqual(only["peak_rss_kb_median"], 120)
        self.assertEqual(only["peak_rss_kb_min"], 100)
        self.assertEqual(only["peak_rss_kb_max"], 140)
        self.assertEqual(only["peak_rss_kb_spread"], 40)
        self.assertIsNone(only["allocation_count"])
        self.assertIsNone(only["allocated_bytes"])

    def test_negative_or_missing_rss_is_rejected(self) -> None:
        for bad in (-1, None):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    memory.summarize(
                        [
                            {
                                "candidate": "canonical-d1d8",
                                "phase": "execute",
                                "metrics": {"peak_rss_kb": bad},
                            }
                        ]
                    )


if __name__ == "__main__":
    unittest.main()
