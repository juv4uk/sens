#!/usr/bin/env python3
"""Independent original-source oracle for the six historical machine-block functions.

This intentionally imports NO current SENS evaluator, migrator or T5 codec.
The original historical observable results must separately match a *real*
current-SENS execution of a SHA-pinned same-stem physical .sens before release.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/machine/block.lisp"
SOURCE_BLOB = "200201b741787c4e144ad4194848acf51d7b439e"
NAMES = frozenset((
    "machine-block", "machine-block-empty", "machine-block-one",
    "machine-block-append", "machine-block-concat", "machine-block-forms",
))
DEFINE, LAMBDA, QUOTE, LIST, APPEND = (
    "00001001", "00001000", "00000001", "00100111", "00101001"
)


class HistoricalError(ValueError):
    pass


def blob(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def parse(raw: bytes) -> list:
    text = raw.decode("utf-8")
    tokens = re.findall(
        r"\(|\)|[^\s()]+",
        "\n".join(line.split(";", 1)[0] for line in text.splitlines()),
    )
    index = 0

    def expression():
        nonlocal index
        if index >= len(tokens):
            raise HistoricalError("unexpected EOF")
        token = tokens[index]
        index += 1
        if token == ")":
            raise HistoricalError("unexpected closing parenthesis")
        if token == "(":
            result = []
            while True:
                if index >= len(tokens):
                    raise HistoricalError("unclosed historical form")
                if tokens[index] == ")":
                    index += 1
                    return result
                result.append(expression())
        if token == "." or any(c in token for c in ('"', "'", chr(96), ",")):
            raise HistoricalError("unsupported historical reader syntax")
        return token

    forms = []
    while index < len(tokens):
        forms.append(expression())
    return forms


class Closure:
    def __init__(self, parameters: list, body: object, env: dict):
        if not all(isinstance(p, str) and p for p in parameters):
            raise HistoricalError("LAMBDA parameters must be symbols")
        if len(set(parameters)) != len(parameters):
            raise HistoricalError("duplicate LAMBDA parameter")
        self.parameters = tuple(parameters)
        self.body = body
        self.env = dict(env)

    def __call__(self, *args):
        if len(args) != len(self.parameters):
            raise HistoricalError("historical function arity mismatch")
        env = dict(self.env)
        env.update(zip(self.parameters, args))
        return evaluate(self.body, env)


def evaluate(expr: object, env: dict):
    if isinstance(expr, str):
        if expr not in env:
            raise HistoricalError("unbound historical symbol: " + expr)
        return env[expr]
    if not isinstance(expr, list) or not expr or not isinstance(expr[0], str):
        raise HistoricalError("unadmitted executable form")
    head, *args = expr
    if head == QUOTE:
        if len(args) != 1:
            raise HistoricalError("QUOTE arity")
        return args[0]
    if head == LIST:
        if len(args) != 1:
            raise HistoricalError("bounded LIST arity")
        return [evaluate(args[0], env)]
    if head == APPEND:
        if len(args) != 2:
            raise HistoricalError("APPEND arity")
        left, right = (evaluate(x, env) for x in args)
        if not isinstance(left, list) or not isinstance(right, list):
            raise HistoricalError("APPEND requires proper lists")
        return left + right
    if head == LAMBDA:
        if len(args) != 2 or not isinstance(args[0], list):
            raise HistoricalError("LAMBDA requires parameters and one body")
        return Closure(args[0], args[1], env)
    if head in env and isinstance(env[head], Closure):
        return env[head](*(evaluate(a, env) for a in args))
    raise HistoricalError("unadmitted historical operator: " + head)


def historical_definitions(raw: bytes) -> dict:
    if blob(raw) != SOURCE_BLOB:
        raise HistoricalError("source drift: original Git blob SHA differs")
    forms = parse(raw)
    if len(forms) != 6:
        raise HistoricalError("historical source must define exactly six functions")
    env = {}
    for form in forms:
        if not isinstance(form, list) or len(form) != 3 or form[0] != DEFINE:
            raise HistoricalError("only historical top-level DEFINE is admitted")
        name = form[1]
        if not isinstance(name, str) or name not in NAMES or name in env:
            raise HistoricalError("unknown/duplicate source definition")
        value = evaluate(form[2], env)
        if not isinstance(value, Closure):
            raise HistoricalError("DEFINE must bind a closure")
        env[name] = value
    if frozenset(env) != NAMES:
        raise HistoricalError("missing historical definition")
    return env


EXPECTED = {
    "empty": [],
    "one_nested": [["mov", ["r1", "r2"]]],
    "append": [["mov", ["r1", "r2"]], ["branch", "L1"], "ret"],
    "concat": [["mov", ["r1", "r2"]], ["branch", "L1"], ["label", "L2"]],
    "forms": [["mov", ["r1", "r2"]], ["branch", "L1"]],
    "identity": [["mov", ["r1", "r2"]], ["branch", "L1"]],
    "append_empty": ["nop"],
    "concat_left_empty": [["mov", ["r1", "r2"]], ["branch", "L1"]],
    "concat_right_empty": [["mov", ["r1", "r2"]], ["branch", "L1"]],
}


def observations(env: dict) -> dict:
    initial = [["mov", ["r1", "r2"]], ["branch", "L1"]]
    return {
        "empty": env["machine-block-empty"](),
        "one_nested": env["machine-block-one"](initial[0]),
        "append": env["machine-block-append"](initial, "ret"),
        "concat": env["machine-block-concat"](initial, [["label", "L2"]]),
        "forms": env["machine-block-forms"](initial),
        "identity": env["machine-block"](initial),
        "append_empty": env["machine-block-append"]([], "nop"),
        "concat_left_empty": env["machine-block-concat"]([], initial),
        "concat_right_empty": env["machine-block-concat"](initial, []),
    }


def evidence() -> dict:
    raw = SOURCE.read_bytes()
    outcome = observations(historical_definitions(raw))
    if outcome != EXPECTED:
        raise HistoricalError("original-source observations differ")
    return {
        "schema": "sens-machine-block-historical-oracle/v1",
        "status": "HISTORICAL_SIDE_ONLY",
        "source": "lib/machine/block.lisp",
        "source_git_blob_sha1": blob(raw),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "cases": outcome,
        "case_count": len(outcome),
        "current_sens_semantic_parity": "NOT_VERIFIED",
        "physical_t5_verified": False,
        "release_admitted": False,
    }


class HistoricalMachineBlockTests(unittest.TestCase):
    def test_pinned_source_and_all_definitions(self):
        self.assertEqual(blob(SOURCE.read_bytes()), SOURCE_BLOB)
        self.assertEqual(frozenset(historical_definitions(SOURCE.read_bytes())), NAMES)

    def test_execute_nine_original_semantic_cases(self):
        self.assertEqual(observations(historical_definitions(SOURCE.read_bytes())), EXPECTED)

    def test_input_order_and_structure_are_not_mutated(self):
        env = historical_definitions(SOURCE.read_bytes())
        original = [["a"], ["b", ["nested"]]]
        snapshot = json.dumps(original)
        self.assertEqual(
            env["machine-block-append"](original, ["c"]),
            original + [["c"]],
        )
        self.assertEqual(env["machine-block-concat"](original, []), original)
        self.assertEqual(json.dumps(original), snapshot)

    def test_unknown_operators_arity_and_nonlists_fail_closed(self):
        env = historical_definitions(SOURCE.read_bytes())
        with self.assertRaises(HistoricalError):
            evaluate(["11111111", "x"], env)
        with self.assertRaises(HistoricalError):
            env["machine-block-one"]()
        with self.assertRaises(HistoricalError):
            env["machine-block-concat"]([], [], [])
        with self.assertRaises(HistoricalError):
            evaluate([APPEND, [QUOTE, []], [QUOTE, "not-a-list"]], {})

    def test_source_drift_and_reader_extensions_fail_closed(self):
        with self.assertRaisesRegex(HistoricalError, "source drift"):
            historical_definitions(SOURCE.read_bytes() + b" ")
        for raw in (b"(", b")", b"('x)", b"(x . y)"):
            with self.subTest(raw=raw), self.assertRaises(HistoricalError):
                parse(raw)

    def test_evidence_explicitly_denies_current_parity(self):
        record = evidence()
        self.assertEqual(record["cases"], EXPECTED)
        self.assertEqual(record["case_count"], 9)
        self.assertEqual(record["status"], "HISTORICAL_SIDE_ONLY")
        self.assertEqual(record["current_sens_semantic_parity"], "NOT_VERIFIED")
        self.assertFalse(record["release_admitted"])
        self.assertFalse(record["physical_t5_verified"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--emit-json":
        destination = Path(sys.argv[2])
        if destination.exists() or destination.is_symlink():
            raise SystemExit("refuse to overwrite oracle evidence")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(evidence(), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print("HISTORICAL_SIDE_ONLY " + str(destination))
    else:
        unittest.main()
