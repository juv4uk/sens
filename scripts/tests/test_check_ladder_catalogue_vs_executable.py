"""Драбина: чекер мусить НАЗИВАТИ незамаплені щаблі, а не мовчати про них."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-ladder-catalogue-vs-executable.py"


class LadderSeparationTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, timeout=60, check=False)

    def test_containment_holds_across_the_ladder(self):
        r = self.run_script("--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PASS", r.stdout)

    def test_unmapped_rungs_are_named_not_silently_skipped(self):
        r = self.run_script()
        # D1-D4, D7, D8, D11 не мають джерела допуску — чекер мусить це сказати.
        for rung in ("D1", "D4", "D7", "D8", "D11"):
            self.assertIn(rung, r.stdout)
        self.assertIn("не замаплено", r.stdout)
        self.assertIn("замаплено 4/11", r.stdout)

    def test_fully_bound_rungs_report_zero_carrier_only(self):
        r = self.run_script()
        # D6 (64/64) і D9 (512/512) — повністю зв'язані.
        for line in r.stdout.splitlines():
            if line.strip().startswith("D6") or line.strip().startswith("D9"):
                self.assertIn("повністю зв'язаний", line)


if __name__ == "__main__":
    unittest.main()
