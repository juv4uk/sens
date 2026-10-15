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
        self.assertIn("f3c-decode-validates-t5", completed.stdout)
        self.assertIn("f3c-bounds-reported-lengths", completed.stdout)

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

        no_validate = body.replace("validate_t5(t5)?;", "/* bypassed */", 1)
        with self.assertRaises(blocked):
            check(no_validate)

        start = body.index("pub fn encode_f3(")
        end = body.index("pub fn decode_f3(")
        route = body[start:end]
        swapped = route.replace(
            "validate_t5(t5)?;\n    if t5.len() > 16 {",
            "if t5.len() > 16 {\n        // mutant: length before Zig validate\n    }\n    if false {\n        validate_t5(t5)?;\n    if t5.len() > 16 {",
            1,
        )
        if swapped == route:
            swapped = route.replace(
                "validate_t5(t5)?;",
                "if t5.len() > 16 { return Ok(None); }\n    // mutant moved validate after length",
                1,
            )
        mutant = body[:start] + swapped + body[end:]
        with self.assertRaises(blocked):
            check(mutant)

    def test_f3c_decode_rejects_validate_bypass(self) -> None:
        """decode_f3 must validate_t5 after unpack; mutants fail closed."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_f3c_decode_validates_t5"]
        blocked = module["CorridorBlocked"]
        body = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        check(body)

        no_validate = body.replace("validate_t5(&output)?;", "/* no validate */", 1)
        with self.assertRaises(blocked):
            check(no_validate)

        stripped = body.replace("validate_t5(&output)?;\n", "", 1)
        if stripped == body:
            stripped = body.replace("validate_t5(&output)?;", "", 1)
        with self.assertRaises(blocked):
            check(stripped)

        for bypass in (
            "let _ = validate_t5(&output);",
            "validate_t5(&output);",
            "// validate_t5(&output)?;",
            "/* validate_t5(&output)?; */",
            "validate_t5(carrier)?;",
            "return Ok(output);\n    validate_t5(&output)?;",
        ):
            with self.subTest(bypass=bypass):
                mutant = body.replace("validate_t5(&output)?;", bypass, 1)
                self.assertNotEqual(mutant, body)
                with self.assertRaises(blocked):
                    check(mutant)

        mutant = body.replace(
            "output.truncate(len as usize);\n    validate_t5(&output)?;",
            "validate_t5(&output)?;\n    output.truncate(len as usize);",
            1,
        )
        self.assertNotEqual(mutant, body)
        with self.assertRaises(blocked):
            check(mutant)

    def test_f3c_bounds_reject_overreport_mutants(self) -> None:
        """encode_f3/decode_f3 must capacity-filter Zig lengths before truncate."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_f3c_bounds_reported_lengths"]
        blocked = module["CorridorBlocked"]
        body = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        check(body)

        no_bound = body.replace(
            "usize::try_from(len).ok().filter(|&n| n < t5.len() && n <= bytes.len())",
            "Some(0usize) /* mutant: no capacity filter */",
            1,
        )
        with self.assertRaises(blocked):
            check(no_bound)

        no_decode_bound = body.replace(
            "usize::try_from(len).ok().filter(|&n| n <= output.len())",
            "Some(0usize) /* mutant: no capacity filter */",
            1,
        )
        with self.assertRaises(blocked):
            check(no_decode_bound)

        no_cap = body.replace("n <= bytes.len()", "true /* mutant */", 1)
        with self.assertRaises(blocked):
            check(no_cap)

    def test_default_zig_build_gate_reversed_or_comment_only_is_blocked(self) -> None:
        """A default Zig build must never return early or pass via a comment."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_default_zig_build_gate"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        real_gate = 'if env::var_os("CARGO_FEATURE_ZIG_TRANSPORT").is_none() {'
        self.assertIn(real_gate, source)
        check(source)

        reversed_gate = source.replace(real_gate, real_gate.replace(
            ".is_none()", ".is_some()"
        ), 1)
        bypasses = (
            reversed_gate,
            reversed_gate + "\n// " + real_gate + " return; }\n",
            source.replace(real_gate + "\n        return;", real_gate + "\n        /* no return */", 1),
        )
        for mutant in bypasses:
            with self.subTest(kind=("comment-spoof" if "// " + real_gate in mutant
                                    else "feature-gate")):
                self.assertNotEqual(mutant, source)
                with self.assertRaisesRegex(blocked, "default Zig gate"):
                    check(mutant)



    def test_f3c_cli_is_truly_zig_only_in_both_build_modes(self) -> None:
        """Fail closed if an F3C Rust codec or fake denial is introduced."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_f3_no_rust_fallback"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(
            encoding="utf-8"
        )
        check(source)

        changes = (
            (
                'Err("F3C physical decode requires Zig; no Rust fallback".into())',
                "sens::frame3_small::decode_explicit_small_f3(bytes)"
                '.map_err(|e| format!("{e:?}"))',
            ),
            (
                'Err("F3C physical encode requires Zig; no Rust fallback".into())',
                "sens::frame3_small::encode_explicit_small_f3(bytes)"
                '.map_err(|e| format!("{e:?}"))',
            ),
            (
                'Err("F3C physical decode requires Zig; no Rust fallback".into())',
                'Ok(bytes.to_vec()) // no Rust fallback',
            ),
            (
                'Err("F3C physical encode requires Zig; no Rust fallback".into())',
                'Ok(Some(bytes.to_vec())) // no Rust fallback',
            ),
            (
                "let restored = zig_transport::decode_f3(bytes)?;",
                'let restored = sens::frame3_small::decode_explicit_small_f3(bytes)'
                '.map_err(|e| format!("{e:?}"))?;',
            ),
            (
                "return zig_transport::encode_f3(bytes);",
                "return Ok(Some(bytes.to_vec())); // zig_transport::encode_f3(bytes);",
            ),
        )
        for original, forged in changes:
            with self.subTest(mutant=original):
                self.assertIn(original, source, "missing F3C code mutation anchor")
                candidate = source.replace(original, forged, 1)
                with self.assertRaises(blocked):
                    check(candidate)

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

    def test_trit_default_egress_comment_only_zig_call_is_not_proof(self) -> None:
        """A Zig-looking comment cannot replace live default-feature T5 bytes."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_t5_egress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(
            encoding="utf-8"
        )
        check(source)
        live = (
            "let bytes = "
            "zig_transport::encode_t5_direct(&admitted_source_words(&projection)?)?;"
        )
        self.assertIn(live, source)
        for commented in ("// " + live, "/* " + live + " */"):
            with self.subTest(comment=commented[:2]):
                # Host-owned fake output is NOT a valid replacement for Zig.
                mutant = source.replace(
                    live, commented + "\n            let bytes = Vec::new();", 1
                )
                self.assertNotEqual(mutant, source)
                with self.assertRaisesRegex(blocked, "live Zig physical"):
                    check(mutant)

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

    def test_route_cannot_borrow_test_only_closing_function(self) -> None:
        """A Zig source check must fail if its closing sentinel exists only in cfg(test)."""
        module = runpy.run_path(str(SCRIPT))
        between = module["_route_between"]
        blocked = module["CorridorBlocked"]
        spoof = (
            'fn zig_ingress() {\n'
            '    zig_transport::decode_t5_words(bytes);\n'
            '}\n'
            '#[cfg(test)]\n'
            'fn next_production_route() {\n'
            '    // test-only witness, NEVER a production boundary\n'
            '}\n'
        )
        with self.assertRaises(blocked):
            between(spoof, "fn zig_ingress(", "\nfn next_production_route(")

        actual = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        live_main = between(actual, "fn main() {", "\n#[cfg(test)]")
        self.assertIn("physical_t5_request", live_main)
        self.assertIn("eval_physical_t5", live_main)
        self.assertNotIn("#[cfg(test)]", live_main)

    def test_main_zig_ingress_rejects_comment_only_spoof(self) -> None:
        """Zig names in comments never prove a Rust -> Zig physical ingress."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_main_t5_ingress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        check(source)  # Positive: the live production Zig return exists.
        live = "return zig_transport::decode_t5_words(bytes);"
        self.assertIn(live, source)
        mutant = source.replace(
            live,
            '// return zig_transport::decode_t5_words(bytes);\n'
            '        return Err("physical bytes never crossed Zig".into());',
            1,
        )
        self.assertNotEqual(mutant, source)
        with self.assertRaisesRegex(blocked, "live Zig return"):
            check(mutant)

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
