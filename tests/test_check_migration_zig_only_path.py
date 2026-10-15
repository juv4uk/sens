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
    if args.write and not args.zig_codec:
        raise ValueError("ZIG_CARRY_REQUIRED_FOR_PUBLICATION")
    zig_temp = tempfile.TemporaryDirectory() if args.zig_codec else None
    zig_binary = zig_codec_bridge.build_transport(Path(zig_temp.name)) if zig_temp else None
    for rel in paths:
        reference_bytes = mig.encode_projection(projection)
        if zig_binary is not None:
            packed = zig_codec_bridge.carry_t5(zig_binary, projection)
            evidence = zig_codec_bridge.verify_t5(zig_binary, packed)
            row["zig_transport"] = evidence
        else:
            packed = reference_bytes
        if args.write:
            staged.append((rel, destination, original, packed, row))
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

    def test_real_repository_migration_driver_has_live_zig_route(self) -> None:
        self.assertEqual(self.module.check(ROOT), [])

    def test_comment_only_zig_verify_is_not_a_release_receipt(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "evidence = zig_codec_bridge.verify_t5(zig_binary, packed)",
                     "evidence = packed  # zig_codec_bridge.verify_t5(zig_binary, packed)")
        self.assertTrue(any("M3:" in msg or "M5:" in msg
                            for msg in self.module.check(self.root)))

    def test_dead_if_false_zig_verifier_is_not_a_receipt(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if False:\n            packed")
        self.assertTrue(any("M3:" in msg or "M5:" in msg
                            for msg in self.module.check(self.root)))

    def test_nested_uninvoked_verifier_is_not_a_receipt(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "evidence = zig_codec_bridge.verify_t5(zig_binary, packed)",
                     "def never_called():\n"
                     "                return zig_codec_bridge.verify_t5(zig_binary, packed)\n"
                     "            evidence = {'unverified': True}")
        self.assertTrue(any("M3:" in msg or "M5:" in msg
                            for msg in self.module.check(self.root)))

    def test_nested_uninvoked_mint_cannot_satisfy_m8(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "packed = zig_codec_bridge.carry_t5(zig_binary, projection)",
                     "packed = reference_bytes\n"
                     "            def never_called():\n"
                     "                for _ in [0]:\n"
                     "                    packed = zig_codec_bridge.carry_t5(zig_binary, projection)\n"
                     "                    zig_codec_bridge.verify_t5(zig_binary, packed)\n"
                     "                    staged.append((rel, destination, original, packed, row))")
        self.assertTrue(any("M8:" in msg for msg in self.module.check(self.root)))

    def test_write_gate_comment_and_pass_do_not_protect_publication(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "if args.write and not args.zig_codec:\n        return 3",
                     "# if args.write and not args.zig_codec:\n    if True:\n        pass")
        self.assertTrue(any("M4:" in msg for msg in self.module.check(self.root)))

    def test_comment_only_build_does_not_prove_pinned_zig(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "zig_binary = zig_codec_bridge.build_transport(Path(zig_temp.name)) if zig_temp else None",
                     "zig_binary = None  # zig_codec_bridge.build_transport(Path(zig_temp.name))")
        self.assertTrue(any("M2:" in msg for msg in self.module.check(self.root)))

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
        t = t.replace("            staged.append((rel, destination, original, packed, row))",
                      "            staged.append((rel, destination, original, packed, row))\n"
                      "            zig_codec_bridge.verify_t5(zig_binary, packed)")
        p.write_text(t, encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_dry_run_only_zig_verifier_cannot_authorize_write(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if not args.write:\n            packed")
        self.assertTrue(any("M5:" in msg for msg in self.module.check(self.root)))

    def test_null_zig_verifier_cannot_authorize_write(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if zig_binary is None:\n            packed")
        self.assertTrue(any("M5:" in msg for msg in self.module.check(self.root)))

    def test_explicit_write_zig_verifier_is_accepted(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if args.write and args.zig_codec:\n            packed")
        self.assertEqual(self.module.check(self.root), [])

    def test_runner_bypassing_driver_is_blocked(self) -> None:
        self._mutate("scripts/migrate-parallel.sh",
                     "scripts/migrate-t5-batch.py", "scripts/sens_t5_codec.py")
        self.assertTrue(self.module.check(self.root))

    def test_bridge_without_pin_is_blocked(self) -> None:
        self._mutate("scripts/zig_codec_bridge.py", '"0.16.0"', '"latest"')
        self.assertTrue(self.module.check(self.root))



    def test_verify_reference_instead_of_published_zig_bytes_is_blocked(self) -> None:
        self._mutate(
            "scripts/migrate-t5-batch.py",
            "zig_codec_bridge.verify_t5(zig_binary, packed)",
            "zig_codec_bridge.verify_t5(zig_binary, reference_bytes)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M5:" in message and "verified-packed" in message
                            for message in failures), failures)

    def test_verify_different_binary_does_not_certify_published_bytes(self) -> None:
        self._mutate(
            "scripts/migrate-t5-batch.py",
            "zig_codec_bridge.verify_t5(zig_binary, packed)",
            "zig_codec_bridge.verify_t5(other_binary, packed)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M5:" in message for message in failures), failures)

    def test_carry_noncanonical_source_cannot_mint_staged_sens(self) -> None:
        self._mutate(
            "scripts/migrate-t5-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(zig_binary, reference_bytes)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M8:" in message for message in failures), failures)

    def test_pinned_carry_optional_digest_matches_real_migrator(self) -> None:
        self._mutate(
            "scripts/migrate-t5-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(zig_binary, projection, "
            "trusted_source_sha256=digest(reference_bytes))",
        )
        self.assertEqual(self.module.check(self.root), [])

    def test_unreviewed_carry_keyword_cannot_authorize_publication(self) -> None:
        self._mutate(
            "scripts/migrate-t5-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(zig_binary, projection, source=reference_bytes)",
        )
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_carry_unpinned_binary_cannot_mint_staged_sens(self) -> None:
        self._mutate(
            "scripts/migrate-t5-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(other_binary, projection)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M8:" in message for message in failures), failures)

    def test_python_reference_cannot_mint_published_bytes(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "packed = zig_codec_bridge.carry_t5(zig_binary, projection)",
                     "packed = mig.encode_projection(projection)")
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_commented_out_carry_is_not_evidence(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "packed = zig_codec_bridge.carry_t5(zig_binary, projection)",
                     "packed = reference_bytes  # zig_codec_bridge.carry_t5(zig_binary, projection)")
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_staging_reference_bytes_is_not_zig_publication(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "staged.append((rel, destination, original, packed, row))",
                     "staged.append((rel, destination, original, reference_bytes, row))")
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_overwriting_zig_carrier_before_staging_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     'row["zig_transport"] = evidence',
                     'row["zig_transport"] = evidence\\n            packed = reference_bytes'.replace("\\n", "\n"))
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_augmented_assignment_corrupting_zig_bytes_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     'row["zig_transport"] = evidence',
                     'row["zig_transport"] = evidence\\n            packed += reference_bytes'.replace("\\n", "\n"))
        self.assertTrue(any("M8:" in msg for msg in self.module.check(self.root)))

    def test_indexed_write_to_zig_bytes_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     'row["zig_transport"] = evidence',
                     'row["zig_transport"] = evidence\\n            packed[0] = 0'.replace("\\n", "\n"))
        self.assertTrue(any("M8:" in msg for msg in self.module.check(self.root)))

    def test_walrus_rebinding_zig_bytes_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     'row["zig_transport"] = evidence',
                     'row["zig_transport"] = (packed := reference_bytes)')
        self.assertTrue(any("M8:" in msg for msg in self.module.check(self.root)))

    def test_carry_only_on_dry_run_is_not_release_evidence(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "if zig_binary is not None:\\n            packed".replace("\\n", "\n"),
                     "if not args.write:\\n            packed".replace("\\n", "\n"))
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_carry_after_staging_is_not_release_evidence(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     "packed = zig_codec_bridge.carry_t5(zig_binary, projection)",
                     "packed = reference_bytes")
        self._mutate("scripts/migrate-t5-batch.py",
                     "staged.append((rel, destination, original, packed, row))",
                     ("staged.append((rel, destination, original, packed, row))"
                      + chr(10)
                      + "            packed = zig_codec_bridge.carry_t5(zig_binary, projection)"))
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_direct_run_without_zig_guard_is_rejected(self) -> None:
        self._mutate("scripts/migrate-t5-batch.py",
                     'if args.write and not args.zig_codec:\\n        raise ValueError("ZIG_CARRY_REQUIRED_FOR_PUBLICATION")'.replace("\\n", "\n"),
                     'if False:\\n        raise ValueError("ZIG_CARRY_REQUIRED_FOR_PUBLICATION")'.replace("\\n", "\n"))
        self.assertTrue(any("M9:" in message for message in self.module.check(self.root)))

if __name__ == "__main__":
    unittest.main()
