"""Fail-closed release preflight trigger regression for the single-CI policy.

Only .github/workflows/ci.yml starts automatically on push/pull_request.
Release Preflight is a *manual* full-workspace gate before exact-SHA GO.
This test checks that neither release docs nor the preflight workflow
silently introduce a second automatic GitHub Actions run.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "release-preflight.yml"
REQUIRED_COMMANDS = (
    "cargo test --locked --workspace",
    "cargo clippy --locked --workspace --all-targets -- -D warnings",
)
ALLOWED_EVENTS = frozenset(("workflow_dispatch", "workflow_call"))


def require_manual_preflight(source: str) -> None:
    """Fail unless preflight is opt-in and contains both full release gates."""
    header = re.search(r"(?m)^on:[ \t]*$", source)
    if header is None:
        raise AssertionError("RELEASE_BLOCKED: preflight has no explicit on: mapping")

    # Extract only the top-level on: section; job names and shell snippets
    # must never be mistaken for workflow event triggers.
    event_lines = []
    for line in source[header.end():].splitlines():
        if line and not line[0].isspace() and not line.startswith("#"):
            break
        event_lines.append(line)
    events = []
    for line in event_lines:
        event = re.match(r"^  ([a-z][a-z0-9_-]*):(?:[ \t]|$)", line)
        if event:
            events.append(event.group(1))

    if "workflow_dispatch" not in events:
        raise AssertionError("RELEASE_BLOCKED: explicit manual preflight unavailable")
    unexpected = set(events) - ALLOWED_EVENTS
    if unexpected:
        raise AssertionError(
            "RELEASE_BLOCKED: additional automatic preflight trigger(s): "
            + ", ".join(sorted(unexpected))
        )
    if len(events) != len(set(events)):
        raise AssertionError("RELEASE_BLOCKED: duplicate preflight event")

    for command in REQUIRED_COMMANDS:
        if command not in source:
            raise AssertionError("RELEASE_BLOCKED: missing preflight gate " + command)

    # A release preflight must really run the pinned Zig 0.16 physical
    # migration bridge. --self-test explicitly skips transport and exits 0,
    # so it can never substitute for the mandatory pre-tag physical proof.
    physical_command = "python3 scripts/migration-zig-gate.py --require-zig"
    if re.search(r"(?m)^          " + re.escape(physical_command) + r"[ \t]*$", source) is None:
        raise AssertionError("RELEASE_BLOCKED: missing full Zig physical migration gate")


class ReleasePreflightScopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_current_manual_preflight_keeps_full_release_gates(self):
        require_manual_preflight(self.workflow)

    def test_negative_guard_rejects_new_automatic_push_and_pr(self):
        for trigger in ("push", "pull_request", "schedule"):
            with self.subTest(trigger=trigger):
                broken = self.workflow.replace(
                    "  workflow_dispatch:\n",
                    f"  {trigger}:\n  workflow_dispatch:\n",
                    1,
                )
                self.assertNotEqual(broken, self.workflow)
                with self.assertRaisesRegex(
                    AssertionError, "additional automatic preflight trigger"
                ):
                    require_manual_preflight(broken)

    def test_negative_guard_rejects_missing_manual_event(self):
        broken = self.workflow.replace("  workflow_dispatch:\n", "", 1)
        self.assertNotEqual(broken, self.workflow)
        with self.assertRaisesRegex(AssertionError, "manual preflight unavailable"):
            require_manual_preflight(broken)

    def test_negative_guard_rejects_missing_full_workspace_test_or_clippy(self):
        for command in REQUIRED_COMMANDS:
            with self.subTest(command=command):
                broken = self.workflow.replace(command, "echo skipped-release-gate", 1)
                self.assertNotEqual(broken, self.workflow)
                with self.assertRaisesRegex(AssertionError, "missing preflight gate"):
                    require_manual_preflight(broken)

    def test_negative_guard_rejects_selftest_only_zig_migration(self):
        current = "python3 scripts/migration-zig-gate.py --require-zig"
        self.assertIn(current, self.workflow)
        for replacement in (
            "python3 scripts/migration-zig-gate.py --self-test",
            "# " + current,
            "echo " + current,
            current + " --self-test",
        ):
            with self.subTest(replacement=replacement):
                broken = self.workflow.replace(current, replacement, 1)
                self.assertNotEqual(broken, self.workflow)
                with self.assertRaisesRegex(
                    AssertionError, "missing full Zig physical migration gate"
                ):
                    require_manual_preflight(broken)

    def test_negative_guard_rejects_floating_event_mapping(self):
        broken = self.workflow.replace(
            "on:\n  workflow_dispatch:\n", "on: [push, pull_request]\n", 1
        )
        self.assertNotEqual(broken, self.workflow)
        with self.assertRaisesRegex(AssertionError, "explicit on: mapping"):
            require_manual_preflight(broken)


if __name__ == "__main__":
    unittest.main()
