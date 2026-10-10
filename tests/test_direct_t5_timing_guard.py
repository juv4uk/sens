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
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for rel in module.FIXTURES.values():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(bytes((0x63, 0x89, 0x06, 0xA1)))
        self.csv_path = self.root / "timing.csv"
        self.rows = [
            {"fixture": name, "bytes": "4", "forms": "1",
             **{key: "124.50" for key in module.TIMINGS}}
            for name in module.FIXTURES
        ]
        self.write_rows(self.rows)

    def write_rows(self, rows, columns=None):
        with self.csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns or module.COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

    def run_guard(self, *, optimized=False):
        return subprocess.run(
            [sys.executable, *(["-O"] if optimized else []), str(GUARD),
             str(self.csv_path), "--root", str(self.root)],
            capture_output=True, text=True, check=False,
        )

    def test_valid_csv_passes_in_both_python_modes(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                self.assertEqual(self.run_guard(optimized=optimized).returncode, 0)

    def test_corrupt_or_partial_data_fails_even_with_optimization(self):
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

    def test_unexpected_csv_columns_fail_closed(self):
        self.write_rows(self.rows, columns=list(reversed(module.COLUMNS)))
        self.assertEqual(self.run_guard(optimized=True).returncode, 2)


if __name__ == "__main__":
    unittest.main()
