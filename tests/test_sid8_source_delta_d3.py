"""Regression witnesses for fail-closed D3 changes in SID8 source patches."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "scripts" / "check_sid8_source_delta_d3.py"
SPEC = importlib.util.spec_from_file_location("sens_sid8_d3_delta_test", P)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class DeltaD3Tests(unittest.TestCase):
    def test_rejects_old_three_field_cond_rewritten_as_d3(self):
        old = "(00001001 f (00001000 (x) (00000111 ((00000010 x) 0 (00000001 ok)))))"
        new = "(0011 f (0010 (x) (110 ((010 x) 0 (001 ok)))))"
        result = mod.newly_introduced(old, new, "lib/example.lisp")
        self.assertTrue(any(item["rule"] == "COND_NOT_TWO_FIELDS"
                            for item in result["introduced"]))

    def test_rejects_host_truth_inside_new_cond(self):
        old = "(00001001 f (00001000 (x) (00000111 (t t (00000001 x)))))"
        new = "(0011 f (0010 (x) (110 (t (001 x)))))"
        result = mod.newly_introduced(old, new, "lib/example.lisp")
        self.assertTrue(any(item["rule"] == "COND_HOST_TRUTH"
                            for item in result["introduced"]))

    def test_accepts_safe_exact_domain_replacement(self):
        old = "(00001001 f (00001000 (x) (00000001 x)))"
        new = "(0011 f (0010 (x) (001 x)))"
        self.assertFalse(mod.newly_introduced(old, new, "lib/example.lisp")
                         ["introduced"])

    def test_unchanged_old_defect_not_called_a_new_regression(self):
        old = "(110 (T (001 ok)))"
        new = "; documentation preserved\n" + old
        self.assertFalse(mod.newly_introduced(old, new, "lib/example.lisp")
                         ["introduced"])


if __name__ == "__main__":
    unittest.main()
