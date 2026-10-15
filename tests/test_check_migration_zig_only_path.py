#!/usr/bin/env python3
"""Negative controls for the migration Zig-only-path guard (#5777/#5779)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "check_migration_zig_only_path.py"

BATCH_OK = """import zig_codec_bridge
def run(args):
    zig_temp = tempfile.TemporaryDirectory() if args.zig_codec else None
    zig_binary = zig_codec_bridge.build_transport(Path(zig_temp.name)) if zig_temp else None
    for rel in paths:
        python_packed = mig.encode_projection(projection)
        packed = python_packed
        if zig_binary is not None:
            packed = zig_codec_bridge.encode_t5(zig_binary, view)
            zig_codec_bridge.require_parity(packed, python_packed)
            evidence = zig_codec_bridge.verify_t5(zig_binary, packed)
            row["zig_transport"] = evidence
        if args.write:
            staged.append((rel, packed, row))
def main():
    parser.add_argument("--zig-codec", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write and not args.zig_codec:
        return 3
    return run(args)
"""

BRIDGE_OK = """class ZigCodecError(ValueError):
    pass
def pinned_compiler():
    expected = PIN_FILE.read_text().strip()
    if expected != "0.16.0":
        raise ZigCodecError("ZIG_CODEC_PIN_DRIFT")
def build_transport(directory):
    if binary.exists():
        raise ZigCodecError("ZIG_CODEC_OUTPUT_EXISTS")
def _built_executable_digest(binary):
    raise ZigCodecError("ZIG_CODEC_UNATTESTED_BINARY: build with build_transport first")
"""


def load_checker():
    spec = importlib.util.spec_from_file_location("sens_migration_zig_only_path", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MigrationZigOnlyPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "scripts").mkdir(parents=True, exist_ok=True)
        (self.root / "scripts/migrate-t5-batch.py").write_text(BATCH_OK, encoding="utf-8")
        (self.root / "scripts/zig_codec_bridge.py").write_text(BRIDGE_OK, encoding="utf-8")
        (self.root / "scripts/migrate-parallel.sh").write_text(
            "python3 scripts/migrate-t5-batch.py --out \"$OUT\" --report \"$R\" \"${chunk[@]}\"\n",
            encoding="utf-8")
        self.module = load_checker()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _mutate(self, rel: str, old: str, new: str) -> None:
        p = self.root / rel
        t = p.read_text(encoding="utf-8")
        assert old in t, (rel, old)
        p.write_text(t.replace(old, new, 1), encoding="utf-8")

    def test_real_shape_passes(self) -> None:
        self.assertEqual(self.module.check(self.root), [])

    def test_missing_bridge_import_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py", "import zig_codec_bridge", "# no bridge")
        self.assertTrue(self.module.check(self.root))

    def test_missing_verify_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py", "zig_codec_bridge.verify_t5(", "noop(")
        self.assertTrue(self.module.check(self.root))

    def test_write_without_zig_gate_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "if args.write and not args.zig_codec:", "if False:")
        self.assertTrue(self.module.check(self.root))

    def test_verify_after_staging_is_blocked(self) -> None:
        p = self.root / "scripts/migrate-t5-batch.py"
        t = p.read_text(encoding="utf-8")
        # move the verify call after the staging
        t = t.replace("            evidence = zig_codec_bridge.verify_t5(zig_binary, packed)\n", "")
        t = t.replace("            staged.append((rel, packed, row))",
                      "            staged.append((rel, packed, row))\n"
                      "            zig_codec_bridge.verify_t5(zig_binary, packed)")
        p.write_text(t, encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_missing_corridor_mint_is_blocked(self) -> None:
        # The corridor must MINT bytes (#5812), not only certify them.
        self._mutate("scripts/migrate-t5-batch.py",
                     "zig_codec_bridge.encode_t5(", "noop_encode(")
        self.assertTrue(self.module.check(self.root))

    def test_missing_parity_control_is_blocked(self) -> None:
        # Python must remain a fail-closed parity control, never the byte source.
        self._mutate("scripts/migrate-t5-batch.py",
                     "zig_codec_bridge.require_parity(", "noop_parity(")
        self.assertTrue(self.module.check(self.root))

    def test_python_codec_minting_publish_bytes_is_blocked(self) -> None:
        # A regression to the legacy path: the publish variable minted in Python.
        self._mutate("scripts/migrate-t5-batch.py",
                     "python_packed = mig.encode_projection(",
                     "packed = mig.encode_projection(")
        self.assertTrue(self.module.check(self.root))

    def test_runner_bypassing_driver_is_blocked(self) -> None:
        self._mutate("scripts/migrate-parallel.sh",
                     "scripts/migrate-t5-batch.py", "scripts/sens_t5_codec.py")
        self.assertTrue(self.module.check(self.root))

    def test_bridge_without_pin_is_blocked(self) -> None:
        self._mutate("scripts/zig_codec_bridge.py", '"0.16.0"', '"latest"')
        self.assertTrue(self.module.check(self.root))


if __name__ == "__main__":
    unittest.main()
