#!/usr/bin/env python3
"""Regression: sterile Zig corridor contract stays fail-closed."""

from __future__ import annotations

import subprocess
import runpy
import re
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

    def test_single_compiled_zig_transport_module_has_live_feature_guard(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_shared_zig_module"]
        blocked = module["CorridorBlocked"]
        trit = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        library = (ROOT / "crates/sens-cli/src/lib.rs").read_text(encoding="utf-8")
        check(trit, library)  # Production symbol comes from one linked Rust library.
        for broken in (
            trit.replace("use sens_cli::zig_transport;", "mod zig_transport;", 1),
            trit.replace("use sens_cli::zig_transport;", "// use sens_cli::zig_transport;", 1),
            trit.replace('#[cfg(feature = "zig-transport")]\nuse sens_cli::zig_transport;',
                         '#[cfg(test)]\nuse sens_cli::zig_transport;', 1),
        ):
            with self.subTest(mutant=broken[:60]), self.assertRaises(blocked):
                check(broken, library)
        for broken in (
            library.replace("pub mod zig_transport;", "mod zig_transport;", 1),
            library.replace("pub mod zig_transport;", "// pub mod zig_transport;", 1),
            library.replace('#[cfg(feature = "zig-transport")]\npub mod zig_transport;',
                            '#[cfg(test)]\npub mod zig_transport;', 1),
        ):
            with self.subTest(mutant=broken[:60]), self.assertRaises(blocked):
                check(trit, broken)

    def test_linter_asset_crosses_only_live_zig_abi_and_rejects_bypass_mutants(self) -> None:
        """Rust can only fetch the checked-in physical linter T5M through Zig."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_linter_zig_only"]
        blocked = module["CorridorBlocked"]
        main = (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8")
        host = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        zig = (ROOT / "zig_transport_root.zig").read_text(encoding="utf-8")
        build = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        assets = (ROOT / "crates/sens-cli/src/zig_transport_assets.rs").read_text(encoding="utf-8")
        check(main, host, zig, build, assets)  # Live, on-disk positive evidence.

        mutants = (
            (
                "main", "let linter_asset = match linter_t5m_asset_zig_only()",
                'let linter_asset = include_bytes!("../../../lib/linter.sens").to_vec()',
            ),
            (
                "main", "zig_transport::linter_t5m_bytes()",
                'vec![] /* Zig call deleted */',
            ),
            (
                "main",
                '"RUST_ZIG_ONLY: linter T5M asset requires Zig; no Rust fallback"',
                '"transport=rust-reference"',
            ),
            (
                "main", 'repl::execute_zig_t5m_asset(&linter_asset, "SENS linter", &mut session)',
                'eval_program("(аналіз-перевірити)", &mut session)',
            ),
            (
                "assets", "pub(super) fn sens_zig_linter_t5m_bytes_copy(output: *mut u8, capacity: usize) -> isize;",
                "pub(super) fn sens_zig_linter_bytes_copy(output: *mut u8, capacity: usize) -> isize;",
            ),
            (
                "host",
                "asset_ffi::sens_zig_linter_t5m_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };\n    if copied != required",
                "asset_ffi::sens_zig_linter_t5m_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };\n    if false",
            ),
            (
                "zig", 'const linter_t5m_asset = @embedFile("lib/linter.sens");',
                'const linter_t5m_asset = @embedFile("lib/linter.lisp");',
            ),
            (
                "zig", "if (capacity < linter_t5m_asset.len) return -2;",
                "if (false) return -2; // unchecked write capacity",
            ),
            (
                "zig", "@memcpy(dst[0..linter_t5m_asset.len], linter_t5m_asset[0..linter_t5m_asset.len]);",
                "// @memcpy(dst[0..linter_t5m_asset.len], linter_t5m_asset[0..linter_t5m_asset.len]);",
            ),
            (
                "build", '.arg("zig_transport_root.zig")',
                '.arg("research/zig-codecs/transport_abi.zig")',
            ),
            (
                "build", 'cargo:rerun-if-changed=../../lib/linter.sens',
                'cargo:rerun-if-changed=../../lib/old-linter.sens',
            ),
        )
        baseline = {"main": main, "host": host, "zig": zig, "build": build, "assets": assets}
        for target, original, forged in mutants:
            with self.subTest(target=target, original=original):
                self.assertIn(original, baseline[target], "missing real mutation anchor")
                changed = dict(baseline)
                changed[target] = changed[target].replace(original, forged, 1)
                with self.assertRaisesRegex(blocked, "LINTER_ZIG_ONLY"):
                    check(changed["main"], changed["host"], changed["zig"], changed["build"], changed["assets"])

    def test_contract_zig_carrier_rejects_direct_rust_source_and_forged_copy(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_contract_zig_only"]
        blocked = module["CorridorBlocked"]
        sources = {
            "main": (ROOT / "crates/sens-cli/src/main.rs").read_text(encoding="utf-8"),
            "host": (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8"),
            "zig": (ROOT / "zig_transport_root.zig").read_text(encoding="utf-8"),
            "build": (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8"),
        }
        check(sources["main"], sources["host"], sources["zig"], sources["build"])
        mutations = (
            ("main", "let contract_source = match contract_source_zig_only()",
             'let contract_source = include_str!("../../../language-contract.lisp")'),
            ("main", "zig_transport::contract_source_bytes()?", "Vec::new()"),
            ("main", '"RUST_ZIG_ONLY: language contract requires Zig; no Rust source fallback"',
             '"rust-reference"'),
            (
                "host",
                "asset_ffi::sens_zig_contract_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };\n    if copied != required",
                "asset_ffi::sens_zig_contract_bytes_copy(bytes.as_mut_ptr(), bytes.len()) };\n    if false",
            ),
            ("zig", '@embedFile("language-contract.lisp")', '@embedFile("lib/linter.lisp")'),
            ("zig", "if (capacity < contract_asset.len) return -2;", "if (false) return -2;"),
            ("zig", "@memcpy(dst[0..contract_asset.len], contract_asset[0..contract_asset.len]);",
             "// @memcpy(dst[0..contract_asset.len], contract_asset[0..contract_asset.len]);"),
            ("build", "cargo:rerun-if-changed=../../language-contract.lisp",
             "cargo:rerun-if-changed=../../stale-contract.lisp"),
        )
        for target, needle, mutant in mutations:
            with self.subTest(target=target, needle=needle):
                self.assertIn(needle, sources[target], "mutation must hit live code")
                modified = dict(sources)
                modified[target] = sources[target].replace(needle, mutant, 1)
                with self.assertRaisesRegex(blocked, "CONTRACT_ZIG_ONLY"):
                    check(modified["main"], modified["host"], modified["zig"], modified["build"])

    def test_sanskrit_repl_uses_current_table_projection(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_sanskrit_surface_zig_only"]
        blocked = module["CorridorBlocked"]
        repl = (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8")
        host = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        zig = (ROOT / "zig_transport_root.zig").read_text(encoding="utf-8")
        build = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        check(repl, host, zig, build)

        direct_embed = repl.replace(
            "fn selected_surface_callable(",
            'const LEGACY_SA: &str = include_str!("../../../lib/surface/sa.lisp");\n'
            "fn selected_surface_callable(",
            1,
        )
        with self.assertRaisesRegex(blocked, "SANSKRIT_ZIG_ONLY"):
            check(direct_embed, host, zig, build)

        renamed_surface_identity = repl.replace(
            "surface_catalog::identity_for_surface_name(surface.code(), &projected_name)?",
            "surface_catalog::identity_for_surface_name(\"legacy-sa\", &projected_name)?",
            1,
        )
        with self.assertRaisesRegex(blocked, "SANSKRIT_ZIG_ONLY"):
            check(renamed_surface_identity, host, zig, build)

    def test_full_ukrainian_comment_sources_stay_out_of_runtime(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_ukr_surface_zig_only"]
        blocked = module["CorridorBlocked"]
        files = {
            "repl": (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8"),
            "host": (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8"),
            "zig": (ROOT / "zig_transport_root.zig").read_text(encoding="utf-8"),
            "build": (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8"),
        }
        check(files["repl"], files["host"], files["zig"], files["build"])
        runtime_source = files["repl"].replace(
            "        let prerequisite_assets = surface_prerequisite_t5m_assets()?;",
            "        let _obsolete = ukr_surface_bytes()?;\n        let prerequisite_assets = surface_prerequisite_t5m_assets()?;",
            1,
        )
        with self.assertRaisesRegex(blocked, "UKR_ZIG_ONLY"):
            check(runtime_source, files["host"], files["zig"], files["build"])

        production_embed = files["repl"].replace(
            "fn build_surface_layer(",
            'const STALE_UKR: &str = include_str!("../../../lib/surface/ukr.lisp");\nfn build_surface_layer(',
            1,
        )
        with self.assertRaisesRegex(blocked, "UKR_ZIG_ONLY"):
            check(production_embed, files["host"], files["zig"], files["build"])

        host = files["host"].replace(
            "#[cfg(test)]\npub fn ukr_surface_bytes(", "pub fn ukr_surface_bytes(", 1
        )
        with self.assertRaisesRegex(blocked, "UKR_ZIG_ONLY"):
            check(files["repl"], host, files["zig"], files["build"])

    def test_compact_uk_comment_sources_stay_out_of_runtime(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_uk_surface_zig_only"]
        blocked = module["CorridorBlocked"]
        files = {
            "repl": (ROOT / "crates/sens-cli/src/repl.rs").read_text(encoding="utf-8"),
            "host": (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8"),
            "zig": (ROOT / "zig_transport_root.zig").read_text(encoding="utf-8"),
            "build": (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8"),
        }
        check(files["repl"], files["host"], files["zig"], files["build"])
        runtime_source = files["repl"].replace(
            "        let prerequisite_assets = surface_prerequisite_t5m_assets()?;",
            "        let _obsolete = uk_surface_bytes()?;\n        let prerequisite_assets = surface_prerequisite_t5m_assets()?;",
            1,
        )
        with self.assertRaisesRegex(blocked, "UK_ZIG_ONLY"):
            check(runtime_source, files["host"], files["zig"], files["build"])

        production_embed = files["repl"].replace(
            "fn build_surface_layer(",
            'const STALE_UK: &str = include_str!("../../../lib/surface/uk.lisp");\nfn build_surface_layer(',
            1,
        )
        with self.assertRaisesRegex(blocked, "UK_ZIG_ONLY"):
            check(production_embed, files["host"], files["zig"], files["build"])

        host = files["host"].replace(
            "#[cfg(test)]\npub fn uk_surface_bytes(", "pub fn uk_surface_bytes(", 1
        )
        with self.assertRaisesRegex(blocked, "UK_ZIG_ONLY"):
            check(files["repl"], host, files["zig"], files["build"])

    def test_corridor_file_has_no_local_t5_codec(self) -> None:
        body = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        self.assertIn("sens_zig_t5_decode_be3", body)
        self.assertIn("sens_zig_t5_encode_be3", body)
        self.assertNotIn("PhysicalT5Program", body)
        self.assertNotIn("ternary_transport", body)
        self.assertNotIn("TRITS_BY_BYTE", body)
        self.assertIn("packed_bits", body)
        self.assertIn("decode_t5m_exact_words", body)
        self.assertIn("encode_t5m_exact_words", body)
        self.assertNotIn("from_width_bits", body)

    def test_t5m_codec_keeps_width_opaque_and_has_no_domain_authority(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_zig_t5m_width_firewall"]
        blocked = module["CorridorBlocked"]
        path = ROOT / "research/zig-codecs/t5m.zig"
        source = path.read_text(encoding="utf-8")
        check(source)

        with self.subTest(mutant="domain table import"):
            mutant = source.replace(
                'const std = @import("std");',
                'const std = @import("std");\nconst domains = @import("domain_ladder.zig");',
                1,
            )
            with self.assertRaisesRegex(blocked, "T5M_WIDTH_FIREWALL"):
                check(mutant)

        with self.subTest(mutant="artificial width ceiling"):
            mutant = source.replace(
                "return width != 0;",
                "return width != 0 and width <= 24;",
                1,
            )
            with self.assertRaisesRegex(blocked, "T5M_WIDTH_FIREWALL"):
                check(mutant)

    def test_f3c_no_savings_rejects_t5m_validation_bypass_mutants(self) -> None:
        """encode_f3 must validate T5M via Zig before a no-savings result."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_f3c_validate_before_no_savings"]
        blocked = module["CorridorBlocked"]
        body = (ROOT / "crates/sens-cli/src/zig_transport.rs").read_text(encoding="utf-8")
        check(body)

        no_validate = body.replace("let logical_words = decode_t5m_words(t5)?;",
                                   "let logical_words = vec![];", 1)
        with self.assertRaises(blocked):
            check(no_validate)

        start = body.index("pub fn encode_f3(")
        end = body.index("pub fn decode_f3(")
        route = body[start:end]
        swapped = route.replace(
            "let logical_words = decode_t5m_words(t5)?;\n    let legacy",
            "if legacy.len() > 16 { return Ok(None); }\n    let logical_words = decode_t5m_words(t5)?;\n    let legacy",
            1,
        )
        self.assertNotEqual(swapped, route, "mutation must move live validation")
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

        no_validate = body.replace("validate_legacy_t5(bytes)?;", "/* no validate */", 1)
        with self.assertRaises(blocked):
            check(no_validate)

        stripped = body.replace("validate_legacy_t5(bytes)?;\n", "", 1)
        if stripped == body:
            stripped = body.replace("validate_legacy_t5(bytes)?;", "", 1)
        with self.assertRaises(blocked):
            check(stripped)

        for bypass in (
            "let _ = validate_legacy_t5(bytes);",
            "validate_legacy_t5(bytes);",
            "// validate_legacy_t5(bytes)?;",
            "/* validate_legacy_t5(bytes)?; */",
            "validate_legacy_t5(carrier)?;",
            "return Ok(words);\n    validate_legacy_t5(bytes)?;",
        ):
            with self.subTest(bypass=bypass):
                mutant = body.replace("validate_legacy_t5(bytes)?;", bypass, 1)
                self.assertNotEqual(mutant, body)
                with self.assertRaises(blocked):
                    check(mutant)

        mutant = body.replace(
            "validate_legacy_t5(bytes)?;\n    let capacity",
            "let capacity",
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

        encode_start = body.index("pub fn encode_f3(")
        encode_end = body.index("pub fn decode_f3(", encode_start)
        encode_route = body[encode_start:encode_end]
        no_bound_route = re.sub(
            r"\.filter\(\|&n\| n < legacy\.len\(\) && n <= bytes\.len\(\)\)",
            ".filter(|_| true)",
            encode_route,
            count=1,
        )
        self.assertNotEqual(no_bound_route, encode_route)
        no_bound = body[:encode_start] + no_bound_route + body[encode_end:]
        with self.assertRaises(blocked):
            check(no_bound)

        decode_start = body.index("pub fn decode_f3(")
        decode_end = body.index("#[cfg(test)]", decode_start)
        decode_route = body[decode_start:decode_end]
        no_decode_route = re.sub(
            r"\.filter\(\|&n\| n <= output\.len\(\)\)",
            ".filter(|_| true)",
            decode_route,
            count=1,
        )
        self.assertNotEqual(no_decode_route, decode_route)
        no_decode_bound = body[:decode_start] + no_decode_route + body[decode_end:]
        with self.assertRaises(blocked):
            check(no_decode_bound)

        no_cap_route = encode_route.replace("n <= bytes.len()", "true /* mutant */", 1)
        no_cap = body[:encode_start] + no_cap_route + body[encode_end:]
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



    def test_default_zig_build_compiles_root_and_links_real_archive(self) -> None:
        """The live default Rust->Zig turnstile needs a pinned compiler and link."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_default_zig_build_gate"]
        blocked = module["CorridorBlocked"]
        build = (ROOT / "crates/sens-cli/build.rs").read_text(encoding="utf-8")
        check(build)

        mutants = (
            ("missing-command", '.arg("build-lib")', '.arg("version")'),
            ("wrong-root", '.arg("zig_transport_root.zig")',
             '.arg("research/zig-codecs/transport_abi.zig")'),
            ("wrong-version-assert", 'actual, pinned,', 'actual, actual,'),
            ("no-archive-emission",
             '.arg(format!("-femit-bin={}", archive.display()))',
             '.arg("-femit-bin=other.a")'),
            ("no-link", 'println!("cargo:rustc-link-lib=static=sens_zig_transport");',
             '// println!("cargo:rustc-link-lib=static=sens_zig_transport");'),
            ("comment-only-build", '.arg("build-lib")',
             '/* .arg("build-lib") */ .arg("version")'),
        )
        for label, old, new in mutants:
            with self.subTest(test_id=label):
                self.assertIn(old, build, "live Cargo build shape changed")
                changed = build.replace(old, new, 1)
                with self.assertRaises(blocked):
                    check(changed)


    def test_f3c_cli_is_truly_zig_only_in_both_build_modes(self) -> None:
        """Fail closed if an F3C Rust codec or fake denial is introduced."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_f3_no_rust_fallback"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(
            encoding="utf-8"
        )
        check(source)
        # Both valid Rust egress forms must preserve the Zig path.
        tail = "zig_transport::encode_f3(bytes)"
        self.assertIn(tail, source, "missing live F3C Zig egress")
        check(source.replace(tail, "return zig_transport::encode_f3(bytes);", 1))

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
                "zig_transport::encode_f3(bytes)",
                "return Ok(Some(bytes.to_vec())); // zig_transport::encode_f3(bytes)",
            ),
            (
                "zig_transport::encode_f3(bytes)",
                "let _ = zig_transport::encode_f3(bytes);\\n        Ok(Some(bytes.to_vec()))",
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
                "ingress",
                "return zig_transport::decode_t5m_exact_words(bytes)?",
                "return sens::decode_ternary_words(bytes).map_err(|e| format!(\"{e:?}\"));",
            ),
            (
                "ingress",
                'Err("physical .sens requires the Zig transport corridor; no Rust fallback".into())',
                'sens::decode_ternary_words(bytes).map_err(|e| format!("{e:?}"))',
            ),
            (
                "eval",
                "let words = decode_physical_t5m_words(bytes)?;",
                "let words = sens::decode_ternary_words(bytes).unwrap();",
            ),
            (
                "eval",
                "sens::PhysicalT5Program::from_exact_domain_words_owned(words)",
                "sens::parse_canonical_binary(\"not exact words\")",
            ),
            (
                "main",
                "eval_physical_t5(&bytes)",
                "sens::decode_ternary_words(&bytes).map(|_| Default::default())",
            ),
        )
        for route_name, old, replacement in replacements:
            with self.subTest(bypass=old):
                self.assertIn(old, source)
                if route_name == "ingress":
                    start = source.index("fn decode_physical_t5m_words(")
                    end = source.index("\nfn eval_physical_t5(", start)
                elif route_name == "eval":
                    start = source.index("fn eval_physical_t5(")
                    end = source.index("\nfn eval_physical_t5_with_benchmark_metrics(", start)
                else:
                    start = source.index("fn main() {")
                    end = source.index("\n#[cfg(test)]", start)
                route = source[start:end]
                changed_route = route.replace(old, replacement, 1)
                self.assertNotEqual(changed_route, route, "mutation must alter the intended live route")
                with self.assertRaises(blocked):
                    check(source[:start] + changed_route + source[end:])


    def test_explain_must_use_typed_words_not_rust_text_reparse(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_explain_typed_word_route"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(
            encoding="utf-8"
        )
        check(source)
        start = source.index("fn explain_t5m_bytes(")
        end = source.index("\nfn require_zig_transport(", start)
        route = source[start:end]
        for old, fake in (
            (
                "sens::ExactDomainWord::from_physical_width_bits(word.width, &word.bits)",
                "sens::parse_canonical_binary(&sens::render_ternary_words_vertical(&words))",
            ),
            (
                "zig_transport::decode_t5m_exact_words(bytes)",
                "sens::decode_ternary_words(bytes)",
            ),
            (
                "sens::PhysicalT5Program::from_exact_domain_words_owned(exact)",
                "exact",
            ),
        ):
            with self.subTest(mutation=old):
                self.assertIn(old, route, "mutate the actual explain function")
                mutant = source[:start] + route.replace(old, fake, 1) + source[end:]
                with self.assertRaises(blocked):
                    check(mutant)

    def test_trit_default_egress_rejects_rust_codec_mutants(self) -> None:
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_t5_egress"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        check(source)

        replacements = (
            (
                "let bytes = zig_transport::encode_t5m_direct(&admitted_source_words(&projection)?)?;",
                "let bytes = sens::encode_binary_projection_ternary(&projection).unwrap();",
            ),
            (
                "let expected_words = admitted_source_words(source)?;",
                "let expected_words = decode_canonical_t5m_words(binary)?;",
            ),
            (
                "zig_transport::verify_t5m_encoding(&expected_words, binary)",
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
            "zig_transport::encode_t5m_direct(&admitted_source_words(&projection)?)?;"
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
                "decode_canonical_t5m_words(physical_t5)",
                "sens::decode_ternary_words(physical_t5)",
            ),
            (
                'Err("E1 physical export requires Zig; no Rust fallback".into())',
                'sens::envelope_e1::encode(&[]).map_err(|e| format!("{e:?}"))',
            ),
            (
                "let e1 = encode_e1_from_t5m(&bytes)?;",
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
        start = source.index("fn eval_e1_bytes(")
        end = source.index("\nfn read_explicit_f3(", start)
        route = source[start:end]

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
        )
        for original, bypass in mutations:
            with self.subTest(mutant=original):
                self.assertIn(original, route)
                mutated_route = route.replace(original, bypass, 1)
                with self.assertRaises(blocked):
                    check(source[:start] + mutated_route + source[end:])

        dispatch_mutant = source.replace(
            "let result = eval_e1_bytes(&e1)?;",
            'let result = sens::eval_e1_program(&e1, &mut session).unwrap();',
            1,
        )
        self.assertNotEqual(dispatch_mutant, source)
        with self.assertRaises(blocked):
            check(dispatch_mutant)

    def test_live_t5_eval_and_core4_reject_rust_execution_bypass_mutants(self) -> None:
        """Mutate the *actual* guarded execution routine, never test fixtures."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_trit_t5_execution"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "crates/sens-cli/src/bin/sens-trit.rs").read_text(encoding="utf-8")
        check(source)
        start = source.index("fn eval_t5m_bytes_core4(")
        end = source.index("\n/// Diagnose a physical packed T5M file", start)
        actual_route = source[start:end]
        mutations = (
            (
                "zig_transport::decode_t5m_exact_words(bytes)?",
                "sens::decode_ternary_words(bytes).unwrap()",
            ),
            (
                "sens::PhysicalT5Program::from_exact_domain_words_owned(words)",
                "sens::PhysicalT5Program::decode(bytes).unwrap()",
            ),
            (
            'Err("physical T5M execution requires Zig; no Rust fallback".into())',
                "sens::eval_t5_program(bytes, &mut sens::Session::default()).map_err(|e| format!(\"{e:?}\"))",
            ),
        )
        for original, bypass in mutations:
            with self.subTest(mutant=original):
                self.assertIn(original, actual_route, "production routine changed")
                changed = source[:start] + actual_route.replace(original, bypass, 1) + source[end:]
                with self.assertRaises(blocked):
                    check(changed)

        entry = "eval_t5m_bytes_core4(&bytes, true)?"
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
            '    zig_transport::decode_t5m_exact_words(bytes);\n'
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
        live = "return zig_transport::decode_t5m_exact_words(bytes)?"
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
            source.replace('use sens_cli::zig_transport;', 'use untrusted_transport;'),
            source.replace('use sens_cli::zig_transport;', '// use sens_cli::zig_transport;'),
            source.replace('#[cfg(feature = "zig-transport")]\nuse sens_cli::zig_transport;', '#[cfg(test)]\nuse sens_cli::zig_transport;'),
            source.replace('fn decode_physical_t5m_words(', 'fn bypass_physical_t5m_words('),
            source.replace('fn eval_physical_t5(', 'fn bypass_eval_physical_t5('),
            source.replace('fn main() {', 'fn other_main() {'),
        ):
            with self.subTest(kind="missing-entrypoint"), self.assertRaises(blocked):
                check(mutant)


    def test_all_zig_abi_v2_exports_are_live_not_comment_or_rust_names(self) -> None:
        """Rust's declared extern cannot stand in for the real Zig symbol."""
        module = runpy.run_path(str(SCRIPT))
        check = module["check_zig_abi_v2_live_exports"]
        blocked = module["CorridorBlocked"]
        source = (ROOT / "research/zig-codecs/transport_abi.zig").read_text(
            encoding="utf-8"
        )
        check(source)
        for name in module["REQUIRED_FFI"]:
            with self.subTest(export=name):
                declaration = f"pub export fn {name}("
                self.assertIn(declaration, source)
                # A visible symbol name in a comment must not satisfy ABI v2.
                changed = source.replace(declaration, "// " + declaration, 1)
                with self.assertRaisesRegex(blocked, "live Zig ABI v2 export"):
                    check(changed)
        changed_version = source.replace(
            "pub export fn sens_zig_codec_abi_version() u32 {\n    return 2;\n}",
            "pub export fn sens_zig_codec_abi_version() u32 {\n    return 3;\n}",
            1,
        )
        self.assertNotEqual(changed_version, source)
        with self.assertRaisesRegex(blocked, "ABI version must return 2"):
            check(changed_version)

if __name__ == "__main__":
    unittest.main(verbosity=2)
