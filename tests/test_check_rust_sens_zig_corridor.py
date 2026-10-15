#!/usr/bin/env python3
"""Negative controls for the Rust<->SENS sterile-Zig-corridor guard (#5777/#5779).

Each invariant must fail CLOSED: mutating it in a mirror of the real corridor
files must make the checker report at least one problem.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_rust_sens_zig_corridor.py"

CORRIDOR_FILES = (
    "crates/sens-cli/Cargo.toml",
    "crates/sens-cli/build.rs",
    "crates/sens-cli/src/zig_transport.rs",
    "crates/sens-cli/src/main.rs",
    "crates/sens-cli/src/bin/sens-trit.rs",
    "research/zig-codecs/transport_abi.zig",
    ".zig-version",
)


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_zig_corridor_guard", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mirror(dst: Path) -> None:
    for rel in CORRIDOR_FILES:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)


def mutate(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"mutation anchor not found in {rel}: {old!r}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class CorridorGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        mirror(self.root)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_corridor_passes(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_default_without_zig_transport_is_blocked(self) -> None:
        mutate(self.root, "crates/sens-cli/Cargo.toml", 'default = ["zig-transport"]', "default = []")
        self.assertTrue(self.module.check(self.root))

    def test_missing_feature_gate_is_blocked(self) -> None:
        mutate(
            self.root,
            "crates/sens-cli/build.rs",
            "CARGO_FEATURE_ZIG_TRANSPORT",
            "CARGO_FEATURE_SOMETHING_ELSE",
        )
        self.assertTrue(self.module.check(self.root))

    def test_semantic_import_in_abi_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/transport_abi.zig",
            '@import("t5/t5.zig")',
            '@import("semantic_registry.zig")',
        )
        self.assertTrue(self.module.check(self.root))

    def test_nonphysical_export_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/transport_abi.zig",
            "pub export fn sens_zig_codec_abi_version",
            "pub export fn host_eval_program",
        )
        self.assertTrue(self.module.check(self.root))

    def test_unpinned_zig_version_is_blocked(self) -> None:
        mutate(self.root, ".zig-version", "0.16.0", "latest")
        self.assertTrue(self.module.check(self.root))

    def test_client_without_packed_bits_is_blocked(self) -> None:
        path = self.root / "crates/sens-cli/src/zig_transport.rs"
        text = path.read_text(encoding="utf-8")
        self.assertIn("packed_bits", text)
        path.write_text(text.replace("packed_bits", "payload_bits"), encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_main_without_zig_decode_is_blocked(self) -> None:
        mutate(
            self.root,
            "crates/sens-cli/src/main.rs",
            "zig_transport::decode_t5_words",
            "sens::decode_ternary_words_FORBIDDEN",
        )
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main(verbosity=2)
