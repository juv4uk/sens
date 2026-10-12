"""Domain-ladder D3 source-delta regressions; no historical SID8 fixtures."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "scripts" / "check_domain_source_delta_d3.py"
SPEC = importlib.util.spec_from_file_location("sens_domain_d3_delta_test", P)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class DeltaD3Tests(unittest.TestCase):
    def test_rejects_new_three_field_cond(self):
        old = "(0011 f (0010 (x) (110 ((010 x) (001 ok)))))"
        new = "(0011 f (0010 (x) (110 ((010 x) 0 (001 ok)))))"
        result = mod.newly_introduced(old, new, "lib/example.lisp")
        self.assertTrue(any(item["rule"] == "COND_NOT_TWO_FIELDS"
                            for item in result["introduced"]))

    def test_rejects_host_truth_inside_new_cond(self):
        old = "(0011 f (0010 (x) (110 ((010 x) (001 x)))))"
        new = "(0011 f (0010 (x) (110 (t (001 x)))))"
        result = mod.newly_introduced(old, new, "lib/example.lisp")
        self.assertTrue(any(item["rule"] == "COND_HOST_TRUTH"
                            for item in result["introduced"]))

    def test_accepts_unmodified_correct_domain_form(self):
        source = "(0011 f (0010 (x) (001 x)))"
        self.assertFalse(mod.newly_introduced(source, source, "lib/example.lisp")["introduced"])

    def test_unchanged_defect_not_new_regression(self):
        old = "(110 (T (001 ok)))"
        new = "; documentation preserved\n" + old
        self.assertFalse(mod.newly_introduced(old, new, "lib/example.lisp")["introduced"])


if __name__ == "__main__":
    unittest.main()
