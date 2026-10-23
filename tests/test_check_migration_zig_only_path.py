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
def carry_t5(binary, canonical_view, *, codec: str = "t5m", trusted_source_sha256=None):
    pass
def verify_t5(binary, physical, *, codec: str = "t5m", trusted_source_sha256=None):
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
        (self.root / "scripts/migrate-t5m-batch.py").write_text(BATCH_OK, encoding="utf-8")
        (self.root / "scripts/zig_codec_bridge.py").write_text(BRIDGE_OK, encoding="utf-8")
        (self.root / "scripts/migrate-parallel.sh").write_text(
            "python3 scripts/migrate-t5m-batch.py --out \"$OUT\" --report \"$R\" \"${chunk[@]}\"\n",
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
        self._mutate("scripts/migrate-t5m-batch.py",
                     "evidence = zig_codec_bridge.verify_t5(zig_binary, packed)",
                     "evidence = packed  # zig_codec_bridge.verify_t5(zig_binary, packed)")
        self.assertTrue(any("M3:" in msg or "M5:" in msg
                            for msg in self.module.check(self.root)))

    def test_dead_if_false_zig_verifier_is_not_a_receipt(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if False:\n            packed")
        self.assertTrue(any("M3:" in msg or "M5:" in msg
                            for msg in self.module.check(self.root)))

    def test_write_gate_comment_and_pass_do_not_protect_publication(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "if args.write and not args.zig_codec:\n        return 3",
                     "# if args.write and not args.zig_codec:\n    if True:\n        pass")
        self.assertTrue(any("M4:" in msg for msg in self.module.check(self.root)))

    def test_comment_only_build_does_not_prove_pinned_zig(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "zig_binary = zig_codec_bridge.build_transport(Path(zig_temp.name)) if zig_temp else None",
                     "zig_binary = None  # zig_codec_bridge.build_transport(Path(zig_temp.name))")
        self.assertTrue(any("M2:" in msg for msg in self.module.check(self.root)))

    def test_missing_bridge_import_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py", "import zig_codec_bridge", "# no bridge")
        self.assertTrue(self.module.check(self.root))

    def test_missing_verify_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py", "zig_codec_bridge.verify_t5(", "noop(")
        self.assertTrue(self.module.check(self.root))

    def test_write_without_zig_gate_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "if args.write and not args.zig_codec:", "if False:")
        self.assertTrue(self.module.check(self.root))

    def test_verify_after_staging_is_blocked(self) -> None:
        p = self.root / "scripts/migrate-t5m-batch.py"
        t = p.read_text(encoding="utf-8")
        # move the verify call after the staging
        t = t.replace("            evidence = zig_codec_bridge.verify_t5(zig_binary, packed)\n", "")
        t = t.replace("            staged.append((rel, destination, original, packed, row))",
                      "            staged.append((rel, destination, original, packed, row))\n"
                      "            zig_codec_bridge.verify_t5(zig_binary, packed)")
        p.write_text(t, encoding="utf-8")
        self.assertTrue(self.module.check(self.root))

    def test_dry_run_only_zig_verifier_cannot_authorize_write(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if not args.write:\n            packed")
        self.assertTrue(any("M5:" in msg for msg in self.module.check(self.root)))

    def test_null_zig_verifier_cannot_authorize_write(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if zig_binary is None:\n            packed")
        self.assertTrue(any("M5:" in msg for msg in self.module.check(self.root)))

    def test_explicit_write_zig_verifier_is_accepted(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "if zig_binary is not None:\n            packed",
                     "if args.write and args.zig_codec:\n            packed")
        self.assertEqual(self.module.check(self.root), [])

    def test_runner_bypassing_driver_is_blocked(self) -> None:
        self._mutate("scripts/migrate-parallel.sh",
                     "scripts/migrate-t5m-batch.py", "scripts/sens_t5_t5m_codec.py")
        self.assertTrue(self.module.check(self.root))

    def test_bridge_without_pin_is_blocked(self) -> None:
        self._mutate("scripts/zig_codec_bridge.py", '"0.16.0"', '"latest"')
        self.assertTrue(self.module.check(self.root))



    def test_verify_reference_instead_of_published_zig_bytes_is_blocked(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.verify_t5(zig_binary, packed)",
            "zig_codec_bridge.verify_t5(zig_binary, reference_bytes)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M5:" in message and "verified-packed" in message
                            for message in failures), failures)

    def test_verify_different_binary_does_not_certify_published_bytes(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.verify_t5(zig_binary, packed)",
            "zig_codec_bridge.verify_t5(other_binary, packed)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M5:" in message for message in failures), failures)

    def test_explicit_legacy_t5_carry_is_not_current_migration_evidence(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            'zig_codec_bridge.carry_t5(zig_binary, projection, codec="t5")',
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M8:" in message for message in failures), failures)

    def test_explicit_legacy_t5_verification_is_not_current_migration_evidence(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.verify_t5(zig_binary, packed)",
            'zig_codec_bridge.verify_t5(zig_binary, packed, codec="t5")',
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M5:" in message for message in failures), failures)

    def test_carry_noncanonical_source_cannot_mint_staged_sens(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(zig_binary, reference_bytes)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M8:" in message for message in failures), failures)

    def test_pinned_carry_optional_digest_matches_real_migrator(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(zig_binary, projection, "
            "trusted_source_sha256=digest(reference_bytes))",
        )
        self.assertEqual(self.module.check(self.root), [])

    def test_unreviewed_carry_keyword_cannot_authorize_publication(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(zig_binary, projection, source=reference_bytes)",
        )
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_carry_unpinned_binary_cannot_mint_staged_sens(self) -> None:
        self._mutate(
            "scripts/migrate-t5m-batch.py",
            "zig_codec_bridge.carry_t5(zig_binary, projection)",
            "zig_codec_bridge.carry_t5(other_binary, projection)",
        )
        failures = self.module.check(self.root)
        self.assertTrue(any("M8:" in message for message in failures), failures)

    def test_python_reference_cannot_mint_published_bytes(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "packed = zig_codec_bridge.carry_t5(zig_binary, projection)",
                     "packed = mig.encode_projection(projection)")
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_commented_out_carry_is_not_evidence(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "packed = zig_codec_bridge.carry_t5(zig_binary, projection)",
                     "packed = reference_bytes  # zig_codec_bridge.carry_t5(zig_binary, projection)")
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_staging_reference_bytes_is_not_zig_publication(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "staged.append((rel, destination, original, packed, row))",
                     "staged.append((rel, destination, original, reference_bytes, row))")
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_overwriting_zig_carrier_before_staging_is_blocked(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     'row["zig_transport"] = evidence',
                     'row["zig_transport"] = evidence\\n            packed = reference_bytes'.replace("\\n", "\n"))
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_carry_only_on_dry_run_is_not_release_evidence(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "if zig_binary is not None:\\n            packed".replace("\\n", "\n"),
                     "if not args.write:\\n            packed".replace("\\n", "\n"))
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_carry_after_staging_is_not_release_evidence(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     "packed = zig_codec_bridge.carry_t5(zig_binary, projection)",
                     "packed = reference_bytes")
        self._mutate("scripts/migrate-t5m-batch.py",
                     "staged.append((rel, destination, original, packed, row))",
                     ("staged.append((rel, destination, original, packed, row))"
                      + chr(10)
                      + "            packed = zig_codec_bridge.carry_t5(zig_binary, projection)"))
        self.assertTrue(any("M8:" in message for message in self.module.check(self.root)))

    def test_direct_run_without_zig_guard_is_rejected(self) -> None:
        self._mutate("scripts/migrate-t5m-batch.py",
                     'if args.write and not args.zig_codec:\\n        raise ValueError("ZIG_CARRY_REQUIRED_FOR_PUBLICATION")'.replace("\\n", "\n"),
                     'if False:\\n        raise ValueError("ZIG_CARRY_REQUIRED_FOR_PUBLICATION")'.replace("\\n", "\n"))
        self.assertTrue(any("M9:" in message for message in self.module.check(self.root)))


class StandaloneThreePassZigMintWitness(unittest.TestCase):
    """One focused CI witness: exact Zig carry + forged/mutant rejection."""

    def test_zig_mints_not_python_and_rejects_mutant_or_fake_receipt(self):
        from types import SimpleNamespace
        from unittest.mock import Mock

        script = ROOT / "scripts/migrate-three-pass.py"
        spec = importlib.util.spec_from_file_location("three_pass_zig_mint_witness", script)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migrator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = migrator
        spec.loader.exec_module(migrator)
        projection = "000\n"
        reference = migrator.encode_projection(projection)
        expected = migrator.hashlib.sha256(reference).hexdigest()
        binary = ROOT / "not-a-real-executable"  # mock only, NEVER a release receipt
        receipt = {
            "physical_sha256": expected,
            "source_pin_status": "MATCHED_CALLER_SUPPLIED_SHA256",
            "zig_binary_sha256": "static-test-mock-not-real-proof",
        }
        bridge = SimpleNamespace(
            carry_t5=Mock(return_value=reference),
            verify_t5=Mock(return_value=receipt),
        )
        physical, actual_receipt = migrator.zig_mint_verified_t5(
            projection, reference, binary, bridge,
        )
        self.assertEqual(physical, reference)
        self.assertEqual(actual_receipt, receipt)
        bridge.carry_t5.assert_called_once_with(
            binary, projection, codec="t5m", trusted_source_sha256=expected,
        )
        bridge.verify_t5.assert_called_once_with(
            binary, reference, codec="t5m", trusted_source_sha256=expected,
        )

        # The physical carrier must NEVER be replaced by the Python reference.
        bridge.carry_t5.return_value = bytes([reference[0] ^ 1]) + reference[1:]
        bridge.verify_t5.reset_mock()
        with self.assertRaisesRegex(
            migrator.SensT5Error, "ZIG_CARRY_REFERENCE_MISMATCH.*first_byte=0",
        ):
            migrator.zig_mint_verified_t5(projection, reference, binary, bridge)
        bridge.verify_t5.assert_not_called()

        # Matching bytes but an unauthenticated receipt are not enough.
        bridge.carry_t5.return_value = reference
        bridge.verify_t5.return_value = {
            **receipt, "source_pin_status": "NOT_SUPPLIED",
        }
        with self.assertRaisesRegex(
            migrator.SensT5Error, "ZIG_CARRY_UNATTESTED_RECEIPT",
        ):
            migrator.zig_mint_verified_t5(projection, reference, binary, bridge)

    def test_unrelated_review_manifest_drift_does_not_block_executable_lisp(self):
        # Перевіряємо механізм міграції, не симулюємо семантику SENS.
        spec = importlib.util.spec_from_file_location(
            "three_pass_scoped_nonprogram", ROOT / "scripts/migrate-three-pass.py"
        )
        assert spec is not None and spec.loader is not None
        migrator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = migrator
        spec.loader.exec_module(migrator)

        with tempfile.TemporaryDirectory() as temp:
            sandbox = Path(temp)
            (sandbox / "lib/domains").mkdir(parents=True)
            # Жодного маніфесту в sandbox: програма не має залежати від
            # перевірки чужих маніфестів даних, їхнього SHA чи дати.
            live = sandbox / "lib/програма.lisp"
            live.write_text("(визначити відповідь (як-є так))\n", encoding="utf-8")
            self.assertIsNone(
                migrator.reject_reviewed_nonprogram_source(live, sandbox)
            )

            # А от файл із визнаного не-виконуваного набору не може
            # обходити відсутню маніфестну авторизацію.
            domain = sandbox / "lib/domains/d4.lisp"
            domain.write_text("(непрограма)\n", encoding="utf-8")
            with self.assertRaisesRegex(
                migrator.SensT5Error, "NONPROGRAM_MANIFEST_UNAVAILABLE"
            ):
                migrator.reject_reviewed_nonprogram_source(domain, sandbox)

    def test_reviewed_nonprogram_never_mints_and_source_drift_is_not_ignored(self):
        """One positive / negative / mutated-source witness for issue #4460."""
        import json
        import subprocess

        spec = importlib.util.spec_from_file_location(
            "three_pass_nonprogram_witness", ROOT / "scripts/migrate-three-pass.py"
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        migrator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = migrator
        spec.loader.exec_module(migrator)

        # Positive: ordinary source outside the ratified NONPROGRAM cohort.
        self.assertIsNone(
            migrator.reject_reviewed_nonprogram_source(ROOT / "lib/forward.lisp")
        )
        for name in ("d1", "d4", "d5", "d6"):
            with self.subTest(domain=name), self.assertRaisesRegex(
                migrator.SensT5Error, "NONPROGRAM_DATA_NOT_EXECUTABLE"
            ):
                migrator.reject_reviewed_nonprogram_source(
                    ROOT / f"lib/domains/{name}.lisp"
                )

        with tempfile.TemporaryDirectory() as temp:
            sandbox = Path(temp)
            (sandbox / "lib/domains").mkdir(parents=True)
            (sandbox / "knowledge").mkdir()
            source = sandbox / "lib/domains/d4.lisp"
            original = (ROOT / "lib/domains/d4.lisp").read_bytes()
            source.write_bytes(original)
            for _, manifest, _ in migrator.NONPROGRAM_MANIFESTS:
                destination = sandbox / manifest
                destination.write_bytes((ROOT / manifest).read_bytes())

            with self.assertRaisesRegex(
                migrator.SensT5Error, "NONPROGRAM_DATA_NOT_EXECUTABLE"
            ):
                migrator.reject_reviewed_nonprogram_source(source, sandbox)

            # The manifest is a SHA-pinned fact, not an everlasting path veto.
            source.write_bytes(original + b"; mutated review input\n")
            with self.assertRaisesRegex(
                migrator.SensT5Error, "NONPROGRAM_SOURCE_SHA_DRIFT"
            ):
                migrator.reject_reviewed_nonprogram_source(source, sandbox)
            source.write_bytes(original)

            manifest = sandbox / migrator.NONPROGRAM_MANIFESTS[0][1]
            record = json.loads(manifest.read_text(encoding="utf-8"))
            record["automatic_sens_companion"] = True
            manifest.write_text(json.dumps(record), encoding="utf-8")
            with self.assertRaisesRegex(
                migrator.SensT5Error, "NONPROGRAM_MANIFEST_SHA_DRIFT"
            ):
                migrator.reject_reviewed_nonprogram_source(source, sandbox)

        # Integration: dry-run must be blocked before minting, not just by
        # the standalone helper. No Zig binary required for dry-run.
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate-three-pass.py"),
                 str(ROOT / "lib/domains/d4.lisp"), "--out", str(dest),
                 "--dry-run", "--report", str(dest / "report.json")],
                capture_output=True, text=True, timeout=30, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads((dest / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["files_blocked"], 0)
            self.assertEqual(report["summary"]["files_not_program"], 1)
            self.assertEqual(report["files"][0]["status"], "not-program")
            self.assertEqual(report["summary"]["files_would_write"], 0)
            self.assertIn("NONPROGRAM_DATA_NOT_EXECUTABLE", report["files"][0]["reason"])
            self.assertFalse((dest / "d4.sens").exists())
            self.assertFalse((dest / "d4").exists())

            # The parallel/batch producer must not evade the same barrier.
            bulk = subprocess.run(
                [sys.executable, str(ROOT / "scripts/migrate-t5m-batch.py"),
                 "lib/domains/d4.lisp", "--root", str(ROOT),
                 "--out", str(dest / "bulk-out"),
                 "--report", str(dest / "bulk-report.json")],
                capture_output=True, text=True, timeout=30, check=False,
            )
            self.assertEqual(bulk.returncode, 2, bulk.stdout + bulk.stderr)
            bulk_report = json.loads(
                (dest / "bulk-report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(bulk_report["summary"]["files_blocked"], 1)
            self.assertEqual(bulk_report["summary"]["files_would_write"], 0)
            self.assertIn(
                "NONPROGRAM_DATA_NOT_EXECUTABLE",
                bulk_report["files"][0]["reason"],
            )
            self.assertFalse((dest / "bulk-out/lib/domains/d4.sens").exists())


if __name__ == "__main__":
    unittest.main()
