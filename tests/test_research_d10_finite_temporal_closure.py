#!/usr/bin/env python3
"""D10 #5000 finite integer STP: graph dual and REAL SMT Z3 independent oracle."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import random
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/research_d10_finite_temporal_closure.py"
spec=importlib.util.spec_from_file_location("research_d10_finite_temporal_closure",SCRIPT)
assert spec is not None and spec.loader is not None
law=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=law
spec.loader.exec_module(law)


class FiniteTemporalClosureTests(unittest.TestCase):
    def test_empty_and_disconnected_are_unbounded_not_zero(self):
        got=law.floyd_closure(3,[])
        self.assertEqual(got["status"],"CONSISTENT")
        self.assertEqual(got["tight_upper_bounds"],[
            [0,None,None],[None,0,None],[None,None,0]])
        self.assertTrue(law.check_certificate(3,[],got))
        self.assertEqual(got,law.bellman_reference(3,[]))

    def test_transitive_tighter_bound_and_directionality(self):
        edges=[(0,1,4),(1,2,3),(0,2,15)]
        got=law.floyd_closure(3,edges)
        self.assertEqual(got["tight_upper_bounds"],[
            [0,4,7],[None,0,3],[None,None,0]])
        self.assertEqual(got,law.bellman_reference(3,edges))
        self.assertTrue(law.check_certificate(3,edges,got))

    def test_negative_upper_bounds_on_consistent_schedules(self):
        edges=[(0,1,-3),(1,0,4),(1,2,2)]
        got=law.floyd_closure(3,edges)
        self.assertEqual(got["status"],"CONSISTENT")
        self.assertEqual(got["tight_upper_bounds"][0][1],-3)
        self.assertEqual(got["tight_upper_bounds"][0][2],-1)
        self.assertEqual(got["tight_upper_bounds"][1][0],4)
        self.assertEqual(got,law.bellman_reference(3,edges))

    def test_parallel_edges_tightest_and_order_independent(self):
        edges=[(0,1,10),(0,1,2),(1,0,-2),(0,1,8)]
        exp=law.floyd_closure(2,edges)
        self.assertEqual(exp["tight_upper_bounds"],[[0,2],[-2,0]])
        self.assertEqual(exp,law.floyd_closure(2,list(reversed(edges))))
        self.assertEqual(exp,law.bellman_reference(2,edges))

    def test_self_loop_and_three_vertex_cycle_have_actual_contradictions(self):
        cases=[(1,[(0,0,-1)],[0,0],[-1]),
               (3,[(0,1,2),(1,2,1),(2,0,-4)],[0,1,2,0],[2,1,-4])]
        for n,edges,vs,ws in cases:
            with self.subTest(n=n):
                got=law.floyd_closure(n,edges)
                self.assertEqual(got["status"],"INCONSISTENT_NEGATIVE_CYCLE")
                self.assertIsNone(got["tight_upper_bounds"])
                self.assertEqual(got["negative_cycle"]["vertices"],vs)
                self.assertEqual(got["negative_cycle"]["weights"],ws)
                self.assertTrue(law.check_certificate(n,edges,got))
                self.assertEqual(got,law.bellman_reference(n,edges))

    def test_minimum_length_then_lex_negative_cycle_certificate(self):
        # Three negative 2-cycles, canonical lex 0->1->0 wins.
        e=[(0,1,-2),(1,0,1),(0,2,-5),(2,0,4),(1,2,-3),(2,1,2)]
        got=law.floyd_closure(3,e)
        self.assertEqual(got["status"],"INCONSISTENT_NEGATIVE_CYCLE")
        self.assertEqual(got["negative_cycle"]["vertices"],[0,1,0])
        self.assertEqual(got,law.bellman_reference(3,e))

    def test_no_false_certificates_or_hidden_approximations(self):
        edges=[(0,1,1),(1,2,1),(0,2,4)]
        correct=law.floyd_closure(3,edges)
        self.assertTrue(law.check_certificate(3,edges,correct))
        wrong={"status":"CONSISTENT","tight_upper_bounds":[
            [0,1,4],[None,0,1],[None,None,0]],"negative_cycle":None}
        self.assertFalse(law.check_certificate(3,edges,wrong))
        cycle=law.floyd_closure(1,[(0,0,-1)])
        cycle["negative_cycle"]["strict_negative_sum"]=0
        self.assertFalse(law.check_certificate(1,[(0,0,-1)],cycle))
        self.assertNotEqual(correct["tight_upper_bounds"][0][2],4)

    def test_reject_malformed_or_unbounded_research_inputs(self):
        cases=[(0,[]),(6,[]),(True,[]),(1,[(0,0,True)]),
               (1,[(0,0,1001)]),(1,[(1,0,0)]),(1,[(0,0,0.5)]),
               (2,[(0,1,0,4)]),(2,["text"]), (1,[(0,0,0)]*81)]
        for n,edges in cases:
            with self.subTest(n=n,edges=str(edges)[:20]):
                with self.assertRaises(law.TemporalError):
                    law.floyd_closure(n,edges)

    def test_large_reproducible_mutation_survey_two_algorithms(self):
        r=law.run_survey()
        self.assertEqual(r["status"],"RESEARCH_HOLD_NOT_SELECTED")
        self.assertEqual(r["cases"],384)
        self.assertGreater(r["inconsistent"],100)
        self.assertGreater(r["unbounded_pairs"],50)
        self.assertEqual(r["d10_selected_delta"],0)
        self.assertEqual(r["original_sens_migrations"],0)

    def test_genuine_z3_int_solver_sat_and_pairwise_optimize(self):
        """Must run against REAL external z3-solver in dedicated GitHub workflow."""
        import os
        if os.environ.get("D10_REQUIRE_Z3")!="1":
            self.skipTest("set D10_REQUIRE_Z3=1 in external oracle CI")
        import z3
        self.assertTrue(z3.get_version_string().startswith("4."))
        rng=random.Random(1962)
        total=0
        sat_count=unsat_count=unbounded_pairs=0
        for n in range(1,5):
            for trial in range(19):
                events=[z3.Int(f"t_{n}_{trial}_{i}") for i in range(n)]
                planted=[rng.randint(-5,5) for _ in range(n)]
                edges=[]
                for i in range(n):
                    for j in range(n):
                        if rng.random()<0.6:
                            edges.append((i,j,planted[j]-planted[i]+rng.randint(0,4)))
                if trial%3==1:
                    edges.append((0,0,-1))
                if trial%3==2 and n>=2:
                    edges.extend([(0,1,-3),(1,0,2)])
                result=law.floyd_closure(n,edges)
                solver=z3.Solver()
                solver.add(*(events[j]-events[i]<=w for i,j,w in edges))
                verdict=solver.check()
                if verdict==z3.unsat:
                    unsat_count+=1
                    self.assertEqual(result["status"],"INCONSISTENT_NEGATIVE_CYCLE")
                    self.assertTrue(law.check_certificate(n,edges,result))
                else:
                    sat_count+=1
                    self.assertEqual(verdict,z3.sat)
                    self.assertEqual(result["status"],"CONSISTENT")
                    for i in range(n):
                        for j in range(n):
                            opt=z3.Optimize()
                            opt.add(*(events[v]-events[u]<=w for u,v,w in edges))
                            obj=opt.maximize(events[j]-events[i])
                            self.assertEqual(opt.check(),z3.sat)
                            bound=opt.upper(obj)
                            actual=None if str(bound) in ("oo","+oo") else int(str(bound))
                            if actual is None:
                                unbounded_pairs+=1
                            self.assertEqual(result["tight_upper_bounds"][i][j],actual,
                                             f"n={n}, edges={edges}, i={i}, j={j}")
                total+=1
        self.assertEqual(total,76)
        self.assertGreater(sat_count,0)
        self.assertGreater(unsat_count,0)
        self.assertGreater(unbounded_pairs,0)


if __name__=="__main__":
    unittest.main()
