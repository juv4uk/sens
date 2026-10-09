#!/usr/bin/env python3
"""#4991: finite directed binary arc-consistency, bounded falsifiers and SWI."""
from __future__ import annotations
import importlib.util
import itertools
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/research_d10_finite_arc_consistency.py"
PROLOG = ROOT / "tests/oracles/d10_finite_arc_consistency.pl"
spec = importlib.util.spec_from_file_location("arc_consistency_research", SOURCE)
model = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(model)


def arc(a, b, pairs):
    return {"from": a, "to": b, "allowed": [list(p) for p in pairs]}


def instance(domains, arcs):
    return {"domains": domains, "arcs": arcs}


def relation(mask):
    return [pair for i, pair in enumerate(itertools.product((0,1), repeat=2))
            if mask & (1 << i)]


class FiniteArcConsistency(unittest.TestCase):
    def test_exhaustive_two_variable_bidirectional_domains_and_relations(self):
        options = ([0], [1], [0,1])
        for a, b in itertools.product(options, repeat=2):
            for p, q in itertools.product(range(16), repeat=2):
                x = instance({"a":list(a),"b":list(b)},
                             [arc("a","b",relation(p)),arc("b","a",relation(q))])
                self.assertEqual(model.queue_fixpoint(x), model.round_fixpoint(x))

    def test_exhaustive_three_variable_chain(self):
        options = ([0], [1], [0,1])
        for a,b,c in itertools.product(options, repeat=3):
            for p,q in itertools.product(range(16), repeat=2):
                x = instance({"a":list(a),"b":list(b),"c":list(c)},
                             [arc("a","b",relation(p)),arc("b","c",relation(q))])
                self.assertEqual(model.queue_fixpoint(x), model.round_fixpoint(x))

    def test_directionality_and_asymmetric_pair_orientation(self):
        x = instance({"a":[0,1],"b":[0,1]},
                     [arc("a","b",[(0,1)])])
        self.assertEqual(model.queue_fixpoint(x)["domains"], {"a":[0],"b":[0,1]})
        rev = instance({"a":[0,1],"b":[0,1]},
                       [arc("b","a",[(0,1)])])
        self.assertEqual(model.queue_fixpoint(rev)["domains"], {"a":[0,1],"b":[0]})

    def test_propagation_revisits_incoming_arcs(self):
        # x=0 supported by y=0 initially, but y=0 is removed by y->z.
        x = instance({"x":[0,1],"y":[0,1],"z":[1]},
                     [arc("x","y",[(0,0),(1,1)]),
                      arc("y","z",[(1,1)])])
        self.assertEqual(model.queue_fixpoint(x)["domains"],
                         {"x":[1],"y":[1],"z":[1]})

    def test_odd_cycle_maintains_nonempty_arc_consistency_but_no_global_model(self):
        ne = [(0,1),(1,0)]
        x = instance({"a":[0,1],"b":[0,1],"c":[0,1]},
                     [arc("a","b",ne),arc("b","c",ne),arc("c","a",ne)])
        self.assertEqual(model.queue_fixpoint(x)["status"], "ARC-CONSISTENT")
        self.assertFalse(model.has_global_solution(x))

    def test_empty_domain_is_not_success_and_order_and_duplicates_do_not_matter(self):
        x = instance({"a":[0],"b":[1]},[arc("a","b",[(0,0)])])
        self.assertEqual(model.queue_fixpoint(x)["status"],
                         "EMPTY-DOMAIN-CONTRADICTION")
        original = instance({"a":[0,1],"b":[0,1]},
                            [arc("a","b",[(1,0)]),arc("b","a",[(0,1)])])
        repeated = instance({"b":[1,0],"a":[1,0]},
                            [arc("b","a",[(0,1)]),arc("a","b",[(1,0)]),
                             arc("a","b",[(1,0)])])
        self.assertEqual(model.queue_fixpoint(original),model.queue_fixpoint(repeated))
        self.assertEqual(model.round_fixpoint(original),model.round_fixpoint(repeated))

    def test_malformed_and_falsified_constraints_fail_closed(self):
        base = instance({"a":[0,1],"b":[0,1]},[arc("a","b",[(0,0)])])
        bad = [
            {"domains":{},"arcs":[]},
            instance({"a":[True],"b":[0]},[]),
            instance({"a":[0,0],"b":[0]},[]),
            instance({"a":[0],"b":[0]},[arc("a","b",[("bad",0)])]),
            instance({"a":[0],"b":[0]},[arc("a","unknown",[])]),
            instance({"a":[0],"b":[0]},[arc("a","a",[(0,0)])]),
            instance({"a":[0],"b":[0]},[arc("a","b",[(0,0),(0,0)])]),
            instance({"a":[0],"b":[0]},[arc("a","b",[(0,0)]),
                                      arc("a","b",[])]),
            instance({"a":[0],"b":[0]},[{"from":"a","to":"b","allowed":[],"host":True}])
        ]
        for case in bad:
            with self.subTest(case=case),self.assertRaises((TypeError,ValueError)):
                model.queue_fixpoint(case)
        original = json.loads(json.dumps(base))
        model.queue_fixpoint(base)
        self.assertEqual(base,original)

    @unittest.skipUnless(shutil.which("swipl"), "real SWI-Prolog not installed")
    def test_independent_swi_prolog_clpfd_arc_support_oracle(self):
        randomizer = random.Random(1977)
        options = ([0], [1], [0,1])
        problems = [
            instance({"a":list(a),"b":list(b)},[arc("a","b",relation(p)),
                                                arc("b","a",relation(q))])
            for a,b in itertools.product(options, repeat=2)
            for p,q in itertools.product(range(16), repeat=2)
            if ((p*31 + q*17) % 29 == 0)
        ]
        ne=[(0,1),(1,0)]
        problems.append(instance({"a":[0,1],"b":[0,1],"c":[0,1]},
                                 [arc("a","b",ne),arc("b","c",ne),arc("c","a",ne)]))
        for _ in range(40):
            domains={n:list(randomizer.choice(options)) for n in ("a","b","c")}
            arcs=[arc("a","b",relation(randomizer.randrange(16))),
                  arc("b","c",relation(randomizer.randrange(16)))]
            problems.append(instance(domains, arcs))
        proc=subprocess.run(
            ["swipl","-q","-s",str(PROLOG)],
            input="\n".join(json.dumps(p) for p in problems)+"\n",
            text=True,capture_output=True,timeout=100
        )
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertTrue(proc.stdout.lstrip().startswith('{"'),
                        f"non-JSON SWI output: {proc.stdout[:500]!r}; {proc.stderr}")
        # SWI json_write_dict wraps wide dictionaries across several lines.
        # Read one complete JSON value at a time; NEVER compare truncated lines.
        got=[]
        decoder=json.JSONDecoder()
        output=proc.stdout
        pos=0
        while pos < len(output):
            while pos < len(output) and output[pos].isspace():
                pos += 1
            if pos >= len(output):
                break
            try:
                value, end=decoder.raw_decode(output, pos)
            except json.JSONDecodeError as exc:
                self.fail(f"malformed SWI JSON offset {pos}: {output[pos:pos+400]!r}; {exc}")
            got.append(value)
            pos=end
        self.assertEqual(len(got),len(problems),proc.stderr)
        for i,(case,oracle) in enumerate(zip(problems,got)):
            with self.subTest(i=i):
                self.assertEqual(model.queue_fixpoint(case),oracle)
                self.assertEqual(model.round_fixpoint(case),oracle)


if __name__ == "__main__":
    unittest.main()
