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
SCRIPT = ROOT / "scripts/migrate-approved-t5.py"
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

    def test_current_d8_and_historical_sid8_must_not_be_conflated(self):
        # Owner's explicit 14-Oct rule removed the VACUOUS automatic W8 block
        # (commit 61417273). The checked-in corpus carries historical SID8,
        # not modern D8 source. Do NOT silently reinstall that obsolete guard.
        # Instead prove the actual transport: auto == explicit historical,
        # current D8 remains exact, and a one-bit unknown SID8 FAILS CLOSED.
        third = ROOT / "tests/fixtures/core1-third-domain-canary/third.lisp"
        original = third.read_bytes()
        encoded = third.with_suffix(".sens").read_bytes()
        self.assertEqual(len(encoded), 38)
        rel = third.relative_to(ROOT).as_posix()
        pin = hashlib.sha256(original).hexdigest()
        entry = [{"path": rel, "sha256": pin}]
        with tempfile.TemporaryDirectory(prefix="approved-t5-provenance-") as td:
            temp = Path(td)
            automatic, out, report = self.run_cli(temp, entry)
            self.assertEqual(automatic.returncode, 0, automatic.stdout + automatic.stderr)
            auto_report = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(auto_report["source_era"], "auto")
            self.assertEqual(auto_report["summary"]["published"], 1)
            self.assertEqual(auto_report["files"][0]["source_era"], "auto")
            self.assertGreater(auto_report["files"][0]["passes"]["pass1-sens8"], 0)
            self.assertEqual(auto_report["files"][0]["semantic_oracle"], "NOT_VERIFIED")
            target = out / third.relative_to(ROOT).with_suffix(".sens")
            self.assertEqual(target.read_bytes(), encoded)
            self.assertEqual(
                auto_report["files"][0]["physical_sha256"],
                hashlib.sha256(encoded).hexdigest(),
            )

            # Explicit historical mode must emit exactly the same T5 bytes,
            # without replacing the automatically published file.
            historical, legacy_out, legacy_report = self.run_cli(
                temp, entry, out=temp / "legacy-output",
                report=temp / "legacy-report.json", source_era="legacy",
            )
            self.assertEqual(historical.returncode, 0, historical.stdout + historical.stderr)
            self.assertEqual(
                (legacy_out / third.relative_to(ROOT).with_suffix(".sens")).read_bytes(),
                encoded,
            )
            self.assertEqual(json.loads(legacy_report.read_text())["source_era"], "legacy")
            self.assertEqual(target.read_bytes(), encoded)

        # Current D8 is a DIFFERENT exact domain from the historical
        # successor. This tests identity preservation, not Rust/Python callability.
        legacy, my, upper, _ = mod.load_engine_maps(ROOT)
        foundation = mod.engine.load_foundation(ROOT / "knowledge/d1-d9-foundation.json")
        d8 = foundation["domains"]["D8"]["residents"]
        tok = mod.engine.Tok("ATOM", "10000000", 0)
        auto = mod.engine.Resolver(legacy, my, upper, "auto", d8)
        current = mod.engine.Resolver(legacy, my, upper, "current", d8)
        historical_words, historical_pass = auto.head(tok)
        current_words, current_pass = current.head(tok)
        self.assertEqual(current_words, ["10000000"])
        self.assertEqual(current_pass, "already-exact")
        self.assertEqual(historical_pass, "pass1-sens8")
        self.assertNotEqual(historical_words, current_words)

        # Real historical QUOTE head 00000001 -> 00000000 is a single-bit
        # mutant with NO mapped SID8 identity. No fallback to current D8
        # or an assumed semantic meaning may occur, even on an SHA snapshot.
        self.assertIn(b"00000001", original)
        mutant = original.replace(b"00000001", b"00000000", 1)
        self.assertEqual(len(mutant), len(original))
        changed_bits = sum(
            (left ^ right).bit_count() for left, right in zip(mutant, original)
        )
        self.assertEqual(changed_bits, 1)
        with self.assertRaisesRegex(
            mod.engine.MigrationError, "legacy-unmapped SID8/Sens8 00000000"
        ):
            mod.migrate_one(third, ROOT, mod.load_engine_maps(ROOT), mutant,
                            source_era="auto")
        self.assertEqual(third.read_bytes(), original)

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
