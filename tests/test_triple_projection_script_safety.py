#!/usr/bin/env python3
"""Read-only, no-fake-green Ukrainian triple and renderer regression (#4449)."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SHELL = ROOT / "scripts/check-triple-projection.sh"
RENDERER = ROOT / "scripts/sens_uk.py"
F = ROOT / "tests/fixtures/migration-d1-cond-cohort"


class SafeTripleScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sens-triple-script-safety-")
        self.root = Path(self.tmp.name)
        for ext in (".lisp", ".sens", ""):
            shutil.copyfile(F / f"branch{ext}", self.root / f"branch{ext}")
        self.source = self.root / "branch.lisp"
        self.binary = self.root / "branch.sens"
        self.view = self.root / "branch"

    def tearDown(self):
        self.tmp.cleanup()

    def checker(self, *args):
        return subprocess.run(
            ["bash", str(SHELL), "--root", str(self.root),
             "--fixture", "branch.lisp", *args],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )

    def renderer(self, *args):
        return subprocess.run(
            [sys.executable, str(RENDERER), *map(str, args)],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )

    def test_actual_committed_triple_passes_without_writing_anything(self):
        before = tuple((self.root / f"branch{ext}").read_bytes()
                       for ext in (".lisp", ".sens", ""))
        result = self.checker()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("result=PASS", result.stdout)
        self.assertIn("release=NOT_ADMITTED", result.stdout)
        self.assertEqual(
            before, tuple((self.root / f"branch{ext}").read_bytes()
                          for ext in (".lisp", ".sens", "")),
        )
        self.assertEqual(sorted(p.name for p in self.root.iterdir()),
                         ["branch", "branch.lisp", "branch.sens"])

    def test_source_wrong_even_if_temp_generation_would_match_is_blocked(self):
        # Old checker merely regenerated a different temporary binary and
        # compared its own view against its own roundtrip. It falsely passed.
        original = self.source.read_bytes()
        self.source.write_text("(перше ())\n", encoding="utf-8")
        result = self.checker()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("BLOCKED", result.stderr)
        self.assertEqual(self.source.read_text(), "(перше ())\n")
        self.source.write_bytes(original)

    def test_committed_physical_or_view_corruption_is_not_self_certified(self):
        first = self.binary.read_bytes()
        self.binary.write_bytes(b"\xf3")
        run = self.checker()
        self.assertEqual(run.returncode, 2)
        self.binary.write_bytes(first)
        view = self.view.read_bytes()
        for fake in (b"", view + b"\n", view.replace(b" ", b"  ", 1), b"0\n"):
            self.view.write_bytes(fake)
            with self.subTest(view=fake[:15]):
                self.assertEqual(self.checker().returncode, 2)
        self.view.write_bytes(view)

    def test_missing_or_symlinked_view_blocks(self):
        self.view.unlink()
        self.assertEqual(self.checker().returncode, 2)
        self.view.symlink_to(F / "branch")
        self.assertEqual(self.checker().returncode, 2)

    def test_unsafe_path_and_no_fixture_cannot_be_success(self):
        for extra in (["--fixture", "../outside.lisp"],
                      ["--fixture", "/etc/passwd.lisp"],
                      ["--fixture", "nonexistent.lisp"]):
            with self.subTest(extra=extra):
                run = subprocess.run(
                    ["bash", str(SHELL), "--root", str(self.root), *extra],
                    cwd=ROOT, capture_output=True, text=True, timeout=60,
                )
                self.assertEqual(run.returncode, 2)
        no_fixture = subprocess.run(
            ["bash", str(SHELL), "--root", str(self.root)],
            cwd=ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(no_fixture.returncode, 2)
        self.assertIn("BLOCKED", no_fixture.stderr)

    def test_full_corpus_proves_d4_but_still_blocks_two_unadmitted_legacy(self):
        # D4 CAAR has a real bounded Ukrainian/T5/view proof with a separate
        # Rust oracle; do not keep an obsolete expectation that it is blocked.
        # Historical third/two-forms still lack verified same-stem views and
        # must remain BLOCKED, not silently skipped or release-admitted.
        result = subprocess.run(
            ["bash", str(SHELL)], cwd=ROOT,
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("result=BLOCKED", result.stdout)
        self.assertIn("PASS tests/fixtures/migration-d1-cond-cohort/branch.lisp", result.stdout)
        self.assertIn("PASS tests/fixtures/migration-d4-selector-cohort/caar.lisp", result.stdout)
        self.assertIn("third.lisp", result.stderr)
        self.assertIn("two-forms.lisp", result.stderr)
        self.assertNotIn("caar.lisp", result.stderr)

    def test_renderer_default_never_rewrites_original_lisp(self):
        origin = (F / "branch.lisp").read_bytes()
        result = self.renderer("render", F / "branch.sens")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.encode("utf-8"), origin)
        self.assertEqual((F / "branch.lisp").read_bytes(), origin)
        self.assertFalse((F / "branch.sens.lisp").exists())

    def test_renderer_explicit_external_staging_is_atomic_and_no_clobber(self):
        target = self.root / "rendered.lisp"
        output = self.renderer("render", self.binary, "--out", target)
        self.assertEqual(output.returncode, 0, output.stderr)
        self.assertEqual(target.read_bytes(), self.source.read_bytes())
        again = self.renderer("render", self.binary, "--out", target)
        self.assertEqual(again.returncode, 2)
        self.assertEqual(target.read_bytes(), self.source.read_bytes())

    def test_renderer_refuses_explicit_repository_source_overwrite(self):
        before = (F / "branch.lisp").read_bytes()
        outcome = self.renderer("render", F / "branch.sens",
                                "--out", F / "branch.lisp")
        self.assertEqual(outcome.returncode, 2)
        self.assertEqual((F / "branch.lisp").read_bytes(), before)

    def test_malformed_d2_and_unproved_dot_renderer_fail_closed(self):
        invalid = (
            ("00",), ("01",), ("10",), ("11",),
            ("10", "01"), ("10", "100", "00", "01"),
            ("10", "100", "01", "01"),
            ("10", "100", "100", "01"),
            ("10", "100", "11", "000", "01"),
        )
        for words in invalid:
            with self.subTest(words=words):
                run = self.renderer("render-words", *words)
                self.assertEqual(run.returncode, 2, run.stdout + run.stderr)
                self.assertIn("BLOCKED", run.stderr)
        valid = self.renderer("render-words", "10", "100", "00", "000", "01")
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(valid.stdout, "(перше ())\n")


if __name__ == "__main__":
    unittest.main()
