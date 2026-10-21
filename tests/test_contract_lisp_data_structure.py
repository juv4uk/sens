#!/usr/bin/env python3
"""Структурне читання актуальних Lisp-даних; НЕ семантичний SENS-оракул."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from check_ukr_callsite_migration import Form, SourceError, atom, parse


def only_form(path: str) -> Form:
    forms = parse((ROOT / path).read_text(encoding="utf-8"))
    if len(forms) != 1 or not isinstance(forms[0], Form):
        raise AssertionError(f"{path}: очікується одна ціла Lisp-форма")
    return forms[0]


def head(node: object) -> str | None:
    return atom(node.values[0]) if isinstance(node, Form) and node.values else None


class ContractLispDataStructure(unittest.TestCase):
    def test_historical_rows_stay_inside_rows_not_in_support_or_rules(self):
        form = only_form("contracts/core1-historical-sid-map.lisp")
        self.assertEqual(head(form), "core1-historical-sid-map/1")
        groups = [head(v) for v in form.values[1:]]
        self.assertEqual(
            groups,
            ["authority", "rows", "historical-support-without-my-lisp-sid", "rules"],
        )
        rows = form.values[2]
        self.assertGreaterEqual(len(rows.values) - 1, 40)
        self.assertTrue(all(head(row) == "row" for row in rows.values[1:]))
        self.assertEqual(head(form.values[3]), "historical-support-without-my-lisp-sid")

    def test_unification_contains_both_outcomes_in_one_lisp_contract(self):
        form = only_form("contracts/unification-outcome-contract.lisp")
        self.assertEqual(head(form), "unification-outcome-contract/1")
        self.assertEqual(len(form.values), 4, "контракт і три групи даних")
        laws = form.values[2:]
        self.assertTrue(all(isinstance(v, Form) and len(v.values) >= 1 for v in laws))
        self.assertTrue(all(head(v.values[0]) == "law" for v in laws))
        self.assertEqual(
            [atom(v.values[0].values[2]) for v in laws],
            [
                "empty-substitution-is-success-data",
                "established-unification-failure-is-not-canon-zero",
            ],
        )

    def test_canon_candidates_retain_fields_within_their_own_forms(self):
        form = only_form("knowledge/canon-sculpt-audit.lisp")
        self.assertEqual(head(form), "canon-sculpt-audit")
        candidates = [v for v in form.values[1:] if head(v) == "candidate"]
        self.assertEqual(len(candidates), 8)
        for candidate in candidates:
            with self.subTest(candidate=repr(candidate.values[1])):
                labels = [head(field) for field in candidate.values[1:]]
                for required in (
                    "identity", "category", "observable-laws",
                    "classification", "falsification-question",
                ):
                    self.assertIn(required, labels)
        self.assertEqual(
            [head(v) for v in form.values[-3:]],
            ["audit-law", "audit-law", "audit-law"],
        )

    def test_research_canon_audit_retains_eight_candidates_and_four_laws(self):
        form = only_form("docs/research/canon-sculpt-audit.lisp")
        self.assertEqual(head(form), "canon-sculpt-audit")
        candidates = [v for v in form.values[1:] if head(v) == "candidate"]
        self.assertEqual(len(candidates), 8)
        self.assertTrue(all("identity" in [head(field) for field in v.values[1:]]
                            for v in candidates))
        self.assertEqual(len([v for v in form.values[1:] if head(v) == "audit-law"]), 4)

    def test_structural_hypotheses_keep_obstruction_and_claim(self):
        form = only_form("docs/research/canon-sculpt-structural-basis.lisp")
        self.assertEqual(head(form), "canon-sculpt-structural-basis")
        hypotheses = [v for v in form.values[1:] if head(v) == "hypothesis"]
        self.assertEqual(len(hypotheses), 5)
        for hypothesis in hypotheses:
            fields = [head(v) for v in hypothesis.values[1:]]
            self.assertIn("candidate", fields)
            self.assertIn("claim-under-test", fields)
        self.assertEqual(head(form.values[-1]), "falsification-plan")

    def test_old_parenthesis_defects_are_actual_parser_failures(self):
        for name, original, damaged in (
            (
                "contracts/core1-historical-sid-map.lisp",
                "(row 11110110 divide DIVIDE lisp15-1962 direct admitted))",
                "(row 11110110 divide DIVIDE lisp15-1962 direct admitted)",
            ),
            (
                "contracts/unification-outcome-contract.lisp",
                "(not-equal . ()))",
                "(not-equal . ())))",
            ),
            (
                "knowledge/canon-sculpt-audit.lisp",
                "(identity CANON_EMPTY_LIST)\n    (surface ())",
                "(identity CANON_EMPTY_LIST)\n    (surface ()))",
            ),
            (
                "docs/research/canon-sculpt-audit.lisp",
                'not sculpture.")',
                'not sculpture."))',
            ),
            (
                "docs/research/canon-sculpt-structural-basis.lisp",
                'lower than atom.")',
                'lower than atom."))',
            ),
        ):
            with self.subTest(name=name):
                source = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn(original, source)
                with self.assertRaises(SourceError):
                    parse(source.replace(original, damaged, 1))


if __name__ == "__main__":
    unittest.main()
