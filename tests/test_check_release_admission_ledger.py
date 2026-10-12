#!/usr/bin/env python3
"""Negative witnesses for the fail-closed release admission-ledger mechanism.

Proves the checker can never admit without every one of F1–F4 well-formed AND an
explicit owner ``ratified=1``, and that the claimed ``typed_word_sha256`` is
verified against the real ``.sens`` bytes.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "check-release-admission-ledger.py"
SPEC = importlib.util.spec_from_file_location("sens_check_release_admission_ledger", PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

REF = "juv4uk/sens@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718:tests/evidence.lisp:1"
DEDUP = "D1-D9@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718=NO-MATCH;D10@f63b46c4eab71c6fd6f3ceea45589b4ef92d2718=NO-MATCH"
REAL_SENS = "tests/fixtures/migration-d1-cond-cohort/branch.sens"


def entry(**over):
    base = {
        "sens": "tests/fixtures/x.sens",
        "typed_word_sha256": "a" * 64,
        "f1_donor_provenance": REF,
        "f2_positive_witness": REF,
        "f2_negative_witness": REF,
        "f3_dedup": DEDUP,
        "f4_t5_execution": REF,
        "ratified": 0,
    }
    base.update(over)
    return base


def ledger(entries):
    return {"schema": MODULE.SCHEMA, "entries": entries}


class FormatTests(unittest.TestCase):
    def check(self, entries):
        return MODULE.validate_ledger(ledger(entries), verify_content=False)

    def test_empty_ledger_admits_nothing(self):
        receipt = self.check([])
        self.assertEqual(receipt["release_admitted"], 0)

    def test_pending_entry_not_admitted(self):
        self.assertEqual(self.check([entry(ratified=0)])["release_admitted"], 0)

    def test_ratified_full_entry_admitted(self):
        receipt = self.check([entry(ratified=1)])
        self.assertEqual(receipt["release_admitted"], 1)
        self.assertEqual(receipt["uk_oracle_verified"], 1)

    def test_unknown_schema_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger({"schema": "other/v9", "entries": []}, verify_content=False)

    def test_bad_provenance_ref_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(f1_donor_provenance="not-a-ref")])

    def test_bad_typed_sha_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(typed_word_sha256="xyz")])

    def test_bad_dedup_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(f3_dedup="D1-D9@abc=NO-MATCH")])

    def test_duplicate_sens_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(), entry()])

    def test_extra_or_missing_field_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(extra="x")])
        with self.assertRaises(MODULE.LedgerBlocked):
            bad = entry()
            del bad["f4_t5_execution"]
            self.check([bad])

    def test_bool_ratified_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            self.check([entry(ratified=True)])


class ContentTests(unittest.TestCase):
    def test_real_fixture_hash_verifies_and_admits(self):
        good = MODULE.content_sha256(ROOT, REAL_SENS)
        receipt = MODULE.validate_ledger(
            ledger([entry(sens=REAL_SENS, typed_word_sha256=good, ratified=1)])
        )
        self.assertEqual(receipt["release_admitted"], 1)

    def test_wrong_content_hash_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(sens=REAL_SENS, typed_word_sha256="b" * 64)]))

    def test_missing_sens_file_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(sens="tests/fixtures/does-not-exist.sens")]))


class CliTests(unittest.TestCase):
    def test_absent_ledger_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(MODULE.main(["--ledger", str(Path(tmp) / "nope.json")]), 2)

    def test_format_only_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            path.write_text(json.dumps(ledger([entry(ratified=1)])), encoding="utf-8")
            self.assertEqual(MODULE.main(["--ledger", str(path), "--no-verify-content"]), 0)


if __name__ == "__main__":
    unittest.main()
