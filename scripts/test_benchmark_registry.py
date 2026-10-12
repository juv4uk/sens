#!/usr/bin/env python3
"""Focused tests for benchmark registry/support-exemption policy."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_registry as registry  # noqa: E402


class SupportExemptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.benchmarks = self.root / "benchmarks"
        self.benchmarks.mkdir()
        self.exemption_file = self.benchmarks / "support-exemptions.json"
        self.old_root = registry.ROOT
        self.old_benchmarks = registry.BENCHMARKS
        self.old_file = registry.EXEMPTION_FILE
        registry.ROOT = self.root
        registry.BENCHMARKS = self.benchmarks
        registry.EXEMPTION_FILE = self.exemption_file

    def tearDown(self) -> None:
        registry.ROOT = self.old_root
        registry.BENCHMARKS = self.old_benchmarks
        registry.EXEMPTION_FILE = self.old_file
        self.temp.cleanup()

    def add_directory(self, name: str, witness: str = "README.md") -> None:
        directory = self.benchmarks / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / witness).write_text("evidence\n", encoding="utf-8")

    def entry(self, name: str = "support-a") -> dict[str, object]:
        return {
            "path": name,
            "reason": "Supporting corpus, not an executable stand.",
            "witness": [f"benchmarks/{name}/README.md"],
            "owner_or_issue": "#4172",
            "reviewed_at": "2026-10-12",
        }

    def write_registry(self, entries: list[dict[str, object]]) -> None:
        self.exemption_file.write_text(
            json.dumps({"schema": registry.EXEMPTION_SCHEMA_ID, "exemptions": entries}),
            encoding="utf-8",
        )

    def test_valid_exemption_is_separate_from_benchmark_stands(self) -> None:
        self.add_directory("support-a")
        self.write_registry([self.entry()])
        exemptions = registry.load_support_exemptions()
        rendered = registry.render([], exemptions)
        self.assertIn("Explicit support-directory exemptions (not benchmark stands)", rendered)
        self.assertIn("**Registered stands:** 0", rendered)
        self.assertIn("**Explicit support-directory exemptions:** 1", rendered)

    def test_duplicate_paths_are_rejected(self) -> None:
        self.add_directory("support-a")
        self.write_registry([self.entry(), self.entry()])
        with self.assertRaisesRegex(registry.RegistryError, "duplicate"):
            registry.load_support_exemptions()

    def test_stale_directory_is_rejected(self) -> None:
        self.add_directory("support-a")
        self.write_registry([self.entry("missing")])
        with self.assertRaisesRegex(registry.RegistryError, "does not exist"):
            registry.load_support_exemptions()

    def test_missing_witness_is_rejected(self) -> None:
        self.add_directory("support-a")
        entry = self.entry()
        entry["witness"] = ["benchmarks/support-a/missing.md"]
        self.write_registry([entry])
        with self.assertRaisesRegex(registry.RegistryError, "witness file does not exist"):
            registry.load_support_exemptions()

    def test_path_traversal_is_rejected(self) -> None:
        self.add_directory("support-a")
        entry = self.entry()
        entry["witness"] = ["benchmarks/support-a/../escape.md"]
        self.write_registry([entry])
        with self.assertRaisesRegex(registry.RegistryError, "stay inside"):
            registry.load_support_exemptions()

    def test_directory_cannot_be_both_manifested_and_exempted(self) -> None:
        self.add_directory("support-a")
        (self.benchmarks / "support-a" / "bench.json").write_text("{}", encoding="utf-8")
        self.write_registry([self.entry()])
        with self.assertRaisesRegex(registry.RegistryError, "cannot also be exempted"):
            registry.load_support_exemptions()

    def test_strict_accepts_only_manifest_or_explicit_exemption(self) -> None:
        self.add_directory("support-a")
        self.add_directory("stand-a")
        (self.benchmarks / "stand-a" / "bench.json").write_text("{}", encoding="utf-8")
        self.write_registry([self.entry()])
        exemptions = registry.load_support_exemptions()
        registry.check_strict({item["path"] for item in exemptions})
        self.add_directory("unclassified")
        with self.assertRaisesRegex(registry.RegistryError, "unclassified"):
            registry.check_strict({item["path"] for item in exemptions})

    def test_new_support_directory_can_be_explicitly_exempted(self) -> None:
        self.add_directory("support-a")
        self.write_registry([self.entry()])
        exemptions = registry.load_support_exemptions()
        fake_diff = SimpleNamespace(returncode=0, stderr="", stdout="A\tbenchmarks/support-a/README.md\n")
        with patch.object(registry.subprocess, "run", return_value=fake_diff), patch.object(
            registry, "_base_has_stand", return_value=False
        ):
            registry.check_new_stands("base", "head", {item["path"] for item in exemptions})


if __name__ == "__main__":
    unittest.main()
