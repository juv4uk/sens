"""Adversarial source-era evidence checks: research not selected D10."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "scripts/check_d10_reason_alternate_define_donor_v1.py"
spec = importlib.util.spec_from_file_location("d10_reason_audit", path)
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class D10ReasonAlternateDefine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = audit.read(audit.LEDGER)
        cls.raw = audit.SOURCE.read_bytes()
        cls.inventory = audit.read(audit.INVENTORY)
        cls.state = audit.read(audit.STATE)
        cls.canonical = audit.read(audit.CANONICAL)
        cls.existing = audit.read(audit.RAW_EXISTING)

    def verify(self, *, ledger=None, raw=None, inventory=None, state=None,
               canonical=None, existing=None):
        return audit.verify(
            self.ledger if ledger is None else ledger,
            self.raw if raw is None else raw,
            self.inventory if inventory is None else inventory,
            self.state if state is None else state,
            self.canonical if canonical is None else canonical,
            self.existing if existing is None else existing,
        )

    def test_exact_37_historical_definitions_and_zero_admissions(self):
        result = self.verify()
        self.assertEqual(result["historical_source_defs"], 37)
        self.assertEqual(result["already_selected_names_not_promoted"], 6)
        self.assertEqual(result["needs_behavioral_dedup"], 26)
        self.assertEqual(result["selected_added"], 0)
        self.assertEqual(result["original_executable_t5_migrations"], 0)

    def test_different_source_byte_or_location_rejected(self):
        with self.assertRaisesRegex(ValueError, "source bytes/SHA"):
            self.verify(raw=self.raw + b" ")
        altered = copy.deepcopy(self.ledger)
        altered["rows"][0]["line"] += 1
        with self.assertRaisesRegex(ValueError, "donor mismatch"):
            self.verify(ledger=altered)

    def test_forged_resident_or_coordinate_rejected(self):
        for edit in ({"ratified": True}, {"coordinate": "0000000001"},
                     {"semantic_law_verified": True}, {"head": "1111"}):
            with self.subTest(edit=edit):
                altered = copy.deepcopy(self.ledger)
                altered["rows"][2].update(edit)
                with self.assertRaisesRegex(ValueError, "donor mismatch"):
                    self.verify(ledger=altered)

    def test_promoted_selected_count_and_replaced_canonical_laws_rejected(self):
        state = copy.deepcopy(self.state)
        state["target"]["ratified_residents"] = 1
        with self.assertRaisesRegex(ValueError, "selected D10 accounting"):
            self.verify(state=state)
        canonical = copy.deepcopy(self.canonical)
        canonical["rows"].pop()
        with self.assertRaisesRegex(ValueError, "39 reviewed"):
            self.verify(canonical=canonical)

    def test_selected_duplicate_not_exchanged_for_new_law(self):
        altered = copy.deepcopy(self.ledger)
        selected = next(x for x in altered["rows"]
                        if x["classification"] == "ALREADY_SELECTED_NAME")
        selected["classification"] = "RESEARCH_UNREVIEWED"
        with self.assertRaisesRegex(ValueError, "donor mismatch"):
            self.verify(ledger=altered)


if __name__ == "__main__":
    unittest.main()
