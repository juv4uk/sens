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
    return expressions


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
            "((010 (001 ()))\n       (mechanism-selector-find-section",
            "((101 (100 (100 sections)) name)\n       (mechanism-selector-find-section", 1)
        self.assertNotEqual(bad, self.source)
        with self.assertRaises(AssertionError):
            MiniOracle(bad).call("mechanism-selector-find-section",
                                 ["rows", [["schema", 0], ["rows", 1]]])
        wrong = self.source.replace(
            "((010 route)\n             (1110",
            "((0100 (010 route))\n             (1110", 1)
        self.assertNotEqual(wrong, self.source)
        m = MiniOracle(wrong, {"mechanism-selector-registry-rows": [["00001100", "plus"]],
                               "mechanism-selector-routes": [["00001100", "prolog", "add"]]})
        with self.assertRaises(AssertionError):
            self.assertEqual(m.call("mechanism-select", ["00001100", "prolog"]),
                             ["mechanism-selected", "00001100", "prolog", "add"])

    def test_d3_d4_d5_d9_operator_widths(self):
        source = self.source
        heads = re.findall(r"\(([01]{3,10})(?=[\s(])", source)
        self.assertFalse(any(len(w) == 8 for w in heads))
        self.assertEqual(heads.count("110101001"), 2)  # D9 READ-ALL
        self.assertEqual(heads.count("110110111"), 2)  # D9 READ-FILE
        self.assertEqual(len("10011"), 5)  # D5 CADDR
        self.assertNotIn("0100", heads)  # прибрано хибне D4 NOT(ATOM)


if __name__ == "__main__":
    unittest.main()
