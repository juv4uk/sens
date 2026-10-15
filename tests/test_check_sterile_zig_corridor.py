#!/usr/bin/env python3
"""Negative controls for the Zig corridor sterility guard (#5777/#5779).

Each sterility invariant must fail CLOSED.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_sterile_zig_corridor.py"

FILES = (
    "research/zig-codecs/transport_abi.zig",
    "research/zig-codecs/host-c/zig_transport_v2.h",
)


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_sterile_zig_corridor", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mirror(dst: Path) -> None:
    for rel in FILES:
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, target)


def mutate(root: Path, rel: str, old: str, new: str) -> None:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"mutation anchor not found in {rel}: {old!r}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


class SterileCorridorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        mirror(self.root)
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_real_corridor_is_sterile(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_nonphysical_export_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/transport_abi.zig",
            "pub export fn sens_zig_codec_abi_version",
            "pub export fn host_opcode",
        )
        self.assertTrue(self.module.check(self.root))

    def test_semantic_import_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/transport_abi.zig",
            '@import("t5/t5.zig")',
            '@import("semantic-registry.zig")',
        )
        self.assertTrue(self.module.check(self.root))

    def test_host_struct_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/transport_abi.zig",
            "const std = @import(\"std\");",
            "const std = @import(\"std\");\nextern struct HostValue { tag: u32 };",
        )
        self.assertTrue(self.module.check(self.root))

    def test_missing_sterility_contract_is_blocked(self) -> None:
        mutate(
            self.root,
            "research/zig-codecs/host-c/zig_transport_v2.h",
            "no SENS semantic registry",
            "some opaque note",
        )
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
