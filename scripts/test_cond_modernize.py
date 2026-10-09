#!/usr/bin/env python3
"""Regression suite: migration must NEVER invert a negative COND branch."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("cond-modernize.py")
spec = importlib.util.spec_from_file_location("cond_modernize", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class SafeCondMigration(unittest.TestCase):
    def test_exact_d3_yes_can_stage(self):
        text = "(110 ((010 x) (1) yes))"
        findings, _ = mod.inspect(text)
        self.assertEqual([f.status for f in findings], ["AUTO_YES"])
        got, selected = mod.stage(text)
        self.assertEqual(got, "(110 ((010 x)  yes))")
        self.assertEqual(len(selected), 1)

    def test_exact_d3_eq_yes(self):
        got, _ = mod.stage("(110 ((101 x y) 1 pass))")
        self.assertEqual(got, "(110 ((101 x y)  pass))")

    def test_no_must_never_become_yes(self):
        text = "(110 ((010 x) (0) fail))"
        self.assertEqual(mod.inspect(text)[0][0].status, "HOLD")
        with self.assertRaisesRegex(mod.Blocked, "negative branch"):
            mod.stage(text)

    def test_mixed_no_cannot_partially_write(self):
        src = "(110 ((010 x) (1) pass) ((010 y) (0) fail))"
        with self.assertRaisesRegex(mod.Blocked, "HOLD"):
            mod.stage(src)

    def test_legacy_sid_eq_requires_migration_bridge(self):
        text = "(00000111 ((00000011 x y) (1) pass))"
        got, _ = mod.inspect(text)
        self.assertEqual(got[0].status, "HOLD")
        self.assertIn("legacy", got[0].reason)
        with self.assertRaises(mod.Blocked):
            mod.stage(text)

    def test_equal_and_cons_not_confused(self):
        for op in ("00100010", "00000100", "00000010", "00000011"):
            with self.subTest(op=op):
                rows, _ = mod.inspect(f"(110 (({op} x y) (1) yes))")
                self.assertEqual(rows[0].status, "HOLD")

    def test_quote_data_is_untouched(self):
        examples = [
            "(001 (110 ((010 x) (1) data)))",
            "(00000001 (110 ((010 x) (1) data)))",
            "'(110 ((010 x) (1) data))",
            '(110 ((010 x) (1) yes)) ; "(110 ((010 z) (1) no))"',
            '"; (110 ((010 x) (1) text))"',
            "#| (110 ((010 x) (1) hidden)) |#",
            "#; (110 ((010 x) (1) ignored))",
        ]
        for source in examples[:3] + examples[4:]:
            with self.subTest(source=source):
                self.assertEqual(mod.inspect(source)[0], [])
        self.assertEqual(len(mod.inspect(examples[3])[0]), 1)

    def test_preserve_outside_exact_span(self):
        src = "; prologue\n(110 ; keep header\n  ((010 x) (1) yes))\n; trailer\n"
        result, _ = mod.stage(src)
        self.assertTrue(result.startswith("; prologue\n"))
        self.assertTrue(result.endswith("; trailer\n"))
        self.assertIn("; keep header", result)
        self.assertEqual(len(mod.inspect(result)[0]), 0)

    def test_sens_literal_pipe_and_pipe_prefix(self):
        source = "(list | |- (110 ((010 x) (1) yes)))"
        findings, _ = mod.inspect(source)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "AUTO_YES")

    def test_pinned_fragment_requires_exact_bytes(self):
        import hashlib
        fragment = "lib/surface/semantic-registry-experiment.lisp"
        expected = "c5a375605cca330445adda18b9f08a7fb5e17c09"
        self.assertEqual(mod.PINNED_NON_PROGRAM_FRAGMENTS[fragment], expected)
        raw = b"  (00000000 (en ()))\n"
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii")
                            + b"\0" + raw).hexdigest()
        self.assertNotEqual(blob, expected)  # no generic skip by filename

    def test_parser_fail_closed(self):
        for source in ('(110 ((010 x) (1) pass)', '"unterminated', '#| unclosed'):
            with self.subTest(source=source):
                with self.assertRaises(mod.Blocked):
                    mod.inspect(source)

    def test_no_implicit_in_place_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.lisp"
            source.write_text("(110 ((010 x) (1) pass))", encoding="utf-8")
            a = subprocess.run([sys.executable, str(SCRIPT), str(source)],
                               capture_output=True, text=True)
            self.assertEqual(a.returncode, 4, a.stdout + a.stderr)
            self.assertIn("BLOCK:", a.stdout)
            self.assertEqual(source.read_text(encoding="utf-8"),
                             "(110 ((010 x) (1) pass))")

    def test_apply_requires_distinct_out(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.lisp"
            source.write_text("(110 ((010 x) (1) pass))", encoding="utf-8")
            missing = subprocess.run([sys.executable, str(SCRIPT), str(source),
                                      "--apply"], capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            same = subprocess.run([sys.executable, str(SCRIPT), str(source),
                                   "--apply", "--out", str(Path(tmp))],
                                  capture_output=True, text=True)
            self.assertNotEqual(same.returncode, 0)
            self.assertEqual(source.read_text(encoding="utf-8"),
                             "(110 ((010 x) (1) pass))")
            staged = subprocess.run([sys.executable, str(SCRIPT), str(source),
                                     "--apply", "--out", str(Path(tmp) / "stage")],
                                    capture_output=True, text=True)
            self.assertEqual(staged.returncode, 0, staged.stderr)
            self.assertEqual((Path(tmp) / "stage" / "sample.lisp")
                             .read_text(encoding="utf-8"),
                             "(110 ((010 x)  pass))")


if __name__ == "__main__":
    unittest.main()
