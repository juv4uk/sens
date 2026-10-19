"""Поведінкові перевірки єдиної файлової метрики української розкладки.

На відміну від звіту викличних голів, перевіряємо кожен символ повного файла,
зокрема коментарі, рядкові дані та файли історичних каталогів.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_ukr_projection_progress.py"
spec = importlib.util.spec_from_file_location("report_ukr_projection_progress", SCRIPT)
assert spec is not None and spec.loader is not None
report = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = report
spec.loader.exec_module(report)


class FileTree(unittest.TestCase):
    def tree(self, files: dict[str, str | bytes]) -> Path:
        root = Path(tempfile.mkdtemp(prefix="sens-ukr-files-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        for name, value in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(value, bytes):
                path.write_bytes(value)
            else:
                path.write_text(value, encoding="utf-8")
        return root

    def cli(self, *args: str) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = report.main(list(args))
        return code, output.getvalue()


class WholeFileMetricTests(FileTree):
    def test_every_character_in_comments_and_strings_is_checked(self):
        root = self.tree({
            "lib/повністю.lisp": '(визначити річ "текст")\n; Примітка\n',
            "lib/також.lisp": "(визначити сума (додати 12 30))\n",
            "lib/коментар.lisp": "(визначити річ 1)\n; TODO\n",
            "lib/рядок.lisp": '(визначити річ "English")\n',
            "lib/код.lisp": "(визначити legacy 1)\n",
            "research/архів.lisp": "; Old version\n",
            "not-lisp.txt": "English",
        })
        result = report.measure(root)
        self.assertEqual(result.total_lisp_files, 6)
        self.assertEqual(result.full_ukr_files, 2)
        self.assertEqual(result.percentage, 33.3)
        self.assertEqual(len(result.unfinished), 4)
        self.assertEqual({r.path for r in result.unfinished}, {
            "lib/коментар.lisp", "lib/рядок.lisp",
            "lib/код.lisp", "research/архів.lisp",
        })
        self.assertEqual(
            report.render(result),
            "УКР-ПРОЄКЦІЯ .lisp: повністю українські файли 2/6 (33.3%)",
        )

    def test_english_comment_removal_really_increments_the_numerator(self):
        root = self.tree({"lib/завдання.lisp": "(визначити річ 1)\n; TODO\n"})
        self.assertEqual(report.measure(root).full_ukr_files, 0)
        (root / "lib/завдання.lisp").write_text(
            "(визначити річ 1)\n; Виконано\n", encoding="utf-8"
        )
        self.assertEqual(report.measure(root).full_ukr_files, 1)

    def test_strings_and_nested_comments_are_not_skipped(self):
        root = self.tree({
            "lib/блок.lisp": "(визначити річ 1)\n#| англійське TODO |#\n",
            "lib/рядок.lisp": '(визначити річ "привіт old")',
            "lib/український.lisp": '(визначити річ "привіт; друг")',
        })
        state = report.measure(root)
        self.assertEqual(state.full_ukr_files, 1)
        self.assertIn("lib/блок.lisp", [x.path for x in state.unfinished])
        self.assertIn("lib/рядок.lisp", [x.path for x in state.unfinished])

    def test_special_unavailable_symbols_and_ukrainian_apostrophe(self):
        root = self.tree({
            "дозволено.lisp": "(визначити ім'я 123)\t; Ґрунт, №1 і ₴20\r\n",
            "типографіка.lisp": "(визначити імʼя 1)\n",
            "значок.lisp": "; тест 🙂\n",
            "машинне.lisp": "(визначити назва #d1:1)\n",
        })
        result = report.measure(root)
        self.assertEqual(result.full_ukr_files, 1)
        reasons = {item.path: item.reason for item in result.unfinished}
        self.assertIn("U+02BC", reasons["типографіка.lisp"])
        self.assertIn("U+1F642", reasons["значок.lisp"])
        self.assertIn("U+0023", reasons["машинне.lisp"])

    def test_empty_file_satisfies_literal_every_character_condition(self):
        root = self.tree({"порожній.lisp": "", "пробіли.lisp": " \t\r\n"})
        result = report.measure(root)
        self.assertEqual(result.full_ukr_files, 2)
        self.assertEqual(result.percentage, 100.0)

    def test_invalid_utf8_and_symlink_cannot_count_as_completed(self):
        root = self.tree({"lib/зіпсований.lisp": b"\xff", "lib/ціль.txt": "тест"})
        (root / "lib/посилання.lisp").symlink_to(root / "lib/ціль.txt")
        result = report.measure(root)
        self.assertEqual(result.total_lisp_files, 2)
        self.assertEqual(result.full_ukr_files, 0)
        reasons = {item.path: item.reason for item in result.unfinished}
        self.assertIn("UnicodeDecodeError", reasons["lib/зіпсований.lisp"])
        self.assertIn("символічне посилання", reasons["lib/посилання.lisp"])

    def test_no_files(self):
        result = report.measure(self.tree({}))
        self.assertEqual(result.total_lisp_files, 0)
        self.assertEqual(result.full_ukr_files, 0)
        self.assertEqual(result.percentage, 0.0)


class ReportCliTests(FileTree):
    def test_default_output_contains_only_requested_metric(self):
        root = self.tree({
            "lib/так.lisp": "(визначити відповідь так)\n",
            "lib/ні.lisp": "(визначити answer так)\n",
        })
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
            code, stdout = self.cli("--root", str(root))
        self.assertEqual(code, 0)
        self.assertEqual(
            stdout.splitlines(),
            ["УКР-ПРОЄКЦІЯ .lisp: повністю українські файли 1/2 (50.0%)"],
        )
        self.assertNotIn("ук==укр", stdout)
        self.assertNotIn("викличні голови", stdout)

    def test_diagnostics_and_limit(self):
        root = self.tree({
            "a.lisp": "; TODO\n",
            "b.lisp": '(визначити а "OLD")\n',
            "c.lisp": "(визначити а)\n",
        })
        code, stdout = self.cli("--root", str(root), "--list", "--top", "1",
                                "--no-annotation")
        self.assertEqual(code, 0)
        self.assertIn("1/3 (33.3%)", stdout)
        self.assertIn("a.lisp: 1:3: U+0054", stdout)
        self.assertIn("… ще 1", stdout)
        self.assertNotIn("b.lisp:", stdout)

    def test_json_has_only_count_denominator_percentage(self):
        root = self.tree({"перший.lisp": "(визначити річ)\n", "другий.lisp": "; TODO\n"})
        destination = root / "report.json"
        code, _ = self.cli("--root", str(root), "--json", str(destination),
                           "--no-annotation")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {
            "total_lisp_files": 2,
            "full_ukr_files": 1,
            "percentage": 50.0,
        })

    def test_errors_on_absent_root(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code, _ = self.cli("--root", "/no/such/ukr-source/dir")
        self.assertEqual(code, 2)
        self.assertIn("--root не є текою", stderr.getvalue())

    def test_github_annotation_can_be_suppressed(self):
        root = self.tree({"a.lisp": "(визначити річ)\n"})
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            self.assertIn("::notice::", self.cli("--root", str(root))[1])
            self.assertNotIn("::notice::", self.cli(
                "--root", str(root), "--no-annotation")[1])

    def test_json_and_file_order_are_deterministic(self):
        root = self.tree({"z.lisp": "; TODO\n", "a.lisp": "(визначити а)\n"})
        original = (root / "a.lisp").read_bytes()
        self.assertEqual(report.measure(root), report.measure(root))
        dest = root / "metrics.json"
        self.cli("--root", str(root), "--json", str(dest), "--no-annotation")
        first = dest.read_bytes()
        self.cli("--root", str(root), "--json", str(dest), "--no-annotation")
        self.assertEqual(first, dest.read_bytes())
        self.assertEqual(original, (root / "a.lisp").read_bytes())


class CurrentRepositoryTests(unittest.TestCase):
    def test_real_repository_is_scanned_without_archive_exclusions(self):
        progress = report.measure(ROOT)
        self.assertGreater(progress.total_lisp_files, 100)
        self.assertEqual(len(progress.unfinished),
                         progress.total_lisp_files - progress.full_ukr_files)
        self.assertGreaterEqual(progress.percentage, 0)
        self.assertLessEqual(progress.percentage, 100)

    def test_keyboard_contract_matches_ratified_projection_guard(self):
        from tests.test_ukrainian_domain_projection_rules import (
            UKRAINIAN_KEYBOARD_OUTPUTS,
        )
        self.assertEqual(report.UKRAINIAN_KEYBOARD_OUTPUTS,
                         UKRAINIAN_KEYBOARD_OUTPUTS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
