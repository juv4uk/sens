"""Тести лише кількості повністю українських .lisp (весь вміст файла)."""
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

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "report_ukr_projection_progress.py"
SPEC = importlib.util.spec_from_file_location("report_ukr_projection_progress", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class UkrainianWholeFileTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="ukr-files-"))
        self.addCleanup(lambda: shutil.rmtree(self.directory, ignore_errors=True))

    def write(self, name: str, data: str | bytes) -> Path:
        path = self.directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))
        return path

    def test_entire_file_with_ukrainian_comments_and_strings_counts(self):
        self.write("lib/гарний.lisp",
                   '; перевірка українською\n'
                   '(визначити назва "Привіт, світе! Ґудзик №1 —")\n')
        # Тире U+2014 не набирається дозволеною українською розкладкою.
        self.assertEqual(mod.measure(self.directory).fully_ukrainian_files, 0)
        self.write("lib/гарний.lisp",
                   '; перевірка українською\n'
                   '(визначити назва "Привіт, світе! Ґудзик №1")\n')
        result = mod.measure(self.directory)
        self.assertEqual((result.fully_ukrainian_files, result.total_lisp_files), (1, 1))
        self.assertEqual(result.percent, 100.0)

    def test_comment_is_part_of_criterion_even_if_program_is_ukrainian(self):
        path = "lib/коментар.lisp"
        self.write(path, "(визначити число 125)\n; TODO\n")
        before = mod.measure(self.directory)
        self.assertEqual(before.fully_ukrainian_files, 0)
        self.assertIn("U+0054", before.pending[0].reason)
        self.write(path, "(визначити число 125)\n; зроблено\n")
        self.assertEqual(mod.measure(self.directory).fully_ukrainian_files, 1)

    def test_quoted_text_is_part_of_criterion(self):
        self.write("lib/слова.lisp", '(визначити слово "English text")\n')
        result = mod.measure(self.directory)
        self.assertEqual(result.fully_ukrainian_files, 0)
        self.assertIn("U+0045", result.pending[0].reason)
        self.write("lib/слова.lisp", '(визначити слово "Український текст")\n')
        self.assertEqual(mod.measure(self.directory).fully_ukrainian_files, 1)

    def test_non_ukrainian_identifiers_not_accepted(self):
        self.write("lib/код.lisp", "(визначити legacy 100)\n")
        result = mod.measure(self.directory)
        self.assertEqual(result.fully_ukrainian_files, 0)
        self.assertIn("U+006C", result.pending[0].reason)

    def test_accepted_keyboard_punctuation_numbers_and_crlf(self):
        self.write("lib/набір.lisp",
                   b'( \xd0\xb3\xd2\x91 0123456789 \xe2\x82\xb4 \xe2\x84\x96 '
                   b"'\\-=./!\";%:?*()_+, )\t\r\n")
        result = mod.measure(self.directory)
        self.assertEqual(result.fully_ukrainian_files, 1)

    def test_non_keyboard_punctuation_and_unicode_are_not_accepted(self):
        self.write("lib/знак.lisp", "(визначити х 1)\n; латиниця@неможлива\n")
        self.assertEqual(mod.measure(self.directory).fully_ukrainian_files, 0)
        self.write("lib/знак.lisp", '(визначити х "тест — тест")\n')
        self.assertEqual(mod.measure(self.directory).fully_ukrainian_files, 0)
        self.write("lib/знак.lisp", '(визначити х "тест")\n')
        self.assertEqual(mod.measure(self.directory).fully_ukrainian_files, 1)

    def test_scans_every_lisp_including_archives_and_tests(self):
        self.write("lib/перший.lisp", "(визначити це 1)\n")
        self.write("tests/другий.lisp", "; український текст\n")
        self.write("research/давній.lisp", "; Archive\n")
        self.write("tests/ігнорувати.txt", "; English\n")
        self.write(".git/ігнорувати.lisp", "; English\n")
        result = mod.measure(self.directory)
        self.assertEqual((result.total_lisp_files, result.fully_ukrainian_files), (3, 2))
        self.assertEqual(result.percent, 66.7)

    def test_empty_whitespace_only_and_invalid_utf8_do_not_count(self):
        self.write("lib/порожній.lisp", "")
        self.write("lib/пробіли.lisp", " \t\r\n")
        self.write("lib/зіпсований.lisp", b"\xff")
        self.write("lib/чинний.lisp", "; коментар\n")
        result = mod.measure(self.directory)
        self.assertEqual((result.total_lisp_files, result.fully_ukrainian_files), (4, 1))
        self.assertEqual(len(result.pending), 3)
        self.assertIn("UTF-8", " ".join(item.reason for item in result.pending))

    def test_symlink_is_not_treated_as_independent_file(self):
        target = self.write("lib/справжній.lisp", "(визначити а 1)\n")
        shortcut = self.directory / "lib" / "посилання.lisp"
        try:
            shortcut.symlink_to(target)
        except (NotImplementedError, OSError):
            self.skipTest("символічні посилання недоступні")
        result = mod.measure(self.directory)
        self.assertEqual((result.total_lisp_files, result.fully_ukrainian_files), (2, 1))

    def test_zero_files_has_zero_percent(self):
        report = mod.measure(self.directory)
        self.assertEqual((report.total_lisp_files, report.fully_ukrainian_files), (0, 0))
        self.assertEqual(report.percent, 0.0)

    def test_cli_prints_only_the_requested_metric_and_json_has_only_three_keys(self):
        self.write("lib/добрий.lisp", "(визначити а 1)\n; гарно\n")
        self.write("lib/поганий.lisp", '(визначити а "English")\n')
        result_file = self.directory / "звіт.json"
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = mod.main(["--root", str(self.directory), "--json", str(result_file),
                           "--no-annotation"])
        self.assertEqual(rc, 0)
        self.assertEqual(stdout.getvalue().splitlines(), [
            "УКР-ПРОЄКЦІЯ: повністю українські файли .lisp — 1/2 (50.0%)"
        ])
        self.assertEqual(json.loads(result_file.read_text(encoding="utf-8")), {
            "fully_ukrainian_files": 1,
            "total_lisp_files": 2,
            "percent": 50.0,
        })

    def test_list_mode_reports_first_disallowed_symbol(self):
        self.write("lib/добрий.lisp", "(визначити а 1)\n")
        self.write("lib/поганий.lisp", "; Test\n")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            rc = mod.main(["--root", str(self.directory), "--list", "--top", "1"])
        self.assertEqual(rc, 0)
        lines = stdout.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("lib/поганий.lisp: 1:3", lines[1])
        self.assertIn("U+0054", lines[1])


if __name__ == "__main__":
    unittest.main()
