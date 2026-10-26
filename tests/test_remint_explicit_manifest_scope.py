"""Guard exact caller-manifest scope during concurrent remint recovery.

This is workflow-orchestration logic only. Native SENS/Zig evaluation remains
the authority for semantics and physical-pair admission.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "remint-drifted-pairs.yml"
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


class RemintExplicitManifestScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.ci_source = CI_WORKFLOW.read_text(encoding="utf-8")

    def test_remint_trigger_uses_exact_git_diff_and_explicit_recovery_marker(self) -> None:
        detector_start = self.ci_source.index("  detect-remint:\n")
        remint_start = self.ci_source.index("  remint-targeted:\n", detector_start)
        detector = self.ci_source[detector_start:remint_start]
        remint = self.ci_source[remint_start:]

        # GitHub push payloads vary between single-commit and batch pushes.
        # The exact commit range is the authority for deciding whether to remint.
        self.assertIn('HEAD_SHA: ${{ github.sha }}', detector)
        self.assertIn('BEFORE_SHA: ${{ github.event.before }}', detector)
        self.assertIn('if [[ "${HEAD_MESSAGE:-}" == *SENS_PAIR_REGEN* ]]; then', detector)
        self.assertIn('git diff-tree --no-commit-id --name-only -r "$HEAD_SHA"', detector)
        self.assertIn('git diff --name-only "$BEFORE_SHA" "$HEAD_SHA"', detector)
        for target in (
            "lib/core4.lisp",
            "lib/lisp-fs.lisp",
            "tests/fixtures/wsm-fs-record-producer.lisp",
            ".github/workflows/ci.yml",
            ".github/workflows/remint-drifted-pairs.yml",
        ):
            self.assertIn(f"'{target}'", detector)

        # The expensive reusable workflow may run only when this diff says so.
        self.assertIn("needs: detect-remint", remint)
        self.assertIn(
            "if: ${{ github.event_name == 'push' && needs.detect-remint.outputs.needed == 'true' }}",
            remint,
        )
        self.assertNotIn("github.event.commits.*.modified", remint)

    def test_commit_recovery_receives_the_original_manifest(self) -> None:
        self.assertIn("REMINT_FILES: ${{ inputs.files }}", self.source)

    def test_f6_producer_uses_exact_dependency_stack_with_core4(self) -> None:
        self.assertIn(
            "tests/fixtures/wsm-fs-record-producer.lisp) "
            "bs=(--binding-source lib/persistent-map.lisp "
            "--binding-source lib/world.lisp "
            "--binding-source lib/content-store.lisp "
            "--binding-source lib/lisp-fs.lisp); "
            "profile_args=(--core4-runtime);;",
            self.source,
        )
        helper = (ROOT / "scripts" / "refresh-verified-t5m-pair.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'tests/semantic/d5-arithmetic-native-t5m-mutant.lisp|lib/lisp-fs.lisp|tests/fixtures/wsm-fs-record-producer.lisp) ;;',
            helper,
        )
        self.assertIn(
            '"${binding_sources[*]}" != "lib/persistent-map.lisp lib/world.lisp lib/content-store.lisp lib/lisp-fs.lisp"',
            helper,
        )

        # The dependency-complete carrier must use the selected runtime profile.
        # A bare sens <.sens> is intentionally Session::bare and rejects D6 closures.
        self.assertIn(
            '! timeout "$native_timeout" "${standalone_runtime[@]}" "$complete" > "$scratch/complete.out"',
            helper,
        )
        self.assertNotIn(
            '! timeout "$native_timeout" "$binary" "$complete" > "$scratch/complete.out"',
            helper,
        )

    def test_d6_d8_association_laws_use_explicit_core4_profile(self) -> None:
        profile_case = (
            "tests/semantic/exact-arithmetic-laws.lisp|tests/semantic/exact-arithmetic-mutant.lisp|"
            "lib/lisp-fs.lisp|tests/semantic/d6-derived-research-batch-01.lisp|"
            "tests/semantic/d8-rassq-until-batch.lisp) profile_args=(--core4-runtime);;"
        )
        self.assertGreaterEqual(self.source.count(profile_case), 2)

        helper = (ROOT / "scripts" / "refresh-verified-t5m-pair.sh").read_text(
            encoding="utf-8"
        )
        helper_profile = (
            "|tests/semantic/d6-derived-research-batch-01.lisp|"
            "tests/semantic/d8-rassq-until-batch.lisp) ;;"
        )
        self.assertIn(helper_profile, helper)

        push_workflow = (ROOT / ".github" / "workflows" / "lisp-to-sens-on-push.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "tests/semantic/d6-derived-research-batch-01.lisp|"
            "tests/semantic/d8-rassq-until-batch.lisp) profile_args=(--core4-runtime);;",
            push_workflow,
        )
        self.assertIn(
            '"${profile_args[@]}"',
            push_workflow,
        )

    def test_explicit_manifest_suppresses_global_recovery_expansion(self) -> None:
        function_start = self.source.index("regenerate_on_current_main() {")
        recovery_start = self.source.index(
            'if [[ -n "${REMINT_FILES:-}" ]]; then', function_start
        )
        recovery_end = self.source.index(
            "# Відновлення після зсуву main:", recovery_start
        )
        guarded_section = self.source[recovery_start:recovery_end]
        explicit_branch = guarded_section.index(
            "REMINT_CURRENT_MAIN_SCOPE explicit-manifest=preserved"
        )
        else_branch = guarded_section.index("\n            else\n", explicit_branch)
        contest_scan = guarded_section.index(
            "for source in benchmarks/contest-uk/*.lisp; do", else_branch
        )
        library_scan = guarded_section.index(
            "for source in lib/*.lisp tests/semantic/d9-string-append-physical.lisp",
            contest_scan,
        )
        close_guard = guarded_section.rfind("\n            fi\n")

        # `explicit_branch` is relative to `guarded_section`; compare in one coordinate system.
        self.assertLess(recovery_start, recovery_start + explicit_branch)
        self.assertLess(explicit_branch, else_branch)
        self.assertLess(else_branch, contest_scan)
        self.assertLess(contest_scan, library_scan)
        self.assertLess(library_scan, close_guard)
        self.assertNotIn(
            "REMINT_CURRENT_MAIN_SCOPE explicit-manifest=preserved",
            guarded_section[else_branch:],
        )


if __name__ == "__main__":
    unittest.main()
