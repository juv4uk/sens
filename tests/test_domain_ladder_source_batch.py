"""Regressions for source-only, all-live-files exact-domain migration intake."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "migrate-domain-ladder-source-batch.py"
SPEC = importlib.util.spec_from_file_location("sens_domain_ladder_source_batch", PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)

class BatchSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mapping, cls.blocked = MOD.authority(ROOT)
        cls.guard = MOD.guard_module(ROOT)

    def test_ratified_map_exact_and_ambiguous_blocked(self):
        self.assertEqual(len(self.mapping), 171)
        self.assertEqual(self.mapping["00001001"], "0011")
        self.assertEqual(self.mapping["00000011"], "101")
        for code in ("00001010", "00110111", "01011010"):
            self.assertNotIn(code, self.mapping)
            self.assertIn(code, self.blocked)

    def test_all_2046_exact_domain_coordinates_are_not_assumed_callable(self):
        witness = MOD.verify_full_domain_bitspace(ROOT)
        self.assertEqual(witness["typed_coordinates"], 2046)
        self.assertEqual(witness["meaningful_bits"], 18434)
        self.assertEqual(witness["runtime_admission_claims_added"], 0)
        self.assertEqual(witness["counts_by_domain"], {
            f"D{width}": 1 << width for width in range(1, 11)
        })
        self.assertEqual(
            sum(width * count for width, count in enumerate(
                [0] + [1 << w for w in range(1, 11)]
            ) if width), 18434
        )

    def test_all_256_historical_donors_have_one_proved_or_held_disposition(self):
        self.assertEqual(len(self.mapping), 171)
        self.assertEqual(len(self.blocked), 85)
        self.assertEqual(len(set(self.mapping) | set(self.blocked)), 256)
        self.assertFalse(set(self.mapping) & set(self.blocked))
        # Equal integer payload is NOT equal identity: W7 data vs W8.
        self.assertNotEqual((7, "0000001"), (8, "00000001"))
        self.assertNotEqual((3, "010"), (4, "0010"))
        for old, word in self.mapping.items():
            self.assertRegex(old, r"^[01]{8}$")
            self.assertRegex(word, r"^[01]{3,9}$")
            self.assertNotEqual(len(word), 2, "D2 structural words are not call-heads")
            self.assertNotEqual(len(word), 10, "D10 has no admitted T5 mechanism")
        for old in ("10101000", "01011010"):
            self.assertIn(old, self.blocked)

    def test_ladder_bitspace_mutations_are_rejected_before_sid8_rewrite(self):
        self.assertEqual(MOD._exact_codebook(["00", "01", "10", "11"], 2, "D2"), 4)
        for corrupted in (
            ["00", "01", "10", "10"],  # duplicate
            ["00", "01", "10", "100"],  # width overflow
            ["00", "01", "10"],  # missing bit pattern
        ):
            with self.subTest(corrupted=corrupted), self.assertRaises(ValueError):
                MOD._exact_codebook(corrupted, 2, "D2")

    def test_quasiquote_never_silently_passes_as_admitted_sid8_program(self):
        for source in (
            "`(00001001 x (00001000 () x))",
            "(00001001 x (00001000 () ,(00000101 x)))",
        ):
            rewritten, count, blockers = MOD.rewrite(source, self.mapping, self.blocked)
            self.assertEqual(rewritten, source)
            self.assertTrue(any("quasiquote/unquote" in blocker for blocker in blockers))

    def test_nested_quoted_data_and_comments_preserved(self):
        old = ";(00000100 ignored)\n(00001001 f (00001000 (x) (00000100 (00000001 00000011) x)))\n"
        new, n, blockers = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(n, 4)
        self.assertFalse(blockers)
        self.assertIn("(0011 f (0010 (x) (111 (001 00000011) x)))", new)
        self.assertIn(";(00000100 ignored)", new)

    def test_ambiguous_head_blocks_entire_file(self):
        old = "(00001001 f (00001000 () (00110111 fun values)))"
        new, n, blockers = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(new, old)
        self.assertEqual(n, 2)
        self.assertTrue(any("00110111" in b for b in blockers))

    def test_cond_three_fields_requires_semantic_translation(self):
        old = "(00001001 f (00001000 (x) (00000111 ((00000010 x) 0 1))))"
        new, n, blockers = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(n, 4)
        self.assertFalse(blockers)
        findings = self.guard.scan_lisp(new, "lib/f.lisp")
        self.assertIn("COND_NOT_TWO_FIELDS", {f.rule for f in findings})

    def test_generated_and_current_domain_data_are_never_mass_rewritten(self):
        names = {
            "lib/machine/encoding/admitted-iclass-index.lisp",
            "lib/machine/cpu/intel-core-i5-6400-inventory.lisp",
            "lib/machine/dispatch/native-first-execute.lisp",
            "lib/island-math-evidence.lisp",
            "knowledge/language-detection-probe.lisp",
        }
        census = MOD.run(ROOT, False, names)
        self.assertEqual(census["summary"]["admitted_heads"], 0)
        self.assertEqual(census["summary"]["admitted_files"], 0)
        self.assertEqual(len(census["files"]), len(names))
        for row in census["files"]:
            with self.subTest(path=row["path"]):
                self.assertEqual(row["status"], "source-era-unproved")

    def test_exact_sha_pinned_schema_metadata_is_not_executable_source(self):
        path = "lib/function-table-mechanisms.lisp"
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["files"][0]["status"], "nonprogram-data-reviewed")
        self.assertEqual(report["files"][0]["potential_heads"], 0)
        self.assertEqual(
            report["files"][0]["source_git_blob_sha"],
            "e749d5696205efb335447859388630c493cf8df2",
        )

    def test_template_strings_are_not_old_executable_define_heads(self):
        source = """; (00001011 ignored)\n(0011 code (0010 () "(00001001 inside-string)"))\n(001 quoted (00001001 ignored))\n'(00001001 ignored)\n#| (00001001 blocked-comment) |#\n"""
        heads = MOD.executable_call_heads(source, self.guard)
        self.assertNotIn("00001001", heads)
        self.assertNotIn("00001011", heads)
        self.assertIn("0011", heads)
        self.assertIn("0010", heads)
        self.assertEqual(
            MOD.executable_call_heads("(00001001 real (00001000 (x) x))", self.guard)
            & {"00001001", "00001000"},
            {"00001001", "00001000"},
        )

    def test_current_d8_in_templates_is_not_misclassified_as_legacy(self):
        paths = {
            "scripts/generate-meta-semantic-registry.lisp",
            "scripts/verify-repo.lisp",
        }
        report = MOD.run(ROOT, False, paths)
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["summary"]["scanned"], 2)
        self.assertEqual(
            {row["status"] for row in report["files"]},
            {"source-era-unproved"},
        )

    def test_historical_W8_read_successors_use_distinct_ratified_D9_codes(self):
        path = "scripts/semantic-authority-guard-enforce.lisp"
        src = (ROOT / path).read_text(encoding="utf-8")
        heads = MOD.executable_call_heads(src, self.guard)
        for old, new in (("01001011", "110101001"),
                         ("10100110", "110110111")):
            self.assertNotIn(old, heads)
            self.assertIn(new, heads)
            self.assertEqual(self.mapping[old], new)
        self.assertIn("(110101001 (110110111 ", src)
        self.assertEqual(
            MOD.pinned_cross_domain_blockers(ROOT, path, heads, self.mapping),
            [], "No retired D8/W8 head may be reused as current D8"
        )
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["files"][0]["status"], "unchanged")

        facts = "knowledge/guard-fact-policy.lisp"
        current_heads = MOD.executable_call_heads(
            (ROOT / facts).read_text(encoding="utf-8"), self.guard
        )
        self.assertNotIn("10011100", current_heads,
                         "six historical LETs must be lowered to D4 LAMBDA")
        self.assertEqual(
            MOD.pinned_cross_domain_blockers(ROOT, facts, current_heads, self.mapping),
            [],
            "No historical W8 LET must remain as executable code",
        )
        self.assertEqual(
            MOD.pinned_cross_domain_blockers(ROOT, facts, set(), self.mapping),
            [],
            "A historical-looking token only in quote/string is not executable",
        )
        self.assertEqual(
            MOD.pinned_cross_domain_blockers(ROOT, "lib/modern-d8.lisp", {"10011100"}, self.mapping),
            [],
            "No global W8 interpretation for legitimate D8 source",
        )

    def test_historical_cond_guard_rejects_other_active_policy_sources(self):
        # Executable historical COND clauses may carry a third explicit
        # expected-result field or a host T fallback. Replacing just the
        # eight-bit head with D3:110 would change semantics at runtime.
        # Fail closed until a source-specific two-branch D1/D3 oracle exists.
        paths = (
            "knowledge/guard-reference.lisp",
        )
        for path in paths:
            with self.subTest(path=path):
                report = MOD.run(ROOT, False, {path})
                self.assertEqual(report["summary"]["admitted_files"], 0)
                self.assertEqual(report["summary"]["blocked_files"], 1)
                # Exact D4 heads have been substituted, but the old
                # three-field/host-truth D3 semantics are intentionally
                # still present, and never declared fully migrated.
                self.assertIn(path, MOD.PARTIAL_D4_WITH_LEGACY_D3)
                row = report["files"][0]
                self.assertEqual(row["status"], "blocked")
                self.assertTrue(
                    any("COND_HOST_TRUTH" in reason
                        or "COND_NOT_TWO_FIELDS" in reason
                        for reason in row["reasons"]),
                    f"{path}: missing D3 semantic blocker {row['reasons']}",
                )

    def test_fact_policy_has_exact_D1_D3_but_no_unsupported_source_admission(self):
        path = "knowledge/guard-fact-policy.lisp"
        text = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(self.guard.scan_lisp(text, path), [])
        self.assertNotIn("(10011100 ", text,
                         "W8 LET must remain lower-domain lambda applications")
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["files"][0]["status"], "unchanged",
                         "Source census does not grant T5/runtime admission")

    def test_semantic_guard_d3_and_d9_reader_are_both_exact_source(self):
        path = "scripts/semantic-authority-guard-enforce.lisp"
        text = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(self.guard.scan_lisp(text, path), [],
                         "no three-field/host-truth D3 may remain")
        self.assertIn("(110101001 (110110111 ", text)
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertEqual(report["summary"]["blocked_files"], 0)
        row = report["files"][0]
        self.assertEqual(row["status"], "unchanged")
        self.assertEqual(row["reasons"], [])

    def test_immutable_guard_reference_not_rewritten_until_cond_law(self):
        report = MOD.run(ROOT, False, {"knowledge/guard-reference.lisp"})
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertGreaterEqual(report["summary"]["blocked_files"], 1)
        self.assertEqual(report["files"][0]["status"], "blocked")

if __name__ == "__main__":
    unittest.main()
