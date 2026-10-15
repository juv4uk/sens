#!/usr/bin/env python3
"""Negative witnesses for the release-path reproducibility guard.

Each test proves the guard fails closed: a drifted toolchain, a floating action
tag, a missing release workflow, or an absent pinned channel must never pass.
"""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-release-pins.py"
SPEC = importlib.util.spec_from_file_location("sens_check_release_pins", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

ALL_WORKFLOWS = MODULE.RELEASE_WORKFLOWS + MODULE.RELEASE_GATING_WORKFLOWS

CHANNEL = '[toolchain]\nchannel = "1.99.0"\nprofile = "minimal"\n'
CHECKOUT_SHA = "fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09"
GOOD_STEP = (
    f"      - uses: actions/checkout@{CHECKOUT_SHA} # v5\n"
    "      - uses: dtolnay/rust-toolchain@1.99.0\n"
    "        with:\n"
    '          toolchain: "1.99.0"\n'
)


def materialize(root: Path, toolchain: str, workflows: dict[str, str]) -> Path:
    (root / "rust-toolchain.toml").write_text(toolchain, encoding="utf-8")
    for rel, body in workflows.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return root


class ReleasePinsTests(unittest.TestCase):
    def test_pinned_release_path_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(
                Path(tmp), CHANNEL, {w: GOOD_STEP for w in ALL_WORKFLOWS}
            )
            channel, errors = MODULE.check(root)
            self.assertEqual(channel, "1.99.0")
            self.assertEqual(errors, [])

    def test_drifted_toolchain_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: dtolnay/rust-toolchain@1.98.0\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in ALL_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("!= pinned channel" in e for e in errors), errors)

    def test_with_toolchain_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = (
                "      - uses: dtolnay/rust-toolchain@1.99.0\n"
                "        with:\n"
                '          toolchain: "1.98.0"\n'
            )
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in ALL_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("with: toolchain" in e for e in errors), errors)

    def test_floating_action_tag_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: actions/checkout@v5\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in ALL_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("not pinned to a 40-hex SHA" in e for e in errors), errors)

    def test_floating_action_tag_with_comment_blocks(self):
        # A trailing `# tag` comment must not let a floating ref slip through.
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: actions/checkout@v5 # v5\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in ALL_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("not pinned to a 40-hex SHA" in e for e in errors), errors)

    def test_missing_release_workflow_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(
                Path(tmp), CHANNEL, {MODULE.RELEASE_WORKFLOWS[0]: GOOD_STEP}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("is missing" in e for e in errors), errors)

    def test_missing_pinned_channel_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(
                Path(tmp),
                '[toolchain]\nprofile = "minimal"\n',
                {w: GOOD_STEP for w in ALL_WORKFLOWS},
            )
            with self.assertRaises(ValueError):
                MODULE.check(root)

    def test_uses_without_ref_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: actions/checkout\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in ALL_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("uses without a ref" in e for e in errors), errors)


    def test_central_zig_ci_is_a_release_gating_workflow(self):
        # Exact-SHA release CI admission relies on this central Zig/SENS job.
        self.assertIn(".github/workflows/ci.yml", MODULE.RELEASE_GATING_WORKFLOWS)

    def test_central_zig_ci_floating_upload_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(
                Path(tmp), CHANNEL, {w: GOOD_STEP for w in ALL_WORKFLOWS}
            )
            central = root / ".github/workflows/ci.yml"
            central.write_text(
                GOOD_STEP + "      - name: Save Zig source measurements\n"
                "        uses: actions/upload-artifact@v4\n",
                encoding="utf-8",
            )
            _, errors = MODULE.check(root)
            self.assertTrue(
                any(".github/workflows/ci.yml" in error and
                    "not pinned to a 40-hex SHA" in error for error in errors),
                errors,
            )

    def test_central_zig_ci_exact_v4_6_2_action_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(
                Path(tmp), CHANNEL, {w: GOOD_STEP for w in ALL_WORKFLOWS}
            )
            central = root / ".github/workflows/ci.yml"
            central.write_text(
                GOOD_STEP + "      - name: Save Zig source measurements\n"
                "        uses: actions/upload-artifact@"
                "ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2\n",
                encoding="utf-8",
            )
            _, errors = MODULE.check(root)
            self.assertEqual(errors, [])

    def test_central_zig_ci_rust_toolchain_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(
                Path(tmp), CHANNEL, {w: GOOD_STEP for w in ALL_WORKFLOWS}
            )
            central = root / ".github/workflows/ci.yml"
            central.write_text(
                "      - uses: dtolnay/rust-toolchain@1.98.0\n",
                encoding="utf-8",
            )
            _, errors = MODULE.check(root)
            self.assertTrue(
                any(".github/workflows/ci.yml" in error and
                    "!= pinned channel 1.99.0" in error for error in errors),
                errors,
            )

    def test_real_release_wasm_pack_action_is_immutable(self):
        workflow = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "uses: jetli/wasm-pack-action@"
            "0d096b08b4e5a7de8c28de67e11e945404e9eefa", workflow
        )
        self.assertNotIn("uses: jetli/wasm-pack-action@0.4.0", workflow)

    def test_release_wasm_pack_tag_mutation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = materialize(
                Path(tmp), CHANNEL, {w: GOOD_STEP for w in ALL_WORKFLOWS}
            )
            release = root / ".github/workflows/release.yml"
            release.write_text(
                GOOD_STEP + "      - uses: jetli/wasm-pack-action@0.4.0\n",
                encoding="utf-8",
            )
            _, errors = MODULE.check(root)
            self.assertTrue(
                any(".github/workflows/release.yml" in error and
                    "not pinned to a 40-hex SHA" in error for error in errors),
                errors,
            )

    def test_real_central_zig_ci_actions_are_sha_pinned(self):
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(
            encoding="utf-8"
        )
        action = (
            "uses: actions/upload-artifact@"
            "ea165f8d65b6e75b540449e92b4886f43607fa02"
        )
        self.assertEqual(workflow.count(action), 2)
        self.assertNotIn("uses: actions/upload-artifact@v4", workflow)


if __name__ == "__main__":
    unittest.main()
