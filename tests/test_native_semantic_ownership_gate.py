"""Перевіряємо лише маршрут тестів, не семантику SENS."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "sens_ownership", ROOT / "scripts/guard_native_semantic_ownership.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
LAW = "tests/semantic/demo-law.lisp"
MUTANT = "tests/semantic/demo-mutant.lisp"
RUNNER = """run_case run_law demo-positive tests/semantic/demo-law.lisp 1
run_case run_law demo-mutant tests/semantic/demo-mutant.lisp 0
echo --t5m-mint verify-view --t5m-pair sens-standalone
"""
CI = "bash scripts/prove-lisp-semantic-t5m.sh"


class LanguageOwnershipRouting(unittest.TestCase):
    def audit(self, paths, runner=RUNNER, files=None, contents=None, ci=CI):
        files = set(files if files is not None else [LAW, MUTANT])
        contents = contents or {}
        return guard.audit_added_paths(
            paths, runner, ci, lambda p: p in files, lambda p: contents[p])

    def test_positive_and_mutant_are_both_registered(self):
        self.assertEqual(self.audit([LAW, MUTANT]), [])

    def test_new_semantic_lisp_without_live_registration_is_red(self):
        changed = RUNNER.replace("tests/semantic/demo-law.lisp", "unknown.lisp")
        self.assertTrue(any("SENS_LAW_NOT_REGISTERED" in err
                            for err in self.audit([LAW], runner=changed)))

    def test_comment_cannot_forge_route(self):
        changed = RUNNER.replace("run_case run_law demo-positive",
                                 "# run_case run_law demo-positive")
        self.assertTrue(any("SENS_LAW_NOT_REGISTERED" in err
                            for err in self.audit([LAW], runner=changed)))

    def test_missing_mutant_is_red(self):
        self.assertTrue(any("SENS_LAW_MUTANT_MISSING" in err
                            for err in self.audit([LAW], files=[LAW])))

    def test_existing_but_unrouted_mutant_is_red(self):
        changed = RUNNER.replace("tests/semantic/demo-mutant.lisp", "unrelated.lisp")
        errors = self.audit([LAW], runner=changed)
        self.assertTrue(any("SENS_LAW_MUTANT_NOT_ROUTED" in err for err in errors))

    def test_existing_but_unrouted_positive_is_red(self):
        changed = RUNNER.replace("tests/semantic/demo-law.lisp", "unrelated.lisp")
        errors = self.audit([MUTANT], runner=changed)
        self.assertTrue(any("SENS_LAW_POSITIVE_NOT_ROUTED" in err for err in errors))

    def test_missing_positive_is_red(self):
        self.assertTrue(any("SENS_LAW_POSITIVE_MISSING" in err
                            for err in self.audit([MUTANT], files=[MUTANT])))

    def test_native_ci_cannot_be_removed_silently(self):
        self.assertTrue(any("NATIVE_LANGUAGE_RUNNER_NOT_IN_CI" in err
                            for err in self.audit([], ci="echo PASS")))

    def test_new_rust_truth_oracle_is_red_but_mechanics_accepted(self):
        path = "crates/sens/tests/new_eval.rs"
        semantic = 'fn test(){ let x = eval(input); assert_eq!(x, Value::Bool(true)); }'
        mechanism = 'fn test(){ let x = eval(input); assert_eq!(x.bytes.len(), 10); }'
        self.assertTrue(any("HOST_SEMANTIC_ORACLE_ADDED" in err
                            for err in self.audit([path], files=[path],
                                                  contents={path: semantic})))
        self.assertEqual(self.audit([path], files=[path], contents={path: mechanism}), [])

    def test_language_prefix_pair_is_supported(self):
        positive = "tests/semantic/language-law-new-idea.lisp"
        negative = "tests/semantic/language-mutant-new-idea.lisp"
        runner = RUNNER + (
            f'cat {positive} > "$law_bundle"\n'
            f'cat {negative} > "$mutant_bundle"\n'
            'run_case run_law new-idea-positive "$law_bundle" 1\n'
            'run_case run_law new-idea-mutant "$mutant_bundle" 0\n'
        )
        self.assertEqual(self.audit([positive, negative], runner=runner,
                                    files=[positive, negative]), [])

    def test_multiline_cat_dashdash_counts_only_with_live_run_case(self):
        positive = "tests/semantic/language-law-multiline.lisp"
        mutant = "tests/semantic/language-mutant-multiline.lisp"
        cat_commands = (
            'cat -- lib/epistemic.lisp \\\n'
            f'  "{positive}" > "$positive_bundle"\n'
            'cat -- lib/epistemic.lisp \\\n'
            f'  "{mutant}" > "$mutant_bundle"\n'
        )
        live = (RUNNER + cat_commands
                + 'run_case run_law multiline-positive "$positive_bundle" 1\n'
                + 'run_case run_law multiline-mutant "$mutant_bundle" 0\n')
        self.assertEqual(
            self.audit([positive, mutant], runner=live, files=[positive, mutant]), []
        )
        # Згадка імен у реальному cat не є доказом без run_case.
        fake = RUNNER + cat_commands + 'echo "$positive_bundle" "$mutant_bundle"\n'
        failures = self.audit([positive, mutant], runner=fake,
                              files=[positive, mutant])
        self.assertTrue(any("SENS_LAW_NOT_REGISTERED" in error for error in failures))
        self.assertTrue(any("SENS_LAW_MUTANT_NOT_ROUTED" in error for error in failures))

    def test_echo_and_unused_cat_do_not_forge_native_execution(self):
        runner = RUNNER + (
            f"echo {'tests/semantic/hidden-law.lisp'}\n"
            'cat tests/semantic/hidden-law.lisp > "$unused_bundle"\n'
        )
        hidden = "tests/semantic/hidden-law.lisp"
        mutant = "tests/semantic/hidden-mutant.lisp"
        errors = self.audit([hidden], runner=runner, files=[hidden, mutant])
        self.assertTrue(any("SENS_LAW_NOT_REGISTERED" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
