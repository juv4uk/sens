"""Regression cases for the independent, read-only pair-release guard."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify-source-pairs.py"
_spec = importlib.util.spec_from_file_location("verify_source_pairs", SCRIPT)
_pairs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pairs)


class PairCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "lib").mkdir()
        self.uk = self.root / "lib" / "тест.lisp"
        self.bin = self.root / "lib" / "тест"
        self.uk.write_text("(так)", encoding="utf-8")
        self.bin.write_bytes(b"1001101")
        self.enc = self.root / "encode.py"
        self.dec = self.root / "decode.py"
        self.enc.write_text("import sys\ns=sys.stdin.buffer.read()\nsys.stdout.buffer.write(b'1001101' if s == '(так)'.encode() else b'BAD')\n", encoding="utf-8")
        self.dec.write_text("import sys\ns=sys.stdout.buffer.write('(так)'.encode() if sys.stdin.buffer.read() == b'1001101' else b'BAD')\n", encoding="utf-8")

    def scan(self, inventory_only=False):
        return _pairs.check(self.root, ["lib/**/*.lisp"], self.enc, self.dec, inventory_only)

    def test_exact_roundtrip_passes(self):
        n, errors = self.scan()
        self.assertEqual((n, errors), (1, []))

    def test_missing_twin_fails(self):
        self.bin.unlink()
        self.assertIn("missing adjacent binary twin", self.scan()[1][0])

    def test_binary_whitespace_fails(self):
        self.bin.write_bytes(b"1001\n101")
        self.assertIn("expected nonempty exact visible-binary", self.scan()[1][0])

    def test_nonkeyboard_and_confusables_fail(self):
        for value in ["(TAK)", "(тaк)", "(так)\u200b", "(так)\r\n"]:
            with self.subTest(value=value):
                self.uk.write_text(value, encoding="utf-8", newline="")
                self.assertIn("forbidden/non-keyboard", self.scan()[1][0])

    def test_decoder_mismatch_fails(self):
        self.dec.write_text("import sys\nsys.stdout.write('(ні)')\n", encoding="utf-8")
        self.assertIn("decode(B) differs", self.scan()[1][0])

    def test_no_bridge_is_not_green(self):
        with self.assertRaises(_pairs.PairError):
            _pairs.verify_pair(self.uk, None, None)

    def test_zero_scope_is_not_green(self):
        self.assertTrue(_pairs.check(self.root, [], self.enc, self.dec)[1])
        self.assertTrue(_pairs.check(self.root, ["none/**/*.lisp"], self.enc, self.dec)[1])

    def test_ukrainian_letters_and_layout_punctuation(self):
        _pairs.validate_ukrainian("(ґ є ї і так?!)".encode(), "fixture")

    def test_symlink_rejected(self):
        self.bin.unlink()
        try:
            self.bin.symlink_to(self.root / "elsewhere")
        except (NotImplementedError, OSError):
            self.skipTest("symlinks unavailable")
        self.assertIn("must not be symlinks", self.scan()[1][0])

    def test_inventory_is_not_codec_evidence(self):
        n, errors = self.scan(inventory_only=True)
        self.assertEqual((n, errors), (1, []))


if __name__ == "__main__":
    unittest.main()
