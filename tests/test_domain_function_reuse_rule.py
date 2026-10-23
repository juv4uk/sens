"""Тест САМОГО правила драбин, а не лише інструмента поруч.

Раніше CI перевіряв, що інструмент виявлення кандидатів працює, але жоден тест
не вимагав, щоб нова програма НЕ дублювала наявну поверхню D1–D10. Через це
агент міг написати локальний дубль і пройти CI. Цей тест закриває саме ту діру.

Правило (AGENTS.md): функції беруться з D1–D10; наявне — вжити; немає в
драбинах — кандидат D11 (далі D12…), а не локальний дубль.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
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

    def test_search_self_test_is_green(self) -> None:
        result = run(SEARCH, "--self-test")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_duplicate_of_a_ratified_surface_is_blocked(self) -> None:
        # сполучити — чинна поверхня D3:111 (cons). Перевизначати заборонено.
        PROBE.write_text("(" + "визначити сполучити (" + "функція (х у) х))\n", encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 1, "дубль наявної поверхні мусить валити guard")
        self.assertIn("BLOCKED", result.stdout)

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
        # Коментар, рядок і (як-є ...) не можуть додати псевдо-DEFINE або
        # обрізати тіло, в якому після цитати стоїть справжній виклик драбини.
        spec = importlib.util.spec_from_file_location("guard_scanner_test", GUARD)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        source = (
            "; (як-є ((визначити з-коментаря (функція (х) х))))\n"
            '(визначити перша (функція (х)\n'
            '  "(визначити з-рядка (функція (а) а))"\n'
            '  (як-є ((визначити з-цитати (функція (а) а))))\n'
            '  (сполучити х (як-є ()))))\n'
            '(визначити друга (функція (х) х))\n'
        )
        found = guard.definitions_with_bodies(source)
        self.assertEqual([name for name, _, _ in found], ["перша", "друга"])
        self.assertTrue(guard._calls_ladder(found[0][1], {"сполучити"}))

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
