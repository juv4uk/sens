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
    ("Full workspace tests (pre-tag, exact SHA)", "cargo test --locked --workspace --no-fail-fast"),
    ("Full workspace Clippy (pre-tag, exact SHA)",
     "cargo clippy --locked --workspace --all-targets -- -D warnings"),
)
REQUIRED_COMMANDS = tuple(command for _, command in REQUIRED_WORKSPACE_STEPS)
ALLOWED_EVENTS = frozenset(("workflow_dispatch", "workflow_call"))
ZIG_RELEASE_SAFE_COMMAND = "zig test research/zig-codecs/tests.zig -O ReleaseSafe -lc"
C_HOST_ABI_COMMAND = "bash research/zig-codecs/host-c/verify.sh"
H2_CORPUS_COMMAND = "python3 research/zig-codecs/host-c/verify_h2_physical_parity.py --self-test --run"


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

    # The exact release migration job cannot be conditional or warn-only.
    job = re.search(r"(?m)^  release-preflight:[ \t]*$", source)
    if job is None:
        raise AssertionError("RELEASE_BLOCKED: missing release-preflight job")
    next_job = re.search(r"(?m)^  [a-zA-Z0-9_-]+:", source[job.end():])
    job_end = job.end() + next_job.start() if next_job else len(source)
    job_body = source[job.end():job_end]
    if re.search(r"(?m)^    (?:if|continue-on-error):", job_body):
        raise AssertionError("RELEASE_BLOCKED: Zig release job must be unconditional")

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

    # YAML can put conditional metadata AFTER a block of live shell text.
    next_step = re.search(r"(?m)^      - ", source[step.end():])
    step_end = step.end() + next_step.start() if next_step else len(source)
    step_scope = source[step.start():step_end]
    if re.search(r"(?m)^        (?:if|continue-on-error):", step_scope):
        raise AssertionError("RELEASE_BLOCKED: Zig release step must be unconditional")

    # Mandatory strict shell must start first and never relax after.
    live_lines = [
        line.strip() for line in body.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if (not live_lines or live_lines[0] != "set -euo pipefail"
            or any(re.match(r"^set\s+\+", line) for line in live_lines[1:])):
        raise AssertionError("RELEASE_BLOCKED: Zig release shell must remain strict")
    # A structural preflight must use the explicit corridor-only mode.
    # Without it, a correct NO-GO on missing SENS/oracle evidence would
    # prematurely abort later independent tests; it cannot grant release.
    structural_command = (
        'python3 scripts/release_go_gate.py . --structural-only '
        '--json "$RUNNER_TEMP/release-go-gate.json"'
    )
    structural_line = "          " + structural_command + "\n"
    if body.count(structural_line) != 1:
        raise AssertionError("RELEASE_BLOCKED: structural-only gate missing or spoofed")
    if re.search(r"(?m)^          python3 scripts/release_go_gate.py (?!.*--structural-only)", body):
        raise AssertionError("RELEASE_BLOCKED: non-structural GO gate inside transport preflight")

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
        r"(?m)^          " + re.escape(C_HOST_ABI_COMMAND) + r"[ \t]*$", body,
    )
    if host_match is None or host_match.start() <= native_match.end():
        raise AssertionError("RELEASE_BLOCKED: missing live Rust-free C Zig ABI witness")

    # A fully optimized native Zig run and a single C ABI example are not
    # evidence of parity on the owner-pinned six-pair migration corpus.
    # Require a LIVE full H2 run after C ABI verification in the same step;
    # --self-test without --run is synthetic and cannot authorize release.
    h2_match = re.search(
        r"(?m)^          " + re.escape(H2_CORPUS_COMMAND) + r"[ \t]*$", body,
    )
    if h2_match is None or h2_match.start() <= host_match.end():
        raise AssertionError(
            "RELEASE_BLOCKED: missing live Zig H2 migration physical corpus"
        )


    # The GO gate has to publish its exact machine receipt. Warn-only,
    # missing, moved or commented-out upload cannot prove a release.
    receipt_step = "      - name: Upload release GO-gate report\n"
    if source.count(receipt_step) != 1:
        raise AssertionError("RELEASE_BLOCKED: missing unique GO-gate artifact step")
    receipt_body = source.split(receipt_step, 1)[1].split("\n      - name:", 1)[0]
    required_upload_lines = (
        "        if: always()",
        "        with:",
        "          name: release-go-gate",
        "          path: ${{ runner.temp }}/release-go-gate.json",
        "          if-no-files-found: error",
    )
    for expected_line in required_upload_lines:
        if re.search(r"(?m)^" + re.escape(expected_line) + r"$", receipt_body) is None:
            raise AssertionError(
                "RELEASE_BLOCKED: missing fail-closed GO-gate artifact evidence: "
                + expected_line.strip()
            )
    # GitHub Actions v4 must be pinned to its immutable 40-hex commit.
    # A floating @v4 label is not a valid release receipt.
    if re.search(
        r"(?m)^        uses: actions/upload-artifact@[0-9a-f]{40} # v4$",
        receipt_body,
    ) is None:
        raise AssertionError(
            "RELEASE_BLOCKED: missing fail-closed GO-gate artifact evidence: "
            "immutable actions/upload-artifact v4 SHA"
        )


class ReleasePreflightScopeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_current_manual_preflight_keeps_full_release_gates(self):
        require_manual_preflight(self.workflow)


    def test_go_gate_report_is_required_and_cannot_be_spoofed(self):
        expected = "          if-no-files-found: error\n"
        self.assertIn(expected, self.workflow)
        live = "      - name: Upload release GO-gate report\n"
        self.assertIn(live, self.workflow)
        pin = re.search(
            r"(?m)^        uses: actions/upload-artifact@[0-9a-f]{40} # v4\n",
            self.workflow,
        )
        self.assertIsNotNone(pin)
        mutations = (
            (expected, "          if-no-files-found: warn\n"),
            (expected, "          if-no-files-found: ignore\n"),
            (expected, "          # if-no-files-found: error\n"),
            ("          path: ${{ runner.temp }}/release-go-gate.json\n",
             "          path: ${{ runner.temp }}/unrelated.json\n"),
            ("          name: release-go-gate\n",
             "          name: unrelated-artifact\n"),
            (pin.group(), "        uses: actions/upload-artifact@v4\n"),
            (pin.group(), "        uses: actions/upload-artifact@v5\n"),
            (pin.group(), "        uses: actions/upload-artifact@1234567 # v4\n"),
            (pin.group(), "        uses: actions/upload-artifact@" + "1" * 40 + " # v3\n"),
            (live, "      - name: Unrelated upload step\n"),
        )
        for before, after in mutations:
            with self.subTest(mutation=after.strip()):
                self.assertIn(before, self.workflow)
                broken = self.workflow.replace(before, after, 1)
                self.assertNotEqual(broken, self.workflow)
                with self.assertRaisesRegex(
                    AssertionError, "GO-gate artifact"
                ):
                    require_manual_preflight(broken)

        # The expected option appearing ONLY inside a comment is insufficient.
        spoof = self.workflow.replace(
            expected,
            "          if-no-files-found: warn\n"
            "          # if-no-files-found: error\n",
            1,
        )
        with self.assertRaisesRegex(AssertionError, "GO-gate artifact"):
            require_manual_preflight(spoof)

    def test_structural_preflight_mode_cannot_be_removed_or_echoed(self):
        live = ('          python3 scripts/release_go_gate.py . --structural-only '
                '--json "$RUNNER_TEMP/release-go-gate.json"\n')
        self.assertIn(live, self.workflow)
        for forged in (
            live.replace(" --structural-only", ""),
            live.replace("python3 ", "echo python3 "),
            live.replace("python3 ", "# python3 "),
        ):
            with self.subTest(forged=forged.strip()):
                modified = self.workflow.replace(live, forged, 1)
                with self.assertRaisesRegex(AssertionError, "structural-only gate"):
                    require_manual_preflight(modified)

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
        # Swap the actual live commands rather than assuming the native
        # suite is the last command in this release step. Independent C-host
        # transport checks may correctly follow it.
        broken = self.workflow.replace(
            "          " + full_gate + "\n",
            "          __REORDER_FULL_GATE__\n", 1,
        )
        broken = broken.replace(
            "          " + command + "\n",
            "          " + full_gate + "\n", 1,
        )
        broken = broken.replace(
            "          __REORDER_FULL_GATE__\n",
            "          " + command + "\n", 1,
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

    def test_negative_guard_rejects_spoofed_h2_physical_migration_corpus(self):
        live = "          " + H2_CORPUS_COMMAND + "\n"
        self.assertIn(live, self.workflow)
        require_manual_preflight(self.workflow)
        for replacement in (
            "# " + H2_CORPUS_COMMAND,
            "echo " + H2_CORPUS_COMMAND,
            "true # " + H2_CORPUS_COMMAND,
            H2_CORPUS_COMMAND + " || true",
            H2_CORPUS_COMMAND + " # ignored",
            H2_CORPUS_COMMAND.replace(" --self-test --run", " --self-test"),
            H2_CORPUS_COMMAND.replace(" --self-test --run", " --run=false"),
            "true",
        ):
            with self.subTest(replacement=replacement):
                forged = self.workflow.replace(live, "          " + replacement + "\n", 1)
                self.assertNotEqual(forged, self.workflow)
                with self.assertRaisesRegex(
                    AssertionError, "missing live Zig H2 migration physical corpus"
                ):
                    require_manual_preflight(forged)

    def test_negative_guard_rejects_h2_in_unrelated_step_or_wrong_order(self):
        live = "          " + H2_CORPUS_COMMAND + "\n"
        host = "          " + C_HOST_ABI_COMMAND + "\n"
        marker = "      - name: Upload release GO-gate report\n"
        for source in (live, host, marker):
            self.assertIn(source, self.workflow)

        # Even a real physical command in an unrelated YAML step does not
        # prove the required Zig release corridor ran the migration corpus.
        extra = (
            "      - name: Decorative H2 separate check\n"
            "        run: |\n"
            "          set -euo pipefail\n"
            + live + "\n"
        )
        misplaced = self.workflow.replace(live, "", 1)
        misplaced = misplaced.replace(marker, extra + marker, 1)
        with self.assertRaisesRegex(
            AssertionError, "missing live Zig H2 migration physical corpus"
        ):
            require_manual_preflight(misplaced)

        # The independent corpus must follow the compiled C ABI witness,
        # not be allowed to run before the prerequisite transport contract.
        reordered = self.workflow.replace(host, "          __SWAP_H2__\n", 1)
        reordered = reordered.replace(live, host, 1)
        reordered = reordered.replace("          __SWAP_H2__\n", live, 1)
        with self.assertRaisesRegex(
            AssertionError, "missing live Zig H2 migration physical corpus"
        ):
            require_manual_preflight(reordered)

    def test_zig_release_failclosed_metadata_and_shell_mutants(self):
        require_manual_preflight(self.workflow)
        job = "    timeout-minutes: 45\n"
        shell = "          set -euo pipefail\n"
        last = "          " + H2_CORPUS_COMMAND + "\n"
        for anchor in (job, shell, last):
            self.assertIn(anchor, self.workflow)
        for inject in ("    if: false\n", "    continue-on-error: true\n"):
            with self.subTest(job=inject):
                changed = self.workflow.replace(job, job + inject, 1)
                with self.assertRaisesRegex(
                    AssertionError, "Zig release job must be unconditional"
                ):
                    require_manual_preflight(changed)
        for inject in ("        if: false\n",
                       "        continue-on-error: true\n"):
            with self.subTest(step=inject):
                changed = self.workflow.replace(last, last + inject, 1)
                with self.assertRaisesRegex(
                    AssertionError, "Zig release step must be unconditional"
                ):
                    require_manual_preflight(changed)
        corridor_start = self.workflow.index("      - name: Sterile Zig corridor ")
        corridor_end = self.workflow.index(
            "      - name: Upload release GO-gate report", corridor_start
        )
        corridor = self.workflow[corridor_start:corridor_end]
        self.assertIn(shell, corridor)
        for inject in ("          set +e\n", "          set +u\n",
                       "          set +o pipefail\n",
                       "          set +o errexit\n"):
            with self.subTest(shell=inject):
                changed_corridor = corridor.replace(shell, shell + inject, 1)
                self.assertNotEqual(changed_corridor, corridor)
                changed = (
                    self.workflow[:corridor_start]
                    + changed_corridor
                    + self.workflow[corridor_end:]
                )
                with self.assertRaisesRegex(
                    AssertionError, "Zig release shell must remain strict"
                ):
                    require_manual_preflight(changed)
        changed_corridor = corridor.replace(
            shell, "          echo bypass\n" + shell, 1
        )
        self.assertNotEqual(changed_corridor, corridor)
        changed = (
            self.workflow[:corridor_start]
            + changed_corridor
            + self.workflow[corridor_end:]
        )
        with self.assertRaisesRegex(
            AssertionError, "Zig release shell must remain strict"
        ):
            require_manual_preflight(changed)

    def test_negative_guard_rejects_floating_event_mapping(self):
        broken = self.workflow.replace(
            "on:\n  workflow_dispatch:\n", "on: [push, pull_request]\n", 1
        )
        self.assertNotEqual(broken, self.workflow)
        with self.assertRaisesRegex(AssertionError, "explicit on: mapping"):
            require_manual_preflight(broken)


if __name__ == "__main__":
    unittest.main()
