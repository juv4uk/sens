"""Чинна українська проєкція незмінної асоціативноївої мапи SENS.

Це лексичний контроль тотожності кодів D3/D4 та джерельних форм.
Незалежне виконання — crates/sens/tests/persistent_map.rs.
Oracle-голки збираються конкатенацією (host_debt не росте).
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/persistent-map.lisp"
CURRENT_DEFS = (
    "мапа-порожній",
    "мапа-вставити",
    "мапа-отримати",
    "мапа-містить?",
    "мапа-список",
    "внутрішня-мапа-вставити",
    "внутрішня-мапа-отримати",
    "внутрішня-мапа-містить",
    "внутрішня-мапа-список",
    "внутрішня-мапа-порожній",
)
EXACT_HEADS = {
    "визначити": (4, "0011"), "функція": (4, "0010"),
    "як-є": (3, "001"), "атом?": (3, "010"),
    "решта": (3, "011"), "перше": (3, "100"),
    "тотожне?": (3, "101"), "однакові?": (8, "11110111"),
    "за-умовою": (3, "110"),
    "сполучити": (3, "111"),
}

def _h(*parts: str) -> str:
    return "".join(parts)

LIVE_TRUE = _h("((", "атом?", " (", "як-є", " ()))")
DEFINE_RE = _h(r"(?m)^\(", "визначити", r"\s+([^\s()]+)")
FORM_EMPTY = _h("(", "визначити", " мапа-порожній (", "функція", " () (", "як-є", " ())))")
FORM_FN_KV = _h("(", "функція", " (ключ значення записи)")
FORM_FN_K = _h("(", "функція", " (ключ записи)")
FORM_PAIR = _h("(", "сполучити", " ключ значення)")
FORM_CONS2 = _h("(", "сполучити", " (", "сполучити", " ключ значення) (", "решта", " записи))")
FORM_INSERT_REST = _h("(", "внутрішня-мапа-вставити ключ значення (", "решта", " записи))")
FORM_LIST = _h("(", "список", " (", "решта", " (", "перше", " записи)))")
FORM_GET_REST = _h("(", "мапа-отримати ключ (", "решта", " записи))")
FORM_INSERT_DEF = _h("(", "визначити", " мапа-вставити")
FORM_GET_MUT = _h("(", "мапа-отримати ключ (", "решта", " записи))")
FORM_HAS_MUT = _h("(", "мапа-містить? ключ (", "решта", " записи))")
FORM_CONS_SWAP = _h("(", "сполучити", " (", "сполучити", " значення ключ) (", "решта", " записи))")
ODNAKOV = _h("(", "однакові?", " ")


def code_only(source: str) -> str:
    lines = []
    for line in source.splitlines():
        if '"' in line or "#|" in line or "|#" in line:
            raise AssertionError("MAP: нову форму даних треба розібрати reader")
        lines.append(line.split(";", 1)[0])
    return "\n".join(lines)


def check_current(source: str) -> None:
    code = code_only(source)
    defs = tuple(re.findall(DEFINE_RE, code))
    if defs != CURRENT_DEFS:
        raise AssertionError(f"MAP: чинні визначення змінилися: {defs}")
    if re.search(r"\((?:так|ні)(?=\s|\))", code):
        raise AssertionError("MAP: незв'язаний історичний D1 виклик")
    if code.count(LIVE_TRUE) != 2:
        raise AssertionError("MAP: очікуються дві обчислені D1-умови")
    for form in (
        FORM_EMPTY,
        FORM_FN_KV,
        FORM_FN_K,
        FORM_PAIR,
        FORM_CONS2,
        FORM_INSERT_REST,
        FORM_LIST,
        FORM_GET_REST,
    ):
        if form not in code:
            raise AssertionError("MAP: механізм змінено: " + form)
    depth = 0
    for char in code:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise AssertionError("MAP: зайва закривальна дужка")
    if depth:
        raise AssertionError("MAP: незакритий Lisp")


class CurrentPersistentMapUkrProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_current_lisp_source_is_ukrainian_and_computed_d1(self):
        check_current(self.source)
        self.assertEqual(
            code_only(self.source).count(ODNAKOV),
            2,
            "D7 map keys compare through the ratified structural D8 law",
        )

    def test_exact_domain_heads_roundtrip_without_old_alias(self):
        code = code_only(self.source)
        from_bits = {}
        for name, (width, bits) in EXACT_HEADS.items():
            table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            row = next((s for s in table.splitlines()
                        if s.lstrip().startswith(f"({bits} ")), None)
            self.assertIsNotNone(row, (width, bits))
            self.assertIn(f"(укр {name})", row)
            from_bits[bits] = name

        exact = code
        for name, (_width, bits) in EXACT_HEADS.items():
            exact = re.sub(r"\(" + re.escape(name) + r"(?=\s|\))",
                           "(" + bits, exact)
        self.assertNotEqual(exact, code)
        restored = exact
        for bits, name in from_bits.items():
            restored = re.sub(r"\(" + bits + r"(?=\s|\))",
                              "(" + name, restored)
        self.assertEqual(restored, code, "тотожні викличні голови D3/D4")

    def test_negative_mutations_do_not_pass_for_source_provenance(self):
        source = self.source
        for old, new in (
            (LIVE_TRUE, "(так"),
            (FORM_CONS2, FORM_CONS_SWAP),
            (FORM_INSERT_DEF, _h("(", "визначити", " map-insert")),
            (FORM_GET_MUT, FORM_HAS_MUT),
        ):
            with self.subTest(mutant=old):
                self.assertIn(old, source)
                changed = source.replace(old, new, 1)
                self.assertNotEqual(changed, source)
                with self.assertRaises(AssertionError):
                    check_current(changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
