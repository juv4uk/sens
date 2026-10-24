"""D10: чекер розділення каталогу й виконуваних має бути fail-closed."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check-d10-catalogue-vs-executable.py"


class D10SeparationTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True, timeout=60, check=False)

    def test_tree_separates_catalogue_from_executable(self):
        result = self.run_script("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)
        self.assertIn("каталог=1024", result.stdout)

    def test_ledger_has_exactly_1024_rows(self):
        ledger = ROOT / "knowledge/d10-catalogue-vs-executable.tsv"
        rows = [l for l in ledger.read_text(encoding="utf-8").splitlines()
                if l and not l.startswith("#")]
        self.assertEqual(len(rows), 1024)
        admitted = [l for l in rows if l.split("\t")[1] == "так"]
        carrier = [l for l in rows if l.split("\t")[1] == "ні"]
        self.assertEqual(len(admitted) + len(carrier), 1024)
        # Ратифікація цілого словника НЕ є допуском: виконуваних МЕНШЕ за каталог.
        self.assertLess(len(admitted), 1024)


if __name__ == "__main__":
    unittest.main()
