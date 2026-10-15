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
        self.assertIn("f3c-validate-before-no-savings", completed.stdout)

    def test_corridor_file_has_no_local_t5_codec(self) -> None:
        body = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        self.assertIn("sens_zig_t5_decode_be3", body)
        self.assertIn("sens_zig_t5_encode_be3", body)
        self.assertNotIn("PhysicalT5Program", body)
        self.assertNotIn("ternary_transport", body)
        self.assertNotIn("TRITS_BY_BYTE", body)
        self.assertIn("packed_bits", body)
        self.assertNotIn("from_width_bits", body)

    def test_f3c_no_savings_rejects_validate_bypass_mutants(self) -> None:
        """encode_f3 must validate via Zig before any length-based Ok(None)."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_f3c_validate_before_no_savings"]
        blocked = module["CorridorBlocked"]
        body = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        check(body)

        # Drop validation entirely: oversize invalid T5 would report None.
        no_validate = body.replace("validate_t5(t5)?;", "/* bypassed */", 1)
        with self.assertRaises(blocked):
            check(no_validate)

        # Put length gate before validation (classic silent bypass).
        start = body.index("pub fn encode_f3(")
        end = body.index("pub fn decode_f3(")
        route = body[start:end]
        swapped = route.replace(
            "validate_t5(t5)?;\n    if t5.len() > 16 {",
            "if t5.len() > 16 {\n        // mutant: length before Zig validate\n    }\n    if false {\n        validate_t5(t5)?;\n    if t5.len() > 16 {",
            1,
        )
        if swapped == route:
            # Anchor may vary slightly; force an early length return without validate.
            swapped = route.replace(
                "validate_t5(t5)?;",
                "if t5.len() > 16 { return Ok(None); }\n    // mutant moved validate after length",
                1,
            )
        mutant = body[:start] + swapped + body[end:]
        with self.assertRaises(blocked):
            check(mutant)

    def test_main_sens_ingress_rejects_real_rust_bypass_mutants(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_main_t5_ingress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        check(source)

        replacements = (
            (
                "return zig_transport::decode_t5_words(bytes);",
                "return sens::decode_ternary_words(bytes).map_err(|e| format!(\"{e:?}\"));",
            ),
            (
                'Err("physical .sens requires the Zig transport corridor; no Rust fallback".into())',
                'sens::decode_ternary_words(bytes).map_err(|e| format!("{e:?}"))',
            ),
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
                self.assertIn(old, source)
                with self.assertRaises(blocked):
                    check(source.replace(old, replacement, 1))

    def test_trit_default_egress_rejects_rust_codec_mutants(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_t5_egress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        check(source)

        replacements = (
            (
                "let bytes = zig_transport::encode_t5_direct(&admitted_source_words(&projection)?)?;",
                "let bytes = sens::encode_binary_projection_ternary(&projection).unwrap();",
            ),
            (
                "let expected_words = admitted_source_words(source)?;",
                "let expected_words = zig_transport::decode_t5_words(binary)?;",
            ),
            (
                "zig_transport::encode_t5(&expected_words, binary)",
                "sens::encode_binary_projection_ternary(source).map_err(|e| format!(\"{e:?}\"))",
            ),
            (
                "sens::parse_binary_source_words(source)",
                "sens::decode_ternary_words(source.as_bytes())",
            ),
        )
        for old, replacement in replacements:
            with self.subTest(bypass=old):
                self.assertIn(old, source, "production mutation anchor missing")
                with self.assertRaises(blocked):
                    check(source.replace(old, replacement, 1))

    def test_trit_default_egress_refuses_missing_or_duplicate_production_arm(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_t5_egress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        anchor = '\n        "encode" => {\n'
        self.assertIn(anchor, source)
        for mutant in (
            source.replace(anchor, '\n        "old_encode" => {\n', 1),
            source.replace(anchor, anchor + anchor, 1),
        ):
            with self.subTest(kind="missing-or-duplicate"), self.assertRaises(blocked):
                check(mutant)

    def test_e1_physical_export_blocks_rust_bypass_mutants(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_e1_egress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        check(source)

        mutations = (
            (
                "zig_transport::encode_e1_direct(&words)",
                "sens::envelope_e1::encode(&words).map_err(|e| format!(\"{e:?}\"))",
            ),
            (
                "decode_canonical_t5_words(physical_t5)",
                "sens::decode_ternary_words(physical_t5)",
            ),
            (
                'Err("E1 physical export requires Zig; no Rust fallback".into())',
                'sens::envelope_e1::encode(&[]).map_err(|e| format!("{e:?}"))',
            ),
            (
                "let e1 = encode_e1_from_t5(&bytes)?;",
                "let e1 = sens::envelope_e1::encode(&[]).unwrap();",
            ),
        )
        for current, bypass in mutations:
            with self.subTest(mutant=current):
                self.assertIn(current, source, "missing production mutant anchor")
                with self.assertRaises(blocked):
                    check(source.replace(current, bypass, 1))

    def test_e1_executable_ingress_rejects_rust_codec_mutants(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_e1_ingress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        check(source)

        mutations = (
            (
                "zig_transport::decode_e1_words(bytes)",
                'sens::envelope_e1::decode(bytes).unwrap()',
            ),
            (
                "let program = sens::PhysicalT5Program::from_exact_words(&words)",
                "let program = sens::PhysicalT5Program::decode(bytes).unwrap()",
            ),
            (
                'Err("E1 physical execution requires Zig; no Rust fallback".into())',
                'sens::eval_e1_program(bytes, &mut sens::Session::default()).map_err(|e| format!("{e:?}"))',
            ),
            (
                "let result = eval_e1_bytes(&e1)?;",
                'let result = sens::eval_e1_program(&e1, &mut session).unwrap();',
            ),
        )
        for original, bypass in mutations:
            with self.subTest(mutant=original):
                self.assertIn(original, source)
                with self.assertRaises(blocked):
                    check(source.replace(original, bypass, 1))

    def test_live_t5_eval_and_core4_reject_rust_execution_bypass_mutants(self) -> None:
        """Mutate the *actual* guarded execution routine, never test fixtures."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_t5_execution"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        check(source)
        start = source.index("fn eval_t5_bytes_core4(")
        end = source.index("\n}\n", start) + len("\n}\n")
        actual_route = source[start:end]
        mutations = (
            (
                "zig_transport::decode_t5_words(bytes)?",
                "sens::decode_ternary_words(bytes).unwrap()",
            ),
            (
                "sens::PhysicalT5Program::from_exact_words(&words)",
                "sens::PhysicalT5Program::decode(bytes).unwrap()",
            ),
            (
                'Err("physical T5 execution requires Zig; no Rust fallback".into())',
                "sens::eval_t5_program(bytes, &mut sens::Session::default()).map_err(|e| format!(\"{e:?}\"))",
            ),
        )
        for original, bypass in mutations:
            with self.subTest(mutant=original):
                self.assertIn(original, actual_route, "production routine changed")
                changed = source[:start] + actual_route.replace(original, bypass, 1) + source[end:]
                with self.assertRaises(blocked):
                    check(changed)

        entry = "eval_t5_bytes_core4(&bytes, true)?"
        self.assertIn(entry, source)
        with self.assertRaises(blocked):
            check(source.replace(entry, "sens::eval_t5_program(&bytes, &mut session)?", 1))

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
