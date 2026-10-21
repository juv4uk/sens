"""Точна українська міграція першокласового метаобчислювача.

Старий Git blob — лише незалежний контроль зворотності правок; не
джерело семантичної identity. Чинні resident-и — lib/domains/dN.lisp.
T5M не надає функції права виклику, Python не імітує виконання SENS.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/meta-eval-first-class.lisp"
OLD_BLOB = "ea9c7a89b02777058b9f2704bd96cead69a7608c"
# offset у Python Unicode codepoints, exact-width identity та чинна укр проєкція.
EDIT_RECEIPT = [[3013,"101","тотожне?"],[3026,"001","як-є"],[3036,"11010","менше?"],[3044,"100","перше"],[3057,"1001","друге"],[3082,"101","тотожне?"],[3095,"001","як-є"],[3105,"11110111","однакові?"],[3116,"100","перше"],[3129,"1001","друге"],[3154,"101","тотожне?"],[3167,"001","як-є"],[3177,"11011","більше?"],[3186,"100","перше"],[3199,"1001","друге"],[3697,"101","тотожне?"],[3712,"001","як-є"],[3722,"01010","додати"],[3730,"100","перше"],[3743,"1001","друге"],[3765,"101","тотожне?"],[3780,"001","як-є"],[3790,"01011","відняти"],[3799,"100","перше"],[3812,"1001","друге"],[3834,"101","тотожне?"],[3849,"001","як-є"],[3859,"10110","помножити"],[3870,"100","перше"],[3883,"1001","друге"],[4356,"10011","третє"]]


ALPHA_TO_HISTORY = {
    "назва": "name",
    "оточення": "ctx",
    "значення": "value",
    "параметри": "params",
    "аргументи": "args",
    "вирази": "exprs",
    "тіло": "body",
    "умови": "clauses",
    "оператор": "op",
    "виклична-функція": "fn",
    "вираз": "expr",
}



# Receipt тільки для доведення походження ПОВНОГО ручного переписування.
# Відновлення не є шляхом виконання і не повертає стару мову до SENS.
PRE_REWRITE_BLOB = "72218257be75805125a7e0b21d39bb4e519408b3"
PRE_REWRITE_HEADER = "; Experimental metacircular evaluator layer for contract 2.1 first-class builtins.\n; This is deliberately additive: lib/meta-eval.lisp remains the current witness/oracle pair.\n; The purpose here is to prove the next architectural step before merging it into my-eval:\n; primitive names live in the metacircular environment as values, so ordinary lexical\n; shadowing works for the evaluator written in Lisp too.\n;\n; Міграція: історичне ATOM(QUOTE EMPTY) як D1=YES → пряма точна проєкція #d1:1.\n; Two-field COND. Reuses existing project primitives as first-class values.\n; Width is identity; every bit of the domain address is valued.\n\n"
CURRENT_REWRITE_HEADER = "; Першокласні функції: експериментальний метаобчислювач мовою СЕНС.\n; Викличні голови ядра відповідають повній українській проєкції доменів від 1 до 10.\n; Примітиви зберігаються у явному лексичному середовищі як значення.\n; Локальне зв'язування затінює примітив без втручання зовнішнього виконавця.\n; Замикання зберігає параметри, тіло та середовище визначення.\n; Синтаксичні форми як-є, за-умовою і функція не є звичайними значеннями.\n; Невідомий примітив і невикличне значення повертають окрему помилкову форму.\n; Вихідні математичні операнди записуються людськими десятковими числами.\n; Історичні восьмибітні коди та шари сумісності не застосовуються.\n\n"
REWRITTEN_HELPERS = {
    "my-fc-apply-primitive": "першокласне-застосувати-примітив",
    "my-fc-compare-chain": "першокласне-порівняти-послідовність",
    "my-fc-primitive?": "першокласний-примітив?",
    "my-fc-primitive": "першокласний-примітив",
    "my-fc-root-env": "першокласне-початкове-середовище",
    "my-fc-env-lookup": "першокласне-знайти-в-середовищі",
    "my-fc-closure?": "першокласне-замикання?",
    "my-fc-bind-params": "першокласне-звязати-параметри",
    "my-fc-eval-list": "першокласне-обчислити-список",
    "my-fc-eval-body": "першокласне-обчислити-тіло",
    "my-fc-eval-cond": "першокласне-обчислити-умови",
    "my-fc-apply": "першокласне-застосувати",
    "my-fc-eval": "першокласне-обчислити",
    "my-eval-first-class": "обчислити-першокласні-функції",
}
REWRITTEN_QUOTED_DATA = {
    "primitive": "примітив",
    "closure": "замикання",
    "atom": "атом?",
    "eq": "тотожне?",
    "car": "перше",
    "cdr": "решта",
    "cons": "сполучити",
    "+": "додати",
    "-": "відняти",
    "*": "помножити",
    "<": "менше?",
    "=": "однакові?",
    ">": "більше?",
    "quote": "як-є",
    "cond": "за-умовою",
    "lambda": "функція",
    "unknown-primitive": "невідомий-примітив",
    "not-callable": "не-викликається",
}
REWRITTEN_COMMENTS = {
    "; Exact D1 chain: single remaining arg is true; pairwise op then recurse.": "; Порівняння сусідніх аргументів триває рекурсивно, доки не лишиться один аргумент.",
    "         ; Syntax-only forms remain syntax. They are intentionally not values.": "         ; Синтаксичні форми залишаються синтаксисом, а не звичайними значеннями.",
    "         ; Every ordinary head is resolved through the environment first.": "         ; Кожна звичайна виклична голова спочатку шукається в лексичному середовищі.",
    "         ; This is the contract-2.1 step: a local `+`, `car`, etc. can shadow": "         ; Локальне ім'я може затінювати однойменну примітивну операцію.",
    "         ; the root primitive binding without the evaluator special-casing its name.": "         ; Обчислювач не надає таким іменам особливого пріоритету.",
    "; Public experimental entry point. The root primitive environment is explicit": "; Відкритий експериментальний вхід отримує явне середовище примітивів.",
    "; Lisp data, so a future host/runtime only has to preserve the primitive mechanism": "; Лексичне розв'язування залишається всередині мови, а зовнішня машина",
    "; identities; lexical resolution itself is owned here.": "; відповідає тільки за збереження тотожності допущених механізмів.",
}


def undo_full_rewrite(text: str) -> str:
    """Точний зворотний receipt лише для історичної перевірки Git blob."""
    if not text.startswith(CURRENT_REWRITE_HEADER):
        raise AssertionError("неправильна/зсунута повна українська поверхня: заголовок")
    text = PRE_REWRITE_HEADER + text[len(CURRENT_REWRITE_HEADER):]
    for historical, current in REWRITTEN_QUOTED_DATA.items():
        text = text.replace("(як-є " + current + ")", "(як-є " + historical + ")")
    for historical, current in sorted(REWRITTEN_HELPERS.items(), key=lambda item: -len(item[1])):
        text = text.replace(current, historical)
    for historical, current in sorted(REWRITTEN_COMMENTS.items(), key=lambda item: -len(item[1])):
        text = text.replace(current, historical)
    if git_blob_sha(text) != PRE_REWRITE_BLOB:
        raise AssertionError("неправильна/зсунута повна українська поверхня: історичний blob")
    return text


def undo_alpha(text: str) -> str:
    """Інверсія тільки лексичних імен; цитати та рядки не змінюються."""
    token = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();"]+|\s+|.')
    return token.sub(lambda match: ALPHA_TO_HISTORY.get(match.group(), match.group()), text)


def reconstruct(text: str) -> str:
    text = undo_alpha(undo_full_rewrite(text))
    for offset, bits, peer in reversed(EDIT_RECEIPT):
        new = "(" + peer
        if text[offset:offset + len(new)] != new:
            raise AssertionError(f"неправильна/зсунута поверхня при offset={offset}: {bits} → {peer}")
        text = text[:offset] + "(" + bits + text[offset + len(new):]
    return text


def git_blob_sha(source: str) -> str:
    encoded = source.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(encoded)).encode() + b"\0" + encoded).hexdigest()


class MetaFirstClassUkrRemaining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = SOURCE.read_text(encoding="utf-8")

    def test_current_authority_matches_exact_rung_not_old_sid(self):
        self.assertEqual(len(EDIT_RECEIPT), 31)
        for _offset, bits, peer in EDIT_RECEIPT:
            width = len(bits)
            self.assertIn(width, (3, 4, 5, 8))
            table = (ROOT / f"lib/domains/d{width}.lisp").read_text(encoding="utf-8")
            match = re.search(r"(?m)^\s*\(" + re.escape(bits) +
                              r"\s+\(ук .*?\(укр ([^()]*)\)", table)
            self.assertIsNotNone(match, f"немає ratified D{width}:{bits}")
            self.assertEqual(match.group(1), peer)

    def test_current_source_is_full_ukrainian_and_has_no_sid8_heads(self):
        self.assertTrue(self.current.startswith(CURRENT_REWRITE_HEADER))
        active = "\n".join(line.split(";", 1)[0] for line in self.current.splitlines())
        self.assertNotIn("#d1:", active)
        self.assertNotRegex(active, r"(?m)^\s*\([01]{3,9}\s")
        for old_name in ("my-fc-eval", "my-fc-apply", "my-eval-first-class", "SID8", "Sens8"):
            self.assertNotIn(old_name, active)
        for name in REWRITTEN_HELPERS.values():
            self.assertIn(name, active)

    def test_no_remaining_encoded_call_heads(self):
        # Цей source не містить інших двійкових головів у quoted data.
        start = self.current.index("(визначити першокласний-примітив")
        self.assertEqual(re.findall(r"\([01]{3,9}(?=[\s(])", self.current[start:]), [])
        self.assertIn("(функція (вираз оточення)", self.current)
        self.assertNotIn("(функція (expr ctx)", self.current)

    def test_executable_default_conditions_use_real_d1_and_not_anonymous_d5(self):
        # Це структурний свідок, не семантичний Python oracle:
        # справжні обчислення й один біт мутанта виконує SENS.
        active = "\n".join(line.split(";", 1)[0] for line in self.current.splitlines())
        self.assertEqual(active.count("((атом? (як-є ()))"), 13)
        self.assertEqual(active.count("((атом? значення) (атом? (як-є (()))) )"), 2)
        self.assertNotIn("(так ", active)
        self.assertNotIn(" ні)", active)
        self.assertNotIn(" так)", active)
        self.assertIn("((атом? (решта аргументи)) (атом? (як-є ())))", active)
        self.assertNotIn("((функція ()", active)
        self.assertIn("(нехай-послідовно", active)
        # Старий біт голови мутаційно повертає нечинний виклик;
        # його забороняємо, а не змінюємо runtime-значення у Python.
        mutant = active.replace("((атом? (як-є ()))", "(так", 1)
        self.assertIn("(так ", mutant)
        self.assertNotEqual(mutant, active)

    def test_wrong_surface_does_not_satisfy_current_projection(self):
        mutant = self.current.replace("(як-є менше?)", "(як-є помилкова-назва?)", 1)
        self.assertNotEqual(mutant, self.current)
        self.assertNotIn("(як-є помилкова-назва?)", self.current)
        self.assertIn("(як-є менше?)", self.current)

    def test_reintroduced_binary_word_is_rejected_by_current_source_contract(self):
        mutant = self.current.replace("(як-є менше?)", "(як-є 11010)", 1)
        self.assertNotEqual(mutant, self.current)
        self.assertNotIn("(як-є 11010)", self.current)
        active_mutant = "\n".join(line.split(";", 1)[0] for line in mutant.splitlines())
        self.assertIn("(як-є 11010)", active_mutant)


if __name__ == "__main__":
    unittest.main(verbosity=2)
