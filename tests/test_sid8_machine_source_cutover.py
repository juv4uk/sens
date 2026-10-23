"""Регресія машинних Lisp-джерел: чинна повна українська проєкція.

Перевірка джерела, не сертифікат виконання чи фізичної оберненості T5M.
Історичні SID8-голови й бітові D4-літерали не є викличним синтаксисом .lisp.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MACHINE = (
    "lib/machine/admission/x86-64.lisp",
    "lib/machine/atoms/x86-64.lisp",
    "lib/machine/encoding/x86-64.lisp",
    "lib/machine/operands/x86-64.lisp",
    "lib/machine/profile/minimal-runtime-x86-64.lisp",
    "lib/machine/projection/x86-64.lisp",
)
HEAD = re.compile(r"\(\s*([^\s()]+)")
LEGACY_HEAD = re.compile(r"(?:(?:sid8|sens8):)?[01]{8}\Z", re.IGNORECASE)


class MachineUkrDomainSource(unittest.TestCase):
    def test_full_ukr_heads_are_from_current_d4(self):
        domain = (ROOT / "lib/domains/d4.lisp").read_text(encoding="utf-8")
        self.assertRegex(domain, r"\(0011\s+\(ук\s+визначити\)\s+\(укр\s+визначити\)")
        self.assertRegex(domain, r"\(0010\s+\(ук\s+функція\)\s+\(укр\s+функція\)")

    def test_six_machine_sources_use_ukr_not_legacy_binary_heads(self):
        self.assertEqual(len(MACHINE), 6)
        for path in MACHINE:
            with self.subTest(path=path):
                source = (ROOT / path).read_text(encoding="utf-8")
                heads = [m.group(1) for m in HEAD.finditer(source)]
                self.assertIn("визначити", heads)
                self.assertIn("функція", heads)
                self.assertFalse(any(LEGACY_HEAD.fullmatch(head) for head in heads))
                self.assertFalse(any(head in {"0010", "0011"} for head in heads))
                self.assertNotRegex(source, r"\(\s*(?:sid8|sens8):[01]{8}(?=\s|\))")

    def test_generated_machine_evidence_is_not_rewritten_as_program(self):
        for path in (
            "lib/machine/encoding/coverage.lisp",
            "lib/machine/encoding/admitted-iclass-index.lisp",
            "lib/machine/encoding/admission-iclass-projection.lisp",
        ):
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("GENERATED", text[:240])


if __name__ == "__main__":
    unittest.main()
