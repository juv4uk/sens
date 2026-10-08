#!/usr/bin/env python3
"""Strict, reversible T5 spaced-view contract; never grants semantic parity."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import sens_t5_codec as codec

spec = importlib.util.spec_from_file_location("spaced_view", SCRIPTS / "sens_t5_spaced_view.py")
assert spec and spec.loader
view = importlib.util.module_from_spec(spec)
spec.loader.exec_module(view)
FIXTURE = Path("tests/fixtures/migration-d1-cond-cohort/branch")
WORDS = "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01"
BYTES = bytes.fromhex("67386515bf123b2dc4a9b1a1")


class ViewContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "repo"
        (self.root / "code").mkdir(parents=True)
        self.source = self.root / "code/demo.lisp"
        self.source.write_text("(як-є ())\n", encoding="utf-8")
        self.binary = self.root / "code/demo.sens"
        self.binary.write_bytes(codec.encode_words(["10", "001", "00", "000", "01"]))
        self.stage = self.base / "out"

    def cli(self, mode, *sources, out=None):
        cmd = [sys.executable, str(SCRIPTS / "sens_t5_spaced_view.py"),
               mode, *(sources or ("code/demo.sens",)),
               "--root", str(self.root)]
        if out is not None:
            cmd += ["--out", str(out)]
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20)

    def test_existing_real_uk_three_files_exact(self):
        raw = (ROOT / FIXTURE.with_suffix(".sens")).read_bytes()
        text = (ROOT / FIXTURE).read_bytes()
        self.assertEqual(raw, BYTES)
        self.assertEqual(text, (WORDS + "\n").encode("ascii"))
        self.assertEqual(codec.decode_bytes(raw), view.parse_view(text))
        self.assertEqual(codec.encode_words(view.parse_view(text)), raw)
        r = view.inspect(ROOT, FIXTURE.with_suffix(".sens"), "verify", ROOT)
        self.assertEqual(r["status"], "PASS_VIEW_ONLY")
        self.assertEqual(r["physical_bytes"], 12)
        self.assertEqual(r["uk_source_bidirectional_oracle"], "NOT_VERIFIED")

    def test_create_preview_verify_and_no_clobber(self):
        original = self.binary.read_bytes()
        readable = self.source.read_bytes()
        p = self.cli("preview", out=self.stage)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertFalse(self.stage.exists())
        created = self.cli("create", out=self.stage)
        self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
        expected = view.canonical_view(codec.decode_bytes(original))
        self.assertEqual((self.stage / "code/demo").read_bytes(), expected)
        receipt = json.loads(self.cli("verify", out=self.stage).stdout)
        self.assertEqual(receipt["files"][0]["typed_word_sha256"],
                         codec.typed_sha256(codec.decode_bytes(original)))
        self.assertEqual(receipt["summary"]["semantic_oracle_passed"], 0)
        again = self.cli("create", out=self.stage)
        self.assertEqual(again.returncode, 2)
        self.assertIn("never overwrite", again.stdout)
        self.assertEqual(self.binary.read_bytes(), original)
        self.assertEqual(self.source.read_bytes(), readable)

    def test_view_width_preservation_and_multiform(self):
        examples = [
            ["0"], ["00"], ["000"], ["0", "00", "000"],
            ["10", "001", "00", "000", "01"],
            ["10", "001", "00", "000", "01", "10", "001", "00", "0", "01"],
            WORDS.split(),
        ]
        for words in examples:
            with self.subTest(words=words):
                physical = codec.encode_words(words)
                self.assertEqual(codec.decode_bytes(physical), words)
                self.assertEqual(codec.encode_words(view.parse_view(view.canonical_view(words))),
                                 physical)

    def test_noncanonical_ascii_is_blocked(self):
        bad = (b"", b"\n", b"0", b"0 ", b" 0\n", b"0 \n", b"0  1\n",
               b"0\t1\n", b"0\r\n", b"0\n\n", b"0\n1\n", b"2\n",
               b"0000000000\n", b"D3:001\n", b"0b1\n",
               b"(001)\n", b"1 2\n", "так\n".encode(), b"0\x00\n")
        for raw in bad:
            with self.subTest(raw=raw):
                with self.assertRaises(codec.SensT5Error):
                    view.parse_view(raw)

    def test_invalid_physical_or_missing_companion_cannot_create(self):
        for raw in (b"", bytes([243]), bytes([242]), 
                    self.binary.read_bytes() + bytes([242])):
            self.binary.write_bytes(raw)
            self.assertEqual(self.cli("create", out=self.stage).returncode, 2)
            self.assertFalse((self.stage / "code/demo").exists())
        self.binary.write_bytes(codec.encode_words(["000"]))
        self.source.unlink()
        self.assertEqual(self.cli("create", out=self.stage).returncode, 2)

    def test_missing_or_corrupt_stored_view_is_rejected(self):
        self.assertEqual(self.cli("verify", out=self.stage).returncode, 2)
        self.assertEqual(self.cli("create", out=self.stage).returncode, 0)
        target = self.stage / "code/demo"
        valid = target.read_bytes()
        for bad in (b"0  1\n", valid + b"\n", valid.replace(b" ", b"  ", 1)):
            target.write_bytes(bad)
            self.assertEqual(self.cli("verify", out=self.stage).returncode, 2)

    def test_traversal_symlink_no_source_or_repo_writes(self):
        for bad in ("../code/demo.sens", "/etc/passwd", "code/demo.lisp",
                    "missing.sens", ".git/x.sens"):
            self.assertEqual(self.cli("create", bad, out=self.stage).returncode, 2)
        (self.root / "code/alias.sens").symlink_to(self.binary)
        self.assertEqual(self.cli("create", "code/alias.sens", out=self.stage).returncode, 2)
        self.assertEqual(self.cli("create", out=self.root / "views").returncode, 3)
        self.assertFalse((self.root / "views").exists())
        self.stage.mkdir()
        (self.stage / "code").symlink_to(self.root / "code", target_is_directory=True)
        self.assertEqual(self.cli("create", out=self.stage).returncode, 2)
        self.assertFalse((self.root / "code/demo").exists())


if __name__ == "__main__":
    unittest.main()
