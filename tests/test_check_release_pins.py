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
                Path(tmp), CHANNEL, {w: GOOD_STEP for w in MODULE.RELEASE_WORKFLOWS}
            )
            channel, errors = MODULE.check(root)
            self.assertEqual(channel, "1.99.0")
            self.assertEqual(errors, [])

    def test_drifted_toolchain_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: dtolnay/rust-toolchain@1.98.0\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in MODULE.RELEASE_WORKFLOWS}
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
                Path(tmp), CHANNEL, {w: step for w in MODULE.RELEASE_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("with: toolchain" in e for e in errors), errors)

    def test_floating_action_tag_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: actions/checkout@v5\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in MODULE.RELEASE_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("not pinned to a 40-hex SHA" in e for e in errors), errors)

    def test_floating_action_tag_with_comment_blocks(self):
        # A trailing `# tag` comment must not let a floating ref slip through.
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: actions/checkout@v5 # v5\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in MODULE.RELEASE_WORKFLOWS}
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
                {w: GOOD_STEP for w in MODULE.RELEASE_WORKFLOWS},
            )
            with self.assertRaises(ValueError):
                MODULE.check(root)

    def test_uses_without_ref_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            step = "      - uses: actions/checkout\n"
            root = materialize(
                Path(tmp), CHANNEL, {w: step for w in MODULE.RELEASE_WORKFLOWS}
            )
            _, errors = MODULE.check(root)
            self.assertTrue(any("uses without a ref" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
