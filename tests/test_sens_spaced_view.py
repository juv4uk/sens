#!/usr/bin/env python3
"""#4694: source-preserving, strict 0/1 view <-> physical T5 roundtrip."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sens_spaced_view.py"
COHORT = Path("tests/fixtures/migration-d1-cond-cohort/branch")
SENS = Path(str(COHORT) + ".sens")
WORDS = "10 110 00 10 0 00 10 100 00 000 01 01 00 10 1 00 1 01 01"
PHYSICAL = bytes.fromhex("67386515bf123b2dc4a9b1a1")

sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("sens_spaced_view_tests", SCRIPT)
assert spec and spec.loader
view = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = view
spec.loader.exec_module(view)


class SpacedViewTests(unittest.TestCase):
    def test_existing_current_uk_canary_three_files_exact(self):
        state, canonical = view.inspect(ROOT, SENS)
        self.assertEqual(canonical, (WORDS + "\n").encode("ascii"))
        self.assertEqual((ROOT / COHORT).read_bytes(), canonical)
        self.assertEqual((ROOT / SENS).read_bytes(), PHYSICAL)
        self.assertEqual(len(PHYSICAL), 12)
        verified, _ = view.inspect(ROOT, SENS, verify_existing=False)
        self.assertEqual(verified["status"], "PHYSICAL_PREVIEW_NOT_RELEASE")
        self.assertEqual(verified["source_semantic_oracle"], "NOT_VERIFIED")
        self.assertEqual(verified["original_executable_migrations_admitted"], 0)
        self.assertFalse(verified["release_certified"])
        self.assertEqual(state["typed_words"], len(WORDS.split()))
        self.assertEqual(view.parse_view(canonical), WORDS.split())
        self.assertEqual(view.encode_words(view.parse_view(canonical)), PHYSICAL)

    def test_all_widths_1_to_9_and_width_collision_preserved(self):
        words = ["0", "00", "000", "1", "01", "001", "111111111"]
        visible = view.canonical_view(words)
        self.assertEqual(view.parse_view(visible), words)
        self.assertEqual(view.decode_bytes(view.encode_words(words)), words)
        self.assertNotEqual(view.encode_words(["0", "00"]), view.encode_words(["000"]))

    def test_multiform_one_atom_nested_D2_can_roundtrip(self):
        for words in (["1"], ["000"], ["10", "110", "00", "1", "01"],
                      ["10", "001", "00", "000", "01", "00", "10", "1", "01"]):
            with self.subTest(words=words):
                b = view.encode_words(words)
                self.assertEqual(view.encode_words(view.parse_view(view.canonical_view(view.decode_bytes(b)))), b)

    def test_invalid_ascii_view_is_always_rejected(self):
        bad = (
            b"", b"\n", b"0", b" 0\n", b"0 \n", b"0  1\n",
            b"0\t1\n", b"0\r\n", b"0\n\n", b"0\n1\n", b"0 2\n",
            b"2\n", b"0 A\n", b"0(1)\n", b"0b0\n", b"D1:0\n",
            b"0 # comment\n", b"0\x00\n", "\u0456\n".encode("utf-8"),
            b"0000000000\n", b"0" * (view.MAX_VIEW_BYTES + 1),
        )
        for candidate in bad:
            with self.subTest(candidate=candidate[:60]), self.assertRaises(view.ViewBlocked):
                view.parse_view(candidate)

    def test_corrupt_physical_padding_and_trailer_fail_closed(self):
        for broken in (b"", b"\xf3", b"\xf2", PHYSICAL + b"\xf2",
                       PHYSICAL + b"\xf3"):
            with self.subTest(hex=broken.hex()):
                with self.assertRaises(view.SensT5Error):
                    view.decode_bytes(broken)

    def test_stale_missing_and_symlink_existing_view_block(self):
        # Truncation can accidentally produce another canonical shorter T5;
        # it still cannot match the fixed source's typed-word/physical digest.
        try:
            truncated = view.decode_bytes(PHYSICAL[:-1])
        except view.SensT5Error:
            pass
        else:
            self.assertNotEqual(truncated, WORDS.split())

        with tempfile.TemporaryDirectory(prefix="sens-view-negative-") as td:
            root = Path(td)
            (root / "p.lisp").write_text("(ук джерело)\n", encoding="utf-8")
            (root / "p.sens").write_bytes(PHYSICAL)
            with self.assertRaisesRegex(view.ViewBlocked, "missing"):
                view.checked_path(root, Path("p"), "")
            # Existing view verification needs Rust, even if ASCII looks correct.
            (root / "p").write_bytes((WORDS + "\n").encode("ascii"))
            with self.assertRaisesRegex(view.ViewBlocked, "Rust"):
                view.inspect(root, Path("p.sens"), reader=None, verify_existing=True)
            (root / "p").unlink()
            (root / "p").symlink_to("p.lisp")
            with self.assertRaisesRegex(view.ViewBlocked, "symlink"):
                view.checked_path(root, Path("p"), "")
            (root / "p").unlink()
            (root / "p.sens").unlink()
            (root / "p.sens").symlink_to("p.lisp")
            with self.assertRaisesRegex(view.ViewBlocked, "symlink"):
                view.inspect(root, Path("p.sens"))

    def test_unsafe_paths_and_staging_inside_repo_block(self):
        for path in (Path("../secrets.sens"), Path("/tmp/anything.sens"), Path("p.lisp")):
            with self.subTest(path=path), self.assertRaises(view.ViewBlocked):
                view.checked_path(ROOT, path, ".sens")
        with self.assertRaisesRegex(view.ViewBlocked, "outside"):
            view.safe_stage(ROOT, ROOT / "should-not-exist", SENS,
                            (WORDS + "\n").encode("ascii"))
        self.assertFalse((ROOT / "should-not-exist").exists())

    def test_external_staging_write_once_and_source_untouched(self):
        before_lisp = (ROOT / (str(COHORT) + ".lisp")).read_bytes()
        before_sens = (ROOT / SENS).read_bytes()
        with tempfile.TemporaryDirectory(prefix="sens-view-stage-") as td:
            mirror = Path(td)
            payload = (WORDS + "\n").encode("ascii")
            output = view.safe_stage(ROOT, mirror, SENS, payload)
            self.assertEqual(output, mirror / COHORT)
            self.assertEqual(output.read_bytes(), payload)
            with self.assertRaisesRegex(view.ViewBlocked, "NO_CLOBBER"):
                view.safe_stage(ROOT, mirror, SENS, b"0\n")
            self.assertEqual(output.read_bytes(), payload)
        self.assertEqual((ROOT / SENS).read_bytes(), before_sens)
        self.assertEqual((ROOT / (str(COHORT) + ".lisp")).read_bytes(), before_lisp)

    @unittest.skipUnless(os.environ.get("SENS_VIEW_READER"), "real Rust CLI set by focused CI")
    def test_real_rust_reader_and_exact_live_view_verify(self):
        reader = Path(os.environ["SENS_VIEW_READER"])
        state, data = view.inspect(ROOT, SENS, reader=reader, verify_existing=True)
        self.assertEqual(data, (ROOT / COHORT).read_bytes())
        self.assertEqual(state["d2_reader"], "PASS")
        self.assertEqual(state["status"], "VIEW_PARITY_ONLY_NOT_RELEASE")
        with tempfile.TemporaryDirectory(prefix="sens-view-actual-") as td:
            root = Path(td)
            for suffix in (".lisp", ".sens", ""):
                (root / ("branch" + suffix)).write_bytes(
                    (ROOT / ("tests/fixtures/migration-d1-cond-cohort/branch" + suffix)).read_bytes()
                )
            (root / "branch").write_bytes(b"10  110\n")
            with self.assertRaisesRegex(view.ViewBlocked, "VIEW"):
                view.inspect(root, Path("branch.sens"), reader=reader, verify_existing=True)
            (root / "branch").unlink()
            with self.assertRaisesRegex(view.ViewBlocked, "missing"):
                view.inspect(root, Path("branch.sens"), reader=reader, verify_existing=True)

    @unittest.skipUnless(os.environ.get("SENS_VIEW_READER"), "real Rust CLI set by focused CI")
    def test_stage_command_external_only_noclobber_preview(self):
        reader = os.environ["SENS_VIEW_READER"]
        with tempfile.TemporaryDirectory(prefix="sens-view-cli-") as td:
            target = Path(td) / "staging"
            args = [sys.executable, str(SCRIPT), "stage", "--root", str(ROOT),
                    "--sens", SENS.as_posix(), "--reader", reader, "--mirror", str(target)]
            preview = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertFalse(target.exists())
            receipt = json.loads(preview.stdout)
            self.assertFalse(receipt["stage_written"])
            run = subprocess.run(args + ["--write"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual((target / COHORT).read_bytes(), (WORDS + "\n").encode("ascii"))
            again = subprocess.run(args + ["--write"], capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertIn("NO_CLOBBER", again.stderr)


if __name__ == "__main__":
    unittest.main()
