"""Exhaustive closed-world independent boundary-reconstruction tests."""
import importlib.util
from itertools import product, permutations
from pathlib import Path
import copy
import unittest

MOD = Path(__file__).resolve().parents[1] / "scripts/check_d10_mitchell_version_space.py"
spec = importlib.util.spec_from_file_location("d10_mitchell_model", MOD)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class MitchellVersionSpaceTests(unittest.TestCase):
    def setUp(self):
        self.dom = [["clear", "cloudy"], ["yes", "no"]]
        self.instances = mod.all_instances(mod.canon_domains(self.dom))

    def test_empty_training_is_full_space_and_bounds_are_distinct(self):
        r = mod.version_space(self.dom, [])
        self.assertEqual(r["S"], (None,))
        self.assertEqual(r["G"], (("*", "*"),))
        self.assertEqual(len(r["version_space"]), 10)

    def test_one_positive_exact_specific_boundary(self):
        x = ("clear", "yes")
        r = mod.version_space(self.dom, [(x, True)])
        self.assertEqual(r["S"], (x,))
        self.assertEqual(r["G"], (("*", "*"),))

    def test_negative_creates_multiple_general_boundaries(self):
        r = mod.version_space(self.dom, [(("clear", "yes"), False)])
        self.assertEqual(r["S"], (None,))
        self.assertEqual(set(r["G"]), {("cloudy", "*"), ("*", "no")})

    def test_positive_and_negative_refine_exactly(self):
        r = mod.version_space(self.dom, [(("clear", "yes"), True), (("clear", "no"), False)])
        self.assertEqual(r["S"], (("clear", "yes"),))
        self.assertEqual(r["G"], (("*", "yes"),))

    def test_same_observation_both_labels_is_not_false_or_unknown(self):
        x = ("clear", "yes")
        r = mod.version_space(self.dom, [(x, True), (x, False)])
        self.assertEqual(r["status"], "CONTRADICTORY-OBSERVATIONS")
        self.assertEqual(r["S"], ())
        self.assertEqual(r["G"], ())

    def test_unrepresentable_even_without_direct_contradiction(self):
        # Positive diagonal requires top conjunction but negative off-diagonal rules it out.
        ex = [(('clear','yes'),True),(('cloudy','no'),True),(('clear','no'),False)]
        self.assertEqual(mod.version_space(self.dom, ex)["status"], "NO-CONSISTENT-CONJUNCTION")

    def test_exhaustive_three_way_labels_all_four_observations(self):
        all_h = mod.hyp_set(mod.canon_domains(self.dom))
        for labels in product((None, False, True), repeat=len(self.instances)):
            examples = [(i, lab) for i,lab in zip(self.instances,labels) if lab is not None]
            r = mod.version_space(self.dom, examples)
            independent = {h for h in all_h if all(mod.covers(h,x) == flag for x,flag in examples)}
            self.assertEqual(set(r["version_space"]), independent)
            self.assertEqual(set(mod.reconstructed_from_boundaries(self.dom, r["S"],r["G"])), independent)
            if independent:
                self.assertEqual(r["status"], "OK")
                self.assertTrue(r["S"] and r["G"])
            else:
                self.assertEqual(r["status"], "NO-CONSISTENT-CONJUNCTION")

    def test_order_does_not_change_observed_boundaries(self):
        cases = [(('clear','yes'),True), (('clear','no'),False), (('cloudy','yes'),False)]
        baseline = mod.version_space(self.dom, cases)
        for seq in permutations(cases):
            self.assertEqual(mod.version_space(self.dom, list(seq)), baseline)

    def test_domain_value_order_canonical(self):
        cases = [(('clear','yes'),True), (('cloudy','no'),False)]
        a = mod.version_space(self.dom,cases)
        b = mod.version_space([list(reversed(x)) for x in self.dom],cases)
        self.assertEqual(a,b)

    def test_invalid_labels_and_outside_domain_fail_closed(self):
        for examples in ([(("clear","yes"),1)], [(("alien","yes"),True)], [(('clear','yes'),"yes")]):
            with self.subTest(examples=examples),self.assertRaises(ValueError):
                mod.version_space(self.dom, examples)

    def test_duplicate_domains_and_reserved_symbols_rejected(self):
        for bad in ([['clear','clear'],['yes','no']], [['*','clear'],['yes','no']], [[],['yes']]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                mod.version_space(bad, [])

    def test_d1_no_and_empty_list_not_coerced(self):
        self.assertIsNone(mod.hyp_set(mod.canon_domains(self.dom))[0])
        with self.assertRaises(ValueError):
            mod.version_space(self.dom, [(('clear','no'),[])])


if __name__ == "__main__":
    unittest.main()
