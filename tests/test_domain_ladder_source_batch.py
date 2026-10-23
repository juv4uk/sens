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
        self.assertEqual(self.mapping["00001001"], "визначити")
        self.assertEqual(self.mapping["00000011"], "тотожне?")
        for code in ("00001010", "00110111", "01011010"):
            self.assertNotIn(code, self.mapping)
            self.assertIn(code, self.blocked)

    def test_historical_sid8_writes_full_current_ukr_projection(self):
        projected = self.mapping
        self.assertEqual(len(projected), 171)
        self.assertEqual(projected["00001001"], "визначити")
        self.assertEqual(projected["00001000"], "функція")
        self.assertEqual(projected["00000011"], "тотожне?")
        self.assertEqual(projected["00000100"], "сполучити")

        # A historical function head becomes the exact resident's HUMAN
        # spelling, never a newly invented eight-bit D8 opcode.
        old = "(00001001 f (00001000 (x) (00000100 (00000001 00000011) x)))"
        new, count, problems = MOD.rewrite(old, projected, self.blocked)
        self.assertEqual(count, 4)
        self.assertEqual(problems, [])
        self.assertEqual(new,
                         "(визначити f (функція (x) (сполучити (як-є 00000011) x)))")
        # Quoted historical payload is data; it must not be converted to
        # a callable function by a blind replacement.
        self.assertIn("(як-є 00000011)", new)
        self.assertEqual(MOD.guard_module(ROOT).scan_lisp(new, "lib/example.lisp"), [])

    def test_ukrainian_apostrophe_does_not_hide_proven_old_heads(self):
        # Апостроф української клавіатури всередині назви не є QUOTE.
        source = "(00001001 ім'я (00001000 (об'єкт) (00000011 об'єкт об'єкт)))"
        rendered, count, errors = MOD.rewrite(source, self.mapping, self.blocked)
        self.assertEqual((count, errors), (3, []))
        self.assertEqual(
            rendered,
            "(визначити ім'я (функція (об'єкт) (тотожне? об'єкт об'єкт)))",
        )

    def test_quoted_w8_head_does_not_block_valid_ukr_rewrite(self):
        # Standalone QUOTE/FUNCTION-QUOTE before a historical bit atom marks
        # DATA, not an executable W8 call or an ambiguous successor.
        source = (
            "('00110111 datum) "
            "(#'00001001 name) "
            "(00001001 f (00001000 (x) (00000011 x x)))"
        )
        updated, count, problems = MOD.rewrite(source, self.mapping, self.blocked)
        self.assertEqual((count, problems), (3, []))
        self.assertEqual(
            updated,
            "('00110111 datum) "
            "(#'00001001 name) "
            "(визначити f (функція (x) (тотожне? x x)))",
        )

    def test_unproved_historical_head_blocks_ukr_rewrite(self):
        projected = self.mapping
        old = "(00001001 f (00001000 () (00110111 fun values)))"
        changed, count, errors = MOD.rewrite(old, projected, self.blocked)
        self.assertEqual(changed, old)
        self.assertEqual(count, 2)
        self.assertTrue(any("00110111" in problem for problem in errors))

    def test_function_genealogy_data_uses_current_ukr_not_legacy_w8_numbers(self):
        # Це перевірка джерела, а НЕ підміна реального запуску SENS.
        # У графі функції — цитовані чинні ідентичності; раніше старі
        # восьмибітні коди без лапок ставали числами D24+.
        import re
        path = "experiments/function-genealogy.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        code = "\\n".join(line for line in source.splitlines()
                          if not line.lstrip().startswith(";"))
        self.assertIsNone(re.search(r"(?<![01])[01]{8}(?![01])", code))
        heads = MOD.executable_call_heads(source, self.guard)
        self.assertIn("визначити", heads)
        self.assertNotIn("00001001", heads)
        for resident in ("(як-є як-є)", "(як-є сполучити)",
                         "(як-є друге)", "(як-є четверте)",
                         "(як-є уніфікувати)", "(як-є застосувати-підстановка)"):
            with self.subTest(resident=resident):
                self.assertIn(resident, code)
        # Раніше два різні SID8 значення вважалися різними функціями.
        # Поточна ратифікація дає одну ідентичність D4:1001 і D6:100111.
        self.assertIn("друге дослід-друге", code)
        self.assertIn("четверте дослід-четверте", code)
        self.assertNotIn("second cadr перший-зразок", code)
        self.assertIn("(однакові? (перше (перше граф)) джерело)", code)

    def test_d7_schema_sha_pin_tracks_owner_ratified_keyboard_v2(self):
        import hashlib
        import json
        schema = json.loads((ROOT / "knowledge/migration-nonprogram-schema-manifest-2026-10-08.json")
                            .read_text(encoding="utf-8"))
        owner = json.loads((ROOT / "knowledge/d7-keyboard-v2-ratified.json")
                           .read_text(encoding="utf-8"))
        entry = next(item for item in schema["entries"]
                     if item["path"] == "contracts/d7-ratification.lisp")
        payload = (ROOT / entry["path"]).read_bytes()
        digest = hashlib.sha1(
            b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
        ).hexdigest()
        self.assertEqual(owner["schema"], "sens.d7.keyboard/v2")
        self.assertEqual(owner["occupancy"], 128)
        self.assertEqual(entry["git_blob_sha1"], digest)
        self.assertEqual(entry["previous_pinned_git_blob_sha1"],
                         "c51ec57ca40ddf585a22ca8cbddab5efb4f11028")
        self.assertIn(b"(status . owner-ratified)", payload)
        self.assertIn(b"knowledge/d7-keyboard-v2-ratified.json", payload)

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
        for old, українська in self.mapping.items():
            self.assertRegex(old, r"^[01]{8}$")
            self.assertTrue(українська)
            self.assertNotRegex(українська, r"^[01]+$",
                                "binary domain word is not a canonical .lisp head")
            self.assertNotEqual(українська, "()",
                                "D3 empty value is not an executable call head")
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
            rewritten, count, empties = MOD.rewrite(source, self.mapping, self.blocked)
            self.assertEqual(rewritten, source)
            self.assertTrue(any("quasiquote/unquote" in empty for empty in empties))

    def test_nested_quoted_data_and_comments_preserved(self):
        old = ";(00000100 ignored)\n(00001001 f (00001000 (x) (00000100 (00000001 00000011) x)))\n"
        new, n, empties = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(n, 4)
        self.assertFalse(empties)
        self.assertIn("(визначити f (функція (x) (сполучити (як-є 00000011) x)))", new)
        self.assertIn(";(00000100 ignored)", new)

    def test_identical_old_and_d8_bytes_never_mean_the_same_function(self):
        # Old SID8:00001001 is DEFINE, whereas current D8:00001001
        # has another resident. Only the dated successor D4 is valid.
        table = (ROOT / "lib/domains/d8.lisp").read_text(encoding="utf-8")
        self.assertIn("(00001001 (ук підмножина?) (укр підмножина?)", table)
        self.assertEqual(self.mapping["00001001"], "визначити")
        self.assertNotEqual(self.mapping["00001001"], "підмножина?")
        source = "(00001001 f (00001000 (x) x))"
        updated, count, problems = MOD.rewrite(source, self.mapping, self.blocked)
        self.assertEqual((count, problems), (2, []))
        self.assertEqual(updated, "(визначити f (функція (x) x))")

    def test_ambiguous_head_blocks_entire_file(self):
        old = "(00001001 f (00001000 () (00110111 fun values)))"
        new, n, empties = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(new, old)
        self.assertEqual(n, 2)
        self.assertTrue(any("00110111" in b for b in empties))

    def test_cond_three_fields_requires_semantic_translation(self):
        old = "(00001001 f (00001000 (x) (00000111 ((00000010 x) 0 1))))"
        new, n, empties = MOD.rewrite(old, self.mapping, self.blocked)
        self.assertEqual(n, 4)
        self.assertFalse(empties)
        findings = self.guard.scan_lisp(new, "lib/f.lisp")
        self.assertIn("COND_NOT_TWO_FIELDS", {f.rule for f in findings})

    def test_migrated_native_executor_contains_no_w8_call_heads(self):
        path = "lib/machine/dispatch/native-first-execute.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        heads = MOD.executable_call_heads(source, self.guard)
        self.assertIn("визначити", heads)
        self.assertIn("функція", heads)
        self.assertFalse(any(MOD.BITS.fullmatch(head) for head in heads))
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["files"][0]["status"], "unchanged")
        self.assertEqual(report["files"][0]["reasons"], [])
        self.assertFalse(report["semantic_admitted"])

    def test_migrated_machine_and_data_sources_are_not_mass_rewritten(self):
        names = {
            "lib/machine/encoding/admitted-iclass-index.lisp",
            "lib/machine/cpu/intel-core-i5-6400-inventory.lisp",
            "lib/machine/dispatch/native-first-execute.lisp",
            "lib/island-math-evidence.lisp",
        }
        census = MOD.run(ROOT, False, names)
        self.assertEqual(census["summary"]["admitted_heads"], 0)
        self.assertEqual(census["summary"]["admitted_files"], 0)
        self.assertEqual(len(census["files"]), len(names))
        for row in census["files"]:
            with self.subTest(path=row["path"]):
                self.assertEqual(row["status"], "unchanged", row)
                self.assertEqual(row["reasons"], [])

    def test_macro_and_machine_sources_are_assessed_not_name_blocked(self):
        paths = {"lib/macro.lisp", "lib/machine/block.lisp"}
        # A file-name list must never suppress source evidence. Genuine
        # parser/semantic findings remain visible in each returned row.
        self.assertFalse(hasattr(MOD, "HOLDS"))
        census = MOD.run(ROOT, False, paths)
        self.assertEqual(census["summary"]["scanned"], 2)
        rows = {row["path"]: row for row in census["files"]}
        self.assertEqual(set(rows), paths)
        for path, row in rows.items():
            with self.subTest(path=path):
                self.assertNotEqual(row["status"], "skipped")
                self.assertNotIn(
                    "filename hold",
                    " ".join(row.get("reasons", [])).lower(),
                )

    def test_selected_census_checks_only_relevant_reviewed_source_pins(self):
        # Real SHA checks stay mandatory for selected inputs. Unrelated
        # reviewed sources cannot stop analysis of lib/macro.lisp.
        from unittest.mock import patch
        selection = {"lib/macro.lisp"}
        loader = MOD.load_nonprogram_classification
        with patch.object(MOD, "load_nonprogram_classification", wraps=loader) as check:
            result = MOD.run(ROOT, False, selection)
        self.assertEqual(result["summary"]["scanned"], 1)
        self.assertEqual(check.call_args.kwargs["selected_paths"], selection)

    def test_live_surface_programs_are_included_in_sid8_migration(self):
        # Стара заборона всього lib/surface/ приховувала чинні DEFINE.
        sources = {"lib/surface/function-signatures.lisp",
                   "lib/surface/uk-acceptance.lisp"}
        report = MOD.run(ROOT, False, sources)
        self.assertEqual({row["path"] for row in report["files"]}, sources)
        for row in report["files"]:
            self.assertEqual(row["status"], "unchanged", row)
            self.assertEqual(row["reasons"], [], row)

        # Історична таблиця зі старими восьмибітними ключами — дані,
        # не виконавча програма і не джерело нової D8-семантики.
        data = MOD.run(ROOT, False, {"lib/surface/semantic-registry.lisp"})
        self.assertEqual(data["summary"]["scanned"], 0)
        self.assertEqual(data["summary"]["admitted_heads"], 0)

    def test_live_function_table_has_no_nonprogram_exemption(self):
        path = "lib/function-table-mechanisms.lisp"
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["scanned"], 1)
        self.assertEqual(report["summary"]["admitted_files"], 0)
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["files"][0]["status"], "unchanged",
                         "Already-Ukrainian DEFINE is current source, not legacy W8")
        self.assertEqual(report["files"][0]["reasons"], [])
        self.assertNotIn("source_git_blob_sha", report["files"][0])

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
            {"unchanged"},
        )
        for path in paths:
            heads = MOD.executable_call_heads(
                (ROOT / path).read_text(encoding="utf-8"), self.guard
            )
            self.assertFalse(any(MOD.BITS.fullmatch(head) for head in heads), path)

    def test_guard_sources_use_current_ukr_d3_d9_without_legacy_source_pin(self):
        cases = {
            "scripts/semantic-authority-guard-enforce.lisp": (
                "читати-всі", "читати-файл", "символ-у-текст", "за-умовою"),
            "knowledge/guard-fact-policy.lisp": (
                "визначити", "функція", "за-умовою", "тотожне?"),
        }
        for path, required in cases.items():
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                heads = MOD.executable_call_heads(source, self.guard)
                for name in required:
                    self.assertIn(name, heads)
                for legacy in ("01001011", "10100110", "10011100",
                               "00000111", "00001001", "00001011"):
                    self.assertNotIn(legacy, heads)
                self.assertEqual(self.guard.scan_lisp(source, path), [])
                report = MOD.run(ROOT, False, {path})
                self.assertEqual(report["summary"]["blocked_files"], 0)
                self.assertEqual(report["files"][0]["status"], "unchanged")
                self.assertEqual(report["files"][0]["reasons"], [])

    def test_guard_reference_uses_ukrainian_heads_without_filename_hold(self):
        path = "knowledge/guard-reference.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        tail = source[source.index("(визначити гвардія-знайти-сценарій"):]
        heads = MOD.executable_call_heads(tail, self.guard)
        for name in ("визначити", "функція", "за-умовою", "тотожне?"):
            self.assertIn(name, heads)
        for old in ("00000010", "00100111", "00000111",
                    "00001001", "00001011", "10011101"):
            self.assertNotIn(old, heads)
        self.assertEqual(self.guard.scan_lisp(tail, path), [])
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["files"][0]["status"], "unchanged")

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
        source = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(self.guard.scan_lisp(source, path), [])
        for current in ("(читати-всі", "(читати-файл", "(символ-у-текст",
                        "(за-умовою", "(тотожне?"):
            self.assertIn(current, source)
        self.assertNotIn("(110101001 (110110111 ", source)
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["files"][0]["status"], "unchanged")

    def test_current_guard_reference_not_blocked_by_historical_cond(self):
        path = "knowledge/guard-reference.lisp"
        source = (ROOT / path).read_text(encoding="utf-8")
        self.assertEqual(self.guard.scan_lisp(source[source.index("(визначити гвардія-знайти-сценарій"):], path), [])
        report = MOD.run(ROOT, False, {path})
        self.assertEqual(report["summary"]["blocked_files"], 0)
        self.assertEqual(report["files"][0]["status"], "unchanged")

    def test_forward_assert_fact_uses_current_ukr_d3_cons(self):
        source = (ROOT / "lib/forward.lisp").read_text(encoding="utf-8")
        self.assertIn("(визначити ствердити-факт!", source)
        self.assertIn("(список (як-є сполучити) факт", source)
        self.assertNotIn("(001 00000100)", source)
        self.assertNotIn("(001 111)", source)
        self.assertEqual(self.guard.scan_lisp(source, "lib/forward.lisp"), [])

        ladder = MOD.verify_full_domain_bitspace(ROOT)
        self.assertEqual(ladder["typed_coordinates"], 2046)
        self.assertEqual(ladder["meaningful_bits"], 18434)
        self.assertEqual(ladder["runtime_admission_claims_added"], 0)

if __name__ == "__main__":
    unittest.main()
