"""Перевірки первинної повної укр-проєкції lib/narrate.lisp."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NARRATE = ROOT / "lib/narrate.lisp"
D9 = ROOT / "lib/domains/d9.lisp"
D10 = ROOT / "lib/domains/d10.lisp"
RESULT_STATUS = ROOT / "lib/result-status.lisp"
# Справжній нативний свідок, не нове D4-визначення.
NARRATE_WITNESS = [
    "за-умовою",
    [["список-із-рівно-двох-елементів?", ["як-є", ["а", "б"]]],
     ["хибне?", ["список-із-рівно-двох-елементів?", ["як-є", ["а", "б", "в"]]]]],
    ["так", ["перше", ["як-є", []]]],
]

TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')

# (ширина, точний ключ, сумісне англійське ім'я, повне укр-ім'я)
PRIMARY = (
    (9, "000011000", "narrate-fact", "пояснити-факт"),
    (9, "000010110", "provenance-goal", "походження-ціль"),
    (9, "000101001", "provenance-source", "походження-джерело"),
    (9, "000001111", "provenance-rule", "походження-правило"),
    (9, "000011100", "provenance-derived-from", "походження-похідний-з"),
    (9, "000111000", "narrate-derivation", "пояснити-виведення"),
    (9, "000011011", "narrate-provenance", "пояснити-походження"),
    (9, "000000001", "narrate-answer", "пояснити-відповідь"),
    (9, "000100110", "narrate-outcome", "пояснити-підсумок"),
    (10, "0010101101", "narrate-proved-outcome", "пояснити-результат-із-доказом"),
    (10, "0010101110", "narrate-invalid-outcome-shape",
     "пояснити-неприпустиму-структуру-результату"),
)

# result-proper-list? — зовнішній binding з lib/result-status.lisp;
# цей файл лише зберігає на нього повну укр-проєкцію.
EXTERNAL_PEER = ("0010010110", "result-proper-list?", "результат-є-правильним-списком?")
HISTORIC = tuple(en for _width, _bits, en, _ukr in PRIMARY)
ВИЛУЧЕНІ_ПСЕВДОНІМИ = {
    "narrate-fact", "provenance-goal", "provenance-source",
    "provenance-rule", "provenance-derived-from",
    "narrate-derivation", "narrate-provenance", "narrate-answer",
    "narrate-outcome", "narrate-proved-outcome", "narrate-invalid-outcome-shape",
}


def read_forms(source: str):
    words = [m.group() for m in TOKEN.finditer(source)
             if not m.group().startswith(";")]
    position = 0

    def read():
        nonlocal position
        if position == len(words):
            raise ValueError("незавершена SENS форма")
        word = words[position]
        position += 1
        if word == ")":
            raise ValueError("зайва закривальна дужка")
        if word != "(":
            return word
        items = []
        while position < len(words) and words[position] != ")":
            items.append(read())
        if position == len(words):
            raise ValueError("незакритий список")
        position += 1
        return items

    result = []
    while position < len(words):
        result.append(read())
    return result


def definitions(source: str, *, final_witness=None):
    forms = read_forms(source)
    if final_witness is not None:
        if not forms or forms[-1] != final_witness:
            raise AssertionError("змінений або відсутній кінцевий SENS-виклик")
        forms = forms[:-1]
    result = {}
    for form in forms:
        if not isinstance(form, list) or not form:
            raise AssertionError("верхня форма має бути справжнім списком SENS")
        # Нативний виклик-свідок вже відокремлено й перевірено вище.
        # Жодну довільну верхню форму не пропускаємо як DEFINE.
        if form[0] not in ("0011", "визначити"):
            raise AssertionError("кожне верхнє визначення — D4:0011")
        if len(form) != 3:
            raise AssertionError("визначення D4:0011 має ім'я й тіло")
        name = form[1]
        if not isinstance(name, str) or name in result:
            raise AssertionError("дубль або неправильне ім'я DEFINE")
        result[name] = form[2]
    return result


def executable_forms(source: str):
    return [form for form in read_forms(source)
            if isinstance(form, list) and form
            and form[0] not in ("0011", "визначити")]


def call_heads(expr):
    """Викличні голови форми; цитовані структури лишаються даними."""
    if not isinstance(expr, list) or not expr:
        return set()
    if expr[0] in ("як-є", "001"):
        return set()
    found = {expr[0]} if isinstance(expr[0], str) else call_heads(expr[0])
    for child in expr[1:]:
        found |= call_heads(child)
    return found


class NarrateUkrPeerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src = NARRATE.read_text(encoding="utf-8")
        cls.defs = definitions(cls.src, final_witness=NARRATE_WITNESS)
        cls.result_status_defs = definitions(RESULT_STATUS.read_text(encoding="utf-8"))
        cls.domains = {
            9: D9.read_text(encoding="utf-8"),
            10: D10.read_text(encoding="utf-8"),
        }

    def test_primary_ukr_names_match_exact_ratified_domain_rows(self):
        for width, bits, english, ukrainian in PRIMARY:
            with self.subTest(domain=width, bits=bits):
                self.assertEqual(len(bits), width)
                rows = [
                    line.strip() for line in self.domains[width].splitlines()
                    if line.lstrip().startswith(f"({bits} ")
                ]
                self.assertEqual(len(rows), 1, f"D{width}:{bits}: expected one row")
                self.assertIn(f"(en {english})", rows[0])
                self.assertIn(f"(укр {ukrainian})", rows[0])
                self.assertIsInstance(self.defs.get(ukrainian), list,
                                      f"{ukrainian}: full name must own the SENS body")
                if english in ВИЛУЧЕНІ_ПСЕВДОНІМИ:
                    self.assertNotIn(english, self.defs,
                                     f"{english}: застарілий дубль не має повертатися")
                else:
                    self.assertEqual(self.defs.get(english), ukrainian,
                                     f"{english}: сумісний вхід має вести до української функції")
                self.assertNotRegex(
                    self.src,
                    rf"(?m)^\s*\({bits}(?:\s|\))",
                    "domain key must not become a raw executable head",
                )

    def test_external_result_status_alias_is_not_redefined_as_a_new_closure(self):
        bits, english, ukrainian = EXTERNAL_PEER
        self.assertEqual(len(bits), 10)
        rows = [
            line.strip() for line in self.domains[10].splitlines()
            if line.lstrip().startswith(f"({bits} ")
        ]
        self.assertEqual(len(rows), 1)
        self.assertIn(f"(en {english})", rows[0])
        self.assertIn(f"(укр {ukrainian})", rows[0])
        # Предикат належить result-status; narrate лише викликає його укр-ім'ям.
        self.assertNotIn(ukrainian, self.defs)
        self.assertIsInstance(self.result_status_defs.get(ukrainian), list)
        # Усі споживачі вже мають повну назву: англійський дубль не відновлюємо.
        self.assertNotIn(english, self.result_status_defs,
                         "Застарілий псевдонім result-proper-list? не повинен повертатися")
        self.assertIn(ukrainian, call_heads(self.defs["пояснити-підсумок"]))
        self.assertNotIn(english, call_heads(self.defs["пояснити-підсумок"]))

    def test_only_needed_english_entrypoints_remain(self):
        for _width, _bits, english, ukrainian in PRIMARY:
            with self.subTest(entrypoint=english):
                if english in ВИЛУЧЕНІ_ПСЕВДОНІМИ:
                    self.assertNotIn(english, self.defs)
                else:
                    self.assertEqual(self.defs.get(english), ukrainian)

    def test_narrate_outcome_has_only_primary_ukrainian_entrypoint(self):
        self.assertIn("пояснити-підсумок", self.defs)
        self.assertNotIn("narrate-outcome", self.defs)
        self.assertEqual(
            self.defs["пояснити-підсумок"][0], "функція"
        )

    def test_outcome_body_uses_full_ukr_heads(self):
        heads = call_heads(self.defs["пояснити-підсумок"])
        english_names = set(HISTORIC)
        self.assertTrue(english_names.isdisjoint(heads), heads)
        self.assertIn("пояснити-неприпустиму-структуру-результату", heads)
        self.assertIn("пояснити-результат-із-доказом", heads)

    def test_no_english_define_aliases_remain(self):
        self.assertFalse(
            set(HISTORIC) & set(self.defs),
            "англомовний DEFINE-дубль повернувся до активної бібліотеки",
        )
        self.assertEqual(set(self.defs) & {"пояснити-факт"}, {"пояснити-факт"})

    def test_real_narrate_witness_is_an_executable_ukr_form(self):
        # Жодного Python-обчислювача: перевірка лише форми,
        # істину/хибу доводить справжнє виконання Lisp у SENS.
        self.assertEqual(
            executable_forms(self.src),
            [["за-умовою",
              [["список-із-рівно-двох-елементів?", ["як-є", ["а", "б"]]],
               ["хибне?", ["список-із-рівно-двох-елементів?",
                             ["як-є", ["а", "б", "в"]]]]],
              ["так", ["перше", ["як-є", []]]]]],
        )

    def test_negative_return_of_removed_alias_is_caught(self):
        for legacy in ("narrate-fact", "narrate-proved-outcome"):
            with self.subTest(legacy=legacy):
                prefix, separator, witness = self.src.rpartition("\n; Два живих закони D1:")
                self.assertTrue(separator)
                broken = (prefix + f"\n(визначити {legacy} пояснити-факт)\n"
                          + separator + witness)
                broken_defs = definitions(broken, final_witness=NARRATE_WITNESS)
                with self.assertRaisesRegex(AssertionError, "застарілий англійський псевдонім"):
                    if legacy in broken_defs:
                        raise AssertionError("застарілий англійський псевдонім повернувся")

    def test_final_native_witness_and_negative_mutations(self):
        self.assertEqual(read_forms(self.src)[-1], NARRATE_WITNESS)
        for changed in (
            self.src.replace(
                "(список-із-рівно-двох-елементів? (як-є (а б в)))",
                "(список-із-рівно-двох-елементів? (як-є (а б)))",
            ),
            self.src + "\n(решта (як-є (а б)))\n",
        ):
            with self.assertRaisesRegex(AssertionError, "кінцевий SENS-виклик"):
                definitions(changed, final_witness=NARRATE_WITNESS)
        with self.assertRaisesRegex(AssertionError, "кінцевий SENS-виклик"):
            definitions(self.src + "\n(список-із-рівно-двох-елементів? (як-є (а б)))\n",
                        final_witness=NARRATE_WITNESS)

    def test_malformed_forms_rejected(self):
        with self.assertRaisesRegex(ValueError, "незакритий"):
            read_forms("(0011 неправильне (0010 ()")


if __name__ == "__main__":
    unittest.main(verbosity=2)
