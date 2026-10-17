"""Тести для scripts/report_ukr_projection_progress.py (детерміновано, на тимчасовому дереві)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_ukr_projection_progress.py"

_spec = importlib.util.spec_from_file_location("report_ukr_projection_progress", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
sys.modules["report_ukr_projection_progress"] = mod
_spec.loader.exec_module(mod)


class MeasureTests(unittest.TestCase):
    def _tree(self, files: dict[str, str]) -> Path:
        d = Path(tempfile.mkdtemp())
        for name, body in files.items():
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        return d

    def test_counts_pairs_and_same(self):
        d = self._tree({"a.lisp": "\n".join([
            "(x (ук так) (укр так))",
            "(y (ук ні) (укр ні-ні))",
            "(z (ук ок) (укр ок))",
        ])})
        m = mod.measure(d)
        self.assertEqual(m["pairs_total"], 3)
        self.assertEqual(m["pairs_same"], 2)
        self.assertEqual(m["files_with_pairs"], 1)
        self.assertAlmostEqual(m["pairs_pct"], 66.7, places=1)

    def test_ignores_non_lisp_files(self):
        d = self._tree({
            "a.lisp": "(x (ук так) (укр так))",
            "b.txt": "(y (ук ні) (укр ні-ні))",
        })
        m = mod.measure(d)
        self.assertEqual(m["lisp_files"], 1)
        self.assertEqual(m["pairs_total"], 1)

    def test_file_ukrainian_surface_detected_after_stripping(self):
        d = self._tree({
            # кирилиця лише в коментарі та рядку -> код не український
            "a.lisp": '; привіт\n"текст"\n(foo bar)\n',
            # кириличний ідентифікатор у коді -> українська поверхня
            "b.lisp": "(визначити річ)\n",
        })
        m = mod.measure(d)
        self.assertEqual(m["files_ukrainian"], 1)

    def test_deterministic_repeat(self):
        d = self._tree({"a.lisp": "(x (ук а) (укр а))"})
        self.assertEqual(mod.measure(d), mod.measure(d))

    def test_render_contains_both_numbers(self):
        m = {"pairs_same": 1, "pairs_total": 2, "pairs_pct": 50.0,
             "files_with_pairs": 1, "files_ukrainian": 3, "lisp_files": 4,
             "files_pct": 75.0}
        line = mod.render(m)
        self.assertIn("1/2", line)
        self.assertIn("3/4", line)


if __name__ == "__main__":
    unittest.main(verbosity=2)
