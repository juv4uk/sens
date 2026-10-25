"""Regression for current D3/D4 Ukrainian Core3 projections.

Static AST equivalence and negative mutants are only guards. The real verdict
belongs to tests/semantic/core3-executors-d3-law.bits under the SENS evaluator.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/core3.lisp"
TABLES = (ROOT / "lib/domains/d3.lisp", ROOT / "lib/domains/d4.lisp")
OLD_LAW = """
(0011 core3-executors
  (111 (001 common-lisp)
    (111 (001 prolog)
      (111 (001 clips)
        (111 (001 datalog)
          (001 ()))))))
(0011 core3-route
  (0010 (sid executor)
    (mechanism-select sid executor)))
(0011 core3-add-routes
  (0010 (sid)
    (1110
      (core3-route sid (001 common-lisp))
      (core3-route sid (001 prolog))
      (core3-route sid (001 clips))
      (core3-route sid (001 datalog)))))
(0011 core3-profile-status
  (0010 ()
    (001
      (core3
        (contract "7" "0")
        (role experimental-kernel-laboratory)
        (selector shared-lisp-owned)
        (lowering partial)
        (clips-result-observation blocked)
        (four-island-round-trip pending)))))

(core3-profile-status)
"""


def scan(source):
    tokens = re.findall(r";[^\n]*|\"(?:\\.|[^\"\\])*\"|[()]|[^\s();]+", source)
    tokens = [x for x in tokens if not x.startswith(";")]
    i = 0
    def node():
        nonlocal i
        if i == len(tokens):
            raise AssertionError("unterminated")
        tok = tokens[i]
        i += 1
        if tok == ")":
            raise AssertionError("extra close")
        if tok != "(":
            return tok
        result = []
        while i < len(tokens) and tokens[i] != ")":
            result.append(node())
        if i == len(tokens):
            raise AssertionError("unterminated")
        i += 1
        return result
    result = []
    while i < len(tokens):
        result.append(node())
    return result


def projection():
    seen = {}
    for path in TABLES:
        for bits, name in re.findall(
            r"(?m)^  \(([01]+) \(ук ([^()\s]+)\)",
            path.read_text(encoding="utf-8"),
        ):
            if len(bits) not in (3, 4):
                continue
            if name in seen:
                raise AssertionError(f"non-unique identity projection: {name}")
            seen[name] = bits
    return seen


def canonicalize(ast, names):
    if not isinstance(ast, list):
        return {
            "ідентичність": "sid",
            "виконавець": "executor",
            "ядро3-виконавці": "core3-executors",
            "ядро3-маршрут": "core3-route",
            "ядро3-додати-маршрути": "core3-add-routes",
            "ядро3-стан-профілю": "core3-profile-status",
            # Додано 2026-10-25: файл уживає українську назву механізму, а
            # словник проєкції її не мав — через це canonicalize давав іншу форму.
            "вибрати-механізм": "mechanism-select",
        }.get(ast, ast)
    if not ast:
        return []
    head = ast[0]
    if head == "як-є" or head == "001":
        return [names.get(head, head), *ast[1:]]
    xs = [canonicalize(x, names) for x in ast]
    if isinstance(xs[0], str):
        xs[0] = names.get(xs[0], xs[0])
    return xs


def verify(source):
    names = projection()
    forms = scan(source)
    if [canonicalize(x, names) for x in forms] != scan(OLD_LAW):
        raise AssertionError("Core3 exact D3/D4 law or quoted data changed")
    # Оновлено 2026-10-25: коміт 74f92fc7 «lib: кінцевий виклик-свідок для 18
    # бібліотечних файлів» НАВМИСНО додав п'яту форму — виклик-свідок
    # (ядро3-стан-профілю) у кінці. Тому перевіряємо: 4 ВИЗНАЧЕННЯ + 1 виклик.
    definitions = [x for x in forms if x and x[0] == "визначити"]
    trailing = [x for x in forms if not (x and x[0] == "визначити")]
    if len(definitions) != 4:
        raise AssertionError("Core3 owner-bound Ukrainian D4 definition lost")
    if len(trailing) != 1 or trailing[0][0] != "ядро3-стан-профілю":
        raise AssertionError(
            "Core3 кінцевий виклик-свідок мусить бути рівно один і саме "
            "(ядро3-стан-профілю), як у коміті 74f92fc7")
    return True


class Core3UkrProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_exact_ratified_names_preserve_4_executor_order_and_shape(self):
        self.assertTrue(verify(self.source))
        self.assertIn("(сполучити", self.source)
        self.assertIn("(як-є", self.source)
        self.assertIn("(список", self.source)

    def test_one_bit_wrong_operation_does_not_preserve_law(self):
        for mutated in (
            self.source.replace("(сполучити", "(решта", 1),
            self.source.replace("(список", "(сполучити", 1),
            self.source.replace("(як-є datalog)", "(як-є clips)", 1),
        ):
            self.assertNotEqual(mutated, self.source)
            with self.assertRaisesRegex(AssertionError, "law or quoted data"):
                verify(mutated)

    def test_profile_contract_version_is_text_not_numeric_literal(self):
        self.assertIn('(contract "7" "0")', self.source)
        self.assertNotIn("(contract 7 0)", self.source)

    def test_current_d4_definition_and_lambda_peer_exactness(self):
        names = projection()
        self.assertEqual(names["визначити"], "0011")
        self.assertEqual(names["функція"], "0010")
        self.assertEqual(self.source.count("(визначити ядро3-"), 4)
        self.assertEqual(self.source.count("(функція ("), 3)
        self.assertTrue(verify(self.source))
        self.assertNotIn("(0011 core3-", self.source)
        self.assertNotIn("(0010 (", self.source)

    def test_negative_wrong_d4_peer_breaks_law(self):
        for corrupted in (
            self.source.replace("(визначити ядро3-маршрут", "(функція ядро3-маршрут", 1),
            self.source.replace("(функція (ідентичність виконавець)", "(визначити (ідентичність виконавець)", 1),
        ):
            self.assertNotEqual(corrupted, self.source)
            with self.assertRaisesRegex(AssertionError, "law or quoted data"):
                verify(corrupted)

    def test_historical_eight_bit_head_never_becomes_d3(self):
        corrupted = self.source.replace("(сполучити", "(00000100", 1)
        with self.assertRaisesRegex(AssertionError, "law or quoted data"):
            verify(corrupted)


if __name__ == "__main__":
    unittest.main()
