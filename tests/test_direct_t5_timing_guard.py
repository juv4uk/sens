"""Незалежні негативні свідки таймінгового контролю, зокрема python -O."""
import csv
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

GUARD = Path(__file__).resolve().parents[1] / "scripts/check_direct_t5_timing.py"
spec = importlib.util.spec_from_file_location("direct_t5_guard", GUARD)
if spec is None or spec.loader is None:
    raise RuntimeError("не знайдено код перевірки")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DirectT5TimingGuard(unittest.TestCase):
    """Exercise valid evidence and adversarial timing/fixture mutations."""
    def setUp(self):
        """Create isolated CSV and fixture inputs for each test."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        authentic = {
            "quote": bytes.fromhex("638906a1"),
            "atom": bytes.fromhex("643806a1"),
            "cond": bytes.fromhex("67386515bf123b2dc4a9b1a1"),
        }
        for name, rel in module.FIXTURES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = authentic[name]
            path.write_bytes(raw)
        self.csv_path = self.root / "timing.csv"
        self.rows = [
            {"fixture": name, "bytes": str(len(authentic[name])), "forms": "1",
             **{key: "124.50" for key in module.TIMINGS}}
            for name in module.FIXTURES
        ]
        self.write_rows(self.rows)

    def write_rows(self, rows, columns=None):
        """Rewrite the temporary evidence with the requested columns."""
        with self.csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns or module.COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

    def run_guard(self, *, optimized=False):
        """Run the validator in standard Python or optimized mode."""
        return subprocess.run(
            [sys.executable, *(["-O"] if optimized else []), str(GUARD),
             str(self.csv_path), "--root", str(self.root)],
            capture_output=True, text=True, check=False,
        )

    def test_valid_csv_passes_in_both_python_modes(self):
        """The same valid evidence passes normally and under ``-O``."""
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assertEqual(self.run_guard(optimized=optimized).returncode, 0)

    def test_corrupt_or_partial_data_fails_even_with_optimization(self):
        """Truncated, duplicate, mistyped, or missing evidence is rejected."""
        mutations = (
            lambda rows: rows.pop(),
            lambda rows: rows.__setitem__(1, dict(rows[0])),
            lambda rows: rows[0].__setitem__("bytes", "5"),
            lambda rows: rows[0].__setitem__("forms", "0"),
            lambda rows: rows[0].__setitem__(module.TIMINGS[0], "nan"),
            lambda rows: rows[0].__setitem__(module.TIMINGS[1], "inf"),
            lambda rows: rows[0].__setitem__(module.TIMINGS[2], "-5"),
        )
        for index, mutate in enumerate(mutations):
            rows = [dict(row) for row in self.rows]
            mutate(rows)
            self.write_rows(rows)
            with self.subTest(case=index):
                self.assertEqual(self.run_guard(optimized=True).returncode, 2)
        self.write_rows(self.rows)
        (self.root / module.FIXTURES["atom"]).unlink()
        self.assertEqual(self.run_guard(optimized=True).returncode, 2)

    def test_replaced_fixture_same_length_is_rejected_with_optimization(self):
        """A byte mutation cannot pass merely because the file size matches."""
        path = self.root / module.FIXTURES["quote"]
        original = path.read_bytes()
        corrupted = bytes((original[0] ^ 1,)) + original[1:]
        self.assertEqual(len(corrupted), len(original))
        path.write_bytes(corrupted)
        witness = self.run_guard(optimized=True)
        self.assertEqual(witness.returncode, 2)
        self.assertIn("змінилася фізична T5-фікстура", witness.stderr)
        path.write_bytes(original)
        self.assertEqual(self.run_guard(optimized=True).returncode, 0)

    def test_unexpected_csv_columns_fail_closed(self):
        """Unexpected CSV order is rejected under optimized Python."""
        self.write_rows(self.rows, columns=list(reversed(module.COLUMNS)))
        self.assertEqual(self.run_guard(optimized=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
