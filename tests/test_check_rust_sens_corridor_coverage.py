#!/usr/bin/env python3
"""Negative controls for the Rust<->SENS corridor-coverage guard (#5777).

A host that bypasses the corridor must be registered; an unregistered bypass must
fail CLOSED.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_rust_sens_corridor_coverage.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_corridor_coverage", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_crate(root: Path, name: str, body: str) -> None:
    src = root / "crates" / name / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "lib.rs").write_text(body, encoding="utf-8")


def write_registry(
    root: Path, exemptions: list, *,
    schema: str = "sens-rust-sens-corridor-coverage/v1",
    codec_owner: str = "crates/sens",
) -> None:
    path = root / "research" / "zig-codecs" / "corridor_host_coverage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema": schema, "codec_owner": codec_owner, "exemptions": exemptions,
    }), encoding="utf-8")


class CorridorCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_tree_is_covered(self) -> None:
        self.assertEqual(self.module.check(ROOT), [])

    def test_unregistered_bypass_is_blocked(self) -> None:
        write_crate(self.root, "rogue", "fn f() { sens::decode_binary_frame(&[]); }")
        write_registry(self.root, [])
        self.assertTrue(self.module.check(self.root))

    def test_registered_bypass_passes(self) -> None:
        write_crate(self.root, "known", "fn f() { sens::decode_binary_frame(&[]); }")
        write_registry(self.root, [{"crate": "crates/known", "reason": "pending", "issue": 5787}])
        self.assertEqual(self.module.check(self.root), [])

    def test_corridor_host_passes(self) -> None:
        write_crate(
            self.root, "cli",
            "fn f() { zig_transport::decode_t5_words(&[]); sens::decode_ternary_words(&[]); }",
        )
        write_registry(self.root, [])
        self.assertEqual(self.module.check(self.root), [])

    def test_unrelated_zig_file_cannot_hide_direct_codec_route(self) -> None:
        # One live Zig call elsewhere in a crate is not an authorization for
        # direct SENS codec access in lib.rs (physical edge must be file-local).
        write_crate(self.root, "split", "fn f() { sens::decode_binary_frame(&[]); }")
        (self.root / "crates/split/src/bridge.rs").write_text(
            "fn g() { zig_transport::decode_t5_words(&[]); }",
            encoding="utf-8",
        )
        write_registry(self.root, [])
        errors = self.module.check(self.root)
        self.assertTrue(
            any("crates/split/src/lib.rs" in error for error in errors),
            f"test_id=zig-cross-file-bypass layer=transport expected=BLOCKED actual={errors!r}",
        )

    def test_same_file_live_zig_call_preserves_corridor_admission(self) -> None:
        write_crate(
            self.root, "joined",
            "fn f() { zig_transport::decode_t5_words(&[]); "
            "sens::decode_binary_frame(&[]); }",
        )
        write_registry(self.root, [])
        self.assertEqual(
            self.module.check(self.root), [],
            "test_id=zig-same-file-ingress layer=transport expected=COVERAGE_OK",
        )

    def test_cfg_test_only_zig_call_cannot_hide_production_bypass(self) -> None:
        # A real Zig invocation in test-only Rust is NOT production FFI.
        write_crate(
            self.root, "testghost",
            "fn physical() { sens::decode_binary_frame(&[]); }\n"
            "#[cfg(test)]\n"
            "fn fake_witness() { zig_transport::decode_t5_words(&[]); }\n",
        )
        write_registry(self.root, [])
        errors = self.module.check(self.root)
        self.assertTrue(
            any("crates/testghost/src/lib.rs" in error for error in errors),
            f"test_id=zig-cfg-test-ghost layer=transport expected=BLOCKED actual={errors!r}",
        )

    def test_cfg_test_module_before_production_cannot_hide_bypass(self) -> None:
        # The guard must inspect real Rust items after a test-only module.
        write_crate(
            self.root, "testfirst",
            "#[cfg(test)]\n"
            "mod tests { fn fake() { zig_transport::decode_t5_words(&[]); } }\n"
            "fn live() { sens::decode_binary_frame(&[]); }\n",
        )
        write_registry(self.root, [])
        errors = self.module.check(self.root)
        self.assertTrue(
            any("crates/testfirst/src/lib.rs" in error for error in errors),
            f"test_id=zig-test-before-production layer=transport "
            f"expected=COVERAGE_BLOCKED actual={errors!r}",
        )

    def test_production_zig_after_cfg_test_module_remains_covered(self) -> None:
        write_crate(
            self.root, "zigafter",
            "#[cfg(test)]\n"
            "mod tests { fn fake() { zig_transport::decode_t5_words(&[]); } }\n"
            "fn live() { zig_transport::decode_t5_words(&[]); "
            "sens::decode_binary_frame(&[]); }\n",
        )
        write_registry(self.root, [])
        self.assertEqual(
            self.module.check(self.root), [],
            "test_id=zig-real-ingress-after-tests layer=transport expected=COVERAGE_OK",
        )

    def test_cfg_all_test_only_zig_is_not_production_proof(self) -> None:
        # Even compound test-only cfg attributes cannot authorize bypassing Zig.
        for gate in (
            'all(test, feature = "bench")',
            'all(feature = "bench", test)',
            'all ( feature = "bench", test )',
            'all (test)',
            'all(unix, any(test, all(test, feature = "bench")))',
            'any(all(test, unix), all(test, windows))',
        ):
            with self.subTest(gate=gate):
                write_crate(
                    self.root, "compound",
                    "fn live() { sens::decode_binary_frame(&[]); }\n"
                    f"#[cfg({gate})]\n"
                    "mod test_only { fn witness() { "
                    "zig_transport::decode_t5_words(&[]); } }\n",
                )
                write_registry(self.root, [])
                errors = self.module.check(self.root)
                self.assertTrue(
                    any("crates/compound/src/lib.rs" in error for error in errors),
                    f"test_id=zig-compound-test-only layer=transport "
                    f"expected=COVERAGE_BLOCKED gate={gate} actual={errors!r}",
                )

    def test_cfg_any_test_or_feature_stays_production_visible(self) -> None:
        # cfg(any(test, feature=...)) can be enabled outside test builds.
        write_crate(
            self.root, "conditional",
            "fn live() { sens::decode_binary_frame(&[]); }\n"
            '#[cfg(any(test, feature = "physical"))]\n'
            "fn possible_ingress() { zig_transport::decode_t5_words(&[]); }\n",
        )
        write_registry(self.root, [])
        self.assertEqual(self.module.check(self.root), [])

    def test_unterminated_cfg_test_item_fails_closed(self) -> None:
        write_crate(
            self.root, "badtest",
            "#[cfg(test)]\n"
            "mod tests { fn fake() { zig_transport::decode_t5_words(&[]); }\n"
            "fn live() { sens::decode_binary_frame(&[]); }\n",
        )
        write_registry(self.root, [])
        errors = self.module.check(self.root)
        self.assertTrue(
            any("cfg(test) boundary is ambiguous" in error for error in errors),
            f"test_id=zig-invalid-test-boundary expected=COVERAGE_BLOCKED actual={errors!r}",
        )

    def test_production_zig_call_still_proves_source_ingress_with_tests(self) -> None:
        write_crate(
            self.root, "realzig",
            "fn physical() { zig_transport::decode_t5_words(&[]); "
            "sens::decode_binary_frame(&[]); }\n"
            "#[cfg(test)]\n"
            "fn witness() { zig_transport::validate_t5(&[]); }\n",
        )
        write_registry(self.root, [])
        self.assertEqual(
            self.module.check(self.root), [],
            "test_id=zig-prod-cfg-test-positive layer=transport expected=COVERAGE_OK",
        )

    def test_comment_only_zig_reference_does_not_hide_bypass(self) -> None:
        write_crate(
            self.root, "comment", "fn f() { sens::decode_binary_frame(&[]); } "
            "// zig_transport::decode_t5_words(&bytes)\n",
        )
        write_registry(self.root, [])
        self.assertTrue(any("crates/comment" in x for x in self.module.check(self.root)))

    def test_string_only_zig_reference_does_not_hide_bypass(self) -> None:
        write_crate(
            self.root, "literal",
            'fn f() { sens::decode_binary_frame(&[]); '
            'let _s = "zig_transport::decode_t5_words(&bytes)"; }',
        )
        write_registry(self.root, [])
        self.assertTrue(any("crates/literal" in x for x in self.module.check(self.root)))

    def test_nested_block_comment_does_not_hide_bypass(self) -> None:
        write_crate(
            self.root, "nested", "/* outer /* inner */ "
            "zig_transport::decode_t5_words(&bytes) */ "
            "fn f() { sens::decode_binary_frame(&[]); }",
        )
        write_registry(self.root, [])
        self.assertTrue(any("crates/nested" in x for x in self.module.check(self.root)))

    def test_raw_string_does_not_hide_bypass(self) -> None:
        write_crate(
            self.root, "raw",
            'fn f() { sens::decode_binary_frame(&[]); '
            'let _s = r###"zig_transport::decode_t5_words(&bytes)"###; }',
        )
        write_registry(self.root, [])
        self.assertTrue(any("crates/raw" in x for x in self.module.check(self.root)))

    def test_bare_module_identifier_does_not_prove_corridor_use(self) -> None:
        write_crate(
            self.root, "module",
            "mod zig_transport; fn f() { sens::decode_binary_frame(&[]); }",
        )
        write_registry(self.root, [])
        self.assertTrue(any("crates/module" in x for x in self.module.check(self.root)))

    def test_string_comment_delimiter_does_not_hide_real_call(self) -> None:
        write_crate(
            self.root, "real",
            'fn f() { let _s = "/*"; '
            'zig_transport::decode_t5_words(&bytes); '
            'sens::decode_binary_frame(&[]); }',
        )
        write_registry(self.root, [])
        self.assertEqual(self.module.check(self.root), [])

    def test_duplicate_exception_is_blocked(self) -> None:
        write_crate(self.root, "known", "fn f(){ sens::decode_binary_frame(&[]); }")
        entry = {"crate": "crates/known", "reason": "pending Zig migration", "issue": 5787}
        write_registry(self.root, [entry, dict(entry)])
        self.assertTrue(any("duplicate exemption" in x for x in self.module.check(self.root)))

    def test_blank_reason_is_not_provenance(self) -> None:
        write_crate(self.root, "known", "fn f(){ sens::decode_binary_frame(&[]); }")
        write_registry(self.root, [{"crate": "crates/known", "reason": "  ", "issue": 5787}])
        self.assertTrue(any("nonblank reason" in x for x in self.module.check(self.root)))

    def test_bool_or_string_issue_is_not_an_issue_number(self) -> None:
        write_crate(self.root, "known", "fn f(){ sens::decode_binary_frame(&[]); }")
        for issue in (True, "5787", 0, -1, None):
            with self.subTest(issue=issue):
                write_registry(self.root, [
                    {"crate": "crates/known", "reason": "pending Zig migration", "issue": issue}
                ])
                self.assertTrue(any("positive GitHub issue" in x
                                    for x in self.module.check(self.root)))

    def test_registry_schema_and_owner_drift_are_blocked(self) -> None:
        (self.root / "crates").mkdir()
        write_registry(self.root, [], schema="legacy")
        self.assertTrue(any("schema mismatch" in x for x in self.module.check(self.root)))
        write_registry(self.root, [], codec_owner="crates/other")
        self.assertTrue(any("codec_owner mismatch" in x
                            for x in self.module.check(self.root)))

    def test_stale_exemption_must_be_retired_after_zig_migration(self) -> None:
        write_crate(self.root, "done", "fn f(){ zig_transport::decode_t5_words(&bytes); }")
        write_registry(self.root, [
            {"crate": "crates/done", "reason": "historical bypass", "issue": 5787}
        ])
        self.assertTrue(any("stale exemption crates/done" in x
                            for x in self.module.check(self.root)))

    def test_exemption_for_nonexistent_crate_is_blocked(self) -> None:
        (self.root / "crates").mkdir()
        write_registry(self.root, [
            {"crate": "crates/ghost", "reason": "invented exemption", "issue": 5787}
        ])
        self.assertTrue(any("stale exemption crates/ghost" in x
                            for x in self.module.check(self.root)))

    def test_nonobject_registry_and_malformed_records_fail_closed(self) -> None:
        (self.root / "crates").mkdir()
        write_registry(self.root, ["not an object"])
        self.assertTrue(any("must be an object" in x for x in self.module.check(self.root)))
        path = self.root / "research" / "zig-codecs" / "corridor_host_coverage.json"
        path.write_text('{"schema":', encoding="utf-8")
        self.assertTrue(any("invalid JSON" in x for x in self.module.check(self.root)))
        path.write_text("[]", encoding="utf-8")
        self.assertTrue(any("must be a JSON object" in x
                            for x in self.module.check(self.root)))

    def test_registry_rejects_nonlist_exemptions_and_invalid_path(self) -> None:
        (self.root / "crates").mkdir()
        path = self.root / "research" / "zig-codecs" / "corridor_host_coverage.json"
        write_registry(self.root, [])
        data = json.loads(path.read_text(encoding="utf-8"))
        data["exemptions"] = {}
        path.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(any("must be a JSON list" in x
                            for x in self.module.check(self.root)))
        write_registry(self.root, [
            {"crate": "../sens", "reason": "rogue", "issue": 5787}
        ])
        self.assertTrue(any("invalid crate path" in x
                            for x in self.module.check(self.root)))

    def test_symlinked_crate_src_file_and_nested_directory_fail_closed(self) -> None:
        if sys.platform == "win32":
            self.skipTest("creating symlinks requires Windows developer permissions")
        # These four paths are NOT an attested Rust source inventory. In
        # particular, rglob may not descend into a symlinked Rust directory.
        external = self.root / "outside"
        external.mkdir()
        (external / "rogue.rs").write_text(
            "fn f() { sens::decode_binary_frame(&[]); }", encoding="utf-8"
        )
        crates = self.root / "crates"
        crates.mkdir()
        (crates / "linkedcrate").symlink_to(external, target_is_directory=True)
        (crates / "linkedsrc").mkdir()
        (crates / "linkedsrc" / "src").symlink_to(external, target_is_directory=True)
        write_crate(self.root, "linkedfile", "fn f() { zig_transport::decode_t5_words(&[]); }")
        (crates / "linkedfile" / "src" / "rogue.rs").symlink_to(external / "rogue.rs")
        write_crate(self.root, "linkeddir", "fn f() { zig_transport::decode_t5_words(&[]); }")
        (crates / "linkeddir" / "src" / "hidden").symlink_to(
            external, target_is_directory=True
        )
        write_registry(self.root, [])
        errors = self.module.check(self.root)
        for expected in (
            "crates/linkedcrate",
            "crates/linkedsrc/src",
            "crates/linkedfile/src/rogue.rs",
            "crates/linkeddir/src/hidden",
        ):
            with self.subTest(path=expected):
                self.assertTrue(
                    any(expected in error and "symlink" in error for error in errors),
                    f"test_id=zig-source-symlink layer=transport "
                    f"expected=BLOCKED({expected}) actual={errors!r}",
                )

    def test_symlinked_crates_root_is_not_a_trustworthy_inventory(self) -> None:
        if sys.platform == "win32":
            self.skipTest("creating symlinks requires Windows developer permissions")
        external = self.root / "outside"
        external.mkdir()
        (self.root / "crates").symlink_to(external, target_is_directory=True)
        write_registry(self.root, [])
        errors = self.module.check(self.root)
        self.assertTrue(
            any("crates/" in error and "symlinked" in error for error in errors),
            f"test_id=zig-symlinked-crates-root layer=transport "
            f"expected=BLOCKED actual={errors!r}",
        )

    def test_codec_owner_is_exempt(self) -> None:
        write_crate(self.root, "sens", "fn f() { decode_binary_frame(&[]); }")
        write_registry(self.root, [])
        self.assertEqual(self.module.check(self.root), [])


if __name__ == "__main__":
    unittest.main()
