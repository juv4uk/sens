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


def write_registry(root: Path, exemptions: list) -> None:
    path = root / "research" / "zig-codecs" / "corridor_host_coverage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": "x", "exemptions": exemptions}), encoding="utf-8")


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

    def test_codec_owner_is_exempt(self) -> None:
        write_crate(self.root, "sens", "fn f() { decode_binary_frame(&[]); }")
        write_registry(self.root, [])
        self.assertEqual(self.module.check(self.root), [])


if __name__ == "__main__":
    unittest.main()
