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
# These commands are meaningful only when the actual named YAML step
# executes them. Comments, echoes, disabled snippets and wrong steps cannot
# certify a complete release after the Zig transport gate.
REQUIRED_WORKSPACE_STEPS = (
    ("Full workspace tests (pre-tag, exact SHA)", "cargo test --locked --workspace"),
    ("Full workspace Clippy (pre-tag, exact SHA)",
     "cargo clippy --locked --workspace --all-targets -- -D warnings"),
)
REQUIRED_COMMANDS = tuple(command for _, command in REQUIRED_WORKSPACE_STEPS)
ALLOWED_EVENTS = frozenset(("workflow_dispatch", "workflow_call"))
ZIG_RELEASE_SAFE_COMMAND = "zig test research/zig-codecs/tests.zig -O ReleaseSafe -lc"


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

    # Require an executable step, not a textual token elsewhere in YAML.
    # These are intentionally single-line, unquoted run: commands: no shell
    # wrappers, error suppression, substitutions or release evidence by echo.
    for step_name, command in REQUIRED_WORKSPACE_STEPS:
        live = re.search(
            r"(?m)^      - name: " + re.escape(step_name)
            + r"[ \\t]*\\n        run: " + re.escape(command) + r"[ \\t]*$",
            source,
        )
        if live is None:
            raise AssertionError("RELEASE_BLOCKED: missing live preflight gate " + command)

    # A release preflight must really run the pinned Zig 0.16 physical
    # migration bridge. --self-test explicitly skips transport and exits 0,
    # so it can never substitute for the mandatory pre-tag physical proof.
    physical_command = "python3 scripts/migration-zig-gate.py --require-zig"
    physical_match = re.search(
        r"(?m)^          " + re.escape(physical_command) + r"[ \t]*$", source
    )
    if physical_match is None:
        raise AssertionError("RELEASE_BLOCKED: missing full Zig physical migration gate")

    # The native transport suite must run on the same checked-out release
    # candidate, in Zig 0.16 ReleaseSafe (optimized WITH runtime safety).
    # Require a live bare shell command, not a comment/echo/ignored failure,
    # and run it AFTER the full physical migration gate.
    step = re.search(
        r"(?m)^      - name: Sterile Zig corridor .*?\n"
        r"        run: \|\n(?P<body>(?:          .*\n)*)", source
    )
    if step is None:
        raise AssertionError("RELEASE_BLOCKED: missing executable Zig corridor step")
    body = step.group("body")
    native_match = re.search(
        r"(?m)^          " + re.escape(ZIG_RELEASE_SAFE_COMMAND)
        + r"[ \t]*$", body,
    )
    if (native_match is None or
            "          set -euo pipefail\n" not in body or
            body.find(physical_command) < 0 or
            native_match.start() <= body.find(physical_command)):
        raise AssertionError("RELEASE_BLOCKED: missing live Zig ReleaseSafe physical suite")


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

    def test_negative_guard_rejects_spoofed_or_suppressed_workspace_go(self):
        # Source-token presence alone is not evidence of a real cargo run.
        for step_name, command in REQUIRED_WORKSPACE_STEPS:
            with self.subTest(step=step_name):
                live = "        run: " + command + "\n"
                self.assertIn(live, self.workflow)
                for forged in (
                    "        run: echo " + command + "\n",
                    "        run: " + command + " || true\n",
                    "        run: " + command + " # ignored\n",
                    "        # run: " + command + "\n",
                    "        run: true # " + command + "\n",
                    "        run: true\n        # " + command + "\n",
                ):
                    with self.subTest(forged=forged):
                        broken = self.workflow.replace(live, forged, 1)
                        self.assertNotEqual(broken, self.workflow)
                        with self.assertRaisesRegex(
                            AssertionError, "missing live preflight gate"
                        ):
                            require_manual_preflight(broken)
                # The exact live command in an unrelated step is not
                # evidence for the named full-workspace GO gate.
                moved = self.workflow.replace(
                    "      - name: " + step_name + "\n",
                    "      - name: Unrelated diagnostic\n", 1,
                )
                self.assertNotEqual(moved, self.workflow)
                with self.assertRaisesRegex(
                    AssertionError, "missing live preflight gate"
                ):
                    require_manual_preflight(moved)

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

    def test_negative_guard_rejects_missing_or_spoofed_zig_release_safe(self):
        command = ZIG_RELEASE_SAFE_COMMAND
        self.assertIn("          " + command + "\n", self.workflow)
        require_manual_preflight(self.workflow)
        mutations = (
            "echo " + command,
            "# " + command,
            command + " || true",
            command + " # ignored",
            command.replace("ReleaseSafe", "ReleaseFast"),
            command.replace("ReleaseSafe", "Debug"),
            "true",
        )
        for replacement in mutations:
            with self.subTest(replacement=replacement):
                broken = self.workflow.replace(
                    "          " + command + "\n",
                    "          " + replacement + "\n", 1,
                )
                self.assertNotEqual(broken, self.workflow)
                with self.assertRaisesRegex(
                    AssertionError, "missing live Zig ReleaseSafe physical suite"
                ):
                    require_manual_preflight(broken)

    def test_negative_guard_rejects_native_suite_before_full_migration(self):
        command = ZIG_RELEASE_SAFE_COMMAND
        full_gate = "python3 scripts/migration-zig-gate.py --require-zig"
        self.assertIn("          " + command, self.workflow)
        broken = self.workflow.replace(
            "          " + full_gate + "\n",
            "          " + command + "\n", 1,
        ).replace(
            "          " + command + "\n\n      - name:",
            "          " + full_gate + "\n\n      - name:", 1,
        )
        self.assertNotEqual(broken, self.workflow)
        with self.assertRaisesRegex(
            AssertionError, "missing live Zig ReleaseSafe physical suite"
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
