#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_d11_selector_seed.py"
SPEC = importlib.util.spec_from_file_location("check_d11_selector_seed", SCRIPT)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class D11SelectorSeedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = MOD.load_documents(ROOT)

    def changed(self):
        return copy.deepcopy(self.documents)

    def assert_rejected(self, docs, test_id):
        with self.assertRaises(MOD.AuditError) as caught:
            MOD.validate_documents(docs)
        self.assertEqual(caught.exception.test_id, test_id)

    def test_all_512_selectors_are_mathematically_defined_not_direct_opcodes(self):
        report = MOD.validate_documents(self.documents)
        self.assertEqual(report["status"], "MECHANICAL_PASS")
        self.assertEqual(report["semantic_status"], "DERIVED_BY_COMPOSITION")
        self.assertEqual(report["derived_count"], 512)
        self.assertEqual(report["derived_status"], "MATHEMATICALLY_DERIVED_SELECTOR_FUNCTIONS")
        self.assertEqual(self.documents["seed"]["law"]["derived_by_law"], True)
        self.assertEqual(self.documents["seed"]["accounting"]["d11_mathematically_defined_selectors"], 512)
        self.assertEqual(self.documents["seed"]["accounting"]["selector_derived_coordinates"], 512)
        self.assertEqual(self.documents["seed"]["accounting"]["defined_d11_selector_functions_in_math"], 512)
        self.assertEqual(self.documents["seed"]["accounting"]["independently_ratified_selector_primitive_laws"], 0)
        self.assertEqual(self.documents["seed"]["accounting"]["derived_selectors_without_direct_opcode_admission"], 512)
        self.assertEqual(report["selector_parents"], 256)
        self.assertEqual(report["unique_coordinates"], 512)
        self.assertEqual(report["unique_names"], 512)
        self.assertEqual(report["testing_only_rows"], 43)
        self.assertEqual(report["derived_testing_coordinate_collisions"], 0)
        self.assertEqual(report["derived_testing_name_collisions"], 0)
        self.assertEqual(report["callable_admissions_added"], 0)
        self.assertEqual(report["ratified_residents_added"], 0)

    def test_historical_pin_drift_is_reported_after_all_parents_are_revalidated(self):
        report = MOD.validate_documents(self.documents)
        self.assertFalse(report["historical_pin_matches_current"])
        self.assertIn("all 256 derived parents revalidated", report["source_pin_note"])

    def test_current_d11_table_has_512_derived_and_43_legacy_rows_stay_archived(self):
        report = MOD.validate_documents(self.documents)
        self.assertEqual(report["derived_count"], 512)
        self.assertEqual(report["testing_only_rows"], 43)
        self.assertEqual(self.documents["seed"]["accounting"]["new_ratified_residents"], 0)
        self.assertEqual(self.documents["seed"]["accounting"]["callable"], 0)

    def test_rejects_attempt_to_make_derived_a_research_derived_or_new_primitive(self):
        docs = self.changed()
        docs["seed"]["law"]["derived_by_law"] = False
        self.assert_rejected(docs, "DERIVED_LAW")

        docs = self.changed()
        docs["seed"]["law"]["opcode_admission"] = "ALLOW_NEW_DIRECT_OPCODE"
        self.assert_rejected(docs, "OPCODE_ADMISSION")

    def test_rejects_truncated_ten_bit_derived(self):
        docs = self.changed()
        docs["seed"]["rows"][0][0] = docs["seed"]["rows"][0][0][:-1]
        self.assert_rejected(docs, "DERIVED_WIDTH")

    def test_rejects_duplicate_derived_coordinate(self):
        docs = self.changed()
        docs["seed"]["rows"][1][0] = docs["seed"]["rows"][0][0]
        self.assert_rejected(docs, "DERIVED_DUP_COORD")

    def test_rejects_duplicate_derived_name(self):
        docs = self.changed()
        docs["seed"]["rows"][1][1] = docs["seed"]["rows"][0][1]
        self.assert_rejected(docs, "DERIVED_DUP_NAME")

    def test_rejects_d11_projection_drift_in_every_surface(self):
        row = next(line for line in self.documents["d11_table"].splitlines()
                   if line.startswith("  (01100000000 "))
        for column in ("ук", "укр", "san", "en"):
            with self.subTest(column=column):
                docs = self.changed()
                import re
                damaged = re.sub(r"(\(" + column + r"\s+)[^()\s]+",
                                 r"\1wrong-projection", row, count=1)
                self.assertNotEqual(damaged, row)
                docs["d11_table"] = docs["d11_table"].replace(row, damaged, 1)
                self.assert_rejected(docs, "D11_TABLE_PROJECTION")

        docs = self.changed()
        damaged = row.replace("(sym ())", "(sym +)", 1)
        self.assertNotEqual(damaged, row)
        docs["d11_table"] = docs["d11_table"].replace(row, damaged, 1)
        self.assert_rejected(docs, "D11_TABLE_PROJECTION")

    def test_rejects_d11_projection_column_order_and_duplicate(self):
        row = next(line for line in self.documents["d11_table"].splitlines()
                   if line.startswith("  (01100000000 "))
        for damaged in (
            row.replace("(ук ", "(tmp ", 1).replace("(укр ", "(ук ", 1).replace("(tmp ", "(укр ", 1),
            row.replace("(san ", "(uk ", 1),
            row.replace("(sym ())", "(sym ()) (sym ())", 1),
        ):
            with self.subTest(damaged=damaged[:100]):
                self.assertNotEqual(damaged, row)
                docs = self.changed()
                docs["d11_table"] = docs["d11_table"].replace(row, damaged, 1)
                self.assert_rejected(docs, "D11_TABLE_PROJECTION")

    def test_rejects_current_d11_table_coordinate_drift(self):
        docs = self.changed()
        self.assertIn("  (01100000000 (ук ", docs["d11_table"])
        docs["d11_table"] = docs["d11_table"].replace(
            "  (01100000000 (ук ", "  (00000000000 (ук ", 1)
        self.assert_rejected(docs, "D11_TABLE_DERIVATION")

    def test_rejects_current_d11_table_name_drift(self):
        docs = self.changed()
        self.assertIn("(LISP CDAAAAAAAAR)", docs["d11_table"])
        docs["d11_table"] = docs["d11_table"].replace(
            "(LISP CDAAAAAAAAR)", "(LISP WRONGSELECTOR)", 1)
        self.assert_rejected(docs, "D11_TABLE_DERIVATION")


    def test_archived_coordinate_overlap_is_accounted_not_forbidden(self):
        docs = self.changed()
        docs["d11_vocabulary"]["table"][0]["bits"] = docs["seed"]["rows"][0][0]
        self.assert_rejected(docs, "ACCOUNTING")
        docs["seed"]["accounting"]["test_coordinate_collisions"] = 1
        docs["seed"]["accounting"]["coordinates_outside_testing_and_derived_selectors"] += 1
        report = MOD.validate_documents(docs)
        self.assertEqual(report["derived_testing_coordinate_collisions"], 1)

    def test_archived_name_overlap_is_accounted_not_forbidden(self):
        docs = self.changed()
        docs["d11_vocabulary"]["table"][0]["lisp"] = docs["seed"]["rows"][0][1]
        self.assert_rejected(docs, "ACCOUNTING")
        docs["seed"]["accounting"]["test_name_collisions"] = 1
        report = MOD.validate_documents(docs)
        self.assertEqual(report["derived_testing_name_collisions"], 1)

    def test_rejects_wrong_selector_suffix_name(self):
        docs = self.changed()
        bits, name = docs["seed"]["rows"][0]
        docs["seed"]["rows"][0][1] = "NOT-A-SELECTOR-NAME"
        self.assert_rejected(docs, "DERIVED_NAME_DERIVATION")

    def test_rejects_derived_without_a_current_d10_selector_parent(self):
        docs = self.changed()
        bits, name = docs["seed"]["rows"][0]
        docs["seed"]["rows"][0][0] = "11111111111"
        self.assert_rejected(docs, "DERIVED_PARENT")

    def test_rejects_accidental_d11_ratification_or_callability(self):
        docs = self.changed()
        docs["seed"]["status"] = "RATIFIED"
        self.assert_rejected(docs, "NOT_MATHEMATICAL_DERIVATION")

        docs = self.changed()
        docs["seed"]["accounting"]["callable"] = 512
        self.assert_rejected(docs, "ACCOUNTING")

    def test_rejects_missing_child_pair(self):
        docs = self.changed()
        docs["seed"]["rows"].pop()
        self.assert_rejected(docs, "DERIVED_COUNT")


    def test_memory_game_covers_all_512_d11_selectors_and_reports_omissions(self):
        game = (ROOT / "research/zig-codecs/ladder_memory_game.zig").read_text(encoding="utf-8")
        for contract in (
            "pub fn questionOrder",
            "pub fn gradeDomain",
            "questionCount(11)",
            "coordinateCount(11)",
            "result.missing",
            "order.len",
            "0x53454e534c414444",
            "512 унікальних відтворюваних запитань",
            " прогалина, хибна відповідь і повтор",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, game)

    def test_selector_codec_benchmark_is_paired_and_uses_identical_words(self):
        codec = (ROOT / "research/zig-codecs/d11_selector_contest.zig").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/d11-ladder-contest.yml").read_text(encoding="utf-8")
        for contract in (
            "const sample_count: usize = 15",
            "const minimum_sample_ns: u64 = 2_000_000",
            "selector9",
            "dense11",
            "raw16",
            "fn encodeRaw16",
            "fn decodeRaw16",
            "RoundtripMismatch",
            "samples={d}",
            "p50_ns_per_roundtrip={d}",
            "p90_ns_per_roundtrip={d}",
            "alternating=YES",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, codec)
        for contract in (
            "zig test -lc research/zig-codecs/ladder_memory_game.zig",
            "zig test -lc research/zig-codecs/d11_selector_contest.zig",
            "mode=raw16 words=64 bytes=128",
            "mode=selector9 words=512 bytes=576",
            "mode=dense11 words=512 bytes=704",
            "mode=raw16 words=512 bytes=1024",
            "p50_ns_per_roundtrip=",
            "p90_ns_per_roundtrip=",
            "samples=15",
        ):
            with self.subTest(workflow_contract=contract):
                self.assertIn(contract, workflow)

    def test_guard_knowledge_records_d11_game_and_codec_limits(self):
        knowledge = (ROOT / "knowledge/d11/охоронець-знання-драбина-d6.uk.md").read_text(encoding="utf-8")
        for contract in (
            "map / foreach unary",
            "512 математично похідних селекторів",
            "не нові примітиви",
            "зовнішнього кадру",
            "15 зразків",
            "p50/p90",
            "не оцінка семантики SENS",
            "Не оголошувати переможця за одним заміром",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, knowledge)



    def test_d13_candidate_catalog_matches_current_d11_parents_exactly(self):
        import re

        d11_source = (ROOT / "lib/domains/d11.lisp").read_text(encoding="utf-8")
        catalog_path = ROOT / "knowledge/d13/селекторні-кандидати-2048-20261024.lisp"
        catalog = catalog_path.read_text(encoding="utf-8")
        parent_pattern = re.compile(
            r"^\s+\(([01]{11})\s+.*?\(LISP ([^()\s]+)\)", re.MULTILINE
        )
        parents = [
            (bits, name)
            for bits, name in parent_pattern.findall(d11_source)
            if re.fullmatch(r"C[AD]{9}R", name)
        ]
        self.assertEqual(512, len(parents))
        self.assertEqual(list(range(768, 1280)), [int(bits, 2) for bits, _ in parents])
        self.assertEqual(512, len({bits for bits, _ in parents}))
        self.assertEqual(512, len({name for _, name in parents}))

        source_pin = re.search(r'\(parent-source-blob-sha "([0-9a-f]{40})"\)', catalog)
        self.assertIsNotNone(source_pin)
        self.assertEqual(MOD.git_blob_sha1(d11_source.encode("utf-8")), source_pin.group(1))
        self.assertIn("(status research-candidate-not-ratified)", catalog)
        self.assertIn("(runtime-admission NO)", catalog)
        self.assertIn("(opcode-admission NO)", catalog)

        row_pattern = re.compile(
            r"^\s+\(([01]{13}) \(LISP ([^()\s]+)\) \(parent ([01]{11})\) \(suffix ([01]{2})\)\)$",
            re.MULTILINE,
        )
        actual = row_pattern.findall(catalog)
        suffix_letters = {"00": "AA", "01": "AD", "10": "DA", "11": "DD"}
        expected = []
        for parent_bits, parent_name in parents:
            for suffix in ("00", "01", "10", "11"):
                candidate_bits = parent_bits + suffix
                candidate_name = parent_name[:-1] + suffix_letters[suffix] + "R"
                expected.append((candidate_bits, candidate_name, parent_bits, suffix))
        self.assertEqual(expected, actual)

        candidate_bits = [row[0] for row in actual]
        candidate_names = [row[1] for row in actual]
        self.assertEqual(2048, len(actual))
        self.assertEqual(2048, len(set(candidate_bits)))
        self.assertEqual(2048, len(set(candidate_names)))
        self.assertEqual(list(range(3072, 5120)), [int(bits, 2) for bits in candidate_bits])
        self.assertTrue(all(re.fullmatch(r"[01]{13}", bits) for bits in candidate_bits))
        self.assertTrue(all(re.fullmatch(r"C[AD]{11}R", name) for name in candidate_names))
        self.assertFalse((ROOT / "lib/domains/d13.lisp").exists())

        guard_ref = (ROOT / "knowledge/guard-reference.lisp").read_text(encoding="utf-8")
        self.assertIn("research-catalog-exactly-matches-parent-plus-two-bits", guard_ref)
        self.assertIn("research-candidate-not-ratified", guard_ref)



    def test_d11_rust_zig_benchmark_uses_identical_preflight_and_timed_contract(self):
        rust = (ROOT / "benchmarks/native/d11_families.rs").read_text(encoding="utf-8")
        zig = (ROOT / "benchmarks/native/d11_families.zig").read_text(encoding="utf-8")
        runner = (ROOT / "benchmarks/native/run-d11-families.sh").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        for token in (
            "const SAMPLE_COUNT: usize = 15",
            "MIN_SAMPLE_NS",
            "CLOCK_MONOTONIC",
            "D11_FAMILIES_PREFLIGHT impl=rust",
            "D11_FAMILIES_SAMPLE impl=rust",
            "allocations=0",
            "black_box",
        ):
            with self.subTest(layer="rust", token=token):
                self.assertIn(token, rust)
        for token in (
            "const sample_count: usize = 15",
            "minimum_sample_ns",
            "clock_monotonic",
            "D11_FAMILIES_PREFLIGHT impl=zig",
            "D11_FAMILIES_SAMPLE impl=zig",
            "allocations=0",
            "doNotOptimizeAway",
        ):
            with self.subTest(layer="zig", token=token):
                self.assertIn(token, zig)
        for token in (
            "same_workload=YES",
            "same_timed_boundary=YES",
            "reusable_fixed_buffers=YES",
            "timed_allocations=0",
            "alternating_process_order=YES",
            "expected_impl",
            "checksum_value != \"9\"",
            "seen[\"rust\" SUBSEP i]",
            "D11_FAMILIES_SUMMARY",
        ):
            with self.subTest(layer="runner", token=token):
                self.assertIn(token, runner)
        self.assertIn("benchmarks/native/run-d11-families.sh", workflow)



if __name__ == "__main__":
    unittest.main()
