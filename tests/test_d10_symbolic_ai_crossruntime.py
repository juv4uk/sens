#!/usr/bin/env python3
"""D10 one-law supplement: >500 REAL SWI term_subsumer comparisons.

No second implementation or semantic ID. Uses existing canonical Python
recursive+iterative LGG and native SWI-Prolog library(terms), not a copied
Prolog implementation. The live candidate remains HOLD/NOT-SELECTED.
"""
from __future__ import annotations

import itertools
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from d10_antiunify_oracle import lgg, lgg_independent, instantiate


def atom(name: str) -> dict:
    return {"atom": name}


def fun(name: str, *args: dict) -> dict:
    return {"fun": name, "args": list(args)}


def to_prolog(t: dict) -> str:
    """Only finite ASCII constructors/atoms from a FIXED test alphabet."""
    if set(t) == {"atom"}:
        if t["atom"] not in ("a", "b", "c", "star", "radio", "optical"):
            raise ValueError("unexpected term atom in independent oracle")
        return t["atom"]
    if set(t) == {"var"}:
        n = t["var"]
        if isinstance(n, bool) or not isinstance(n, int) or not 0 <= n <= 64:
            raise ValueError("unexpected generated hole")
        return f"V{n}"
    if set(t) == {"fun", "args"}:
        if t["fun"] not in ("f", "g", "pair", "nest", "observation", "band"):
            raise ValueError("unexpected term constructor")
        if not t["args"]:
            raise ValueError("empty functor not admitted by canonical oracle")
        return f'{t["fun"]}(' + ",".join(to_prolog(x) for x in t["args"]) + ")"
    raise ValueError("unexpected first-order representation")


def oracle_program(rows: list[tuple[dict, dict, dict]]) -> str:
    """Compile trusted bounded terms as ground Prolog facts with expected vars."""
    parts = [
        ":- use_module(library(terms)).",
        ":- initialization(main, main).",
        "proof(Id, A, B, Expected) :-",
        "    term_subsumer(A, B, Actual),",
        "    ( Actual =@= Expected -> true",
        "      ; format(user_error, 'LGG mismatch at case ~w~n', [Id]), fail ),",
        "    subsumes_term(Actual, A), subsumes_term(Actual, B).",
        "main :-",
        "    ( forall(case(Id, A, B, Expected), proof(Id, A, B, Expected))",
        "      -> writeln('SWI_NATIVE_LGG_COHORT_PASS'), halt(0)",
        "      ; halt(2) ).",
    ]
    for index, (left, right, pattern) in enumerate(rows):
        parts.append(f"case({index},{to_prolog(left)},{to_prolog(right)},"
                     f"{to_prolog(pattern)}).")
    return "\n".join(parts) + "\n"


def actual_swipl(program: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory(prefix="sens-d10-existing-lgg-swipl-") as td:
        path = Path(td) / "oracle.pl"
        path.write_text(program, encoding="utf-8")
        return subprocess.run(["swipl", "-q", "-s", str(path)],
                              capture_output=True, text=True, timeout=40)


class CanonicalLGGNativePrologTests(unittest.TestCase):
    def require_native_prolog(self):
        if shutil.which("swipl") is not None:
            return
        if os.environ.get("D10_REQUIRE_SWIPL") == "1":
            self.fail("required real independent SWI-Prolog was not installed")
        self.skipTest("dedicated CI enables D10_REQUIRE_SWIPL=1")

    def test_529_ground_ordered_pairs_against_real_native_term_subsumer(self):
        terms = [atom(x) for x in ("a", "b", "c")]
        terms += [fun("f", atom(x)) for x in ("a", "b", "c")]
        terms += [fun("g", atom(x)) for x in ("a", "b", "c")]
        terms += [fun("pair", atom(x), atom(y))
                  for x, y in itertools.product(("a", "b", "c"), repeat=2)]
        terms += [fun("nest", fun("f", atom(x)), fun("g", atom(y)))
                  for x, y in itertools.product(("a", "b"), repeat=2)]
        terms += [fun("observation", atom("star"), fun("band", atom("radio"))),
                  fun("observation", atom("star"), fun("band", atom("optical")))]
        self.assertEqual(len(terms), 24)
        rows = []
        for a, b in itertools.product(terms, repeat=2):
            recursive = lgg(a, b)
            self.assertEqual(recursive, lgg_independent(a, b))
            pattern = recursive["generalization"]
            self.assertEqual(instantiate(pattern, recursive["left_substitution"]), a)
            self.assertEqual(instantiate(pattern, recursive["right_substitution"]), b)
            self.assertEqual(pattern, lgg(b, a)["generalization"])
            rows.append((a, b, pattern))
        self.assertEqual(len(rows), 576)
        self.require_native_prolog()
        observed = actual_swipl(oracle_program(rows))
        self.assertEqual(observed.returncode, 0, observed.stderr)
        self.assertIn("SWI_NATIVE_LGG_COHORT_PASS", observed.stdout)

    def test_native_prolog_detects_more_general_but_reconstructible_shape(self):
        self.require_native_prolog()
        left, right = fun("pair", atom("a"), atom("a")), fun("pair", atom("b"), atom("b"))
        correct = lgg(left, right)["generalization"]
        self.assertEqual(correct, fun("pair", {"var": 0}, {"var": 0}))
        wrong = fun("pair", {"var": 0}, {"var": 1})
        self.assertNotEqual(wrong, correct)
        fails = actual_swipl(oracle_program([(left, right, wrong)]))
        self.assertEqual(fails.returncode, 2)
        self.assertIn("LGG mismatch at case 0", fails.stderr)

    def test_native_prolog_detects_invalid_shared_swapped_pair(self):
        self.require_native_prolog()
        left, right = fun("pair", atom("a"), atom("b")), fun("pair", atom("b"), atom("a"))
        self.assertEqual(lgg(left, right)["generalization"],
                         fun("pair", {"var": 0}, {"var": 1}))
        false_sharing = fun("pair", {"var": 0}, {"var": 0})
        fails = actual_swipl(oracle_program([(left, right, false_sharing)]))
        self.assertEqual(fails.returncode, 2)
        self.assertIn("LGG mismatch", fails.stderr)

    def test_no_second_candidate_is_created_by_crossruntime_fixture(self):
        source = (ROOT / "knowledge/d10-symbolic-ai-antiunification-research-v1.json").read_text(
            encoding="utf-8")
        self.assertIn('"stable_id": "d10.symbolic-ai.ground-term-lgg.research.20261009"', source)
        self.assertIn('"decision": "PENDING-OWNER-REVIEW-NOT-SELECTED"', source)
        self.assertIn('"coordinate": null', source)
        # The test only runs witnesses; it never updates inventory/TSV or
        # creates a physical .sens program.


if __name__ == "__main__":
    unittest.main()
