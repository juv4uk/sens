#!/usr/bin/env python3
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/migration-legacy-top4-successor-audit-2026-10-08.json"

class LegacyTop4SuccessorAudit(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(LEDGER.read_text())

    def test_audit_is_bounded_and_never_authorizes_rewrite(self):
        self.assertEqual(self.data["schema"], "sens-legacy-successor-audit/1")
        entries = self.data["entries"]
        self.assertEqual(
            [entry["legacy_sid8"] for entry in entries],
            ["00100010", "01001011", "00101111", "00111010"],
        )
        for entry in entries:
            self.assertTrue(entry["executable_rewrite"].startswith("BLOCKED-"))
            self.assertEqual(len(entry["legacy_sid8"]), 8)
            self.assertNotEqual(entry["legacy_sid8"], entry["successor_identity"]["bits"])

    def test_current_targets_are_present_in_owner_authority(self):
        d8 = (ROOT / "contracts/d8-ratification.lisp").read_text()
        d9 = (ROOT / "contracts/d9-ratification.lisp").read_text()
        d4 = (ROOT / "contracts/d4-bootstrap-ratification.lisp").read_text()

        self.assertIn('(resident "11110111" "EQUAL"', d8)
        self.assertIn('(resident "110101001" "READ-ALL"', d9)
        self.assertIn('(resident "110011110" "STRING-APPEND"', d9)
        self.assertIn("(D4:1001 CADR)", d4)

    def test_same_legacy_bits_mean_different_current_d8_residents(self):
        d8 = (ROOT / "contracts/d8-ratification.lisp").read_text()
        self.assertIn('(resident "00100010" "SIGNUM"', d8)
        self.assertIn('(resident "01001011" "ABS∘RECIP"', d8)
        self.assertIn('(resident "00101111" "VCONS"', d8)
        self.assertIn('(resident "00111010" "SET-DIFFERENCE"', d8)

    def test_second_projection_is_evidence_driven_not_bit_driven(self):
        tail = (ROOT / "knowledge/d9-registry-tail-v1.json").read_text()
        self.assertIn('"registry_name": "second"', tail)
        self.assertIn('"lower_identity": "D4:1001 CADR"', tail)

if __name__ == "__main__":
    unittest.main()
