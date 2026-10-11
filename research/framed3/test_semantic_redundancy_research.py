"""Незалежні позитивні й негативні свідки; працюють також із Python -O."""
import unittest
from semantic_redundancy_research import (
    Form, Word, definitely_impossible, finite_candidates,
    admitted_research_codes, rank, unrank, words,
)


def f(*items):
    return Form(items)


class SemanticRedundancyProof(unittest.TestCase):
    def test_atom_without_argument_not_a_program(self):
        atom = Word("010")
        self.assertTrue(definitely_impossible(f(atom)))
        self.assertTrue(definitely_impossible(f(f(atom))))
        self.assertEqual(words(f(f(atom))), ("10", "10", "010", "01", "01"))
        self.assertFalse(definitely_impossible(f(atom, Word("0"))))

    def test_quote_data_is_not_an_executable_call(self):
        dead_as_code = f(f(Word("010")))
        quoted = f(Word("001"), dead_as_code)
        self.assertTrue(definitely_impossible(dead_as_code))
        self.assertFalse(definitely_impossible(quoted))
        self.assertFalse(definitely_impossible(dead_as_code, data=True))
        self.assertTrue(definitely_impossible(f(Word("001"))))
        self.assertTrue(definitely_impossible(f(Word("001"), Word("0"), Word("1"))))

    def test_known_fixed_arities_and_evaluated_arguments(self):
        arities = {"001": 1, "010": 1, "011": 1, "100": 1,
                   "101": 2, "111": 2}
        for code, arity in arities.items():
            for count in range(4):
                with self.subTest(code=code, count=count):
                    self.assertEqual(definitely_impossible(
                        f(Word(code), *(Word("0") for _ in range(count)))),
                        count != arity)
        for code in ("010", "011", "100", "101", "111"):
            args = (f(Word("010")),) + (Word("0"),) * (arities[code] - 1)
            self.assertTrue(definitely_impossible(f(Word(code), *args)))

    def test_do_not_prohibit_unproven_dynamic_calls_and_cond_clause_data(self):
        # Dynamic operator could return a callable; do not assert impossibility.
        self.assertFalse(definitely_impossible(f(f(Word("001"), Word("0")))))
        # COND clauses are syntax forms, NOT ordinary calls.
        self.assertFalse(definitely_impossible(f(Word("110"), f(Word("010")))))
        self.assertFalse(definitely_impossible(f(Word("000"))))

    def test_dense_bounded_rank_never_assigns_dead_code(self):
        universe, codes = finite_candidates(), admitted_research_codes()
        self.assertGreater(len(universe) - len(codes), 0)
        self.assertLess(len(codes), len(universe))
        self.assertEqual(len(set(codes)), len(codes))
        for i, node in enumerate(codes):
            self.assertFalse(definitely_impossible(node))
            self.assertEqual(rank(node), i)
            self.assertEqual(unrank(i), node)
        for dead in universe:
            if definitely_impossible(dead):
                with self.assertRaises(ValueError):
                    rank(dead)
        with self.assertRaises(ValueError):
            unrank(len(codes))
        with self.assertRaises(ValueError):
            rank(f(f(Word("010"))))
        self.assertIn(f(Word("001"), f(f(Word("010")))), codes)


if __name__ == "__main__":
    unittest.main()
