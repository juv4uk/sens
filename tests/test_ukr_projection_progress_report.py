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
    def test_nested_agent_worktree_does_not_distort_main_repository_percentage(self):
        root = self.tree({
            "lib/так.lisp": "(визначити відповідь так)\n",
            ".worktrees/інша-гілка/lib/legacy.lisp": "(define answer yes)\n",
        })
        result = report.measure(root)
        self.assertEqual(result.total_lisp_files, 1)
        self.assertEqual(result.fully_ukrainian_files, 1)
        self.assertEqual(result.percent, 100.0)

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
        self.assertEqual(result.fully_ukrainian_files, 2)
        self.assertEqual(result.percent, 33.3)
        self.assertEqual(len(result.pending), 4)
        self.assertEqual({r.path for r in result.pending}, {
            "lib/коментар.lisp", "lib/рядок.lisp",
            "lib/код.lisp", "research/архів.lisp",
        })
        self.assertEqual(
            report.render(result),
            "УКР-ПРОЄКЦІЯ: повністю українські файли .lisp — 2/6 (33.3%)",
        )

    def test_source_projection_ignores_comments_strings_and_quoted_data(self):
        root = self.tree({
            "lib/ок.lisp": '(визначити сума (функція (значення) (додати значення 1)))\n'
                            '; English comment is not executable\n'
                            '(визначити схема (як-є dimension-1))\n',
            "lib/alias.lisp": '; opt-in повна укр-поверхня\n(визначити old-name нова-назва)\n',
            "lib/not-ok.lisp": '(визначити сума (функція (x) (add x 1)))\n',
            "lib/raw.lisp": '(101 x)\n',
            "lib/domains/d9.lisp": '(101000000 (ук приклад) (укр приклад))\n',
            "lib/surface/uk-inventory.lisp": '; metadata\n',
        })
        result = report.measure_source_projection(root)
        self.assertEqual(result.total_source_files, 4)
        self.assertEqual(result.fully_projected_source_files, 1)
        self.assertEqual(result.percent, 25.0)
        reasons = {item.path: item.reason for item in result.pending}
        self.assertTrue(
            "англомовний локальний параметр" in reasons["lib/not-ok.lisp"]
            or "англомовна виклична голова" in reasons["lib/not-ok.lisp"]
        )
        self.assertIn("сира бінарна голова", reasons["lib/raw.lisp"])
        self.assertIn("англомовна назва визначення", reasons["lib/alias.lisp"])
        self.assertEqual(result.excluded_nonprogram_files, 2)

    def test_live_surface_definitions_count_but_metadata_do_not(self):
        root = self.tree({
            "lib/surface/діюче.lisp":
                "(визначити обчислити (функція (аргумент) аргумент))\n",
            "lib/surface/старе.lisp":
                "(define old-name (функція (x) x))\n",
            "lib/surface/метадані.lisp":
                "(простори (укр джерело) (en source))\n",
            "lib/surface/вкладені-дані.lisp":
                "(опис (визначити це-дані 1))\n",
            "lib/surface/пошкоджене.lisp":
                "(визначити незакрите (функція (аргумент) аргумент)\n",
            "lib/звичайне.lisp":
                "(визначити результат (функція (значення) значення))\n",
        })
        result = report.measure_source_projection(root)
        self.assertEqual(result.total_source_files, 4)
        self.assertEqual(result.excluded_nonprogram_files, 2)
        self.assertEqual(result.fully_projected_source_files, 2)
        reasons = {entry.path: entry.reason for entry in result.pending}
        self.assertIn("lib/surface/старе.lisp", reasons)
        self.assertIn("lib/surface/пошкоджене.lisp", reasons)
        self.assertNotIn("lib/surface/метадані.lisp", reasons)
        self.assertNotIn("lib/surface/вкладені-дані.lisp", reasons)

    def test_retired_comment_only_lib_files_are_not_counted_as_programs(self):
        root = self.tree({
            "lib/списане.lisp": "; ФАЙЛ ВИВЕДЕНО З УЖИТКУ\\n".replace("\\n", "\n"),
            "lib/блокові-дані.lisp": "#| коментар #| вкладений |# кінець |#\\n".replace("\\n", "\n"),
            "lib/чинне.lisp": "(визначити результат (атом? (як-є ())))\n",
            "lib/пошкоджене.lisp": "#| незакритий коментар",
        })
        progress = report.measure_source_projection(root)
        self.assertEqual(progress.excluded_nonprogram_files, 2)
        self.assertEqual(progress.total_source_files, 2)
        self.assertEqual(progress.fully_projected_source_files, 1)
        self.assertIn("lib/пошкоджене.lisp",
                      {entry.path for entry in progress.pending})
        # У повнофайловому обліку жоден файл не зникає.
        self.assertEqual(report.measure(root).total_lisp_files, 4)

    def test_isa_catalogue_is_data_not_a_lisp_program(self):
        # Це фізичні факти CPU, не D7/українські викличні імена.
        # Новий executable у тій самій теці НЕ можна приховувати.
        root = self.tree({
            "lib/machine/isa/avx.lisp":
                "; апаратний опис\n"
                "(isa-catalogue-1 (extension AVX) "
                "(instructions (instruction VADDPS)))\n",
            "lib/machine/isa/реальна.lisp":
                "(визначити обчислити (функція (аргумент) (атом? аргумент)))\n",
            "lib/machine/isa/старе.lisp":
                "(визначити old-name (функція (x) x))\n",
            "lib/живе.lisp": "(визначити правда (атом? (як-є ())))\n",
        })
        progress = report.measure_source_projection(root)
        self.assertEqual(progress.excluded_nonprogram_files, 1)
        self.assertEqual(progress.total_source_files, 3)
        self.assertEqual(progress.fully_projected_source_files, 2)
        self.assertIn("lib/machine/isa/старе.lisp",
                      {entry.path for entry in progress.pending})
        # Загальна метрика всього .lisp дерева не має «зникати».
        self.assertEqual(report.measure(root).total_lisp_files, 4)

    def test_latin_value_reference_is_not_mistaken_for_quoted_data(self):
        root = self.tree({
            "lib/значення.lisp": "(визначити результат legacy-value)\\n".replace("\\n", "\n"),
            "lib/аргумент.lisp": "(визначити результат (тотожне? так legacy-value))\\n".replace("\\n", "\n"),
            "lib/цитата.lisp": "(визначити протокол (як-є legacy-value))\\n".replace("\\n", "\n"),
        })
        result = report.measure_source_projection(root)
        self.assertEqual(result.total_source_files, 3)
        self.assertEqual(result.fully_projected_source_files, 1)
        reasons = {item.path: item.reason for item in result.pending}
        self.assertIn("англомовне посилання на значення", reasons["lib/значення.lisp"])
        self.assertIn("англомовне посилання на значення", reasons["lib/аргумент.lisp"])
        self.assertNotIn("lib/цитата.lisp", reasons)

    def test_variadic_function_binder_must_be_ukrainian(self):
        # Голий параметр функції прив'язує решту аргументів.
        # Коментарі та цитовані імена не змінюють виконуваний контракт.
        root = self.tree({
            "lib/старий.lisp":
                "(визначити зібрати (функція rest-args rest-args))\n",
            "lib/чинний.lisp":
                "(визначити зібрати (функція решта-аргументів решта-аргументів))\n",
            "lib/цитата.lisp":
                "(визначити назви (як-є (функція rest-args rest-args)))\n",
        })
        state = report.measure_source_projection(root)
        self.assertEqual(state.total_source_files, 3)
        self.assertEqual(state.fully_projected_source_files, 2)
        reasons = {x.path: x.reason for x in state.pending}
        self.assertIn("англомовний локальний параметр", reasons["lib/старий.lisp"])
        self.assertNotIn("lib/чинний.lisp", reasons)
        self.assertNotIn("lib/цитата.lisp", reasons)

    def test_primary_projection_report_is_separate_from_keyboard_completion(self):
        root = self.tree({
            "lib/код.lisp": '(визначити сума (функція (значення) (додати значення 1)))\n',
            "lib/коментар.lisp": '(визначити сума (функція (значення) (додати значення 1)))\n; TODO\n',
        })
        self.assertEqual(report.measure_source_projection(root).fully_projected_source_files, 2)
        self.assertEqual(report.measure(root).fully_ukrainian_files, 1)


    def test_compatibility_comments_never_hide_unmigrated_definitions(self):
        files = {
            "lib/quantity.lisp": (
                "(визначити головна-назва "
                "(функція (значення) значення))\n"
                "; Сумісні історичні імена схем залишаються зовнішніми\n"
                "(визначити old-name головна-назва)\n"
            ),
            "lib/mechanism-selector.lisp": (
                "(визначити головна-назва "
                "(функція (значення) значення))\n"
                "; Сумісні англомовні назви залишаються псевдонімами "
                "тих самих Lisp-значень.\n"
                "(визначити old-name головна-назва)\n"
            ),
            "lib/alias.lisp": (
                "(визначити головна-назва "
                "(функція (значення) значення))\n"
                "; Сумісні зовнішні назви вказують на ті самі значення, "
                "без другої реалізації.\n"
                "(визначити old-name головна-назва)\n"
            ),
        }
        root = self.tree(files)
        projected = report.measure_source_projection(root)
        self.assertEqual(projected.total_source_files, 3)
        self.assertEqual(projected.fully_projected_source_files, 0)
        self.assertEqual(projected.percent, 0.0)
        self.assertEqual(len(projected.pending), 3)

        # Compatibility names stay English; the strict keyboard metric is different.
        keyboard = report.measure(root)
        self.assertEqual(keyboard.total_lisp_files, 3)
        self.assertEqual(keyboard.fully_ukrainian_files, 0)

        code, stdout = self.cli("--root", str(root), "--no-annotation")
        self.assertEqual(code, 0)
        self.assertIn("повністю українські файли .lisp — 0/3 (0.0%)", stdout)
        self.assertIn(
            "виконувані назви, голови та параметри в активних lib-файлах — "
            "0/3 (0.0%)",
            stdout,
        )

    def test_english_comment_removal_really_increments_the_numerator(self):
        root = self.tree({"lib/завдання.lisp": "(визначити річ 1)\n; TODO\n"})
        self.assertEqual(report.measure(root).fully_ukrainian_files, 0)
        (root / "lib/завдання.lisp").write_text(
            "(визначити річ 1)\n; Виконано\n", encoding="utf-8"
        )
        self.assertEqual(report.measure(root).fully_ukrainian_files, 1)

    def test_strings_and_nested_comments_are_not_skipped(self):
        root = self.tree({
            "lib/блок.lisp": "(визначити річ 1)\n#| англійське TODO |#\n",
            "lib/рядок.lisp": '(визначити річ "привіт old")',
            "lib/український.lisp": '(визначити річ "привіт; друг")',
        })
        state = report.measure(root)
        self.assertEqual(state.fully_ukrainian_files, 1)
        self.assertIn("lib/блок.lisp", [x.path for x in state.pending])
        self.assertIn("lib/рядок.lisp", [x.path for x in state.pending])

    def test_special_unavailable_symbols_and_ukrainian_apostrophe(self):
        root = self.tree({
            "дозволено.lisp": "(визначити ім'я 123)\t; Ґрунт, №1 і ₴20\r\n",
            "типографіка.lisp": "(визначити імʼя 1)\n",
            "значок.lisp": "; тест 🙂\n",
            "машинне.lisp": "(визначити назва #d1:1)\n",
        })
        result = report.measure(root)
        self.assertEqual(result.fully_ukrainian_files, 1)
        reasons = {item.path: item.reason for item in result.pending}
        self.assertIn("U+02BC", reasons["типографіка.lisp"])
        self.assertIn("U+1F642", reasons["значок.lisp"])
        self.assertIn("U+0023", reasons["машинне.lisp"])

    def test_empty_file_does_not_count_as_completed_program(self):
        root = self.tree({"порожній.lisp": "", "пробіли.lisp": " \t\r\n"})
        result = report.measure(root)
        self.assertEqual(result.fully_ukrainian_files, 0)
        self.assertEqual(result.percent, 0.0)

    def test_invalid_utf8_and_symlink_cannot_count_as_completed(self):
        root = self.tree({"lib/зіпсований.lisp": b"\xff", "lib/ціль.txt": "тест"})
        (root / "lib/посилання.lisp").symlink_to(root / "lib/ціль.txt")
        result = report.measure(root)
        self.assertEqual(result.total_lisp_files, 2)
        self.assertEqual(result.fully_ukrainian_files, 0)
        reasons = {item.path: item.reason for item in result.pending}
        self.assertIn("UnicodeDecodeError", reasons["lib/зіпсований.lisp"])
        self.assertIn("символічне посилання", reasons["lib/посилання.lisp"])

    def test_no_files(self):
        result = report.measure(self.tree({}))
        self.assertEqual(result.total_lisp_files, 0)
        self.assertEqual(result.fully_ukrainian_files, 0)
        self.assertEqual(result.percent, 0.0)


