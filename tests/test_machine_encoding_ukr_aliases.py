"""D7/T5M: машинні виконавчі імена без змішування кирилиці з ASCII.

Тест не емулює SENS; перевіряє лише українську вихідну поверхню.
Справжня семантика і фізичний T5M вимагають окремого виконання.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENCODER = ROOT / "lib/machine/encoding/x86-64.lisp"


class MachineEncodingUkrAliases(unittest.TestCase):
    def test_only_one_ukrainian_binding_for_each_machine_operation(self):
        src = ENCODER.read_text(encoding="utf-8")
        for name in (
            "машина-ціла-частка-та-залишок",
            "машина-байти-без-знака",
            "машина-сполучити-байти",
        ):
            with self.subTest(name=name):
                self.assertEqual(
                    len(re.findall(r"(?m)^\(визначити\s+" + re.escape(name) + r"(?=\s)", src)),
                    1,
                )
        names = re.findall(r"(?m)^\(визначити\s+([^\s()]+)", src)
        mixed = [
            name for name in names
            if re.search(r"[A-Za-z]", name)
            and re.search(r"[\u0400-\u052F]", name)
        ]
        self.assertEqual(mixed, [])

    def test_mixed_legacy_aliases_do_not_return(self):
        src = ENCODER.read_text(encoding="utf-8")
        for name in ("x86-ціла-частка-залишок", "x86-байти-без-знака",
                     "x86-сполучити-байти"):
            with self.subTest(alias=name):
                self.assertNotRegex(
                    src, r"(?m)^\(визначити\s+" + re.escape(name) + r"\s"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
