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
C_HOST_ABI_COMMAND = "bash research/zig-codecs/host-c/verify.sh"


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
            + r"[ \t]*\n        run: " + re.escape(command) + r"[ \t]*$",
            source,
        )
        if live is None:
            raise AssertionError("RELEASE_BLOCKED: missing live preflight gate " + command)

    # A release preflight must really run the pinned Zig 0.16 physical
    # migration bridge. --self-test explicitly skips transport and exits 0,
    # so it can never substitute for the mandatory pre-tag physical proof.
    physical_command = "python3 scripts/migration-zig-gate.py --require-zig"
    # The full physical migration command must be LIVE in the SAME named
    # Zig step as the ReleaseSafe suite, never in an unrelated step or comment.
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
    physical_match = re.search(
        r"(?m)^          " + re.escape(physical_command) + r"[ \t]*$", body
    )
    if physical_match is None:
        raise AssertionError("RELEASE_BLOCKED: missing full Zig physical migration gate")
    native_match = re.search(
        r"(?m)^          " + re.escape(ZIG_RELEASE_SAFE_COMMAND)
        + r"[ \t]*$", body,
    )
    if (native_match is None or
            "          set -euo pipefail\n" not in body or
            native_match.start() <= physical_match.end()):
        raise AssertionError("RELEASE_BLOCKED: missing live Zig ReleaseSafe physical suite")

    # Independent compiled C caller, actually executing the Zig ABI v2,
    # must run after the optimized native Zig suite in the very same step.
    # A simulated self-test or a comment is not a cross-host proof.
    host_match = re.search(
        r"(?m)^          " + re.escape(C_HOST_ABI_COMMAND) + r"[ \\t]*$", body,
    )
    if host_match is None or host_match.start() <= native_match.end():
        raise AssertionError("RELEASE_BLOCKED: missing live Rust-free C Zig ABI witness")


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
                with self.assertRaisesRegex(AssertionError, "missing live preflight gate"):
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

    def test_zig_migration_in_other_step_is_not_release_evidence(self):
        command = "python3 scripts/migration-zig-gate.py --require-zig"
        live = "          " + command + "\n"
        marker = "      - name: Sterile Zig corridor (Rust↔SENS only via Zig ABI v2)\n"
        self.assertIn(live, self.workflow)
        self.assertIn(marker, self.workflow)
        for spoof in ("# " + command, "echo " + command, "true # " + command):
            with self.subTest(spoof=spoof):
                wrong_step = (
                    "      - name: Unrelated migration command\n"
                    "        run: |\n"
                    "          set -euo pipefail\n"
                    + live + "\n"
                )
                broken = self.workflow.replace(live, "          " + spoof + "\n", 1)
                broken = broken.replace(marker, wrong_step + marker, 1)
                self.assertNotEqual(broken, self.workflow)
                self.assertIn(wrong_step, broken)
                with self.assertRaisesRegex(
                    AssertionError, "missing full Zig physical migration gate"
                ):
                    require_manual_preflight(broken)

    def test_zig_migration_must_run_before_release_safe_suite(self):
        physical = "          python3 scripts/migration-zig-gate.py --require-zig\n"
        native = "          " + ZIG_RELEASE_SAFE_COMMAND + "\n"
        self.assertIn(physical, self.workflow)
        self.assertIn(native, self.workflow)
        broken = self.workflow.replace(physical, "          __REORDER__\n", 1)
        broken = broken.replace(native, physical, 1)
        broken = broken.replace("          __REORDER__\n", native, 1)
        with self.assertRaisesRegex(
            AssertionError, "missing live Zig ReleaseSafe physical suite"
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


    def test_negative_guard_rejects_forged_or_skipped_c_zig_abi_witness(self):
        # A release-ready transport corridor includes an independent C caller.
        live = "          " + C_HOST_ABI_COMMAND + "\n"
        self.assertIn(live, self.workflow)
        require_manual_preflight(self.workflow)
        for replacement in (
            "# " + C_HOST_ABI_COMMAND,
            "echo " + C_HOST_ABI_COMMAND,
            "true # " + C_HOST_ABI_COMMAND,
            C_HOST_ABI_COMMAND + " || true",
            C_HOST_ABI_COMMAND + " # ignored",
            C_HOST_ABI_COMMAND + " --self-test",
            "true",
        ):
            with self.subTest(replacement=replacement):
                broken = self.workflow.replace(
                    live, "          " + replacement + "\n", 1,
                )
                self.assertNotEqual(broken, self.workflow)
                with self.assertRaisesRegex(
                    AssertionError, "missing live Rust-free C Zig ABI witness",
                ):
                    require_manual_preflight(broken)

    def test_negative_guard_rejects_c_abi_only_in_unrelated_step(self):
        live = "          " + C_HOST_ABI_COMMAND + "\n"
        marker = "      - name: Upload release GO-gate report\n"
        self.assertIn(live, self.workflow)
        self.assertIn(marker, self.workflow)
        fake = ("      - name: Unrelated decorative C test\n"
                "        run: |\n"
                "          set -euo pipefail\n" + live + "\n")
        broken = self.workflow.replace(live, "", 1).replace(
            marker, fake + marker, 1,
        )
        self.assertNotEqual(broken, self.workflow)
        with self.assertRaisesRegex(
            AssertionError, "missing live Rust-free C Zig ABI witness",
        ):
            require_manual_preflight(broken)

    def test_negative_guard_rejects_c_abi_before_optimized_zig_suite(self):
        native = "          " + ZIG_RELEASE_SAFE_COMMAND + "\n"
        host = "          " + C_HOST_ABI_COMMAND + "\n"
        self.assertIn(native, self.workflow)
        self.assertIn(host, self.workflow)
        broken = self.workflow.replace(native, "          __REORDER__\n", 1)
        broken = broken.replace(host, native, 1)
        broken = broken.replace("          __REORDER__\n", host, 1)
        with self.assertRaisesRegex(
            AssertionError, "missing live Rust-free C Zig ABI witness",
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
