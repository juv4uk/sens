"""Guard exact caller-manifest scope during concurrent remint recovery.

This is workflow-orchestration logic only. Native SENS/Zig evaluation remains
the authority for semantics and physical-pair admission.
"""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "remint-drifted-pairs.yml"


class RemintExplicitManifestScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WORKFLOW.read_text(encoding="utf-8")

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

        self.assertLess(recovery_start, explicit_branch)
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
