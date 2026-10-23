#!/usr/bin/env python3
"""Real approved-manifest -> physical T5 transactions, never text or partial."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/migrate-approved-t5m.py"
SOURCE = ROOT / "tests/fixtures/migration-d1-cond-cohort/branch.lisp"
BINARY = SOURCE.with_suffix(".sens")
REL = SOURCE.relative_to(ROOT).as_posix()


def actual_d2_reader() -> Path:
    advertised = os.environ.get("SENS_TRIT_BIN")
    binary = Path(advertised) if advertised else ROOT / "target/debug/sens-trit"
    if not binary.is_file():
        subprocess.run(["cargo", "build", "-q", "-p", "sens-cli", "--bin", "sens-trit"],
                       cwd=ROOT, check=True, timeout=240)
    if not binary.is_file():
        raise RuntimeError("real Rust sens-trit reader is required for publication tests")
    return binary.resolve()

spec = importlib.util.spec_from_file_location("approved_t5_transaction", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class ApprovedT5TransactionTests(unittest.TestCase):
    def test_current_domain_map_api_is_three_values_and_no_sid8_dispatch(self):
        """CI_GLUE_NO_SEMANTICS: API alignment, not a callable SENS verdict."""
        maps = mod.load_engine_maps(ROOT)
        self.assertEqual(len(maps), 3, "CURRENT_MAP_API_RED expected=my,upper,text7")
        my, upper, text7 = maps
        self.assertTrue(my and upper, "CURRENT_MAP_API_RED missing ratified surfaces")
        self.assertIn("keyboard-v2", text7, "CURRENT_MAP_API_RED D7 v2 missing")
        live = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            "my, upper, _historical_bridge_provenance = engine.build_three_pass_maps(",
            live, "CURRENT_MAP_API_RED third return must remain nonauthoritative",
        )
        self.assertIn(
            "engine.Resolver(my, upper, d9_residents=d9_residents)",
            live, "CURRENT_MAP_API_RED D9 width argument lost",
        )
        self.assertNotIn(
            "engine.Resolver(my, upper, admitted_d8",
            live, "CURRENT_MAP_API_RED retired D8 positional bridge reintroduced",
        )

    def test_true_rust_d2_rejects_t5_transport_valid_invalid_program(self):
        words = ["01"]  # D2 CLOSE alone is transport-valid, grammar-invalid.
        physical = mod.engine.encode_projection("01\n")
        self.assertEqual(mod.engine.decode_bytes(physical), words)
        with self.assertRaisesRegex(mod.engine.SensT5Error, "Rust D2 reader rejected"):
            mod.verify_rust_d2(physical, words, actual_d2_reader())

    def test_missing_reader_blocks_before_publication(self):
        with tempfile.TemporaryDirectory(prefix="approved-t5-no-rust-") as td:
            temp = Path(td)
            manifest = temp / "manifest.json"
            manifest.write_text(json.dumps({"files": [REL]}), encoding="utf-8")
            output = temp / "out"
            result = subprocess.run([
                sys.executable, str(SCRIPT), str(ROOT), "--manifest", str(manifest),
                "--out", str(output), "--report", str(temp / "report.json"),
            ], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires --reader", result.stderr)
            self.assertFalse(output.exists())

    def run_cli(self, temp: Path, entries: list[dict | str], *,
                out: Path | None = None, report: Path | None = None,
                source_era: str | None = None):
        manifest = temp / "manifest.json"
        manifest.write_text(json.dumps({"files": entries}), encoding="utf-8")
        out = out or temp / "output"
        report = report or temp / "report.json"
        command = [sys.executable, str(SCRIPT), str(ROOT), "--manifest", str(manifest),
                   "--out", str(out), "--report", str(report),
                   "--reader", str(actual_d2_reader())]
        if source_era is not None:
            command.extend(["--source-era", source_era])
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=120)
        return proc, out, report

    def test_preexisting_cond_lisp_to_exact_main_binary_and_no_overwrite(self):
        """Actual checked-in .lisp corpus, not an invented example."""
        self.assertTrue(SOURCE.is_file())
        self.assertTrue(BINARY.is_file())
        self.assertEqual(BINARY.read_bytes(), bytes.fromhex("67386515bf123b2dc4a9b1a1"))
        original = SOURCE.read_bytes()
        pin = hashlib.sha256(original).hexdigest()
        with tempfile.TemporaryDirectory(prefix="approved-t5-real-") as td:
            temp = Path(td)
            proc, output, report = self.run_cli(
                temp, [{"path": REL, "sha256": pin}]
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            target = output / SOURCE.relative_to(ROOT).with_suffix(".sens")
            self.assertEqual(target.read_bytes(), BINARY.read_bytes())
            self.assertEqual(target.suffix, ".sens")
            self.assertFalse((output / SOURCE.relative_to(ROOT).with_suffix("")).exists())
            self.assertFalse((output / SOURCE.relative_to(ROOT)).exists())
            record = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(record["summary"]["published"], 1)
            self.assertEqual(record["files"][0]["d2_syntax"], "PASS")
            self.assertEqual(record["files"][0]["semantic_oracle"], "NOT_VERIFIED")
            row = record["files"][0]
            self.assertEqual(row["source_sha256"], pin)
            self.assertEqual(row["typed_word_sha256"], mod.engine.typed_sha256(
                mod.engine.decode_bytes(BINARY.read_bytes())
            ))
            self.assertEqual(row["physical_sha256"], hashlib.sha256(BINARY.read_bytes()).hexdigest())
            self.assertEqual(SOURCE.read_bytes(), original)
            again, _, new_report = self.run_cli(temp, [{"path": REL, "sha256": pin}])
            self.assertEqual(again.returncode, 1)
            self.assertEqual(target.read_bytes(), BINARY.read_bytes())
            self.assertEqual(json.loads(new_report.read_text())["summary"]["published"], 0)

    def test_mixed_valid_and_invalid_never_commits_partial_output(self):
        with tempfile.TemporaryDirectory(prefix="approved-t5-block-") as td:
            temp = Path(td)
            pin = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
            proc, output, report = self.run_cli(temp, [
                {"path": REL, "sha256": pin},
                # Source was migrated and is now valid; an intentionally
                # incorrect pin remains invalid regardless of source-era.
                # This proves mixed-validity publication is atomic.
                {"path": "benchmarks/arithmetic.lisp", "sha256": "0" * 64},
            ])
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            self.assertFalse((output / SOURCE.relative_to(ROOT).with_suffix(".sens")).exists())
            result = json.loads(report.read_text())
            self.assertEqual(result["summary"]["published"], 0)
            self.assertEqual(result["summary"]["files_ready"], 1)
            self.assertEqual(result["summary"]["files_blocked"], 1)

    def test_publication_rejects_missing_zig_without_creating_carrier(self):
        # A working Rust D2 reader cannot replace the sole Zig physical mint.
        with tempfile.TemporaryDirectory(prefix="approved-t5-no-zig-") as td:
            temp = Path(td)
            manifest = temp / "manifest.json"
            manifest.write_text(json.dumps({"files": [{"path": REL,
                "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest()}]}))
            output = temp / "output"
            result = subprocess.run([
                sys.executable, str(SCRIPT), str(ROOT), "--manifest", str(manifest),
                "--out", str(output), "--report", str(temp / "report.json"),
                "--reader", str(actual_d2_reader()),
            ], cwd=ROOT, capture_output=True, text=True, timeout=120,
                env={**os.environ, "ZIG": str(temp / "missing-zig")})
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertFalse(list(output.rglob("*.sens")) if output.exists() else False)
            receipt = json.loads((temp / "report.json").read_text())
            self.assertEqual(receipt["summary"]["published"], 0)
            self.assertIn("ZIG_CODEC_UNAVAILABLE", receipt["files"][-1]["reason"])

    def test_migration_requires_zig_minted_bytes_not_python_reference(self):
        from unittest import mock
        maps = mod.load_engine_maps(ROOT)
        original = SOURCE.read_bytes()
        with mock.patch.object(mod.bridge, "carry_t5",
                               side_effect=mod.bridge.ZigCodecError("ZIG_MINT_FAILED")):
            with self.assertRaisesRegex(mod.bridge.ZigCodecError, "ZIG_MINT_FAILED"):
                mod.migrate_one(SOURCE, ROOT, maps, original,
                                zig_binary=Path("provided-attested-binary"))
        with mock.patch.object(mod.bridge, "carry_t5", return_value=b"wrong"):
            with self.assertRaisesRegex(mod.engine.SensT5Error,
                                         "ZIG_MIGRATION_REFERENCE_MISMATCH"):
                mod.migrate_one(SOURCE, ROOT, maps, original,
                                zig_binary=Path("provided-attested-binary"))

    def test_wrong_sha_and_traversal_are_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="approved-t5-sha-") as td:
            temp = Path(td)
            proc, output, report = self.run_cli(temp, [
                {"path": REL, "sha256": "0" * 64},
            ])
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(json.loads(report.read_text())["summary"]["published"], 0)
            self.assertFalse((output / SOURCE.relative_to(ROOT).with_suffix(".sens")).exists())
            proc, output, report = self.run_cli(temp, ["../evil.lisp"])
            self.assertEqual(proc.returncode, 1)
            self.assertFalse(list(output.rglob("*.sens")) if output.exists() else False)

    def test_snapshot_is_same_byte_sequence_hashed_and_translated(self):
        maps = mod.load_engine_maps(ROOT)
        original = SOURCE.read_bytes()
        with tempfile.TemporaryDirectory(prefix="approved-t5-snapshot-") as td:
            temp = Path(td)
            source = temp / "branch.lisp"
            source.write_bytes(original)
            # A concurrent edit after snapshot is supplied must NOT create
            # a result whose claimed SHA comes from the other file contents.
            source.write_text("(unmapped runtime function)\n", encoding="utf-8")
            dest, physical, row = mod.migrate_one(source, temp, maps, original)
            self.assertEqual(dest, Path("branch.sens"))
            self.assertEqual(physical, BINARY.read_bytes())
            self.assertEqual(row["source_sha256"], hashlib.sha256(original).hexdigest())
            self.assertNotEqual(row["source_sha256"],
                                hashlib.sha256(source.read_bytes()).hexdigest())

    def test_never_write_mirror_or_report_inside_source_repository(self):
        with tempfile.TemporaryDirectory(prefix="approved-t5-root-") as td:
            temp = Path(td)
            manifest = temp / "manifest.json"
            manifest.write_text(json.dumps({"files": [REL]}))
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), str(ROOT),
                 "--manifest", str(manifest),
                 "--out", str(ROOT / "unsafe-publish"),
                 "--report", str(temp / "report.json")],
                cwd=ROOT, capture_output=True, text=True, timeout=120
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("OUTSIDE the source repository", proc.stderr)


if __name__ == "__main__":
    unittest.main()