class ReportCliTests(FileTree):
    def test_default_output_contains_both_progress_metrics(self):
        root = self.tree({
            "lib/так.lisp": "(визначити відповідь так)\n",
            "lib/ні.lisp": "(визначити answer так)\n",
        })
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "false"}):
            code, stdout = self.cli("--root", str(root))
        self.assertEqual(code, 0)
        self.assertEqual(
            stdout.splitlines(),
            [
                "УКР-ПРОЄКЦІЯ: повністю українські файли .lisp — 1/2 (50.0%)",
                "УКР-ПРОЄКЦІЯ: виконувані назви, голови та параметри в активних lib-файлах — 1/2 (50.0%)",
            ],
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

    def test_json_has_only_count_denominator_percent(self):
        root = self.tree({"перший.lisp": "(визначити річ)\n", "другий.lisp": "; TODO\n"})
        destination = root / "report.json"
        code, _ = self.cli("--root", str(root), "--json", str(destination),
                           "--no-annotation")
        self.assertEqual(code, 0)
        payload = json.loads(destination.read_text(encoding="utf-8"))
        self.assertEqual({
            "total_lisp_files": payload["total_lisp_files"],
            "fully_ukrainian_files": payload["fully_ukrainian_files"],
            "percent": payload["percent"],
        }, {
            "total_lisp_files": 2,
            "fully_ukrainian_files": 1,
            "percent": 50.0,
        })
        self.assertIn("source_projection", payload)
        self.assertEqual(payload["source_projection"]["total_source_files"], 0)

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
    def test_reason_proof_marker_is_ukrainian_d7_atom_not_unsupported_string(self):
        # Перевіряємо тільки проєкцію source: сам SENS/Zig доводить
        # фізичну оборотність і виконання, не лексичний тест Python.
        source = (ROOT / "lib/reason.lisp").read_text(encoding="utf-8")
        self.assertIn("(друкувати (як-є висновок))", source)
        self.assertNotIn('(друкувати "|-")', source)
        self.assertNotIn("(як-є |-)", source)
        tokens = report.tokenize_lisp(source)
        self.assertIn(("ATOM", "висновок"),
                      [(t.kind, t.value) for t in tokens])
        self.assertFalse(any(
            "|" in t.value for t in tokens
            if t.kind in ("ATOM", "STRING")
        ))

    def test_real_repository_is_scanned_without_archive_exclusions(self):
        progress = report.measure(ROOT)
        self.assertGreater(progress.total_lisp_files, 100)
        self.assertEqual(len(progress.pending),
                         progress.total_lisp_files - progress.fully_ukrainian_files)
        self.assertGreaterEqual(progress.percent, 0)
        self.assertLessEqual(progress.percent, 100)

    def test_ci_selects_surface_definitions_for_real_sens_execution(self):
        # An entire excluded directory hid active Ukrainian Lisp functions from
        # native T5M execution. This protects the changed-file integration,
        # not a Python substitute for SENS semantic tests.
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        selection = workflow.split('id: changed-t5m-lisp', 1)[1].split('          PY', 1)[0]
        self.assertIn('from report_ukr_projection_progress import tokenize_lisp, _contains_source_definitions',
                      selection)
        self.assertIn('name.startswith("lib/surface/") and not _contains_source_definitions(path)',
                      selection)
        self.assertNotIn('"lib/surface/", "knowledge/"', selection)
        self.assertIn('T5M_CHANGED_FILE', selection)



if __name__ == "__main__":
    unittest.main(verbosity=2)
