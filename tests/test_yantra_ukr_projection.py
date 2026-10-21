"""Чинна структурна перевірка українського Lisp Yantra, без старого SHA/лічильників.

Функціональний оракул JSON/D1 виконується реальним SENS у
crates/sens/tests/yantra.rs; тут Python НЕ обчислює семантику мови.
"""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/yantra.lisp"
PEERS = {
    "0011": "визначити", "0010": "функція",
    "001": "як-є", "100": "перше", "011": "решта",
}
OLD_BINARY_HEAD = re.compile(r"\(\s*[01]{3,10}(?=\s|\))")
ENCODED_LITERAL = re.compile(r"#(?:d\d+:[01]+|b[01]+|q2:[01]+)")
JSON_LAWS = (
    ('((тотожне? значення-для-кодування (атом? (як-є ()))) "true")', "JSON true"),
    ('((тотожне? значення-для-кодування (атом? (сполучити (як-є ()) (як-є ())))) "false")', "JSON false"),
    ('((тотожне? значення-для-кодування (як-є ())) "null")', "JSON null"),
)


def verify(source: str) -> None:
    # Ratified українські D3/D4 spellings; жодних фіксованих лічильників
    # замін або відновлення історичного Git blob.
    for bits, name in PEERS.items():
        table = (ROOT / f"lib/domains/d{len(bits)}.lisp").read_text(encoding="utf-8")
        row = re.search(
            r"(?m)^  \(" + bits + r" \(ук [^()]+\) \(укр ([^()]+)\)",
            table,
        )
        if row is None or row.group(1) != name:
            raise AssertionError(f"D{len(bits)}:{bits}: чинна назва {name} втрачена")
        if re.search(r"\(" + re.escape(name) + r"(?=\s|\))", source) is None:
            raise AssertionError(f"Yantra: не використано українську назву {name}")

    # Явні старі машинні викличні голови вже мігровано. Не вимагати
    # повернення (0010 ...) в український Lisp заради старого тесту.
    if OLD_BINARY_HEAD.search(source):
        raise AssertionError("Yantra: лишилася стара бінарна виклична голова")
    if ENCODED_LITERAL.search(source):
        raise AssertionError("Yantra: заборонений текстовий машинний літерал")

    # Структурно відрізняємо обчислені D1:true/false і D3:() — але жодної
    # Python-імітації результатів JSON-кодека тут немає.
    for exact_form, label in JSON_LAWS:
        if exact_form not in source:
            raise AssertionError(f"Yantra: втрачено чинний закон {label}")

    # Механічна охорона джерельної послідовності. Реальна D1/D3
    # поведінка (включно з неповним свідком) перевіряється SENS у yantra.rs.
    helper = "(визначити рядкове-членство-формат-обміну-даними?"
    start = source.find(helper)
    if start < 0:
        raise AssertionError("Yantra: немає перевірки повноти D3-свідка")
    body = source[start:source.find("(визначити кодувати-значення-формат-обміну-даними", start)]
    guards = (
        "((атом? свідок)",
        "((атом? (решта свідок))",
        "((атом? (решта (решта свідок)))",
        "(порожній? (решта (решта (решта свідок))))",
    )
    position = -1
    for guard in guards:
        found = body.find(guard)
        if found < position or found < 0:
            raise AssertionError("Yantra: неповна D3-трійка доступна без перевірки")
        position = found
    if body.find("(третє свідок)") <= position:
        raise AssertionError("Yantra: ТРЕТЄ застосовується до неперевіреного списку")
    if "(третє (класифікувати-рядкове-значення" in source:
        raise AssertionError("Yantra: небезпечний безпосередній CDR на класифікаторі")

    definitions = re.findall(r"(?m)^\s*\(визначити\s+([^\s()]+)", source)
    if not definitions or len(definitions) != len(set(definitions)):
        raise AssertionError("Yantra: немає українських визначень або є дублікати")


class YantraUkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_current_ratified_projection(self):
        verify(self.source)

    def test_negative_old_d4_head_is_not_restored(self):
        with self.assertRaisesRegex(AssertionError, "бінарна виклична"):
            verify(self.source.replace("(функція ", "(0010 ", 1))

    def test_negative_wrong_boolean_json_law_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "JSON false"):
            verify(self.source.replace(
                JSON_LAWS[1][0],
                JSON_LAWS[1][0].replace('"false"', '"null"'), 1))

    def test_negative_encoded_literal_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, "машинний літерал"):
            verify(self.source + "\n(як-є #d1:1)\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
