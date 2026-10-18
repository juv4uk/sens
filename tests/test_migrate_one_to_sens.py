#!/usr/bin/env python3
"""Перевірки фізичної міграції з української Lisp-проєкції в Zig T5M."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.sens_t5_codec import decode_t5m_bytes, encode_t5m_projection

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-one-to-sens.py"
PROVEN = ROOT / "lib" / "surface" / "ukr-acceptance.lisp"
EXISTING = PROVEN.with_suffix(".sens")


def invoke(source: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(source), *args],
        cwd=ROOT, capture_output=True, text=True
    )


class CanonicalOneFileMigration(unittest.TestCase):
    def test_real_proven_canary_dry_run_does_not_write(self):
        before = PROVEN.read_bytes()
        result = invoke(PROVEN, "--dry-run", "--codec", "t5", "--source-surface", "default")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        state = json.loads(result.stdout)
        self.assertEqual(state["status"], "would-write")
        self.assertEqual(state["semantic_parity"], "NOT_VERIFIED")
        self.assertEqual(state["codec"], "t5")
        self.assertEqual(state["physical_sha256"], hashlib.sha256(encode_t5m_projection(" ".join(state["words"]) + "\n")).hexdigest())
        self.assertEqual(PROVEN.read_bytes(), before)

    def test_existing_target_is_never_overwritten(self):
        before = EXISTING.read_bytes()
        result = invoke(PROVEN, "--codec", "t5", "--source-surface", "default")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing overwrite", result.stderr)
        self.assertEqual(EXISTING.read_bytes(), before)

    def test_existing_view_does_not_leave_orphan_physical_carrier(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "ukr-acceptance.sens"
            view = output.with_suffix("")
            view.write_bytes(b"preexisting view\\n")
            result = invoke(PROVEN, "--output", str(output), "--codec", "t5", "--source-surface", "default")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing overwrite", result.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(view.read_bytes(), b"preexisting view\\n")

    def test_real_binary_staging_agrees_with_current_canonical_three_pass(self):
        before = PROVEN.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "ukr-acceptance.sens"
            result = invoke(PROVEN, "--output", str(output), "--codec", "t5", "--source-surface", "default")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "written")
            self.assertEqual(report["semantic_parity"], "NOT_VERIFIED")
            self.assertEqual(report["source"], str(PROVEN.relative_to(ROOT)))
            self.assertEqual(report["bytes"], len(output.read_bytes()))
            self.assertEqual(decode_t5m_bytes(output.read_bytes()), report["words"])
            self.assertEqual(output.read_bytes(), encode_t5m_projection(" ".join(report["words"]) + "\n"))
            self.assertTrue(output.with_suffix("").is_file())
            self.assertEqual(report["view_sha256"], hashlib.sha256(output.with_suffix("").read_bytes()).hexdigest())
            view = output.with_suffix("")
            expected_view = (" ".join(report["words"]) + "\n").encode("ascii")
            self.assertEqual(view.read_bytes(), expected_view)
            self.assertEqual(report["view"], str(view))
            self.assertEqual(report["view_sha256"], hashlib.sha256(expected_view).hexdigest())
            self.assertEqual(report["physical_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            second = invoke(PROVEN, "--output", str(output), "--codec", "t5", "--source-surface", "default")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("refusing overwrite", second.stderr)
        self.assertEqual(PROVEN.read_bytes(), before)

    def test_unknown_ukrainian_identifiers_are_not_encoded_as_fake_calls(self):
        # A genuinely unknown Ukrainian head must fail closed, never become a
        # fake call or unstructured text. The former fixture
        # lib/surface/ukr-acceptance.lisp is now a registered, migrated pair
        # (it has a committed .sens and its identifiers are registered ukr
        # surfaces), so it no longer demonstrates an unknown identifier.
        source = ROOT / "tests" / "fixtures" / "unknown-uk-head.lisp"
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "unknown-uk-head.sens"
            result = invoke(source, "--codec", "t5", "--source-surface", "default", "--output", str(target))
            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "blocked")
            self.assertIn("reason", report)
            self.assertFalse(target.exists())
        self.assertEqual(source.read_bytes(), before)

    def test_in_repository_publication_is_not_policy_blocked(self):
        # Owner decision permits repository targets. This policy test must
        # never publish or delete an existing canonical physical .sens file.
        # Actual write-new-only and no-clobber are tested independently.
        source = ROOT / "benchmarks" / "lists.lisp"
        target = source.with_suffix(".sens")
        source_before = source.read_bytes()
        target_before = target.read_bytes() if target.is_file() else None
        result = invoke(source, "--dry-run", "--codec", "t5", "--source-surface", "default")
        self.assertNotIn("in-repository publication needs independent",
                         result.stderr)
        self.assertEqual(source.read_bytes(), source_before)
        if target_before is None:
            self.assertFalse(target.exists() or target.is_symlink(),
                             "dry-run must not create a physical .sens")
        else:
            self.assertEqual(target.read_bytes(), target_before,
                             "dry-run must preserve pre-existing physical .sens")

    def test_peer_identity_requires_loaded_surface_environment(self):
        """A single-file staging tool must not invent imports from core/uk.lisp.

        This historical witness explicitly requires the peer bindings to be
        loaded before evaluating it.  The current D1-D9 word migrator cannot
        attest that `модуль` and `abs` refer to one executable identity, so the
        D7 keyboard/v2 mixed-script guard rejects it instead of guessing.
        A missing environment is a real BLOCK, never physical admission.
        """
        source = ROOT / "lib" / "surface" / "peer-identity-acceptance.lisp"
        target = source.with_suffix(".sens")
        original_source = source.read_bytes()
        result = invoke(source, "--dry-run")
        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["codec"], "t5m")
        self.assertEqual(report["output"], "lib/surface/peer-identity-acceptance.sens")
        self.assertIn("mixed-script identifier is ambiguous", report["reason"])
        self.assertFalse(target.exists(), "blocked staging must not emit physical SENS")
        self.assertEqual(source.read_bytes(), original_source)

    def test_source_symlink_cannot_hide_original_identity(self):
        # A link into the repo must not silently become the canonical source path.
        with tempfile.TemporaryDirectory() as td:
            alias = Path(td) / "alias.lisp"
            alias.symlink_to(PROVEN)
            before = PROVEN.read_bytes()
            result = invoke(alias, "--dry-run", "--codec", "t5", "--source-surface", "default")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source path contains symlink", result.stderr)
            self.assertEqual(PROVEN.read_bytes(), before)

    def test_dangling_output_symlink_does_not_publish_to_other_target(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            actual = base / "unrequested.sens"
            alias = base / "requested.sens"
            alias.symlink_to(actual)
            result = invoke(PROVEN, "--output", str(alias), "--codec", "t5", "--source-surface", "default")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("output path contains symlink", result.stderr)
            self.assertTrue(alias.is_symlink())
            self.assertFalse(actual.exists(), "symlink must not redirect physical T5 publication")

    def test_output_parent_symlink_does_not_redirect_publication(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            actual_dir = base / "actual"
            actual_dir.mkdir()
            alias_dir = base / "alias"
            alias_dir.symlink_to(actual_dir, target_is_directory=True)
            result = invoke(PROVEN, "--output", str(alias_dir / "data.sens"),
                            "--codec", "t5", "--source-surface", "default")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("output path contains symlink", result.stderr)
            self.assertFalse((actual_dir / "data.sens").exists())

    def test_source_outside_repository_is_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "outside.lisp"
            source.write_text("000\n", encoding="utf-8")
            result = invoke(source, "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside the repository", result.stderr)


if __name__ == "__main__":
    unittest.main()
