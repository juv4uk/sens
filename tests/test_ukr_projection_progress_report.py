"""Тести для scripts/report_ukr_projection_progress.py.

Покривають: відкидання коментарів (і збереження рядків), підрахунок пар
((), лапки, голий токен), файлову метрику, рендер, CLI-контракт (коди виходу,
--json, --list, --no-annotation), детермінованість і крайові випадки.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
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


class TempTree(unittest.TestCase):
    """База: тимчасове дерево, яке гарантовано прибирається."""

    def tree(self, files: dict[str, str]) -> Path:
        d = Path(tempfile.mkdtemp(prefix="ukr-proj-"))
        self.addCleanup(lambda: __import__("shutil").rmtree(d, ignore_errors=True))
        for name, body in files.items():
            p = d / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        return d


class StripTests(unittest.TestCase):
    def test_strip_comments_removes_line_comment(self):
        stripped = mod.strip_comments("a ; comment\nb")
        self.assertNotIn("comment", stripped)
        self.assertEqual(stripped.split(), ["a", "b"])

    def test_strip_comments_keeps_semicolon_inside_string(self):
        self.assertEqual(mod.strip_comments('(x "a;b")').strip(), '(x "a;b")')

    def test_strip_comments_keeps_escaped_quote_in_string(self):
        self.assertEqual(mod.strip_comments(r'(x "a\";b")').strip(), r'(x "a\";b")')

    def test_strip_comments_and_strings_removes_string(self):
        self.assertEqual(mod.strip_comments_and_strings('(x "привіт" y)').split(), ["(x", "y)"])

    def test_strip_comments_and_strings_handles_escapes(self):
        self.assertEqual(mod.strip_comments_and_strings(r'"a\"b"').strip(), "")


class ScannerTests(unittest.TestCase):
    def test_read_token_forms(self):
        self.assertEqual(mod.read_token("  ()", 0), ("()", 4))
        self.assertEqual(mod.read_token(' "к"', 0), ('"к"', 4))
        self.assertEqual(mod.read_token("  так)", 0), ("так", 5))
        self.assertEqual(mod.read_token("   ", 0), (None, 3))

    def test_iter_pairs_simple(self):
        self.assertEqual(list(mod.iter_pairs("(x (ук так) (укр ні))")), [("так", "ні")])

    def test_iter_pairs_quoted_values(self):
        self.assertEqual(list(mod.iter_pairs('(x (ук "к") (укр "ґ"))')), [('"к"', '"ґ"')])

    def test_iter_pairs_skips_comment(self):
        self.assertEqual(list(mod.iter_pairs("; (ук а) (укр б)\n(x (ук в) (укр в))")),
                         [("в", "в")])

    def test_iter_pairs_skips_pairs_inside_a_string(self):
        self.assertEqual(list(mod.iter_pairs('(x "(ук так) (укр ні)")')), [])

    def test_iter_pairs_requires_ukr_partner(self):
        self.assertEqual(list(mod.iter_pairs("(x (ук так) (san на)")), [])

    def test_iter_pairs_handles_empty_forms(self):
        self.assertEqual(list(mod.iter_pairs("(x (ук ()) (укр ()))")), [("()", "()")])

    def test_iter_pairs_keeps_apostrophe_inside_value(self):
        # регресія: апостроф усередині значення (зв'язати) не має рвати токен
        self.assertEqual(list(mod.iter_pairs("(x (ук зв'язати) (укр зв'язати))")),
                         [("зв'язати", "зв'язати")])


class PairCountingTests(TempTree):
    def test_counts_same_and_different(self):
        d = self.tree({"a.lisp": "\n".join([
            "(x (ук так) (укр так))",
            "(y (ук ні) (укр ні-ні))",
            "(z (ук ок) (укр ок))",
        ])})
        p = mod.measure(d)
        self.assertEqual(p.pairs_total, 3)
        self.assertEqual(p.pairs_same, 2)
        self.assertEqual(p.pairs_pending, 1)

    def test_pairs_in_comments_are_ignored(self):
        d = self.tree({"a.lisp": "\n".join([
            "; (ук так) (укр ні-ні) -- лише коментар",
            "(x (ук так) (укр так))",
        ])})
        p = mod.measure(d)
        self.assertEqual(p.pairs_total, 1)
        self.assertEqual(p.pairs_same, 1)

    def test_pairs_in_strings_are_ignored(self):
        d = self.tree({"a.lisp": '(x "(ук так) (укр ні-ні)")\n'})
        p = mod.measure(d)
        self.assertEqual(p.pairs_total, 0)

    def test_empty_and_quoted_pairs(self):
        d = self.tree({"a.lisp": "\n".join([
            '(x (ук ()) (укр ()))',      # обидві порожні -> збіг
            '(y (ук "к") (укр "к"))',     # лапки -> збіг
            '(z (ук "к") (укр "ґ"))',     # лапки, різні -> розбіг
        ])})
        p = mod.measure(d)
        self.assertEqual((p.pairs_total, p.pairs_same), (3, 2))

    def test_norm_unquotes(self):
        self.assertEqual(mod._norm('"к"'), "к")
        self.assertEqual(mod._norm("()"), "()")
        self.assertEqual(mod._norm("ґ"), "ґ")


class FileMetricTests(TempTree):
    def test_cyrillic_only_in_comment_or_string_is_not_ukrainian(self):
        d = self.tree({"a.lisp": '; привіт\n"текст"\n(foo bar)\n'})
        self.assertEqual(mod.measure(d).files_ukrainian, 0)

    def test_cyrillic_identifier_is_ukrainian(self):
        d = self.tree({"b.lisp": "(визначити річ)\n"})
        self.assertEqual(mod.measure(d).files_ukrainian, 1)

    def test_non_lisp_files_ignored(self):
        d = self.tree({"a.lisp": "(x (ук так) (укр так))", "b.txt": "(y (ук ні) (укр ні-ні))"})
        p = mod.measure(d)
        self.assertEqual(p.lisp_files, 1)
        self.assertEqual(p.pairs_total, 1)

    def test_nested_directories_are_walked(self):
        d = self.tree({"deep/er/a.lisp": "(визначити річ)"})
        self.assertEqual(mod.measure(d).lisp_files, 1)

    def test_empty_tree(self):
        d = self.tree({})
        p = mod.measure(d)
        self.assertEqual(p.lisp_files, 0)
        self.assertEqual(p.pairs_pct, 0.0)
        self.assertEqual(p.files_pct, 0.0)


class ProgressTests(unittest.TestCase):
    def test_percentages_and_pending(self):
        p = mod.Progress(lisp_files=4, files_with_pairs=2, pairs_total=8,
                         pairs_same=6, files_ukrainian=3)
        self.assertEqual(p.pairs_pct, 75.0)
        self.assertEqual(p.files_pct, 75.0)
        self.assertEqual(p.pairs_pending, 2)

    def test_render_has_both_numbers(self):
        line = mod.render(mod.Progress(lisp_files=4, files_with_pairs=1, pairs_total=2,
                                       pairs_same=1, files_ukrainian=3))
        self.assertIn("1/2", line)
        self.assertIn("3/4", line)

    def test_to_dict_has_derived_fields(self):
        d = mod.Progress(lisp_files=2, pairs_total=2, pairs_same=1).to_dict()
        self.assertEqual(d["pairs_pct"], 50.0)
        self.assertEqual(d["pairs_pending"], 1)
        self.assertNotIn("files", d)


class CliTests(TempTree):
    def _run(self, argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mod.main(argv)
        return rc, buf.getvalue()

    def test_exit_0_when_threshold_met(self):
        d = self.tree({"a.lisp": "(x (ук так) (укр так))"})
        rc, out = self._run(["--root", str(d), "--min-pairs-pct", "100"])
        self.assertEqual(rc, 0)
        self.assertIn("100.0%", out)

    def test_exit_1_when_below_threshold_and_names_remainder(self):
        d = self.tree({"a.lisp": "(x (ук ні) (укр ні-ні))"})
        rc, out = self._run(["--root", str(d), "--min-pairs-pct", "100"])
        self.assertEqual(rc, 1)
        self.assertIn("НЕ ЗАВЕРШЕНА", out)
        self.assertIn("лишилось 1 пар", out)

    def test_exit_2_on_bad_root(self):
        rc, _ = self._run(["--root", "/no/such/dir/xyz"])
        self.assertEqual(rc, 2)

    def test_annotation_present_by_default_and_suppressed(self):
        d = self.tree({"a.lisp": "(x (ук так) (укр так))"})
        _, out_on = self._run(["--root", str(d)])
        _, out_off = self._run(["--root", str(d), "--no-annotation"])
        self.assertIn("::error::", out_on)
        self.assertNotIn("::error::", out_off)

    def test_json_report_written(self):
        d = self.tree({"a.lisp": "(x (ук ні) (укр ні-ні))"})
        out_json = d / "report.json"
        rc, _ = self._run(["--root", str(d), "--json", str(out_json)])
        self.assertEqual(rc, 0)
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        self.assertEqual(payload["pairs_total"], 1)
        self.assertEqual(payload["pairs_pending"], 1)
        self.assertEqual(payload["pending_files"][0]["pending"], 1)

    def test_list_and_top(self):
        d = self.tree({
            "a.lisp": "(x (ук ні) (укр ні-ні))",
            "b.lisp": "\n".join(["(y (ук ні) (укр ні-ні))", "(z (ук ок) (укр ок-ок))"]),
        })
        rc, out = self._run(["--root", str(d), "--list", "--top", "1"])
        self.assertEqual(rc, 0)
        self.assertIn("Непереведених файлів: 2", out)
        self.assertIn("… ще 1", out)


class DeterminismTests(TempTree):
    def test_repeat_is_identical(self):
        d = self.tree({"a.lisp": "(x (ук а) (укр а))", "b/c.lisp": "(визначити річ)"})
        self.assertEqual(mod.measure(d).to_dict(), mod.measure(d).to_dict())

    def test_real_repo_smoke(self):
        """Скрипт має відпрацювати на справжньому репо й дати узгоджені числа."""
        p = mod.measure(ROOT)
        self.assertGreater(p.lisp_files, 100)
        self.assertLessEqual(p.pairs_same, p.pairs_total)
        self.assertGreaterEqual(p.pairs_pct, 0.0)
        self.assertLessEqual(p.pairs_pct, 100.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
