"""Непрозорі артефакти: 46 *-law.sens без читаного .lisp-джерела."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "report-opaque-law-artifacts.py"


class OpaqueLawTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, timeout=60, check=False)

    def test_the_opaque_count_is_measured(self):
        r = self.run_script("--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("*-law.sens=119", r.stdout)
        self.assertIn("НЕПРОЗОРИХ=46", r.stdout)

    def test_a_known_opaque_artifact_is_named(self):
        r = self.run_script()
        self.assertIn("core-sentinel-null", r.stdout)  # один із 4 рядків ledger'а

    def test_filling_pointers_blindly_is_forbidden(self):
        r = self.run_script("--check")
        self.assertIn("ЗАБОРОНЕНО", r.stdout)


if __name__ == "__main__":
    unittest.main()
