import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_d10_maling_symbolic_differentiation",
    ROOT / "scripts/check_d10_maling_symbolic_differentiation.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MalingDifferentiationLaw(unittest.TestCase):
    def test_constant_and_variable_rules(self):
        self.assertEqual(MODULE.derivative(MODULE.const(7), "x"), MODULE.const(0))
        self.assertEqual(MODULE.derivative(MODULE.var("x"), "x"), MODULE.const(1))
        self.assertEqual(MODULE.derivative(MODULE.var("y"), "x"), MODULE.const(0))

    def test_sum_rule_is_structural_and_unsimplified(self):
        expr = MODULE.add(MODULE.var("x"), MODULE.var("y"))
        self.assertEqual(
            MODULE.derivative(expr, "x"),
            MODULE.add(MODULE.const(1), MODULE.const(0)),
        )

    def test_product_rule_preserves_original_children_and_order(self):
        expr = MODULE.mul(MODULE.var("x"), MODULE.var("x"))
        self.assertEqual(
            MODULE.derivative(expr, "x"),
            MODULE.add(
                MODULE.mul(MODULE.const(1), MODULE.var("x")),
                MODULE.mul(MODULE.var("x"), MODULE.const(1)),
            ),
        )

    def test_input_not_mutated(self):
        expr = MODULE.mul(MODULE.add(MODULE.var("x"), MODULE.const(2)), MODULE.var("y"))
        before = copy.deepcopy(expr)
        MODULE.derivative(expr, "x")
        self.assertEqual(expr, before)

    def test_malformed_shapes_and_types_rejected(self):
        bad_inputs = [
            {"kind": "const", "value": True},
            {"kind": "var", "name": ""},
            {"kind": "add", "left": MODULE.var("x")},
            {"kind": "sub", "left": MODULE.var("x"), "right": MODULE.var("y")},
        ]
        for bad in bad_inputs:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    MODULE.derivative(bad, "x")
        with self.assertRaises(ValueError):
            MODULE.derivative(MODULE.var("x"), "")

    def test_cyclic_host_object_rejected(self):
        expr = {"kind": "add"}
        expr["left"] = expr
        expr["right"] = MODULE.const(1)
        with self.assertRaises(ValueError):
            MODULE.derivative(expr, "x")

    def test_all_small_expression_trees_match_independent_coefficient_oracle(self):
        expressions = MODULE.exhaustive_small_expressions(2)
        self.assertEqual(len(expressions), 6055)
        for expr in expressions:
            for target in ("x", "y"):
                with self.subTest(expr=expr, target=target):
                    MODULE.assert_derivative_law(expr, target)

    def test_seeded_deeper_expressions_match_independent_coefficient_oracle(self):
        import random
        rng = random.Random(1959)
        atoms = [MODULE.const(-3), MODULE.const(-1), MODULE.const(0),
                 MODULE.const(2), MODULE.var("x"), MODULE.var("y")]

        def make_expr(depth):
            if depth <= 0 or rng.random() < 0.28:
                return copy.deepcopy(rng.choice(atoms))
            a, b = make_expr(depth - 1), make_expr(depth - 1)
            return MODULE.add(a, b) if rng.randrange(2) == 0 else MODULE.mul(a, b)

        for _ in range(750):
            expr = make_expr(5)
            for target in ("x", "y"):
                MODULE.assert_derivative_law(expr, target)


if __name__ == "__main__":
    unittest.main()
