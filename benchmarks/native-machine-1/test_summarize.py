"""Regression of evidence handling: never report a ratio for a blocked lane."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("summarize.py")
SPEC = importlib.util.spec_from_file_location("native_machine_summarize", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

class EvidenceGuard(unittest.TestCase):
    def check(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "raw.tsv"
            path.write_text("case\tlane\titeration\telapsed_ns\tvalue\tstatus\n" + rows)
            return MOD.summarize(path)

    def test_blocked_native_yields_no_ratio(self):
        data = self.check(
            "car\tinterpreter-source\t0\t100\t2\tPASS\n"
            "car\tnative-admitted-cpu\t-1\t0\t\tBLOCKED:old-COND\n")
        self.assertIsNone(data["ratios"][0]["interpreter_over_native_median"])

    def test_identical_values_allow_ratio(self):
        data = self.check(
            "car\tinterpreter-source\t0\t100\t2\tPASS\n"
            "car\tnative-admitted-cpu\t0\t50\t2\tPASS\n")
        self.assertEqual(data["ratios"][0]["interpreter_over_native_median"], 2)

    def test_parity_mismatch_never_becomes_benchmark(self):
        with self.assertRaises(ValueError):
            self.check(
                "car\tinterpreter-source\t0\t100\t2\tPASS\n"
                "car\tnative-admitted-cpu\t0\t50\t3\tPASS\n")

    def test_negative_and_zero_time_rejected(self):
        with self.assertRaises(ValueError):
            self.check("car\tinterpreter-source\t0\t0\t2\tPASS\n")

if __name__ == "__main__":
    unittest.main()
