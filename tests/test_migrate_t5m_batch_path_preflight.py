#!/usr/bin/env python3
"""Негативні свідки адрес шляхів пакетної фізичної міграції T5.

Тут перевіряється лише безпечна публікація файлів, не семантика SENS.
Усі артефакти створюються виключно в тимчасовому каталозі.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-t5m-batch.py"


@unittest.skipIf(os.name == "nt", "символічні посилання тестуються на POSIX")
class BatchPathPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(SCRIPT.parent))
        spec = importlib.util.spec_from_file_location("sens_batch_path_preflight", SCRIPT)
        assert spec is not None and spec.loader is not None
        cls.batch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.batch)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-t5-paths-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repository"
        self.repo.mkdir()
        self.out = self.base / "mirror"
        self.out.mkdir()
        self.report = self.base / "receipt.json"

    def invoke(self, *, root=None, out=None, report=None, publish=False):
        # --write requires the same Zig-only physical path as production.
        # These collision cases MUST reject before Zig is ever compiled.
        arguments = [sys.executable, str(SCRIPT), "missing.lisp",
                     "--root", str(root or self.repo),
                     "--out", str(out or self.out),
                     "--report", str(report or self.report)]
        if publish:
            arguments.extend(("--write", "--zig-codec"))
        return subprocess.run(
            arguments, cwd=ROOT, capture_output=True, text=True, timeout=15,
        )

    def test_regular_paths_and_stable_pins(self):
        repo = self.batch.resolve_without_links(self.repo, "source repository")
        out = self.batch.resolve_without_links(self.out, "output mirror")
        report = self.batch.resolve_without_links(self.report, "report")
        self.assertEqual((repo, out, report), (self.repo, self.out, self.report))
        self.batch.verify_pinned_paths(
            argparse.Namespace(root=self.repo, out=self.out, report=self.report),
            repo, out, report,
        )

    def test_report_symlink_never_replaces_existing_external_bytes(self):
        protected = self.base / "protected.json"
        protected.write_bytes(b"ORIGINAL-DO-NOT-CLOBBER")
        alias = self.base / "report-link.json"
        alias.symlink_to(protected)
        result = self.invoke(report=alias)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(protected.read_bytes(), b"ORIGINAL-DO-NOT-CLOBBER")
        self.assertTrue(alias.is_symlink())

    def test_existing_physical_sens_bytes_never_become_json_receipt(self):
        # Regression: without this guard stage.replace(report) can overwrite
        # an already-published byte-exact .sens with text, even in dry-run.
        (self.out / "lib").mkdir()
        protected = self.out / "lib" / "third.sens"
        original = bytes((0x00, 0xff, 0x21, 0x03, 0x00))
        protected.write_bytes(original)
        for publish in (False, True):
            with self.subTest(publish=publish):
                outcome = self.invoke(report=protected, publish=publish)
                self.assertEqual(outcome.returncode, 3, outcome.stdout + outcome.stderr)
                self.assertIn("ZIG_REPORT_OUTPUT_COLLISION layer=transport", outcome.stderr)
                self.assertEqual(protected.read_bytes(), original)
        self.assertEqual(list((self.out / "lib").iterdir()), [protected])

    def test_nested_report_inside_output_mirror_rejected_before_zig(self):
        embedded_report = self.out / "reports" / "receipt.json"
        for publish in (False, True):
            with self.subTest(publish=publish):
                outcome = self.invoke(report=embedded_report, publish=publish)
                self.assertEqual(outcome.returncode, 3, outcome.stdout + outcome.stderr)
                self.assertIn("ZIG_REPORT_OUTPUT_COLLISION layer=transport", outcome.stderr)
                self.assertFalse(embedded_report.exists())
                self.assertEqual(list(self.out.iterdir()), [])

    def test_dangling_report_symlink_rejected(self):
        alias = self.base / "dangling.json"
        alias.symlink_to(self.base / "not-created.json")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.batch.resolve_without_links(alias, "report")
        self.assertFalse((self.base / "not-created.json").exists())

    def test_output_directory_symlink_rejected_before_discovery(self):
        alias = self.base / "mirror-link"
        alias.symlink_to(self.out, target_is_directory=True)
        result = self.invoke(out=alias)
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("symlink", result.stderr)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_linked_parent_and_linked_root_rejected(self):
        alias = self.base / "directory-link"
        alias.symlink_to(self.out, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.batch.resolve_without_links(alias / "receipt.json", "report")
        root_alias = self.base / "repository-link"
        root_alias.symlink_to(self.repo, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.batch.resolve_without_links(root_alias, "source repository")

    def test_parent_traversal_rejected(self):
        with self.assertRaisesRegex(ValueError, "parent traversal"):
            self.batch.resolve_without_links(self.repo / ".." / "mirror", "output mirror")

    def test_rebound_path_fails_pinned_recheck(self):
        original = self.batch.resolve_without_links(self.report, "report")
        args = argparse.Namespace(root=self.repo, out=self.out, report=self.report)
        self.batch.verify_pinned_paths(args, self.repo, self.out, original)
        alias = self.base / "late-report-link.json"
        alias.symlink_to(self.base / "protected.json")
        args.report = alias
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.batch.verify_pinned_paths(args, self.repo, self.out, original)


if __name__ == "__main__":
    unittest.main()
