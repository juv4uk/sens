#!/usr/bin/env python3
"""Нинішня пакетна міграція D1–D11/T5M: транспортні й негативні перевірки.

Не підміняє SENS eval, не робить Python семантичним оракулом і
не оголошує жодне джерело допущеним до релізу.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
DRIVER = SCRIPTS / "migrate-t5m-batch.py"
FIXTURE = REPO / "tests/fixtures/migration-d1-cond-cohort/branch"
SPEC = importlib.util.spec_from_file_location("sens_t5m_current_batch", DRIVER)
assert SPEC is not None and SPEC.loader is not None
batch = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = batch
SPEC.loader.exec_module(batch)

from sens_t5_t5m_codec import decode_t5m_bytes, encode_t5m_projection, typed_sha256


class CurrentBatchTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-batch-current-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "input"
        (self.root / "lib").mkdir(parents=True)
        self.source = self.root / "lib/branch.lisp"
        shutil.copyfile(FIXTURE.with_suffix(".lisp"), self.source)
        self.out = self.base / "out"
        self.report = self.base / "report.json"

    def call(self, *paths, write=False, zig=False, era="auto", out=None):
        return subprocess.run([
            sys.executable, str(DRIVER),
            *(paths or ("lib/branch.lisp",)),
            "--root", str(self.root), "--out", str(out or self.out),
            "--report", str(self.report), "--source-era", era,
            *(["--zig-codec"] if zig else []),
            *(["--write"] if write else []),
        ], cwd=REPO, capture_output=True, text=True, timeout=25)

    def test_d11_current_authority_and_t5m_are_the_only_batch_defaults(self):
        self.assertEqual(batch.INPUTS["foundation"],
                         REPO / "knowledge/d1-d11-foundation.json")
        self.assertEqual(len(batch.mig.load_foundation(batch.INPUTS["foundation"])
                             ["domains"]["D10"]["residents"]), 1024)
        # Ratification does not grant runtime callability or release admission.
        self.assertNotEqual(batch.INPUTS["foundation"],
                            REPO / "knowledge/d1-d9-foundation.json")
        self.assertNotIn("historical_map", batch.INPUTS)
        self.assertNotIn("legacy_coverage", batch.INPUTS)

    def test_real_fixture_has_independent_exact_physical_t5m_roundtrip(self):
        # Mechanism-only codec proof, NEVER an evaluator or semantic proof.
        view = FIXTURE.read_text(encoding="ascii")
        words = view.strip().split(" ")
        physical = encode_t5m_projection(view)
        self.assertEqual(decode_t5m_bytes(physical), words)
        self.assertEqual(len(typed_sha256(words)), 64)
        self.assertNotEqual(physical, view.encode("ascii"))

    def test_dry_run_uses_t5m_without_creating_physical_outputs(self):
        original = self.source.read_bytes()
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(self.report.is_file())
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual(report["summary"]["files_seen"], 1)
        self.assertEqual(report["summary"]["files_written"], 0)
        self.assertEqual(report["summary"]["files_would_write"], 1, report)
        self.assertEqual(report["authority"]["codec"],
                         "physical-T5M-5-trits-per-byte")
        self.assertEqual(report["authority"]["source_era"], "auto")
        self.assertEqual(report["files"][0]["status"], "would-write")
        self.assertFalse(self.out.exists())
        self.assertEqual(self.source.read_bytes(), original)

    def test_batch_output_in_repo_is_documented_without_semantic_admission(self):
        help_result = subprocess.run(
            [sys.executable, str(DRIVER), "--help"],
            cwd=REPO, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("дозволено і корінь джерел", help_result.stdout)
        self.assertNotIn("never source root", help_result.stdout)
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertTrue(report["mechanical_only"])
        self.assertIs(report["semantic_runtime_verified_by_this_tool"], False)
        self.assertIs(report["release_admitted_by_this_tool"], False)
        self.assertEqual(
            report["summary"]["mechanically_packable_files"],
            report["summary"]["files_would_write"],
        )

    def test_neither_legacy_source_era_nor_python_bytes_can_publish(self):
        old = self.call(era="legacy")
        self.assertEqual(old.returncode, 3, old.stdout + old.stderr)
        self.assertIn("RETIRED_SID8_SOURCE_ERA", old.stderr)
        unauthorized = self.call(write=True)
        self.assertEqual(unauthorized.returncode, 3,
                         unauthorized.stdout + unauthorized.stderr)
        self.assertIn("--zig-codec", unauthorized.stderr)
        self.assertFalse((self.out / "lib/branch.sens").exists())
        self.assertFalse((self.out / "lib/branch").exists())

    def test_unrepresentable_source_is_blocked_instead_of_minted(self):
        unknown = self.root / "lib/unknown.lisp"
        unknown.write_text("(НЕВІДОМА_☃ ())\n", encoding="utf-8")
        p = self.call("lib/unknown.lisp")
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        state = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(state["summary"]["files_admitted"], 0)
        self.assertEqual(state["summary"]["files_blocked"], 1)
        self.assertEqual(state["files"][0]["status"], "blocked")
        self.assertFalse((self.out / "lib/unknown.sens").exists())

    def test_unsafe_paths_fail_but_in_repo_output_is_not_a_blocker(self):
        forbidden = self.root / "lib/link.lisp"
        forbidden.symlink_to(self.source)
        for path in ("../escape.lisp", "lib/link.lisp", "missing.lisp", ""):
            with self.subTest(path=path):
                p = self.call(path)
                self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)

        original = self.source.read_bytes()
        for mirror in (self.root, self.root / "published"):
            with self.subTest(mirror=str(mirror)):
                result = self.call(out=mirror)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                report = json.loads(self.report.read_text(encoding="utf-8"))
                self.assertEqual(report["summary"]["files_would_write"], 1)
                self.assertEqual(report["summary"]["files_written"], 0)
                self.assertFalse((mirror / "lib/branch.sens").exists())
        self.assertFalse((self.root / "published").exists())
        self.assertEqual(self.source.read_bytes(), original)

    def test_root_dot_is_an_explicit_safe_batch_selection(self):
        result = self.call(".", out=self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(self.report.read_text(encoding="utf-8"))
        self.assertEqual(report["summary"]["files_seen"], 1)
        self.assertEqual(report["summary"]["files_would_write"], 1)
        self.assertEqual(report["files"][0]["path"], "lib/branch.lisp")
        self.assertFalse(self.source.with_suffix(".sens").exists())


if __name__ == "__main__":
    unittest.main()
