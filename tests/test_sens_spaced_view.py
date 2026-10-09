#!/usr/bin/env python3
"""#4694: фізичний .sens <-> людиночитаний view з exact-width словами."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sens_spaced_view as view
from sens_t5_codec import SensT5Error, decode_bytes, encode_words

FIXTURE = ROOT / "tests/fixtures/migration-d1-cond-cohort"
EXPECTED = "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01\n"
T5_HEX = "67386515bf123b2dc4a9b1a1"


class PhysicalSpacedViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sens-spaced-view-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.root = self.work / "repository"
        self.directory = self.root / "fixtures"
        self.directory.mkdir(parents=True)
        self.source = self.directory / "branch.lisp"
        self.sens = self.directory / "branch.sens"
        self.plain = self.directory / "branch"
        self.source.write_bytes((FIXTURE / "branch.lisp").read_bytes())
        self.sens.write_bytes((FIXTURE / "branch.sens").read_bytes())
        self.plain.write_bytes((FIXTURE / "branch").read_bytes())

    def test_committed_fixture_is_exact_three_file_witness(self):
        self.assertEqual((FIXTURE / "branch").read_bytes(), EXPECTED.encode("ascii"))
        self.assertEqual((FIXTURE / "branch.sens").read_bytes(), bytes.fromhex(T5_HEX))
        self.assertEqual(view.render_view(decode_bytes(self.sens.read_bytes())),
                         self.plain.read_bytes())
        self.assertEqual(encode_words(view.parse_view(self.plain.read_bytes())),
                         self.sens.read_bytes())
        record = view.check_or_stage(self.root, "fixtures/branch.sens")
        self.assertEqual(record["status"], "VERIFY")
        self.assertEqual(record["words"], 19)
        self.assertEqual(record["physical_bytes"], 12)
        self.assertEqual(record["semantic_oracle"], "NOT_VERIFIED_BY_VIEW_TOOL")
        self.assertFalse(record["release_admitted"])

    def test_no_clobber_stage_outside_repository(self):
        output = self.work / "staging"
        output.mkdir()
        result = view.check_or_stage(self.root, "fixtures/branch.sens", stage=output)
        self.assertEqual(result["status"], "STAGED_NO_CLOBBER")
        self.assertEqual((output / "fixtures/branch").read_bytes(), EXPECTED.encode("ascii"))
        self.assertEqual(self.plain.read_bytes(), EXPECTED.encode("ascii"))
        with self.assertRaises(view.ViewError):
            view.check_or_stage(self.root, "fixtures/branch.sens", stage=output)

    def test_preview_stage_never_writes_and_rejects_existing_target(self):
        output = self.work / "preview-stage"
        output.mkdir()
        source_before = self.source.read_bytes()
        sens_before = self.sens.read_bytes()
        receipt = view.check_or_stage(
            self.root, "fixtures/branch.sens", stage=output, preview=True
        )
        self.assertEqual(receipt["status"], "PREVIEW_NO_WRITE")
        self.assertFalse((output / "fixtures").exists())
        self.assertEqual(receipt["d2_reader"], "NOT_CHECKED")
        self.assertFalse(receipt["release_admitted"])
        self.assertEqual(self.source.read_bytes(), source_before)
        self.assertEqual(self.sens.read_bytes(), sens_before)
        dest = output / "fixtures/branch"
        dest.parent.mkdir()
        dest.write_bytes(b"stale")
        with self.assertRaisesRegex(view.ViewError, "overwrite"):
            view.check_or_stage(self.root, "fixtures/branch.sens",
                                stage=output, preview=True)
        self.assertEqual(dest.read_bytes(), b"stale")

    def test_optional_rust_reader_still_blocks_false_D2_program(self):
        dummy = self.work / "sens-trit"
        dummy.write_bytes(b"fake binary")
        with patch.object(view.subprocess, "run", return_value=subprocess.CompletedProcess(
                ["sens-trit", "open"], 2, b"", b"InvalidProgramSyntax")):
            with self.assertRaisesRegex(view.ViewError, "Rust D2"):
                view.check_or_stage(self.root, "fixtures/branch.sens", reader=dummy)
        expected = EXPECTED.encode("ascii")
        with patch.object(view.subprocess, "run", return_value=subprocess.CompletedProcess(
                ["sens-trit", "open"], 0, expected, b"")):
            receipt = view.check_or_stage(self.root, "fixtures/branch.sens", reader=dummy)
            self.assertEqual(receipt["d2_reader"], "PASS")
        with patch.object(view.subprocess, "run", return_value=subprocess.CompletedProcess(
                ["sens-trit", "open"], 0, b"0 00\n", b"")):
            with self.assertRaisesRegex(view.ViewError, "Rust D2"):
                view.check_or_stage(self.root, "fixtures/branch.sens", reader=dummy)

    @unittest.skipUnless(os.environ.get("SENS_VIEW_READER"), "actual Rust reader provided in focused CI")
    def test_real_rust_reader_preview_and_verify_cli(self):
        reader = os.environ["SENS_VIEW_READER"]
        staging = self.work / "actual-preview"
        staging.mkdir()
        script = ROOT / "scripts/sens_spaced_view.py"
        cmd = [sys.executable, str(script), "--root", str(self.root),
               "--sens", "fixtures/branch.sens", "--reader", reader,
               "--preview-stage", str(staging)]
        process = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertFalse((staging / "fixtures").exists())
        receipt = json.loads(process.stdout)
        self.assertEqual(receipt["status"], "PREVIEW_NO_WRITE")
        self.assertEqual(receipt["d2_reader"], "PASS")
        self.assertFalse(receipt["release_admitted"])
        verified = view.check_or_stage(self.root, "fixtures/branch.sens",
                                       reader=Path(reader))
        self.assertEqual(verified["d2_reader"], "PASS")
        # An unclosed D2 OPEN is physically canonical T5 but not a program.
        # A single atom "1" is potentially syntactically legal: do not misuse
        # it to claim Rust rejected actual D2 syntax.
        self.sens.write_bytes(encode_words(["10"]))
        with self.assertRaisesRegex(view.ViewError, "Rust D2"):
            view.check_or_stage(self.root, "fixtures/branch.sens", reader=Path(reader))

    def test_distinct_domain_widths_survive_cycle(self):
        sequence = ["0", "00", "000", "1", "10", "101010101"]
        physical = encode_words(sequence)
        recovered = decode_bytes(physical)
        self.assertEqual(recovered, sequence)
        self.assertEqual(view.parse_view(view.render_view(recovered)), sequence)
        self.assertEqual(encode_words(view.parse_view(view.render_view(recovered))), physical)
        self.assertNotEqual(sequence[0], sequence[1])
        self.assertNotEqual(sequence[1], sequence[2])

    def test_single_atom_and_multiple_words(self):
        for sequence in (["1"], ["000"], ["10", "110", "01"],
                         ["10", "001", "00", "000", "01"]):
            with self.subTest(words=sequence):
                self.assertEqual(view.parse_view(view.render_view(sequence)), sequence)
                self.assertEqual(decode_bytes(encode_words(sequence)), sequence)

    def test_view_rejects_all_noncanonical_whitespace_and_content(self):
        bad = [b"", b"\n", b"0", b"0\n\n", b" 0\n", b"0 \n", b"0  1\n",
               b"0\t1\n", b"0\r\n", b"0\x001\n", b"0\xc2\xa01\n",
               b"0 2\n", b"0000000000\n", b"D3:110\n",
               b"(110)\n", b"0b1\n", b"1 # comment\n"]
        for data in bad:
            with self.subTest(data=data), self.assertRaises(view.ViewError):
                view.parse_view(data)

    def test_verified_pair_rejects_stale_view(self):
        cases = [b"0\n", EXPECTED.encode("ascii") + b"\n",
                 EXPECTED.encode("ascii").replace(b" ", b"  ", 1)]
        for data in cases:
            self.plain.write_bytes(data)
            with self.subTest(data=data[:16]), self.assertRaises(view.ViewError):
                view.check_or_stage(self.root, "fixtures/branch.sens")

    def test_t5_corruption_does_not_fallback_to_text(self):
        originals = self.sens.read_bytes()
        for invalid in (originals + bytes([243]), originals + bytes([242]),
                        bytes([243]), b""):
            self.sens.write_bytes(invalid)
            with self.subTest(data=invalid.hex()), self.assertRaises((SensT5Error, view.ViewError)):
                view.check_or_stage(self.root, "fixtures/branch.sens")
        self.sens.write_bytes(originals)

    def test_missing_sources_fail_closed(self):
        self.source.unlink()
        with self.assertRaises(view.ViewError):
            view.check_or_stage(self.root, "fixtures/branch.sens")
        self.source.write_bytes(b"(\xff)\n")
        with self.assertRaises(view.ViewError):
            view.check_or_stage(self.root, "fixtures/branch.sens")
        self.source.write_bytes((FIXTURE / "branch.lisp").read_bytes())
        self.plain.unlink()
        with self.assertRaises(view.ViewError):
            view.check_or_stage(self.root, "fixtures/branch.sens")

    def test_no_traversal_extension_or_repo_staging(self):
        for name in ("../branch.sens", "fixtures/../branch.sens",
                     "/tmp/branch.sens", "fixtures/branch.lisp",
                     "fixtures\\branch.sens", "fixtures/.sens"):
            with self.subTest(name=name), self.assertRaises(view.ViewError):
                view.check_or_stage(self.root, name)
        with self.assertRaises(view.ViewError):
            view.check_or_stage(self.root, "fixtures/branch.sens", stage=self.root)

    def test_symlink_source_and_staging_rejected(self):
        external = self.work / "other.sens"
        external.write_bytes(self.sens.read_bytes())
        self.sens.unlink()
        self.sens.symlink_to(external)
        with self.assertRaises(view.ViewError):
            view.check_or_stage(self.root, "fixtures/branch.sens")
        self.sens.unlink()
        self.sens.write_bytes(external.read_bytes())
        output = self.work / "stage"
        output.mkdir()
        (output / "fixtures").symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(view.ViewError):
            view.check_or_stage(self.root, "fixtures/branch.sens", stage=output)

    def test_cli_verify_machine_readable_ledger_and_block(self):
        script = ROOT / "scripts/sens_spaced_view.py"
        cmd = [sys.executable, str(script), "--root", str(self.root),
               "--sens", "fixtures/branch.sens", "--verify"]
        run = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["schema"], "sens-t5-spaced-view/v1")
        self.assertEqual(report["view"], "fixtures/branch")
        self.assertEqual(len(report["typed_word_sha256"]), 64)
        self.assertFalse(report["release_admitted"])
        self.plain.write_bytes(b"1\n")
        blocked = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("BLOCKED", blocked.stderr)


if __name__ == "__main__":
    unittest.main()
