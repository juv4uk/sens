"""Тест САМОГО правила драбин, а не лише інструмента поруч.

Раніше CI перевіряв, що інструмент виявлення кандидатів працює, але жоден тест
не вимагав, щоб нова програма НЕ дублювала наявну поверхню D1–D10. Через це
агент міг написати локальний дубль і пройти CI. Цей тест закриває саме ту діру.

Правило (AGENTS.md): функції беруться з D1–D10; наявне — вжити; немає в
драбинах — кандидат D11 (далі D12…), а не локальний дубль.
"""
from __future__ import annotations

import subprocess
import sys
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
        PROBE.write_text("(визначити сполучити (функція (х у) х))\n", encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 1, "дубль наявної поверхні мусить валити guard")
        self.assertIn("BLOCKED", result.stdout)

    def test_genuinely_new_name_is_a_candidate_not_a_block(self) -> None:
        PROBE.write_text("(визначити цілком-нова-річ-з-тесту (функція (х) х))\n", encoding="utf-8")
        result = run(GUARD, "--file", str(PROBE.relative_to(ROOT)))
        self.assertEqual(result.returncode, 0, "нове ім'я — не дубль, а кандидат D11")
        self.assertIn("КАНДИДАТ D11", result.stdout)

    def test_search_finds_an_existing_surface_by_name(self) -> None:
        result = run(SEARCH, "сполучити")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("сполучити", result.stdout)


if __name__ == "__main__":
    unittest.main()
