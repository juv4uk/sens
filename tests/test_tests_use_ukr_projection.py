"""Тести мусять бути написані укр-проєкцією, а не двійковими кодами.

Навіщо: агенти вчаться з тестів. Якщо SENS-програми в тестах написані кодами
(`(00001001 …` замість `(визначити …`), то й нові програми пишуться кодами —
саме це й сталося. Міграція на укр-проєкцію покрила `lib/`, але тести лишились
на застарілому кодуванні.

Чому окремий чекер, а не наявний `check_no_encoded_source_literals.py`: той
ловить БУДЬ-ЯКУ числову голову, і на тестах дає сотні хибних спрацювань на
законних тестових числах. Тут точне правило: голова форми, що є двійковим
рядком довжини 3..11, — це код домену, а не ім'я проєкції.

Політика власника: «все де 8бітне виключай». Тобто кодові голови заборонені.
Наявний борг заморожено у `knowledge/tests-legacy-binary-heads.json` (це БОРГ,
не дозвіл): чекер забороняє будь-який НОВИЙ кодовий голова, а список мусить
скорочуватися до нуля.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEBT = ROOT / "knowledge" / "tests-legacy-binary-heads.json"

# Двійкова голова форми: ( <3..11 біт> <пробіл>
BINARY_HEAD = re.compile(r"\(\s*([01]{3,11})\s")


def scan_text(text: str) -> list[str]:
    return [m.group(1) for m in BINARY_HEAD.finditer(text)]


def frozen_debt() -> dict[str, int]:
    document = json.loads(DEBT.read_text(encoding="utf-8"))
    return dict(document["files"])


def offenders() -> dict[str, int]:
    found: dict[str, int] = {}
    for base, pattern in ((ROOT / "tests", "*.py"), (ROOT / "crates", "**/tests/*.rs")):
        iterator = base.rglob(pattern) if pattern.startswith("**") else base.glob(pattern)
        for path in sorted(iterator):
            rel = path.relative_to(ROOT).as_posix()
            heads = scan_text(path.read_text(encoding="utf-8", errors="ignore"))
            if heads:
                found[rel] = len(heads)
    return found


class TestsUseUkrainianProjection(unittest.TestCase):
    def test_no_new_binary_coded_heads_appear_in_tests(self) -> None:
        debt = frozen_debt()
        new = {rel: n for rel, n in offenders().items() if rel not in debt}
        self.assertEqual(
            new,
            {},
            "тести мусять бути укр-проєкцією: нові двійкові голови [01]{3,11} заборонені "
            "(усе 8-бітне — легасі). Наявний борг заморожено у "
            "knowledge/tests-legacy-binary-heads.json і мусить скорочуватися.",
        )

    def test_frozen_debt_only_shrinks(self) -> None:
        debt = frozen_debt()
        current = offenders()
        # Жоден файл боргу не сміє мати БІЛЬШЕ кодових голів, ніж заморожено.
        grown = {rel: (debt[rel], current[rel]) for rel in debt if rel in current and current[rel] > debt[rel]}
        self.assertEqual(grown, {}, f"борг не сміє зростати: {grown}")

    def test_scanner_detects_binary_head_and_ignores_projection(self) -> None:
        self.assertEqual(scan_text("(00001001 x (00001000 (y) y))"), ["00001001", "00001000"])
        self.assertEqual(scan_text("(визначити x (функція (y) y))"), [])
        self.assertEqual(scan_text("(0011 x (0010 (y) y))"), ["0011", "0010"])


if __name__ == "__main__":
    unittest.main()
