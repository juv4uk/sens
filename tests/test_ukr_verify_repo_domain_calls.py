"""Чинний український опис вимог до перевірки репозиторію.

Статична перевірка не є обчислювачем СЕНС і не сертифікує реліз.
Застаріле відтворення історичного Git blob за номерами рядків вилучено.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/verify-repo.lisp"

FUNCTION = "вимоги-перевірки-репозиторію"
REQUIRED = (
    "визначити", "функція", "за-умовою", "атом?", "тотожне?",
    "перше", "решта", "сполучити", "як-є", "список", "нехай",
)


def check_descriptor(source: str) -> None:
    """Відмовляти старому та підробленому успіху, не вдавати SENS-eval."""
    body = "\n".join(line for line in source.splitlines()
                     if not line.lstrip().startswith(";"))
    if not re.search(r"\(визначити\s+" + FUNCTION + r"\s+\(функція\s*\(\)", body):
        raise ValueError("немає чинного українського опису")
    if not re.search(r"\(стан\s+очікує-незалежної-перевірки\)", body):
        raise ValueError("декларація неправдиво заявляє перевірений стан")
    if not re.search(r"\(релізний-допуск\s+не-надано\)", body):
        raise ValueError("відсутня чесна заборона недоведеного релізу")
    if re.search(r"\(стан\s+(?:pass|успішно|пройдено)\)", body):
        raise ValueError("підроблений PASS")
    if re.search(r"\(визначити\s+(?:verify-repo|[A-Za-z][\w!?-]*)\b", body):
        raise ValueError("повернулися історичні латинські визначення")
    if re.search(r"\(\s*[01]{3,11}(?=\s|\))", body):
        raise ValueError("сирі бітові голови в проєкції")
    if re.search(r"\(за-умовою\s*\(\(атом\?\s+[^()]+\)\s+так\)\s*\(так\s+так\)", body):
        raise ValueError("фіктивний предикат завжди повертає так")
    if body.count("(вимоги-перевірки-репозиторію)") != 1:
        raise ValueError("немає єдиного виклику українського опису")
    if not all(re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", body)
               for name in REQUIRED):
        raise ValueError("втрачено перелік чинних мовних механізмів")


class VerifyRepoUkrDescriptorTests(unittest.TestCase):
    def test_current_ukrainian_source_is_only_requirements_not_pass(self):
        source = SOURCE.read_text(encoding="utf-8")
        check_descriptor(source)
        self.assertNotIn("(status pass)", source)
        self.assertNotIn("verify-repo-no-sid8-heads", source)

    def test_old_fake_success_or_obsolete_definition_fails(self):
        source = SOURCE.read_text(encoding="utf-8")
        for mutated in (
            source.replace("очікує-незалежної-перевірки", "pass", 1),
            source.replace("не-надано", "надано", 1),
            source.replace("вимоги-перевірки-репозиторію",
                           "verify-repo-uk-projection", 1),
            source.replace("(визначити ", "(0011 ", 1),
            source.replace("сполучити", "помилковий-виклик", 1),
        ):
            with self.subTest(mutated=mutated[:90]):
                with self.assertRaises(ValueError):
                    check_descriptor(mutated)

    def test_comments_do_not_change_requirement(self):
        source = SOURCE.read_text(encoding="utf-8")
        check_descriptor("; Інший коментар\n" + source)


if __name__ == "__main__":
    unittest.main()
