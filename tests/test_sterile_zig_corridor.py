#!/usr/bin/env python3
"""Regression: sterile Zig corridor contract stays fail-closed."""

from __future__ import annotations

import subprocess
import runpy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_sterile_zig_corridor.py"


class SterileZigCorridorTests(unittest.TestCase):
    def test_script_passes_on_tree(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("STERILE_ZIG_CORRIDOR_PASS", completed.stdout)

    def test_corridor_file_has_no_local_t5_codec(self) -> None:
        body = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        self.assertIn("sens_zig_t5_decode_be3", body)
        self.assertIn("sens_zig_t5_encode_be3", body)
        self.assertNotIn("PhysicalT5Program", body)
        self.assertNotIn("ternary_transport", body)
        self.assertNotIn("TRITS_BY_BYTE", body)

    def test_main_sens_ingress_rejects_real_rust_bypass_mutants(self) -> None:
        # Source-hygiene only, no Zig semantic oracle; no repo file mutation.
        module = runpy.run_path(str(SCRIPT))
        check = module["check_main_t5_ingress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        check(source)  # positive: current main retains the Zig-only route

        replacements = (
            # Default Zig call replaced by an accidental direct Rust codec.
            (
                "return zig_transport::decode_t5_words(bytes);",
                "return sens::decode_ternary_words(bytes).map_err(|e| format!(\"{e:?}\"));",
            ),
            # An explicit Rust fallback under feature-negative is still a bypass.
            (
                'Err("physical .sens requires the Zig transport corridor; no Rust fallback".into())',
                'sens::decode_ternary_words(bytes).map_err(|e| format!("{e:?}"))',
            ),
            # Zig helper exists but the production evaluator bypasses it.
            (
                "let words = decode_physical_t5_words(bytes)?;",
                "let words = sens::decode_ternary_words(bytes).unwrap();",
            ),
            (
                "sens::parse_canonical_word_sequence(&words)",
                "sens::parse_canonical_binary(\"not exact words\")",
            ),
            (
                "eval_physical_t5(&bytes)",
                "sens::decode_ternary_words(&bytes).map(|_| Default::default())",
            ),
        )
        for old, replacement in replacements:
            with self.subTest(bypass=old):
                self.assertEqual(source.count(old), 1)
                with self.assertRaises(blocked):
                    check(source.replace(old, replacement))

    def test_main_sens_ingress_fails_on_missing_or_duplicate_route(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_main_t5_ingress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        for mutant in (
            source.replace('mod zig_transport;', 'mod untrusted_transport;'),
            source.replace('fn decode_physical_t5_words(', 'fn bypass_physical_t5_words('),
            source.replace('fn eval_physical_t5(', 'fn bypass_eval_physical_t5('),
            source.replace('fn main() {', 'fn other_main() {'),
        ):
            with self.subTest(kind="missing-entrypoint"), self.assertRaises(blocked):
                check(mutant)


if __name__ == "__main__":
    unittest.main(verbosity=2)
