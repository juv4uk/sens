"""Перевірка єдиного показника: повністю українські .lisp-файли.

Справжні випробування повнофайлової перевірки: рядки та коментарі
не є винятками; будь-який недоступний з розкладки символ знімає файл із
лічильника, незалежно від семантики Lisp.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
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
    def tree(self, files: dict[str, str]) -> Path:
        path = Path(tempfile.mkdtemp(prefix="ukr-proj-"))
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        for name, source in files.items():
            file = path / name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(source, encoding="utf-8")
        return path

    def run_report(self, *args: str):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = mod.main(list(args))
        return status, stdout.getvalue()


class WholeFileKeyboardTests(TempTree):
    def test_comment_and_string_with_latin_make_the_whole_file_incomplete(self):
        root = self.tree({
            "lib/готовий.lisp": "(визначити число -125,5)\n; українською\n",
            "lib/коментар.lisp": "(визначити число 1)\n; TODO\n",
            "lib/рядок.lisp": '(визначити імʼя "English")\n',
        })
        report = mod.measure(root)
        self.assertEqual(report["files_total"], 3)
        self.assertEqual(report["files_fully_ukrainian"], 1)
        self.assertEqual(report["files_remaining"], 2)
        self.assertEqual(report["pct"], 33.3)
        reasons = {item["path"]: item for item in report["pending_files"]}
        self.assertEqual(reasons["lib/коментар.lisp"]["character"], "T")
        self.assertEqual(reasons["lib/коментар.lisp"]["line"], 2)
        self.assertEqual(reasons["lib/коментар.lisp"]["column"], 3)
        self.assertEqual(reasons["lib/рядок.lisp"]["character"], "ʼ")

    def test_quoted_english_text_alone_is_not_allowed(self):
        root = self.tree({
            "lib/текст.lisp": '(визначити текст "English")\n',
        })
        issue = mod.measure(root)["pending_files"][0]
        self.assertEqual((issue["line"], issue["column"], issue["character"]),
                         (1, 19, "E"))

    def test_ukrainian_punctuation_numbers_spaces_and_newlines_are_allowed(self):
        root = self.tree({
            "приклад.lisp": "(визначити число -25,25)\n"
                           "; Ґ ґ Ї ї Є є І і ' \" № ₴ + = ? : ! \\ /\t\n",
        })
        report = mod.measure(root)
        self.assertEqual(report["files_fully_ukrainian"], 1)
        self.assertEqual(report["pct"], 100.0)

    def test_typographic_apostrophe_and_machine_hash_fail(self):
        root = self.tree({
            "типографіка.lisp": "(визначити об’єкт 1)\n",
            "машинний.lisp": "(визначити вміст #d1:1)\n",
        })
        report = mod.measure(root)
        self.assertEqual(report["files_fully_ukrainian"], 0)
        chars = [x["character"] for x in report["pending_files"]]
        self.assertEqual(chars, ["#", "’"])

    def test_percentage_changes_only_when_the_entire_file_is_correct(self):
        root = self.tree({
            "lib/готовий.lisp": "(визначити річ 1)\n",
            "lib/не-готовий.lisp": "(визначити річ 1)\n; TODO\n",
        })
        self.assertEqual(mod.measure(root)["pct"], 50.0)
        (root / "lib/не-готовий.lisp").write_text(
            "(визначити річ 1)\n; готово\n", encoding="utf-8")
        self.assertEqual(mod.measure(root)["pct"], 100.0)

    def test_all_directories_count_including_tables_history_and_tests(self):
        root = self.tree({
            "lib/domains/d4.lisp": "(укр назва)\n",
            "research/archive/old.lisp": "(legacy)\n",
            "tests/тест.lisp": "(українська)\n",
            "ignore.txt": "(legacy)\n",
            ".git/objects/example.lisp": "(legacy)\n",
        })
        report = mod.measure(root)
        self.assertEqual(report["files_total"], 3)
        self.assertEqual(report["files_fully_ukrainian"], 2)

    def test_empty_and_whitespace_only_files_are_not_completed(self):
        root = self.tree({
            "порожній.lisp": "",
            "пробіли.lisp": "\n \t\n",
        })
        report = mod.measure(root)
        self.assertEqual(report["files_fully_ukrainian"], 0)
        self.assertTrue(all(p["reason"] == "порожній файл"
                            for p in report["pending_files"]))

    def test_invalid_utf8_is_not_silently_ignored(self):
        root = self.tree({"зіпсований.lisp": "(визначити 1)\n"})
        (root / "зіпсований.lisp").write_bytes(b"\xff")
        report = mod.measure(root)
        self.assertEqual(report["files_fully_ukrainian"], 0)
        self.assertEqual(report["pending_files"][0]["reason"],
                         "неможливо прочитати UTF-8")

    def test_symlink_is_not_assumed_to_be_completed(self):
        root = self.tree({"основний.lisp": "(визначити число 1)\n"})
        (root / "посилання.lisp").symlink_to(root / "основний.lisp")
        report = mod.measure(root)
        self.assertEqual(report["files_total"], 2)
        self.assertEqual(report["files_fully_ukrainian"], 1)
        self.assertIn("посилання", report["pending_files"][0]["reason"])

    def test_empty_tree_is_not_one_hundred_percent(self):
        report = mod.measure(self.tree({}))
        self.assertEqual(report["files_total"], 0)
        self.assertEqual(report["files_fully_ukrainian"], 0)
        self.assertEqual(report["pct"], 0.0)

    def test_order_and_counts_are_deterministic(self):
        root = self.tree({"в.lisp": "(legacy)\n", "а.lisp": "(назва)\n"})
        self.assertEqual(mod.measure(root), mod.measure(root))
        self.assertEqual(mod.measure(root)["pending_files"][0]["path"], "в.lisp")


class ReportInterfaceTests(TempTree):
    def test_stdout_and_json_contain_only_the_same_file_metric(self):
        root = self.tree({
            "а.lisp": "(визначити а 1)\n",
            "б.lisp": "(define b 1)\n",
        })
        output = root / "report.json"
        status, stdout = self.run_report(
            "--root", str(root), "--no-annotation", "--json", str(output))
        self.assertEqual(status, 0)
        self.assertEqual(
            stdout.strip(), "ПОВНІСТЮ УКРАЇНСЬКІ .lisp: 1/2 (50.0%); залишилося 1 файлів")
        data = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(data["files_fully_ukrainian"], 1)
        self.assertEqual(data["files_total"], 2)
        self.assertEqual(data["pct"], 50.0)
        self.assertEqual(len(data["pending_files"]), 1)
        self.assertNotIn("pairs_pct", data)
        self.assertNotIn("active_heads_pct", data)
        self.assertNotIn("executable_ukr", data)

    def test_list_shows_first_illegal_character_and_location(self):
        root = self.tree({"а.lisp": "(назва)\n; TODO\n", "б.lisp": "(other)\n"})
        status, stdout = self.run_report(
            "--root", str(root), "--no-annotation", "--list", "--top", "1")
        self.assertEqual(status, 0)
        self.assertIn("а.lisp:2:3: символ поза українською розкладкою U+0054 'T'", stdout)
        self.assertIn("… ще 1", stdout)

    def test_annotation_is_information_only(self):
        root = self.tree({"а.lisp": "(legacy)\n"})
        status, stdout = self.run_report("--root", str(root))
        self.assertEqual(status, 0)
        self.assertIn("::notice::ПОВНІСТЮ УКРАЇНСЬКІ .lisp:", stdout)
        self.assertNotIn("::error::", stdout)

    def test_bad_root_is_usage_error(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            status, _ = self.run_report("--root", "/no/such/dir/report-ukr")
        self.assertEqual(status, 2)

    def test_bad_top_is_usage_error(self):
        root = self.tree({})
        status, _ = self.run_report("--root", str(root), "--top", "-1")
        self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
