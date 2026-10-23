#!/usr/bin/env python3
"""Перевірки фізичної міграції від доведеного D1/D3 SENS-свідка до Zig T5M."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.sens_t5_t5m_codec import decode_t5m_bytes, encode_t5m_projection

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migrate-one-to-sens.py"
PROVEN = ROOT / "tests" / "fixtures" / "migration-d1-cond-cohort" / "branch.lisp"
EXISTING = PROVEN.with_suffix(".sens")


def invoke(source: Path, *args: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(source), *args],
        cwd=ROOT, capture_output=True, text=True
    )


class CanonicalOneFileMigration(unittest.TestCase):
    def test_zastarilyi_t5_ne_publikuie_sens(self):
        # Історичний T5 не карбує нових виконуваних файлів.
        original = PROVEN.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-t5-retired-") as td:
            target = Path(td) / "branch.sens"
            attempt = invoke(PROVEN, "--output", str(target), "--codec", "t5")
            self.assertNotEqual(attempt.returncode, 0)
            self.assertIn("LEGACY_T5_PUBLICATION_DISABLED", attempt.stderr)
            self.assertFalse(target.exists())
            self.assertFalse(target.with_suffix("").exists())
        self.assertEqual(PROVEN.read_bytes(), original)

    def test_existing_d1_d3_canary_dry_run_does_not_write(self):
        before = PROVEN.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "branch.sens"
            result = invoke(PROVEN, "--output", str(target), "--dry-run",
                            "--codec", "t5m", "--source-surface", "ук")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            state = json.loads(result.stdout)
            self.assertEqual(state["status"], "would-write")
            self.assertEqual(state["codec"], "t5m")
            self.assertEqual(state["physical_producer"], "PYTHON_REFERENCE_ONLY")
            self.assertIsNone(state["zig_transport"])
            self.assertEqual(state["semantic_parity"], "NOT_VERIFIED")
            self.assertGreater(state["bytes"], 0)
            self.assertEqual(len(state["physical_sha256"]), 64)
            self.assertFalse(target.exists())
            self.assertFalse(target.with_suffix("").exists())
        self.assertEqual(PROVEN.read_bytes(), before)

    def test_unadmitted_string_preserves_real_source_error(self):
        """Do not silently encode an unrepresentable Lisp string as D3 EMPTY."""
        source = ROOT / "lib" / "surface" / "ukr-acceptance.lisp"
        original = source.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ukr-acceptance.sens"
            result = invoke(source, "--output", str(target),
                            "--codec", "t5m", "--source-surface", "ук", "--dry-run")
            self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertIn("STRING_LITERAL_UNADMITTED", report["reason"])
            self.assertEqual(report["token"], '""')
            self.assertFalse(target.exists())
        self.assertEqual(source.read_bytes(), original)

    def test_existing_target_is_never_overwritten(self):
        before = EXISTING.read_bytes()
        result = invoke(PROVEN, "--codec", "t5m", "--source-surface", "укр")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing overwrite", result.stderr)
        self.assertEqual(EXISTING.read_bytes(), before)

    def test_existing_view_does_not_leave_orphan_physical_carrier(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "branch.sens"
            view = output.with_suffix("")
            view.write_bytes(b"preexisting view\\n")
            result = invoke(PROVEN, "--output", str(output), "--codec", "t5m", "--source-surface", "укр")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing overwrite", result.stderr)
            self.assertFalse(output.exists())
            self.assertEqual(view.read_bytes(), b"preexisting view\\n")

    def test_d1_d3_binary_staging_agrees_with_current_canonical_three_pass(self):
        before = PROVEN.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "branch.sens"
            result = invoke(PROVEN, "--output", str(output),
                            "--codec", "t5m", "--source-surface", "ук")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "written")
            self.assertEqual(report["codec"], "t5m")
            self.assertEqual(report["semantic_parity"], "NOT_VERIFIED")
            self.assertEqual(report["source"], str(PROVEN.relative_to(ROOT)))
            data = output.read_bytes()
            words = decode_t5m_bytes(data)
            self.assertGreater(len(words), 0)
            self.assertEqual(data, encode_t5m_projection(" ".join(words) + "\n"))
            self.assertEqual(report["bytes"], len(data))
            view = output.with_suffix("")
            expected_view = (" ".join(words) + "\n").encode("ascii")
            self.assertEqual(view.read_bytes(), expected_view)
            self.assertEqual(report["view"], str(view))
            self.assertEqual(report["view_sha256"], hashlib.sha256(expected_view).hexdigest())
            self.assertEqual(report["physical_sha256"], hashlib.sha256(data).hexdigest())
            self.assertIsInstance(report["zig_transport"], dict)
            second = invoke(PROVEN, "--output", str(output),
                            "--codec", "t5m", "--source-surface", "ук")
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("refusing overwrite", second.stderr)
            self.assertEqual(output.read_bytes(), data)
            self.assertEqual(view.read_bytes(), expected_view)
        self.assertEqual(PROVEN.read_bytes(), before)

    def test_explicit_refresh_replaces_stale_d1_d3_carrier_and_view_pair(self):
        source_before = PROVEN.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "branch.sens"
            view = output.with_suffix("")
            output.write_bytes(b"stale physical carrier")
            view.write_bytes(b"stale extensionless view\\n")

            result = invoke(PROVEN, "--output", str(output), "--codec", "t5m",
                            "--source-surface", "ук", "--replace-existing")
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["status"], "replaced")
            self.assertEqual(report["target_action"], "replace-existing-pair")
            words = decode_t5m_bytes(output.read_bytes())
            self.assertGreater(len(words), 0)
            self.assertEqual(output.read_bytes(), encode_t5m_projection(" ".join(words) + "\n"))
            expected_view = (" ".join(words) + "\n").encode("ascii")
            self.assertEqual(view.read_bytes(), expected_view)
            self.assertNotEqual(output.read_bytes(), b"stale physical carrier")
            self.assertNotEqual(view.read_bytes(), b"stale extensionless view\\n")

            physical_after, view_after = output.read_bytes(), view.read_bytes()
            refused = invoke(PROVEN, "--output", str(output), "--codec", "t5m",
                             "--source-surface", "ук")
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("refusing overwrite", refused.stderr)
            self.assertEqual(output.read_bytes(), physical_after)
            self.assertEqual(view.read_bytes(), view_after)
        self.assertEqual(PROVEN.read_bytes(), source_before)

    def test_batch_zig_t5m_refresh_existing_pair_preserves_exact_words(self):
        # Реальний pinned Zig + той самий мігратор, не Python-симуляція.
        source_before = PROVEN.read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-batch-t5m-refresh-") as td:
            out = Path(td)
            carrier, view = out / "branch.sens", out / "branch"
            report_path = out / "batch-report.json"
            stale_carrier, stale_view = b"stale T5M", b"stale spaced view\n"
            carrier.write_bytes(stale_carrier)
            view.write_bytes(stale_view)
            command = [
                sys.executable, str(ROOT / "scripts/migrate-three-pass.py"),
                str(PROVEN), "--out", str(out), "--report", str(report_path),
                "--codec", "t5m", "--source-surface", "ук",
            ]

            denied = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True
            )
            self.assertEqual(denied.returncode, 2, denied.stderr + denied.stdout)
            self.assertEqual(carrier.read_bytes(), stale_carrier)
            self.assertEqual(view.read_bytes(), stale_view)

            updated = subprocess.run(
                command + ["--refresh-existing"], cwd=ROOT,
                capture_output=True, text=True
            )
            self.assertEqual(updated.returncode, 0, updated.stderr + updated.stdout)
            receipt = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["mode"], "refresh-existing-zig-minted")
            self.assertEqual(receipt["summary"]["files_written"], 1)
            self.assertEqual(receipt["summary"]["files_blocked"], 0)
            self.assertEqual(receipt["files"][0]["status"], "refreshed")
            self.assertIsInstance(receipt["files"][0]["zig_transport"], dict)
            physical = carrier.read_bytes()
            words = decode_t5m_bytes(physical)
            self.assertTrue(words)
            self.assertEqual(
                physical, encode_t5m_projection(" ".join(words) + "\n")
            )
            self.assertEqual(
                view.read_bytes(), (" ".join(words) + "\n").encode("ascii")
            )
            self.assertNotEqual(physical, stale_carrier)
            self.assertNotEqual(view.read_bytes(), stale_view)
        self.assertEqual(PROVEN.read_bytes(), source_before)

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
            result = invoke(source, "--codec", "t5m", "--source-surface", "укр", "--output", str(target))
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
        result = invoke(source, "--dry-run", "--codec", "t5m", "--source-surface", "укр")
        self.assertNotIn("in-repository publication needs independent",
                         result.stderr)
        self.assertEqual(source.read_bytes(), source_before)
        if target_before is None:
            self.assertFalse(target.exists() or target.is_symlink(),
                             "dry-run must not create a physical .sens")
        else:
            self.assertEqual(target.read_bytes(), target_before,
                             "dry-run must preserve pre-existing physical .sens")

    def test_peer_identity_uses_current_ukrainian_projection_without_legacy_snapshot(self):
        """Сучасне джерело не повинно відповідати старій помилці mixed-script.

        Це тільки перевірка мігратора, а не доказ виконання SENS чи
        семантичного допуску. Недоведена залежність лишається BLOCKED.
        """
        source = ROOT / "lib" / "surface" / "peer-identity-acceptance.lisp"
        before = source.read_bytes()
        target = source.with_suffix(".sens")
        view = source.with_suffix("")
        target_before = target.read_bytes() if target.is_file() else None
        view_before = view.read_bytes() if view.is_file() else None

        result = invoke(source, "--dry-run", "--codec", "t5m",
                        "--source-surface", "укр")
        self.assertIn(result.returncode, (0, 2), result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertEqual(report["source"], "lib/surface/peer-identity-acceptance.lisp")
        self.assertEqual(report["codec"], "t5m")
        self.assertNotIn("mixed-script identifier", report.get("reason", ""))
        if result.returncode == 0:
            self.assertEqual(report["status"], "would-write")
            self.assertEqual(report["physical_producer"], "PYTHON_REFERENCE_ONLY")
            self.assertEqual(report["semantic_parity"], "NOT_VERIFIED")
            self.assertIsNone(report["zig_transport"])
        else:
            self.assertEqual(report["status"], "blocked")
            self.assertTrue(report["reason"], "Непідтверджена залежність повинна мати діагноз")

        # Позитивний preview і явна відмова однаково не публікують носій.
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(target.read_bytes() if target.is_file() else None, target_before)
        self.assertEqual(view.read_bytes() if view.is_file() else None, view_before)

    def test_source_symlink_cannot_hide_original_identity(self):
        # A link into the repo must not silently become the canonical source path.
        with tempfile.TemporaryDirectory() as td:
            alias = Path(td) / "alias.lisp"
            alias.symlink_to(PROVEN)
            before = PROVEN.read_bytes()
            result = invoke(alias, "--dry-run", "--codec", "t5m", "--source-surface", "ук")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source path contains symlink", result.stderr)
            self.assertEqual(PROVEN.read_bytes(), before)

    def test_dangling_output_symlink_does_not_publish_to_other_target(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            actual = base / "unrequested.sens"
            alias = base / "requested.sens"
            alias.symlink_to(actual)
            result = invoke(PROVEN, "--output", str(alias), "--codec", "t5m", "--source-surface", "ук")
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
                            "--codec", "t5m", "--source-surface", "ук")
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
