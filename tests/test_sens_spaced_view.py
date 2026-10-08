#!/usr/bin/env python3
"""Tests for exact extensionless binary view: read-only triple and staged inverse."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, typed_sha256

spec = importlib.util.spec_from_file_location("sens_exact_spaced_view", ROOT / "scripts/sens_spaced_view.py")
assert spec and spec.loader
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)

FIXTURE = Path("tests/fixtures/migration-d1-cond-cohort/branch.sens")
VIEW = FIXTURE.with_suffix("")
HUMAN = FIXTURE.with_suffix(".lisp")
READABLE = b"10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01\n"


class SpacedViewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="sens-triple-view-")
        self.addCleanup(temp.cleanup)
        self.working = Path(temp.name)
        self.root = self.working / "repo"
        self.stage = self.working / "stage"
        self.report = self.working / "report.json"
        self.reader = ROOT / "target/debug/sens-trit"
        for rel in (FIXTURE, HUMAN, VIEW):
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dst)

    def invoke(self, *flags, reader=True, source=FIXTURE):
        args = [
            "--root", str(self.root), "--source", str(source),
            "--report", str(self.report),
        ]
        if reader:
            args += ["--reader", str(self.reader)]
        args += list(flags)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = app.main(args)
        obj = json.loads(out.getvalue())
        self.assertEqual(json.loads(self.report.read_text(encoding="utf-8")), obj)
        return code, obj

    def test_existing_canary_has_real_uk_source_t5_and_exact_visible_view(self):
        binary = (ROOT / FIXTURE).read_bytes()
        self.assertEqual(len(binary), 12)
        self.assertEqual((ROOT / HUMAN).read_text(encoding="utf-8"),
                         "(за-умовою (ні (перше ())) (так так))\n")
        self.assertEqual((ROOT / VIEW).read_bytes(), READABLE)
        self.assertEqual(app.render_view(decode_bytes(binary)), READABLE)
        self.assertEqual(encode_words(app.parse_view(READABLE)), binary)
        self.assertEqual(
            typed_sha256(app.parse_view(READABLE)), typed_sha256(decode_bytes(binary))
        )

    def test_real_rust_d2_read_only_verify_existing_triple(self):
        self.assertTrue(self.reader.is_file(), "cargo build -p sens-cli --bin sens-trit")
        code, obj = self.invoke("--verify")
        self.assertEqual(code, 0, obj)
        self.assertEqual(obj["status"], "VIEW_MATCHES_T5")
        self.assertEqual(obj["rust_d2_syntax"], "PASS")
        self.assertEqual(obj["t5_roundtrip"], "PASS")
        self.assertEqual(obj["files_written"], 0)
        self.assertEqual(obj["semantic_oracle"], "NOT_VERIFIED")
        self.assertEqual(obj["canonical_uk_surface"], "NOT_VERIFIED")
        self.assertFalse(obj["release_admitted"])
        self.assertEqual(obj["spaced_ascii_sha256"], app.sha256(READABLE))
        self.assertEqual((self.root / VIEW).read_bytes(), READABLE)

    def test_safe_stage_and_second_no_clobber(self):
        code, report = self.invoke("--stage", "--out-root", str(self.stage))
        self.assertEqual(code, 0, report)
        self.assertEqual(report["status"], "STAGED_VIEW_T5_ONLY")
        self.assertEqual(report["files_written"], 1)
        target = self.stage / VIEW
        self.assertEqual(target.read_bytes(), READABLE)
        self.assertEqual(encode_words(app.parse_view(target.read_bytes())),
                         (self.root / FIXTURE).read_bytes())
        again, denied = self.invoke("--stage", "--out-root", str(self.stage))
        self.assertEqual(again, 2, denied)
        self.assertIn("never overwrite", denied["reason"])
        self.assertEqual(target.read_bytes(), READABLE)

    def test_preview_does_not_write_and_does_not_require_rust(self):
        before = (self.root / VIEW).read_bytes()
        code, obj = self.invoke(reader=False)
        self.assertEqual(code, 0, obj)
        self.assertEqual(obj["status"], "PREVIEW_ONLY")
        self.assertEqual(obj["files_written"], 0)
        self.assertEqual(obj["rust_d2_syntax"], "NOT_VERIFIED")
        self.assertFalse(self.stage.exists())
        self.assertEqual((self.root / VIEW).read_bytes(), before)

    def test_w0_w00_w000_stay_different_through_real_codec(self):
        cases = [
            ["0"], ["00"], ["000"], ["0", "00", "000"],
            ["10", "10", "000", "01", "01"],
            ["000", "1", "00", "01", "10", "000", "01"],
        ]
        for words in cases:
            with self.subTest(words=words):
                data = app.render_view(words)
                self.assertEqual(app.parse_view(data), words)
                self.assertEqual(decode_bytes(encode_words(words)), words)
                self.assertEqual(
                    encode_words(app.parse_view(data)), encode_words(words)
                )

    def test_strict_view_grammar_rejects_noncanonical_ascii(self):
        bad = [
            b"", b"\n", b"10 01", b"10 01\n\n", b"10  01\n",
            b" 10 01\n", b"10 01 \n", b"10\t01\n", b"10 01\r\n",
            b"10 2 01\n", b"10 (01)\n", b"D2:10 01\n", b"0b10\n",
            "10 \u0456 01\n".encode(), b"0000000000\n", b"10\x00 01\n",
        ]
        for raw in bad:
            with self.subTest(input=raw), self.assertRaises(app.ViewBlocked):
                app.parse_view(raw)

    def test_tampered_or_missing_checked_in_view_is_blocked(self):
        target = self.root / VIEW
        target.write_bytes(b"10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 0 01 01\n")
        code, blocked = self.invoke("--verify")
        self.assertEqual(code, 2, blocked)
        self.assertIn("stale or tampered", blocked["reason"])
        target.unlink()
        code, blocked = self.invoke("--verify")
        self.assertEqual(code, 2, blocked)
        self.assertIn("missing", blocked["reason"])

    def test_corrupt_t5_and_overpadding_fail_before_view(self):
        binary = self.root / FIXTURE
        original = binary.read_bytes()
        for bad in (original + bytes([243]), original + bytes([242]), bytes([243])):
            with self.subTest(data=bad):
                binary.write_bytes(bad)
                code, obj = self.invoke(reader=False)
                self.assertEqual(code, 2, obj)
                self.assertEqual(obj["files_written"], 0)
        binary.write_bytes(original)

    def test_symlink_paths_and_repo_writes_rejected(self):
        code, r = self.invoke("--stage", "--out-root", str(self.root))
        self.assertEqual(code, 2, r)
        self.assertIn("outside", r["reason"])
        code, r = self.invoke("--stage", "--out-root", str(self.root / "child"))
        self.assertEqual(code, 2, r)
        self.assertEqual(r["files_written"], 0)
        linked = self.working / "link.sens"
        linked.symlink_to(self.root / FIXTURE)
        code, r = self.invoke(source="../link.sens", reader=False)
        self.assertEqual(code, 2, r)
        self.assertIn("relative", r["reason"])
        # Do not follow same-stem source links either.
        (self.root / HUMAN).unlink()
        (self.root / HUMAN).symlink_to(ROOT / HUMAN)
        code, r = self.invoke(reader=False)
        self.assertEqual(code, 2, r)
        self.assertIn("unsafe", r["reason"])

    def test_stage_without_actual_rust_reader_fails_closed(self):
        code, obj = self.invoke("--stage", "--out-root", str(self.stage), reader=False)
        self.assertEqual(code, 2, obj)
        self.assertIn("--reader", obj["reason"])
        self.assertFalse(self.stage.exists())

    def test_external_same_stem_view_cannot_masquerade_as_new_binary(self):
        code, r = self.invoke("--verify", "--out-root", str(self.stage))
        self.assertEqual(code, 2, r)
        self.assertIn("uses original", r["reason"])
        self.assertEqual((self.root / FIXTURE).read_bytes(), (ROOT / FIXTURE).read_bytes())


if __name__ == "__main__":
    unittest.main()
