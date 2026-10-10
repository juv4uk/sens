#!/usr/bin/env python3
"""µCPU slot prototype: real T5, strict D1/D3 and bounded differential oracles."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks/microcpu"))
sys.path.insert(0, str(ROOT / "scripts"))

from slot_cpu import (  # noqa: E402
    Blocked, EMPTY, Pair, Predicate, SKIP_ZERO, JUMP,
    compile_t5, run, visible,
)
from sens_t5_codec import decode_bytes, encode_words  # noqa: E402


def call(*values):
    """Only test fixture notation; compiled .sens still has zero textual names."""
    words = ["10"]
    for i, value in enumerate(values):
        if i:
            words.append("00")
        words.extend(value if isinstance(value, list) else [value])
    return [*words, "01"]


Q = call("001", "000")
PAIR = call("111", Q, Q)
ATOM_FALSE = call("010", PAIR)
ATOM_TRUE = call("010", "000")
EQ_TRUE = call("101", Q, Q)
EQ_FALSE = call("101", "0", "1")
CONDITIONAL = call("110", call(ATOM_FALSE, "0"), call(ATOM_TRUE, "1"))


def physical(words):
    return encode_words(words)


class SlotTapeTests(unittest.TestCase):
    def assert_result(self, words, expected):
        source = physical(words)
        compiled = compile_t5(source)
        self.assertEqual(compiled.physical_bytes, len(source))
        self.assertEqual(compiled.word_count, len(words))
        self.assertGreaterEqual(compiled.slot_count, 1)
        self.assertEqual(visible(run(compiled)), expected)
        self.assertEqual(visible(run(compiled)), expected, "warm replay must be deterministic")
        self.assertEqual(decode_bytes(source), words)

    def test_current_real_physical_quote_and_pair(self):
        for path, expected in (
            ("tests/fixtures/migration-quote-cohort-main/quote-legacy.sens", "()"),
            ("tests/fixtures/migration-pair-cohort-main/pair-cons.sens", "(())"),
        ):
            with self.subTest(path=path):
                self.assertEqual(visible(run(compile_t5((ROOT / path).read_bytes()))), expected)

    def test_d1_is_not_host_boolean_or_structural_empty(self):
        self.assertNotEqual(Predicate(0), EMPTY)
        self.assertNotEqual(Predicate(1), EMPTY)
        self.assertNotEqual(Predicate(0), Predicate(1))
        for words, answer in [(["0"], "0"), (["1"], "1"), (["000"], "()")]:
            self.assert_result(words, answer)

    def test_seven_ratified_d3_operations_in_closed_subset(self):
        for words, expected in [
            (Q, "()"),
            (ATOM_TRUE, "1"),
            (ATOM_FALSE, "0"),
            (EQ_TRUE, "1"),
            (EQ_FALSE, "0"),
            (PAIR, "(())"),
            (call("100", PAIR), "()"),
            (call("011", PAIR), "()"),
            (CONDITIONAL, "1"),
            (call("110", call("0", "1")), "()"),
        ]:
            with self.subTest(words=words):
                self.assert_result(words, expected)

    def test_literal_quote_preserves_data_not_executable_heads(self):
        self.assert_result(call("001", call("111", "0", "1")), "(111 0 1)")
        self.assert_result(call("100", call("001", call("000", "1"))), "()")

    def test_conditional_branches_are_forward_only_and_lazy(self):
        bad_when_evaluated = call("100", "000")  # CAR structural ()
        program = call("110", call("1", "1"), call("0", bad_when_evaluated))
        tape = compile_t5(physical(program))
        self.assertEqual(run(tape), Predicate(1))
        self.assertTrue(all(arg > i for form in tape.forms
                            for i, (op, arg) in enumerate(form)
                            if op in (SKIP_ZERO, JUMP)))
        self.assert_result(call("110", call("0", "1"), call("1", "0")), "0")

    def test_three_field_cond_rejected_before_running(self):
        for invalid in [
            call("110", call("1", "1", "0")),
            call("110", call("1")),
            call("110", "1"),
        ]:
            with self.subTest(words=invalid), self.assertRaises(Blocked):
                compile_t5(physical(invalid))

    def test_wrong_domain_cond_and_partial_eq_fail_closed(self):
        with self.assertRaisesRegex(Blocked, "exact D1"):
            run(compile_t5(physical(call("110", call(Q, "1")))))
        with self.assertRaisesRegex(Blocked, "only atoms"):
            run(compile_t5(physical(call("101", PAIR, Q)))
        with self.assertRaisesRegex(Blocked, "expects a pair"):
            run(compile_t5(physical(call("100", "000")))

    def test_no_legacy_functions_or_d4_and_no_illegal_d2(self):
        for invalid in [
            ["10", "01"],       # cannot replace D3 structural EMPTY
            ["10", "001"],      # unclosed
            ["11"],             # D2 dotted syntax unsupported
            ["1000"],           # D4 alone is not executable in this prototype
            ["10", "1000", "01"],
            ["00000111"],       # old eight-bit identity never callable
            ["10", "1", "01"],  # D1 data is not a callable operator
        ]:
            with self.subTest(words=invalid), self.assertRaises(Blocked):
                compile_t5(physical(invalid))

    def test_bad_t5_transport_never_dispatches(self):
        for raw in [b"", bytes([243]), physical(Q) + bytes([242])]:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                compile_t5(raw)

    @unittest.skipUnless(os.getenv("SENS_CLI_PATH"), "SENS_CLI_PATH not provided")
    def test_independent_rust_sens_oracle_on_same_physical_bytes(self):
        cli = os.environ["SENS_CLI_PATH"]
        corpus = [
            Q, PAIR, ATOM_TRUE, ATOM_FALSE, EQ_TRUE, EQ_FALSE,
            CONDITIONAL, call("100", PAIR), call("011", PAIR),
        ]
        with tempfile.TemporaryDirectory(prefix="sens-microcpu-oracle-") as temp:
            for i, words in enumerate(corpus):
                with self.subTest(case=i):
                    f = Path(temp) / f"case-{i}.sens"
                    f.write_bytes(physical(words))
                    observed = subprocess.run(
                        [cli, str(f)], check=False, capture_output=True, text=True, timeout=10
                    )
                    self.assertEqual(observed.returncode, 0, observed.stderr)
                    self.assertEqual(observed.stdout.strip(),
                                     visible(run(compile_t5(f.read_bytes()))))


if __name__ == "__main__":
    unittest.main()
