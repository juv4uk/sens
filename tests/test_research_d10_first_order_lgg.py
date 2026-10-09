#!/usr/bin/env python3
"""Fail-closed D10 research: Plotkin-style first-order LGG vs REAL SWI-Prolog.

Research only — PASS never increments selected, ratified or migration counts.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/research_d10_first_order_lgg.py"
ORACLE = ROOT / "tests/oracles/d10_first_order_lgg.pl"
DOSSIER = ROOT / "knowledge/d10-first-order-lgg-research-v1.json"
spec = importlib.util.spec_from_file_location("d10_lgg", SCRIPT)
assert spec and spec.loader
lgg = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lgg
spec.loader.exec_module(lgg)


def atom(symbol: str) -> dict:
    return {"a": symbol}


def fn(symbol: str, *arguments: dict) -> dict:
    return {"f": symbol, "args": list(arguments)}


def validate_dossier(state: dict) -> None:
    if (set(("schema", "status", "selection", "ratified", "coordinate", "domain",
             "semantic_name", "decision", "source_evidence", "comparison")) - set(state)):
        raise ValueError("unreviewed D10 evidence shape")
    if (state["schema"] != "sens-d10-first-order-lgg-research/v1"
            or state["domain"] != "D10"
            or state["status"] != "HOLD-CORE-VS-LIBRARY-REVIEW"
            or state["selection"] != "RESEARCH-ONLY-NOT-SELECTED"
            or state["ratified"] is not False
            or state["coordinate"] is not None
            or state["decision"] != "HOLD"):
        raise ValueError("false D10 selection, coordinate or ratification")
    if state["semantic_name"] != "FIRST-ORDER-LEAST-GENERAL-GENERALIZATION":
        raise ValueError("semantic name drift")
    comp = state["comparison"]
    if (comp.get("exact_D1_D9_duplicate") != "NOT-INDEPENDENTLY-VERIFIED"
            or comp.get("exact_selected_D10_duplicate") != "NOT-INDEPENDENTLY-VERIFIED"):
        raise ValueError("dedup has not been independently proved")
    sources = state["source_evidence"]
    known = {
        "lib/reason.lisp": "dadc52a2f40f2f30ad77642898afb81980044c08",
        "knowledge/d10-ai-interest-proposal-v1.json": "879d5547af1ff98f316ca288970b3c9505082428",
    }
    for path, expected_blob in known.items():
        if len([x for x in sources if x.get("path") == path and
                x.get("git_blob_sha1") == expected_blob]) != 1:
            raise ValueError("source donor SHA lost or falsified")
        proc = subprocess.run(["git", "hash-object", "--", path], cwd=ROOT,
                              capture_output=True, text=True, check=True)
        if proc.stdout.strip() != expected_blob:
            raise ValueError("live donor Git blob changed without semantic review")
    if not any(x.get("role") == "historical_origin" and "Plotkin" in x.get("title", "")
               and x.get("url", "").startswith("https://") for x in sources):
        raise ValueError("historical anti-unification provenance missing")


class FirstOrderLGGResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dossier = json.loads(DOSSIER.read_text(encoding="utf-8"))

    def test_evidence_is_source_pinned_research_and_not_selected(self):
        validate_dossier(self.dossier)
        self.assertEqual(len(self.dossier["positive_witnesses"]), 3)
        self.assertEqual(self.dossier["independent_oracles"]["actual_SENS_binary_oracle"],
                         "NOT_PROVEN")
        self.assertIsNone(self.dossier["coordinate"])
        for row in self.dossier["positive_witnesses"]:
            result = lgg.anti_unify(row["left"], row["right"])
            self.assertEqual(result["generalizer"], row["expected_generalizer"])

    def test_repeated_disagreement_is_one_hole_not_two(self):
        a, b = fn("pair", atom("a"), atom("a")), fn("pair", atom("b"), atom("b"))
        result = lgg.anti_unify(a, b)
        self.assertEqual(result["generalizer"],
                         fn("pair", {"hole": "V0"}, {"hole": "V0"}))
        self.assertEqual(len(result["left_substitution"]), 1)
        self.assertEqual(len(result["right_substitution"]), 1)
        self.assertEqual(lgg.instantiate(result["generalizer"], result["left_substitution"]), a)
        self.assertEqual(lgg.instantiate(result["generalizer"], result["right_substitution"]), b)
        corrupt = copy.deepcopy(result)
        corrupt["generalizer"]["args"][1] = {"hole": "V1"}
        corrupt["left_substitution"].append({"hole": "V1", "term": atom("a")})
        corrupt["right_substitution"].append({"hole": "V1", "term": atom("b")})
        # These TWO overly-general patterns still reconstruct sources, so a
        # mere substitution witness is insufficient without LGG minimality.
        self.assertEqual(lgg.instantiate(corrupt["generalizer"],
                                         corrupt["left_substitution"]), a)
        with self.assertRaisesRegex(lgg.AntiUnifyBlocked, "MINIMALITY"):
            lgg.check_result(a, b, corrupt)

    def test_ordered_pairs_and_shared_subterms_from_grammar_and_astronomy(self):
        a, b = fn("pair", atom("a"), atom("b")), fn("pair", atom("b"), atom("a"))
        result = lgg.anti_unify(a, b)
        self.assertEqual(result["generalizer"],
                         fn("pair", {"hole": "V0"}, {"hole": "V1"}))
        x = fn("observe", fn("band", atom("a")), fn("pitch", atom("a")))
        y = fn("observe", fn("band", atom("b")), fn("pitch", atom("b")))
        self.assertEqual(lgg.anti_unify(x, y)["generalizer"],
                         fn("observe", fn("band", {"hole": "V0"}),
                            fn("pitch", {"hole": "V0"})))
        self.assertEqual(lgg.anti_unify(x, x)["generalizer"], x)

    def test_constructor_arity_and_name_conflicts_reject_false_shared_shape(self):
        terms = [
            (fn("f", atom("a")), fn("f", atom("b"), atom("a"))),
            (fn("f", atom("a")), fn("g", atom("a"))),
            (atom("f"), fn("f")),
        ]
        for a, b in terms:
            with self.subTest(a=a, b=b):
                result = lgg.anti_unify(a, b)
                self.assertEqual(result["generalizer"], {"hole": "V0"})
                lgg.check_result(a, b, result)

    def test_non_ground_binder_framing_and_limits_fail_closed(self):
        invalid = [{"hole": "V0"}, {}, {"a": ""}, {"a": "0"},
                   {"a": 3}, {"f": "a", "args": "bad"},
                   {"f": "a", "args": [], "bind": "x"},
                   {"f": "a", "args": [{"hole": "V0"}]},
                   {"f": "p", "args": [atom("x")] * 17},
                   {"f": "p", "args": [atom("x")] * 130}]
        for term in invalid:
            with self.subTest(term=str(term)[:65]):
                with self.assertRaises(lgg.AntiUnifyBlocked):
                    lgg.anti_unify(term, atom("x"))
        chain = atom("end")
        for _ in range(18):
            chain = fn("f", chain)
        with self.assertRaisesRegex(lgg.AntiUnifyBlocked, "BOUND"):
            lgg.anti_unify(chain, atom("ok"))

    def test_exhaustive_small_finite_ground_oracles_and_swapped_source(self):
        terms = [atom("a"), atom("b"), atom("c"), fn("nil")]
        for symbol in ("f", "g"):
            terms += [fn(symbol, atom(x)) for x in ("a", "b", "c")]
        terms += [fn("pair", atom(x), atom(y))
                  for x in ("a", "b", "c") for y in ("a", "b", "c")]
        terms += [fn("nest", fn("f", atom(x)), fn("g", atom(y)))
                  for x in ("a", "b") for y in ("a", "b")]
        cases = [{"left": a, "right": b} for a in terms for b in terms]
        self.assertGreaterEqual(len(cases), 400)
        expected = []
        for row in cases:
            a, b = row["left"], row["right"]
            result = lgg.anti_unify(a, b)
            lgg.check_result(a, b, result)
            reverse = lgg.anti_unify(b, a)
            self.assertEqual(result["generalizer"], reverse["generalizer"])
            self.assertEqual(lgg.instantiate(result["generalizer"],
                                             result["left_substitution"]), a)
            self.assertEqual(lgg.instantiate(result["generalizer"],
                                             result["right_substitution"]), b)
            expected.append(result)
        if shutil.which("swipl") is None:
            if os.environ.get("D10_REQUIRE_SWIPL") == "1":
                self.fail("independent SWI-Prolog unavailable (must not silently pass CI)")
            self.skipTest("real SWI-Prolog comparison is enforced by dedicated CI")
        with tempfile.TemporaryDirectory(prefix="d10-lgg-prolog-") as td:
            file = Path(td) / "cases.json"
            file.write_text(json.dumps(cases, ensure_ascii=False), encoding="utf-8")
            p = subprocess.run(["swipl", "-q", "-s", str(ORACLE), "--", str(file)],
                               capture_output=True, text=True, timeout=90)
            self.assertEqual(p.returncode, 0, p.stderr)
            observed = json.loads(p.stdout)
        self.assertEqual(len(observed), len(expected))
        for index, (a, b) in enumerate(zip(observed, expected)):
            self.assertEqual(a, b, f"real SWI-Prolog mismatch at sample {index}")

    def test_falsified_dossier_metadata_is_blocked(self):
        def mutate(path, value):
            state = copy.deepcopy(self.dossier)
            target = state
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            return state
        counterexamples = [
            (["coordinate"], "0000000000"),
            (["ratified"], True),
            (["status"], "RATIFIED"),
            (["selection"], "SELECTED"),
            (["decision"], "SELECT"),
            (["comparison", "exact_D1_D9_duplicate"], "NO-MATCH"),
            (["comparison", "exact_selected_D10_duplicate"], "NO-MATCH"),
            (["source_evidence"], self.dossier["source_evidence"][:2]),
        ]
        for path, value in counterexamples:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    validate_dossier(mutate(path, value))

    def test_cli_readonly_bounded_and_negative_cases(self):
        with tempfile.TemporaryDirectory(prefix="d10-lgg-cli-") as td:
            path = Path(td) / "cases.json"
            cases = [{"left": fn("pair", atom("x"), atom("x")),
                      "right": fn("pair", atom("y"), atom("y"))}]
            path.write_text(json.dumps(cases), encoding="utf-8")
            cmd = [sys.executable, str(SCRIPT), "--cases", str(path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)[0],
                             lgg.anti_unify(cases[0]["left"], cases[0]["right"]))
            self.assertEqual(json.loads(path.read_text()), cases)
            path.write_text(json.dumps([{"left": {"hole": "V0"}, "right": atom("x")}]))
            fail = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(fail.returncode, 2)
            self.assertIn("BLOCKED", fail.stderr)


if __name__ == "__main__":
    unittest.main()
