#!/usr/bin/env python3
"""Focused fail-closed pin witnesses for the host-neutral Zig migration gate."""
from contextlib import redirect_stderr
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "migration-zig-gate.py"
SPEC = importlib.util.spec_from_file_location("migration_zig_gate_pin", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class ZigPinFailClosed(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".zig-version").write_text("0.16.0\n", encoding="ascii")
        self.action = self.root / ".github" / "actions" / "install-zig" / "action.yml"
        self.action.parent.mkdir(parents=True)
        self.override = mock.patch.object(gate, "ROOT", self.root)
        self.override.start()
        self.addCleanup(self.override.stop)

    def write_action(self, version="0.16.0"):
        self.action.write_text(
            "name: install-zig\ninputs:\n  version:\n"
            "    required: false\n"
            f'    default: "{version}"\n'
            "runs:\n  using: composite\n",
            encoding="utf-8",
        )

    def test_valid_version_in_version_input_passes(self):
        self.write_action()
        receipt = gate.check_zig_pin()
        self.assertEqual((receipt["status"], receipt["exit"]), ("PASS", 0))

    def test_missing_action_fails_instead_of_claiming_pass(self):
        receipt = gate.check_zig_pin()
        self.assertEqual((receipt["status"], receipt["exit"]), ("FAIL", 1))
        self.assertIn("missing regular install-zig", receipt["detail"])

    def test_symlinked_action_fails_without_following_target(self):
        actual = self.root / "not-authorized-action.yml"
        actual.write_text(
            'inputs:\n  version:\n    default: "0.16.0"\n',
            encoding="utf-8",
        )
        self.action.symlink_to(actual)
        self.assertEqual(gate.check_zig_pin()["status"], "FAIL")

    def test_other_input_or_comment_cannot_spoof_version_default(self):
        self.write_action("0.17.0")
        body = self.action.read_text(encoding="utf-8")
        body += (
            '# default: "0.16.0"\n'
            '  note:\n    default: "0.16.0"\n'
        )
        self.action.write_text(body, encoding="utf-8")
        receipt = gate.check_zig_pin()
        self.assertEqual(receipt["status"], "FAIL")
        self.assertIn("inputs.version.default drift", receipt["detail"])

    def test_self_test_cannot_bypass_explicit_require_zig(self):
        with mock.patch("sys.argv", [str(SCRIPT), "--self-test", "--require-zig"]):
            with mock.patch.object(gate, "run_step", side_effect=AssertionError("must not run")):
                with redirect_stderr(io.StringIO()) as stderr:
                    with self.assertRaises(SystemExit) as caught:
                        gate.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("cannot satisfy --require-zig", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
