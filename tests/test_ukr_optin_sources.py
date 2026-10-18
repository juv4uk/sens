"""Доказові регресії вузької міграції opt-in модулів на повне SENS укр.

Жодного Python evaluator для семантики SENS: перевіряємо тільки форму вихідних
S-expressions, ratified identity, незмінність історичних виконуваних законів
(після оберненої заміни peer spelling) та наявність binding-псевдонімів.
Фізичний SENS eval і admissibility не випливають із цих AST-тестів.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / "lib/epistemic.lisp"
STORE = ROOT / "lib/content-store.lisp"
CORE = ROOT / "lib/core4.lisp"
D9 = ROOT / "lib/domains/d9.lisp"
D10 = ROOT / "lib/domains/d10.lisp"

TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
UNDO = {
    "доказ?": "evidence?",
    "доказ-підсумок": "evidence-outcome",
    "отримати-посилання-доказу-на-твердження": "evidence-claim-ref",
    "намір?": "intent?",
    "отримати-необхідні-можливості-наміру": "intent-requires",
}
EXPECTED_SUPPORT = """
(0011 supporting-evidence
  (0010 (evidence claim-ref)
    (110
      ((0100 (evidence? evidence)) (001 ()))
      ((0100 (epistemic--claim-ref? claim-ref)) (001 ()))
      ((0100 (101 (evidence-outcome evidence) (001 supports))) (001 ()))
      ((0100 (епістеміка--рівні-посилання? (evidence-claim-ref evidence) claim-ref)) (001 ()))
      (#d1:1 evidence))))
"""
EXPECTED_INTENT = """
(0011 intent-capabilities-satisfied?
  (0010 (intent effective-capabilities)
    (110
      ((0100 (intent? intent)) #d1:0)
      (#d1:1
       (epistemic--all-required-present? (intent-requires intent) effective-capabilities)))))
"""

# Це точні D9/D10 координати, не SID8, не фізичні опкоди.
PEERS = (
    (10, "0001110110", "make-claim", "створити-структуроване-твердження"),
    (10, "0010011001", "source-ref?", "це-належне-посилання-на-джерело?"),
    (10, "0001110111", "observation-source", "отримати-джерело-спостереження"),
    (10, "0010000111", "evidence-claim-ref", "отримати-посилання-доказу-на-твердження"),
    (10, "0001111011", "intent-requires", "отримати-необхідні-можливості-наміру"),
    (9, "101100001", "supporting-evidence", "підтверджувальний-доказ"),
    (10, "0001111110", "intent-capabilities-satisfied?",
     "усі-необхідні-можливості-наміру-забезпечені?"),
    (9, "101010110", "evidence?", "доказ?"),
    (9, "101111111", "evidence-outcome", "доказ-підсумок"),
    (9, "101101100", "intent?", "намір?"),
    (9, "101100011", "map-empty", "мапа-порожній"),
)


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


def definitions(source: str):
    result = {}
    for form in read_forms(source):
        if not isinstance(form, list) or len(form) != 3 or form[0] not in ("0011", "визначити"):
            raise AssertionError("кожне верхнє визначення — D4:0011")
        name = form[1]
        if not isinstance(name, str) or name in result:
            raise AssertionError("дубль або неправильне ім'я DEFINE")
        result[name] = form[2]
    return result


def restore_call_heads(tree):
    """Обернена зміна ТІЛЬКИ executable head; параметри й quoted data не чіпаємо."""
    if not isinstance(tree, list):
        return "#d1:0" if tree == "ні" else tree
    if not tree:
        return []
    first = tree[0]
    if first == "001":
        return tree  # quoted data збереглися побайтово за логічною формою
    restorations = {**UNDO, "хибне?": "0100", "тотожне?": "101",
                    "як-є": "001", "функція": "0010",
                    "атом?": "010", "решта": "011", "перше": "100", "за-умовою": "110", "сполучити": "111", "застосувати": "0000", "обчислити": "0001", "визначити": "0011", "порожній?": "0101", "решта-першого": "0110", "решта-решти": "0111", "перше-першого": "1000", "друге": "1001", "знайти": "1010", "зв'язати": "1011", "обчислити-умови": "1100", "обчислити-список": "1101", "список": "1110", "приєднати": "1111"}
    head = restorations.get(first, first) if isinstance(first, str) else restore_call_heads(first)
    return [head] + [restore_call_heads(arg) for arg in tree[1:]]


def verify(ep: str, store: str, core: str, domains: dict[int, str]):
    epdefs, storedefs = definitions(ep), definitions(store)

    # Слово з таблиці має рівно свій ratified domain і full spelling.
    for width, bits, english, full in PEERS:
        rows = [line.strip() for line in domains[width].splitlines()
                if line.lstrip().startswith(f"({bits} ")]
        if len(rows) != 1 or (f"(en {english})" not in rows[0]
                              or f"(укр {full})" not in rows[0]):
            raise AssertionError(f"D{width}:{bits}: peer spelling / identity drift")

    aliases = {
        "створити-структуроване-твердження": "створити-твердження",
        "make-claim": "створити-структуроване-твердження",
        "це-належне-посилання-на-джерело?": "source-ref?",
        "отримати-джерело-спостереження": "observation-source",
        "отримати-посилання-доказу-на-твердження": "evidence-claim-ref",
        "отримати-необхідні-можливості-наміру": "intent-requires",
        "підтверджувальний-доказ": "supporting-evidence",
        "усі-необхідні-можливості-наміру-забезпечені?":
            "intent-capabilities-satisfied?",
    }
    for name, target in aliases.items():
        if epdefs.get(name) != target:
            raise AssertionError(f"{name}: потрібний exact-value DEFINE alias на {target}")
    for old in ("make-observation", "make-claim", "make-evidence", "make-intent",
                "source-ref?", "observation-source", "evidence-claim-ref",
                "intent-requires", "supporting-evidence", "intent-capabilities-satisfied?"):
        if old not in epdefs:
            raise AssertionError(f"історичний entrypoint {old} утрачено")

    # Епістемічні історичні входи оголошено в самому opt-in модулі;
    # map-empty є bootstrap alias у Core4. Обидва випадки — те саме значення,
    # а не повторна функція під новим ім'ям.
    for source_name, same_closure in (
        ("evidence?", "доказ?"), ("intent?", "намір?"),
    ):
        if epdefs.get(source_name) != same_closure:
            raise AssertionError(f"{source_name}: opt-in peer identity порушено")
    if "(0011 map-empty мапа-порожній)" not in core:
        raise AssertionError("map-empty: core peer identity порушено")
    for value in ("створити-твердження", "доказ-підсумок"):
        if f"(0011 {value}\n" not in core and f"(0011 {value} " not in core:
            raise AssertionError(f"{value}: джерельний SENS closure не визначений")

    # Суворий мовний допуск: історична латинська виклична голова НЕ стає
    # ukr лише тому, що обернена нормалізація дає той самий закон.
    def heads(expr):
        if not isinstance(expr, list) or not expr:
            return set()
        first = expr[0]
        if first in ("як-є", "001"):
            return {first}
        result = {first} if isinstance(first, str) else heads(first)
        for child in expr[1:]:
            result |= heads(child)
        return result

    live = set()
    for name in ("supporting-evidence", "intent-capabilities-satisfied?"):
        live |= heads(epdefs[name])
    if not set(UNDO).issubset(live) or set(UNDO.values()) & live:
        raise AssertionError("SENS закон: не вся виклична поверхня стала повною укр")

    for name, frozen in (
        ("supporting-evidence", EXPECTED_SUPPORT),
        ("intent-capabilities-satisfied?", EXPECTED_INTENT),
    ):
        golden = definitions(frozen)[name]
        actual = restore_call_heads(epdefs[name])
        if actual != golden:
            raise AssertionError(f"{name}: після peer normalization змінився SENS закон")

    expected_empty = ["0010", [], "map-empty"]
    if restore_call_heads(storedefs["empty-content-store"])[0:2] != expected_empty[0:2]:
        raise AssertionError("empty-content-store: змінені arity/форма D4 LAMBDA")
    if storedefs["empty-content-store"] != ["функція", [], "мапа-порожній"]:
        raise AssertionError("порожнє сховище має посилатися на чинний SENS peer")

    # Інші історичні входи та shapes сховища лишаються дієвими.
    for name in ("content-store-put", "content-store-get", "content-store-contains?",
                 "content-store-put-world", "content-store-size"):
        if name not in storedefs:
            raise AssertionError(f"content-store: утрачене визначення {name}")
    if storedefs.get("вміст-сховище-покласти") != "content-store-put":
        raise AssertionError("content-store-put: історичний/укр alias не тотожний")
    if storedefs.get("вміст-сховище-покласти-світ") != "content-store-put-world":
        raise AssertionError("content-store-put-world: історичний/укр alias не тотожний")
    return True


class OptInUkrMigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ep = EP.read_text(encoding="utf-8")
        cls.store = STORE.read_text(encoding="utf-8")
        cls.core = CORE.read_text(encoding="utf-8")
        cls.domains = {d: (ROOT / f"lib/domains/d{d}.lisp").read_text(encoding="utf-8")
                       for d in (9, 10)}

    def test_exact_identity_and_laws(self):
        self.assertTrue(verify(self.ep, self.store, self.core, self.domains))

    def test_data_tags_are_not_transliterated(self):
        for spelling in ("(001 digest)", "(001 proof)", "(001 test)",
                         "(001 observation)", "(001 claim-ref)", "(як-є supports)"):
            self.assertIn(spelling, self.ep)

    def test_old_english_calls_do_not_remain_in_migrated_laws(self):
        epdefs = definitions(self.ep)
        selected = (epdefs["supporting-evidence"],
                    epdefs["intent-capabilities-satisfied?"])
        def heads(expr):
            if not isinstance(expr, list) or not expr:
                return []
            if expr[0] == "001":
                return []
            return ([
                expr[0]
            ] if isinstance(expr[0], str) else heads(expr[0])) + [
                s for v in expr[1:] for s in heads(v)
            ]
        left = set(s for tree in selected for s in heads(tree))
        self.assertTrue(set(UNDO.values()).isdisjoint(left), left)
        self.assertTrue(set(UNDO).issubset(left), left)

    def test_negative_old_latin_call(self):
        broken = self.ep.replace("(доказ? evidence)", "(evidence? evidence)", 1)
        self.assertNotEqual(broken, self.ep)
        with self.assertRaisesRegex(AssertionError, "SENS закон"):
            verify(broken, self.store, self.core, self.domains)

    def test_negative_wrong_ukr_identity(self):
        broken = dict(self.domains)
        broken[10] = broken[10].replace(
            "(укр створити-структуроване-твердження)",
            "(укр інша-семантика)", 1)
        self.assertNotEqual(broken[10], self.domains[10])
        with self.assertRaisesRegex(AssertionError, "peer spelling"):
            verify(self.ep, self.store, self.core, broken)

    def test_negative_wrong_alias(self):
        broken = self.ep.replace(
            "(визначити make-claim створити-структуроване-твердження)",
            "(визначити make-claim створити-доказ)", 1)
        self.assertNotEqual(broken, self.ep)
        with self.assertRaisesRegex(AssertionError, "exact-value DEFINE"):
            verify(broken, self.store, self.core, self.domains)

    def test_negative_store_falls_back_to_english(self):
        broken = self.store.replace(
            "(функція () мапа-порожній)", "(функція () map-empty)", 1)
        self.assertNotEqual(broken, self.store)
        with self.assertRaisesRegex(AssertionError, "чинний SENS peer"):
            verify(self.ep, broken, self.core, self.domains)

    def test_negative_removing_historical_entrypoint(self):
        broken = self.ep.replace("(визначити make-observation створити-спостереження)", "", 1)
        with self.assertRaisesRegex(AssertionError, "entrypoint"):
            verify(broken, self.store, self.core, self.domains)

    def test_ratifed_ukrainian_d3_d4_surface_in_both_modules(self):
        wanted = {"0010": "функція", "0011": "визначити",
                  "010": "атом?", "011": "решта", "100": "перше",
                  "101": "тотожне?", "110": "за-умовою",
                  "0100": "хибне?", "1001": "друге"}
        for bits, full in wanted.items():
            table = (ROOT / f"lib/domains/d{len(bits)}.lisp").read_text(encoding="utf-8")
            rows = [line for line in table.splitlines()
                    if line.lstrip().startswith(f"({bits} ")]
            self.assertEqual(len(rows), 1)
            self.assertIn(f"(укр {full})", rows[0])
        for source in (self.ep, self.store):
            parsed = read_forms(source)
            self.assertTrue(parsed)
            self.assertTrue(all(form[0] == "визначити" for form in parsed))
            for bits in wanted:
                self.assertNotRegex(source, r"\(" + re.escape(bits) + r"(?=[\s(])")
        self.assertTrue(verify(self.ep, self.store, self.core, self.domains))

    def test_negative_old_raw_head_is_rejected_by_projection_rule(self):
        old = self.ep.replace("(за-умовою", "(110", 1)
        self.assertNotEqual(old, self.ep)
        self.assertRegex(old, r"\(110(?=[\s(])")
        for bits in ("110", "0011", "0010"):
            self.assertNotRegex(self.ep, r"\(" + bits + r"(?=[\s(])")

    def test_malformed_forms_rejected(self):
        with self.assertRaisesRegex(ValueError, "незакритий"):
            read_forms("(0011 неправильне (0010 ())")
        with self.assertRaisesRegex(ValueError, "закривальна"):
            read_forms("())")

if __name__ == "__main__":
    unittest.main()
