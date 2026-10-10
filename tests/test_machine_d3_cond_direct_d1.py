#!/usr/bin/env python3
"""Narrow x86 D5 subtraction guard migration: preserve exact D1 predicate."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/cond-modernize.py"
SOURCE = ROOT / "lib/machine/lowering/semantic-x86-64.lisp"
CAPABILITY = ROOT / "lib/machine/capability-axis.lisp"
spec = importlib.util.spec_from_file_location("machine_d3_cond_inventory", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def descend(form):
    if form.opaque:
        return
    yield form
    for child in form.children:
        yield from descend(child)


class ExactD1MachineDifferenceGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.roots = mod.parse(cls.source)
        cls.definition = next(
            (root for root in cls.roots
             if mod.head(root) == "00001001"
             and len(root.children) > 1
             and root.children[1].atom == "x86-current-d5-difference-u64-safe?"),
            None,
        )

    def test_d5_subtract_guard_passes_exact_d1_comparison_without_rematching(self):
        self.assertIsNotNone(self.definition)
        direct = []
        for form in descend(self.definition):
            if mod.head(form) != "00000111":
                continue
            for clause in form.children[1:]:
                self.assertEqual(
                    len(clause.children), 2,
                    f"three-part machine COND at line {clause.line}",
                )
                if mod.head(clause.children[1]) == "00011110":
                    direct.append(clause.children[1])
        self.assertEqual(len(direct), 1, "one D1 >= comparison must flow directly")
        self.assertEqual(
            [child.atom for child in direct[0].children],
            ["00011110", "left", "right"],
        )

    def test_machine_lowering_has_no_active_three_part_cond(self):
        found, _ = mod.inspect(self.source)
        self.assertEqual(
            found, [],
            f"unmigrated three-part COND: {[(x.line, x.reason) for x in found]}",
        )

    def test_domain_machine_capability_lookup_uses_only_d1_two_field_cond(self):
        text = CAPABILITY.read_text(encoding="utf-8")
        findings, forms = mod.inspect(text)
        self.assertEqual(findings, [], "machine capability axis must contain no old three-field COND")
        names = {
            "machine-capability-find-domain-row",
            "machine-capabilities-for-domain",
            "machine-capability-find-row",
            "machine-target-witness-status",
        }
        definitions = [
            root for root in forms
            if mod.head(root) == "00001001"
            and len(root.children) > 1 and root.children[1].atom in names
        ]
        self.assertEqual(len(definitions), 4)
        # Width, bit payload and symbolic target keys are atom-only D3 EQ.
        # Deep EQUAL is not an admitted comparison authority here.
        eq_heads = [
            form for definition in definitions for form in descend(definition)
            if mod.head(form) == "00000011"
        ]
        old_equal = [
            form for definition in definitions for form in descend(definition)
            if mod.head(form) == "00100010"
        ]
        self.assertEqual(len(eq_heads), 3)
        self.assertEqual(old_equal, [])
        number_of_clauses = 0
        for definition in definitions:
            for form in descend(definition):
                if mod.head(form) != "00000111":
                    continue
                for clause in form.children[1:]:
                    self.assertEqual(len(clause.children), 2, f"three-field at {clause.line}")
                    test = clause.children[0]
                    self.assertNotEqual(test.atom, "t", "host truthiness must not select branches")
                    number_of_clauses += 1
        self.assertGreaterEqual(number_of_clauses, 10)
        # Preserve the no-row result as structural empty, not D1:0.
        self.assertIn("((00000010 rows) (00000001 ()))", text)
        self.assertIn("((00000010 row) (00000001 ()))", text)

    def test_legacy_three_part_comparison_is_still_detected_not_accepted(self):
        historical = (
            "(00000111 "
            "((00011110 left right) 1 t) "
            "((00011110 left right) 0 (00000001 ())))"
        )
        found, _ = mod.inspect(historical)
        self.assertEqual(len(found), 2)
        self.assertTrue(all(item.status == "HOLD" for item in found))


if __name__ == "__main__":
    unittest.main()
