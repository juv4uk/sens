"""Сканер похідних: застарілі вигляди та не-канонічні .sens."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "report-derived-drift.py"


class DerivedDriftTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, timeout=280, check=False)

    def test_no_stale_views_in_active_tree(self):
        r = self.run_script("--check")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("вигляд-ЗАСТАРІЛИЙ=0", r.stdout)
        self.assertIn("PASS", r.stdout)

    def test_undecodable_sens_are_counted_with_archive_split(self):
        r = self.run_script()
        self.assertIn("НЕ-ДЕКОДУЄТЬСЯ=439", r.stdout)
        self.assertIn("архівних=108", r.stdout)


if __name__ == "__main__":
    unittest.main()
