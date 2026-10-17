"""Точковий source-oracle D1/D3/D4/D5 для обходу механізмів SENS.

НЕ є Rust/T5 runtime parity: інтерпретує лише потрібну підмножину
доменних форм без зовнішніх host-capabilities.
"""
from pathlib import Path
import re
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "lib/mechanism-selector.lisp"
TOKEN = re.compile(r';[^\n]*|"(?:\\.|[^"\\])*"|[()]|[^\s();]+')
NAMES = (
    "mechanism-selector-find-section",
    "mechanism-selector-registry-has-sid?",
    "mechanism-selector-find-route",
    "mechanism-select",
)




def _canonicalize_current_heads(node):
    """Projection-only normalization for the existing legacy mechanical oracle.

    Source of meanings: live D3/D4 uk columns. This test does not admit
    invocation from residence or emulate the full SENS runtime.
    """
    if not isinstance(node, list):
        return node
    if not node:
        return []
    first = node[0]
    if isinstance(first, str) and first in {"001", "як-є"}:
        # QUOTE arguments are data: never lower surface names inside them.
        return [_canonicalize_current_heads(first), *node[1:]]
    result = [_canonicalize_current_heads(part) for part in node]
    if isinstance(result[0], str):
        result[0] = _CANONICAL_UK_TO_BITS.get(result[0], result[0])
    return result


def _ratified_uk_mapping():
    root = SOURCE.parents[1] / "lib" / "domains"
    by_name = {}
    for width in (3, 4):
        table = (root / f"d{width}.lisp").read_text(encoding="utf-8")
        rows = re.findall(r"(?m)^  \(([01]+) \(ук ([^()\s]+)\)", table)
        for bits, uk in rows:
            if len(bits) != width or uk in by_name:
                raise AssertionError(f"ratified projection collision: D{width}:{bits} {uk}")
            by_name[uk] = bits
    return by_name


_CANONICAL_UK_TO_BITS = _ratified_uk_mapping()

def parse(source):
    tokens = [m.group() for m in TOKEN.finditer(source)
              if not m.group().startswith(";")]
    pos = 0

    def read():
        nonlocal pos
        if pos == len(tokens):
            raise AssertionError("незавершене S-вираження")
        token = tokens[pos]
        pos += 1
        if token != "(":
            if token == ")":
                raise AssertionError("зайва дужка")
            return token
        out = []
        while pos < len(tokens) and tokens[pos] != ")":
            out.append(read())
        if pos == len(tokens):
            raise AssertionError("незакрита дужка")
        pos += 1
        return out

    expressions = []
    while pos < len(tokens):
        expressions.append(read())
    return [_canonicalize_current_heads(x) for x in expressions]


def extract_functions(source):
    functions = {}
    for form in parse(source):
        if isinstance(form, list) and len(form) == 3 and form[0] == "0011":
            functions[form[1]] = form[2]
    return {name: functions[name] for name in NAMES}


def is_atom(value):
    return not isinstance(value, list) or not value


class MiniOracle:
    """Підмножина D3/4/5, без примусової host truthiness."""

    def __init__(self, source, globals_=None):
        self.functions = extract_functions(source)
        self.globals = dict(globals_ or {})

    def call(self, name, args, depth=0):
        if depth > 96:
            raise AssertionError("не завершується обхід списку")
        fn = self.functions[name]
        if fn[0] != "0010":
            raise AssertionError("функція має бути D4:0010 LAMBDA")
        return self.eval(fn[2], dict(zip(fn[1], args)), depth + 1)

    def eval(self, expr, env, depth=0):
        if depth > 96:
            raise AssertionError("циклічний обхід")
        if not isinstance(expr, list):
            if expr in env:
                return env[expr]
            if expr in self.globals:
                return self.globals[expr]
            raise AssertionError(f"незв'язаний символ: {expr}")
        if not expr:
            return []
        head, *args = expr
        ev = lambda e: self.eval(e, env, depth + 1)

        if head == "001":  # D3 QUOTE
            if len(args) != 1:
                raise AssertionError("QUOTE арність")
            return args[0]
        if head == "010":  # D3 ATOM -> exact D1
            return is_atom(ev(args[0]))
        if head == "0100":  # D4 NOT -> exact D1
            value = ev(args[0])
            if type(value) is not bool:
                raise AssertionError("NOT потребує D1")
            return not value
        if head == "101":  # D3 EQ -> exact D1
            a, b = ev(args[0]), ev(args[1])
            if not is_atom(a) or not is_atom(b):
                raise AssertionError("EQ приймає лише атоми")
            return a == b
        if head == "110":  # D3 COND, (predicate expression)
            for clause in args:
                if len(clause) != 2:
                    raise AssertionError("COND потребує рівно 2 поля")
                condition = ev(clause[0])
                if type(condition) is not bool:
                    raise AssertionError("COND потребує D1")
                if condition:
                    return ev(clause[1])
            return []
        if head == "100":  # D3 CAR
            return ev(args[0])[0]
        if head == "011":  # D3 CDR
            return ev(args[0])[1:]
        if head == "1001":  # D4 CADR
            return ev(args[0])[1]
        if head == "10011":  # D5 CADDR
            return ev(args[0])[2]
        if head == "1110":  # D4 LIST, only data shape
            return [ev(arg) for arg in args]
        if head == "0010":  # D4 LAMBDA
            return ("lambda", args[0], args[1], dict(env))
        if isinstance(head, list):
            tag, params, body, saved = ev(head)
            if tag != "lambda" or len(params) != len(args):
                raise AssertionError("невідповідність LAMBDA")
            scope = {**saved, **dict(zip(params, [ev(arg) for arg in args]))}
            return self.eval(body, scope, depth + 1)
        if head in self.functions:
            return self.call(head, [ev(arg) for arg in args], depth + 1)
        raise AssertionError(f"невідомий виклик: {head}")


class MechanismSelectorWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_section_scans_first_middle_and_absent(self):
        m = MiniOracle(self.source)
        sections = [["schema", "v1"], ["rows", ["x"]], ["profile-routes", ["p"]]]
        self.assertEqual(m.call("mechanism-selector-find-section", ["schema", sections]), sections[0])
        self.assertEqual(m.call("mechanism-selector-find-section", ["rows", sections]), sections[1])
        self.assertEqual(m.call("mechanism-selector-find-section", ["missing", sections]), [])
        self.assertEqual(m.call("mechanism-selector-find-section", ["rows", []]), [])

    def test_registry_scans_complete_list(self):
        m = MiniOracle(self.source)
        rows = [["00000001", "quote"], ["00001100", "plus"]]
        self.assertEqual(m.call("mechanism-selector-registry-has-sid?", ["00001100", rows]), "yes")
        self.assertEqual(m.call("mechanism-selector-registry-has-sid?", ["11111111", rows]), "no")
        self.assertEqual(m.call("mechanism-selector-registry-has-sid?", ["00000001", rows]), "yes")
        self.assertEqual(m.call("mechanism-selector-registry-has-sid?", ["00000001", []]), "no")

    def test_routes_scan_matching_sid_and_executor(self):
        m = MiniOracle(self.source)
        routes = [["00000001", "evaluator", "quote"],
                  ["00001100", "prolog", "add"],
                  ["00001100", "clips", "add"]]
        self.assertEqual(m.call("mechanism-selector-find-route", ["00001100", "clips", routes]), routes[2])
        self.assertEqual(m.call("mechanism-selector-find-route", ["00001100", "prolog", routes]), routes[1])
        self.assertEqual(m.call("mechanism-selector-find-route", ["00001100", "datalog", routes]), [])

    def test_selection_distinguishes_unknown_unavailable_selected(self):
        sid = "00001100"
        env = {
            "mechanism-selector-registry-rows": [["00000001", "quote"], [sid, "plus"]],
            "mechanism-selector-routes": [[sid, "prolog", "bounded-exact-add"]],
        }
        m = MiniOracle(self.source, env)
        self.assertEqual(m.call("mechanism-select", [sid, "prolog"]),
                         ["mechanism-selected", sid, "prolog", "bounded-exact-add"])
        self.assertEqual(m.call("mechanism-select", [sid, "clips"]),
                         ["mechanism-unavailable", sid, "clips"])
        self.assertEqual(m.call("mechanism-select", ["10101010", "prolog"]),
                         ["mechanism-selection-failure", "sid-not-in-function-table", "10101010"])

    def test_wrong_fallback_and_inverted_route_are_detected(self):
        bad = self.source.replace(
            "((атом? (як-є ()))\n       (mechanism-selector-find-section",
            "((101 (100 (100 sections)) name)\n       (mechanism-selector-find-section", 1)
        self.assertNotEqual(bad, self.source)
        self.assertNotEqual(
            MiniOracle(bad).call("mechanism-selector-find-section",
                                 ["rows", [["schema", "v"], ["rows", "v"]]]),
            ["rows", "v"],
        )
        wrong = self.source.replace(
            "((атом? route)\n             (список",
            "((хибне? (атом? route))\n             (список", 1)
        self.assertNotEqual(wrong, self.source)
        m = MiniOracle(wrong, {"mechanism-selector-registry-rows": [["00001100", "plus"]],
                               "mechanism-selector-routes": [["00001100", "prolog", "add"]]})
        with self.assertRaises(AssertionError):
            self.assertEqual(m.call("mechanism-select", ["00001100", "prolog"]),
                             ["mechanism-selected", "00001100", "prolog", "add"])

    def test_domain_tables_are_exact_width_without_invented_residency(self):
        # D7 v2 keyboard exposes 128 coordinates; historical owner
        # occupancy 126/128 is a DIFFERENT admission question.
        expected = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
        root = SOURCE.parents[1]
        for width, population in enumerate(expected, 1):
            with self.subTest(domain=f"D{width}"):
                table = (root / f"lib/domains/d{width}.lisp").read_text(
                    encoding="utf-8"
                )
                words = re.findall(r"(?m)^  \\(([01]+)\\s", table)
                self.assertEqual(len(words), population)
                self.assertEqual(
                    words,
                    [format(i, f"0{width}b") for i in range(population)],
                )

    def test_negative_nine_bit_read_truncation(self):
        # D9 READ-ALL/READ-FILE are exact current residents, not W8 slots.
        # Quote/data, parser path, and old positional SID have no authority.
        table = (SOURCE.parents[1] / "lib/domains/d9.lisp").read_text(encoding="utf-8")
        rows = dict(re.findall(r"(?m)^  \(([01]{9}) \(ук ([^()\s]+)\)", table))
        self.assertEqual(rows["110101001"], "читати-всі")
        self.assertEqual(rows["110110111"], "читати-файл")
        forms = parse(self.source)
        self.assertEqual(forms[0][2],
                         ["100", ["читати-всі", ["читати-файл",
                          '"lib/surface/semantic-registry.lisp"']]])
        self.assertEqual(forms[1][2],
                         ["100", ["читати-всі", ["читати-файл",
                          '"lib/function-table-mechanisms.lisp"']]])
        mutation = self.source.replace("(читати-всі ", "(10101001 ", 1)
        self.assertNotEqual(mutation, self.source)
        mutated = parse(mutation)
        self.assertEqual(mutated[0][2][1][0], "10101001")
        self.assertNotEqual(mutated[0][2], forms[0][2])
        self.assertEqual(len(mutated[0][2][1][0]), 8)  # W8 is not D9
        self.assertNotIn("(10101001 ", self.source)

    def test_d3_d4_d5_d9_operator_widths(self):
        source = self.source
        heads = re.findall(r"\(([01]{3,10})(?=[\s(])", source)
        self.assertFalse(any(len(w) in (8, 9) for w in heads))
        self.assertEqual(source.count("(читати-всі "), 2)
        self.assertEqual(source.count("(читати-файл "), 2)
        self.assertEqual(len("10011"), 5)  # D5 CADDR
        self.assertNotIn("0100", heads)  # NOT(ATOM) not reintroduced


    def test_ukrainian_projection_maps_to_exact_ratified_identity(self):
        mapping = _CANONICAL_UK_TO_BITS
        self.assertEqual(mapping["як-є"], "001")
        self.assertEqual(mapping["тотожне?"], "101")
        self.assertEqual(mapping["за-умовою"], "110")
        self.assertEqual(mapping["друге"], "1001")
        self.assertEqual(mapping["список"], "1110")
        self.assertIn("(за-умовою", self.source)
        self.assertIn("(тотожне?", self.source)
        self.assertIn("(як-є", self.source)
        self.assertIn("(список", self.source)
        # The same source now parses into the old canonical machine identities.
        self.assertEqual(extract_functions(self.source)["mechanism-select"][0], "0010")

    def test_wrong_ukrainian_identity_does_not_pass_route_law(self):
        bad = self.source.replace("(тотожне? executor", "(сполучити executor", 1)
        self.assertNotEqual(bad, self.source)
        m = MiniOracle(bad, {
            "mechanism-selector-registry-rows": [["00001100", "plus"]],
            "mechanism-selector-routes": [["00001100", "prolog", "add"]],
        })
        with self.assertRaises(AssertionError):
            m.call("mechanism-select", ["00001100", "prolog"])

if __name__ == "__main__":
    unittest.main()
