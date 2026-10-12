#!/usr/bin/env python3
"""Negative witnesses for the fail-closed release admission-ledger mechanism.

Proves the checker can never admit without every one of F1–F4 well-formed AND an
explicit owner ``ratified=1``, and that malformed ledgers fail closed.
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


class AdmissionLedgerTests(unittest.TestCase):
    def test_empty_ledger_admits_nothing(self):
        receipt = MODULE.validate_ledger(ledger([]))
        self.assertEqual(receipt["release_admitted"], 0)
        self.assertEqual(receipt["uk_oracle_verified"], 0)

    def test_pending_entry_not_admitted(self):
        receipt = MODULE.validate_ledger(ledger([entry(ratified=0)]))
        self.assertEqual(receipt["release_admitted"], 0)

    def test_ratified_full_entry_admitted(self):
        receipt = MODULE.validate_ledger(ledger([entry(ratified=1)]))
        self.assertEqual(receipt["release_admitted"], 1)
        self.assertEqual(receipt["uk_oracle_verified"], 1)

    def test_unknown_schema_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger({"schema": "other/v9", "entries": []})

    def test_bad_provenance_ref_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(f1_donor_provenance="not-a-ref")]))

    def test_bad_typed_sha_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(typed_word_sha256="xyz")]))

    def test_bad_dedup_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(f3_dedup="D1-D9@abc=NO-MATCH")]))

    def test_duplicate_sens_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(), entry()]))

    def test_extra_or_missing_field_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(extra="x")]))
        with self.assertRaises(MODULE.LedgerBlocked):
            bad = entry()
            del bad["f4_t5_execution"]
            MODULE.validate_ledger(ledger([bad]))

    def test_bool_ratified_blocks(self):
        with self.assertRaises(MODULE.LedgerBlocked):
            MODULE.validate_ledger(ledger([entry(ratified=True)]))

    def test_absent_ledger_exits_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            self.assertEqual(MODULE.main(["--ledger", str(missing)]), 2)

    def test_written_ledger_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            path.write_text(json.dumps(ledger([entry(ratified=1)])), encoding="utf-8")
            self.assertEqual(MODULE.main(["--ledger", str(path)]), 0)


if __name__ == "__main__":
    unittest.main()
