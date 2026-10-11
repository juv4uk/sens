#!/usr/bin/env python3
"""Регресія H-NIL: доказ береться з чинного поля Contract 11.8."""

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/research-2019-h-nil-corpus.py"
spec = importlib.util.spec_from_file_location("h_nil_current_corpus", SCRIPT)
assert spec is not None and spec.loader is not None
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)

LAW = (
    "Core.D3 000 structural empty is not historical exact-eight-bit 00000000 "
    "and is not PredicateBit 0 or Number zero. "
    "Equal packed numeric zero across domains never collapses those identities."
)


def contract_with_law(law: str) -> str:
    return '(structural-empty-non-alias\n . "' + law + '")\n'


class GroundSeparationContractTests(unittest.TestCase):
    def test_current_ratified_contract(self):
        source = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")
        self.assertTrue(audit.contract_has_ground_separation(source))

    def test_correct_scoped_law(self):
        self.assertTrue(audit.contract_has_ground_separation(contract_with_law(LAW)))

    def test_old_function8_wording_is_not_enough(self):
        self.assertFalse(audit.contract_has_ground_separation(
            "function 00000000 is not the empty-list value; "
            "() is represented as a structural empty value outside the function space"
        ))

    def test_scattered_true_phrases_are_not_one_law(self):
        self.assertFalse(audit.contract_has_ground_separation(
            '(some-other-field . "' + LAW + '")\n'
            '(structural-empty-non-alias . "No normative distinction")\n'
        ))

    def test_commented_out_normative_field_is_not_evidence(self):
        self.assertFalse(audit.contract_has_ground_separation(
            '; ' + contract_with_law(LAW)
        ))

    def test_law_without_d1_disjunction_fails_closed(self):
        self.assertFalse(audit.contract_has_ground_separation(
            contract_with_law(LAW.replace("not PredicateBit 0 or Number zero", "same as PredicateBit 0"))
        ))


    def test_current_ratified_domain_coordinates(self):
        import json
        foundation = json.loads(
            (ROOT / "knowledge/d1-d9-foundation.json").read_text(encoding="utf-8")
        )
        self.assertTrue(audit.foundation_has_ground_separation(foundation))

    def test_wrong_width_or_zero_identity_fails_closed(self):
        self.assertFalse(audit.foundation_has_ground_separation({
            "status": "owner-ratified", "domains": {
                "D3": {"width": 8, "residents": {"000": "EMPTY"}},
                "D8": {"width": 8, "residents": {"00000000": "CODE-CHAR"}},
            }
        }))
        self.assertFalse(audit.foundation_has_ground_separation({
            "status": "owner-ratified", "domains": {
                "D3": {"width": 3, "residents": {"000": "EMPTY"}},
                "D8": {"width": 8, "residents": {"00000000": "NIL"}},
            }
        }))

    def test_missing_pins_cannot_count_as_proof(self):
        self.assertFalse(audit.foundation_has_ground_separation({"status": "owner-ratified"}))
        self.assertFalse(audit.foundation_has_ground_separation({
            "status": "unratified", "domains": {
                "D3": {"width": 3, "residents": {"000": "EMPTY"}},
                "D8": {"width": 8, "residents": {"00000000": "CODE-CHAR"}},
            }
        }))

    def test_d8_coordinate_table_not_executable_source(self):
        self.assertIn(Path("lib/domains/d8.lisp"), audit.METADATA_LISP)
        self.assertNotIn(Path("lib/machine/encoding/x86-64.lisp"), audit.METADATA_LISP)
        heads = audit.call_heads(audit.tokenize_lisp("(00000000 1)"))
        self.assertEqual([h.text for h in heads], ["00000000"])


if __name__ == "__main__":
    unittest.main()
