"""Тест САМОГО правила драбин, а не лише інструмента поруч.

Раніше CI перевіряв, що інструмент виявлення кандидатів працює, але жоден тест
не вимагав, щоб нова програма НЕ дублювала наявну поверхню D1–D10. Через це
агент міг написати локальний дубль і пройти CI. Цей тест закриває саме ту діру.

Правило (AGENTS.md): функції беруться з D1–D10; наявне — вжити; немає в
драбинах — кандидат D11 (далі D12…), а не локальний дубль.
"""
from __future__ import annotations

import importlib.util
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "guard-domain-function-reuse.py"
SEARCH = ROOT / "scripts" / "search-domain-function.py"
PROBE = ROOT / "lib" / "_rule_probe.lisp"


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(script), *args], cwd=ROOT,
                          capture_output=True, text=True, check=False)


class DomainFunctionReuseRule(unittest.TestCase):
    def tearDown(self) -> None:
        if PROBE.exists():
            PROBE.unlink()

    def test_guard_self_test_is_green(self) -> None:
        result = run(GUARD, "--self-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_guard_fails_closed_when_ladder_discovery_is_incomplete(self) -> None:
        spec = importlib.util.spec_from_file_location("guard_empty_ladder_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        output = StringIO()
        with mock.patch.object(guard, "ladder_names", return_value=set()):
            with redirect_stderr(output):
                status = guard.main(["--file", "lib/core4.lisp"])
        self.assertEqual(status, 2, output.getvalue())
        self.assertIn("НЕ ПЕРЕВІРЕНО", output.getvalue())
        self.assertIn(f"щонайменше {guard.MINIMUM_RATIFIED_SURFACES}", output.getvalue())

    def test_staged_guard_reads_git_index_not_dirty_worktree(self) -> None:
        # Механіка pre-commit: staged дубль не можна приховати чистим worktree.
        spec = importlib.util.spec_from_file_location("guard_staged_index_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "lib").mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            probe = root / "lib" / "staged.lisp"
            probe.write_text("(визначити сполучити (функція (х у) х))\n", encoding="utf-8")
            subprocess.run(["git", "add", "lib/staged.lisp"], cwd=root, check=True)
            probe.write_text("(атом? (як-є ()))\n", encoding="utf-8")
            output = StringIO()
            with mock.patch.object(guard, "ROOT", root):
                with mock.patch.object(guard, "MINIMUM_RATIFIED_SURFACES", 1):
                    with mock.patch.object(guard, "ladder_names", return_value={"сполучити"}):
                        with mock.patch.object(guard, "project_definition_sites", return_value={}):
                            with redirect_stdout(output):
                                status = guard.main(["--staged"])
            self.assertEqual(status, 1, output.getvalue())
            self.assertIn("BLOCKED", output.getvalue())

    def test_staged_guard_handles_control_characters_in_git_paths(self) -> None:
        # Git -z має зберігати справжнє ім'я з TAB, а не quoted-path.
        spec = importlib.util.spec_from_file_location("guard_git_nul_paths_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "lib").mkdir()
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            rel = "lib/staged\tname.lisp"
            (root / rel).write_text(
                "(визначити сполучити (функція (х у) х))\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "--", rel], cwd=root, check=True)
            output = StringIO()
            with mock.patch.object(guard, "ROOT", root):
                with mock.patch.object(guard, "MINIMUM_RATIFIED_SURFACES", 1):
                    with mock.patch.object(guard, "ladder_names", return_value={"сполучити"}):
                        with mock.patch.object(guard, "project_definition_sites", return_value={}):
                            with redirect_stdout(output):
                                self.assertEqual(guard.changed_files(mock.Mock(file=None, paths_from=None, staged=True)), [rel])
                                status = guard.main(["--staged"])
            self.assertEqual(status, 1, output.getvalue())
            self.assertIn("BLOCKED", output.getvalue())

    def test_search_self_test_is_green(self) -> None:
        result = run(SEARCH, "--self-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_duplicate_of_a_ratified_surface_is_blocked(self) -> None:
        # сполучити — чинна поверхня D3:111 (cons). Перевизначати заборонено.
        PROBE.write_text("(" + "визначити сполучити (" + "функція (х у) х))\n", encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 1, "дубль наявної поверхні мусить валити guard")
        self.assertIn("BLOCKED", result.stdout)

    def test_blocked_batch_cannot_register_d11_candidates(self) -> None:
        # Якщо поряд із кандидатом є дубль D3, відмова має бути без побічного запису.
        PROBE.write_text(
            "(визначити сполучити (функція (х у) х))\n"
            "(визначити нова-проба-реєстру-охоронця "
            "(функція (х) (сполучити х (як-є ()))))\n",
            encoding="utf-8",
        )
        spec = importlib.util.spec_from_file_location("guard_registration_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        output = StringIO()
        with mock.patch.object(guard, "register_candidates", return_value=1) as register:
            with redirect_stdout(output):
                status = guard.main(["--file", str(PROBE.relative_to(ROOT)), "--register"])
        self.assertEqual(status, 1, output.getvalue())
        self.assertIn("КАНДИДАТ D11", output.getvalue())
        self.assertIn("НЕ ЗАРЕЄСТРОВАНО", output.getvalue())
        register.assert_not_called()

    def test_new_name_without_ladder_call_or_marker_is_blocked(self) -> None:
        # Свідомий вибір: або вживай поверхню драбини, або познач пропозицію D11.
        PROBE.write_text("(" + "визначити цілком-нова-річ-з-тесту (" + "функція (х) х))\n", encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 1, "нове ім'я без виклику драбини і без маркера — BLOCKED")
        self.assertIn("BLOCKED", result.stdout)

    def test_new_name_with_d11_marker_is_a_candidate(self) -> None:
        PROBE.write_text("; D11-пропозиція: справді нової операції немає в драбинах\n"
                         "(" + "визначити цілком-нова-річ-з-тесту (" + "функція (х) х))\n", encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 0, "з маркером — кандидат D11, не блок")
        self.assertIn("КАНДИДАТ D11", result.stdout)

    def test_new_name_that_calls_the_ladder_is_allowed(self) -> None:
        PROBE.write_text("(" + "визначити цілком-нова-річ-з-тесту (" + "функція (х) (" + "сполучити х (" + "як-є ()))))\n",
                         encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 0, "кличе драбину — припустимо")
        self.assertIn("КАНДИДАТ D11", result.stdout)

    def test_project_helper_does_not_substitute_for_a_ladder_call(self) -> None:
        # Старий внутрішній helper не є поверхнею D1–D10. Його виклик
        # не повинен обходити правило «драбина або явна пропозиція D11».
        spec = importlib.util.spec_from_file_location("guard_project_helper_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        helper = "знайти-хвіст-за-умовою"
        self.assertIn(helper, guard.project_names(ROOT))
        self.assertNotIn(helper, guard.ladder_names(ROOT))
        body = "(" + helper + " х)"
        PROBE.write_text(
            "(" + "визначити " + "нове-імя-з-тесту "
            + "(" + "функція (х) " + body + "))\n",
            encoding="utf-8",
        )
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("BLOCKED", result.stdout)

    def test_usage_counts_active_call_sites_not_unique_names(self) -> None:
        # Механічний лічильник має рахувати два виклики, а не одну унікальну назву.
        twice = "(" + "сполучити х (" + "сполучити х (" + "як-є ())))"
        PROBE.write_text(
            "(" + "визначити " + "двічі-вжити-поверхню "
            + "(" + "функція (х) " + twice + "))\n",
            encoding="utf-8",
        )
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ВЖИВАННЯ ДРАБИН: lib/_rule_probe.lisp: 2 викликів", result.stdout)

    def test_usage_ignores_comment_only_calls(self) -> None:
        # Коментар не є викликом; він не має створити хибну згоду охоронця.
        source = (
            "; (" + "сполучити" + " вигаданий-приклад)\n"
            + "(" + "визначити " + "без-реального-виклику "
            + "(" + "функція (х) х))\n"
        )
        PROBE.write_text(source, encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("ВЖИВАННЯ ДРАБИН: lib/_rule_probe.lisp: 0 викликів", result.stdout)
        self.assertIn("BLOCKED", result.stdout)

    def test_tracked_new_definition_is_not_its_own_duplicate(self) -> None:
        # Механіка guard, не семантичний оракул Lisp: git ls-files включає
        # нове ім'я в поточний файл, але воно не може дублювати саме себе.
        spec = importlib.util.spec_from_file_location("guard_reuse_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lib = root / "lib"
            lib.mkdir()
            (lib / "one.lisp").write_text("(" + "визначити проба (" + "функція (х) х))\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "lib/one.lisp"], cwd=root, check=True)
            sites = guard.project_definition_sites(root)
            self.assertEqual(sites["проба"], {"lib/one.lisp"})
            self.assertFalse(guard.duplicates_project_definition(sites, "проба", "lib/one.lisp"))
            self.assertTrue(guard.duplicates_project_definition(sites, "проба", "lib/two.lisp"))
            (lib / "two.lisp").write_text("(" + "визначити проба (" + "функція (х) х))\n", encoding="utf-8")
            subprocess.run(["git", "add", "lib/two.lisp"], cwd=root, check=True)
            sites = guard.project_definition_sites(root)
            self.assertTrue(guard.duplicates_project_definition(sites, "проба", "lib/one.lisp"))

    def test_quoted_definitions_are_data_not_project_duplicates(self) -> None:
        # Механічний аудит Lisp-джерела: цитата не реєструє функцію.
        spec = importlib.util.spec_from_file_location("guard_quote_probe", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lib = root / "lib"
            lib.mkdir()
            quote = "(" + "як-є" + " ((" + "визначити" + " уявна (" + "функція" + " (х) х)))))"
            real = "(" + "визначити" + " справжня (" + "функція" + " (х) х))"
            (lib / "one.lisp").write_text(quote + "\n" + real + "\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "lib/one.lisp"], cwd=root, check=True)
            sites = guard.project_definition_sites(root)
            self.assertNotIn("уявна", sites)
            self.assertEqual(sites["справжня"], {"lib/one.lisp"})

    def test_scanner_ignores_comments_strings_and_quoted_definitions(self) -> None:
        # Коментар, рядок і цитована форма не реєструють визначення.
        # Після цитати чинний виклик драбини не повинен губитися.
        spec = importlib.util.spec_from_file_location("guard_scanner_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        # Точний той самий Lisp-вхід збираємо частинами: Python перевіряє
        # тільки механіку сканера, а не містить окремого мовного оракула.
        source = (
            "; (" + "як-є ((" + "визначити з-коментаря (" + "функція (х) х))))\n"
            + '(' + 'визначити перша (' + 'функція (х)\n'
            + '  "(' + 'визначити з-рядка (' + 'функція (а) а))"\n'
            + '  (' + 'як-є ((' + 'визначити з-цитати (' + 'функція (а) а))))\n'
            + '  (' + 'сполучити х (' + 'як-є ()))))\n'
            + '(' + 'визначити друга (' + 'функція (х) х))\n'
        )
        found = guard.definitions_with_bodies(source)
        self.assertEqual([name for name, _, _ in found], ["перша", "друга"])
        self.assertTrue(guard._calls_ladder(found[0][1], guard.ladder_names(ROOT)))

    def test_search_finds_an_existing_surface_by_name(self) -> None:
        result = run(SEARCH, "сполучити")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("сполучити", result.stdout)

    def test_search_reuses_guard_scanner_for_existing_lisp_definitions(self) -> None:
        # Перевіряємо механіку пошуковика, а не семантичний результат SENS.
        # Ім'я є визначенням чинної lib/fs.lisp, не новою функцією в Python.
        result = run(SEARCH, "читати-файл-із-декодованого")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("УЖЕ ВИЗНАЧЕНО", result.stdout)
        self.assertIn("lib/fs.lisp", result.stdout)
        self.assertIn("ВЕРДИКТ: точний збіг", result.stdout)


if __name__ == "__main__":
    unittest.main()
