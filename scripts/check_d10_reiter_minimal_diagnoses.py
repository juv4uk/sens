#!/usr/bin/env python3
"""D10 research-only finite minimal diagnoses from GIVEN conflict hyperedges.

Historical reference: Reiter (1987) model-based diagnosis; de Kleer &
Williams (1987). The host algorithm here is a conditional algebraic
transversal enumerator, not a device fault detector, original AI engine,
ratified SENS opcode or .sens binary oracle.
"""
from __future__ import annotations

import argparse
import copy
from itertools import combinations, product
import json
from pathlib import Path
import random
import unittest

ROOT=Path(__file__).resolve().parents[1]
DOSSIER=ROOT/"knowledge/d10-reiter-minimal-diagnoses-20261009.json"
D10=ROOT/"knowledge/d10-v1-semantic-inventory.json"
D1D9=ROOT/"knowledge/d1-d9-foundation.json"
SEMANTIC="FINITE-MINIMAL-DIAGNOSES"


def validate_input(universe, conflicts):
    if not isinstance(universe,(tuple,list)):
        raise TypeError("ordered finite universe required")
    if not isinstance(conflicts,(tuple,list)):
        raise TypeError("ordered finite conflict collection required")
    if any(type(v) is not str or not v for v in universe):
        raise TypeError("symbolic reference IDs must be opaque nonempty strings")
    if len(universe)!=len(set(universe)):
        raise ValueError("duplicate component identities")
    positions={v:i for i,v in enumerate(universe)}
    clean=[]
    for row in conflicts:
        if not isinstance(row,(tuple,list)):
            raise TypeError("each conflict must be a finite component set")
        if any(type(v) is not str or v not in positions for v in row):
            raise ValueError("conflict contains unknown component")
        clean.append(frozenset(positions[v] for v in row))
    return tuple(universe),tuple(clean)


def private_certificates(choice,conflicts):
    """Construct first original-index private witness for each chosen component."""
    witnesses=[]
    for component in sorted(choice):
        idx=next((i for i,conflict in enumerate(conflicts)
                  if conflict.intersection(choice)=={component}),None)
        if idx is None:
            raise AssertionError("a purported minimal diagnosis lacks private conflict")
        witnesses.append((component,idx))
    return tuple(witnesses)


def enumerate_diagnoses(universe,conflicts):
    """One exact branching solver; prunes supersets of known diagnoses."""
    names,edges=validate_input(universe,conflicts)
    for idx,edge in enumerate(edges):
        if not edge:
            return ("NO-DIAGNOSIS",idx)
    solutions=set()
    def explore(chosen):
        if any(solution <= chosen for solution in solutions):
            return
        uncovered=next((edge for edge in edges if not (chosen&edge)),None)
        if uncovered is None:
            solutions.difference_update(tuple(s for s in solutions if chosen < s))
            solutions.add(chosen)
            return
        for value in sorted(uncovered):
            explore(chosen|frozenset((value,)))
    explore(frozenset())
    ordered=sorted(solutions,key=lambda s:tuple(sorted(s)))
    entries=[]
    for solution in ordered:
        witness=private_certificates(solution,edges)
        entries.append((
            tuple(names[i] for i in sorted(solution)),
            tuple((names[i],index) for i,index in witness)
        ))
    return ("DIAGNOSES",tuple(entries))


def independent_powerset_oracle(universe,conflicts):
    """Independent finite model: enumerate ALL subsets and filter by minimality."""
    names,edges=validate_input(universe,conflicts)
    for idx,edge in enumerate(edges):
        if not edge:
            return ("NO-DIAGNOSIS",idx)
    all_sets=[]
    for n in range(len(names)+1):
        for entries in combinations(range(len(names)),n):
            candidate=frozenset(entries)
            if all(candidate&edge for edge in edges):
                all_sets.append(candidate)
    minimal=[s for s in all_sets if not any(t<s for t in all_sets)]
    minimal.sort(key=lambda s:tuple(sorted(s)))
    result=[]
    for solution in minimal:
        witnesses=[]
        for i in sorted(solution):
            # Different implementation computes private witnesses by scanning.
            candidate=[ix for ix,e in enumerate(edges) if (solution&e)=={i}]
            assert candidate
            witnesses.append((names[i],min(candidate)))
        result.append((tuple(names[i] for i in sorted(solution)),tuple(witnesses)))
    return ("DIAGNOSES",tuple(result))


def validate_dossier(doc,inv,foundation):
    c=doc["candidate"]
    assert doc["schema"]=="d10-reiter-finite-minimal-diagnoses-research/v1"
    assert doc["status"]=="RESEARCH-PENDING-OWNER-REVIEW"
    assert doc["history"][0]["author"]=="Raymond Reiter"
    assert doc["history"][0]["year"]==1987
    assert doc["history"][0]["doi"]=="10.1016/0004-3702(87)90062-2"
    assert doc["history"][1]["doi"]=="10.1016/0004-3702(87)90063-4"
    assert doc["history"][1]["year"]==1987
    assert doc["history"][0]["url"].startswith("https://www.sciencedirect.com/")
    assert doc["original_vs_ours"].startswith("Reiter supplies")
    assert c["semantic_name"]==SEMANTIC
    assert c["proposal_id"]=="D10P-5007"
    assert c["width"]==10 and c["coordinate"] is None
    assert c["ratified"] is False and c["selected"] is False
    assert c["proposal_status"]=="pending-review"
    assert c["surface_uk"] and c["surface_ukr"] and c["law"]
    assert len(c["sample_cases"])>=5 and len(c["falsifiers"])>=8
    assert c["precise_scope"] and c["derivability"]
    assert len(c["nonduplicate_neighbors"])>=5
    assert len(c["owner_hobby_fanout"])>=6
    assert len(doc["holds"])>=4 and all(x["status"].startswith("HOLD-") for x in doc["holds"])
    assert doc["ledger_effect"]=={
      "pending_rows":1,"selected_additions":0,
      "ratified_additions":0,"allocated_coordinates":0}
    assert inv["domain"]=="D10" and inv["capacity"]==1024
    assert inv["accounting"]["ratified_d10_residents"]==0
    assert inv["accounting"]["selected_semantic_candidates"]>=doc["snapshot"]["selected"]
    assert len(inv["rows"])==inv["accounting"]["selected_semantic_candidates"]
    assert SEMANTIC not in {r["semantic_name"] for r in inv["rows"]}
    assert doc["snapshot"]["inventory_sha"]=="3db40a04c1094c9ea13b0c8d6099ef1d882cf203"
    assert foundation["status"]=="owner-ratified"
    assert SEMANTIC not in {str(v).upper()
                           for d in foundation["domains"].values()
                           for v in d["residents"].values()}
    assert c["coordinate"] is None
    print("D10 REITER: source-pinned pending, zero selected/ratified/coordinates PASS")


class DiagnosisLawTests(unittest.TestCase):
    def test_canonical_historical_dual_example(self):
        actual=enumerate_diagnoses(("a","b","c"),(("a","b"),("b","c")))
        self.assertEqual(actual,("DIAGNOSES",(
          (("a","c"),(("a",0),("c",1))),
          (("b",),(("b",0),))
        )))

    def test_empty_family_vs_unhittable_empty_conflict(self):
        self.assertEqual(enumerate_diagnoses(("a","b"),()),
                         ("DIAGNOSES",(((),()),)))
        self.assertEqual(enumerate_diagnoses((),()),
                         ("DIAGNOSES",(((),()),)))
        self.assertEqual(enumerate_diagnoses(("a",), ((),)),
                         ("NO-DIAGNOSIS",0))
        self.assertEqual(enumerate_diagnoses(("a",), (("a",),(),())),
                         ("NO-DIAGNOSIS",1))

    def test_redundant_conflict_and_duplicate_components_within_edge(self):
        expected=enumerate_diagnoses(("a","b","c"),
                                      (("a","b"),("b","c")))
        for conflicts in [
          (("a","b"),("a","b","c"),("b","c")),
          (("a","b","a"),("b","c")),
          (("a","b"),("b","c"),("a","b"))
        ]:
            observed=enumerate_diagnoses(("a","b","c"),conflicts)
            # Solution identities are invariant; original private witness
            # indices are provenance and should change when reordered.
            self.assertEqual(tuple(z[0] for z in observed[1]),
                             tuple(z[0] for z in expected[1]))

    def test_diagnoses_private_conflicts(self):
        rng=random.Random(87)
        for _ in range(1200):
            size=rng.randint(0,7)
            universe=tuple(f"c{i}" for i in range(size))
            edges=[]
            for _ in range(rng.randint(0,8)):
                edges.append(tuple(c for c in universe if rng.randrange(2)))
            actual=enumerate_diagnoses(universe,edges)
            brute=independent_powerset_oracle(universe,edges)
            self.assertEqual(actual,brute)
            if actual[0]=="DIAGNOSES":
                for diag,cert in actual[1]:
                    self.assertEqual(len(cert),len(diag))
                    for chosen,idx in cert:
                        self.assertEqual(set(edges[idx]) & set(diag),{chosen})

    def test_exhaustive_small_conflict_hypergraphs(self):
        uni=("a","b","c","d")
        powersets=[tuple(uni[i] for i in range(4) if mask&(1<<i))
                   for mask in range(16)]
        total=0
        for number in range(4):
            for ids in product(range(16),repeat=number):
                edges=tuple(powersets[i] for i in ids)
                self.assertEqual(enumerate_diagnoses(uni,edges),
                                 independent_powerset_oracle(uni,edges))
                total+=1
        self.assertEqual(total,4369)
        print(f"D10 REITER: {total} exact 4-component conflict-family combinations")

    def test_input_identity_guard(self):
        failures=[
          (("a","a"),(("a",),)),
          (("a",), (("b",),)),
          (("a",), (("a",1),)),
          (("a",), (True,)),
          ((1,), ()),
          (("a",), "a"),
          ("a", ()),
        ]
        for u,e in failures:
            with self.subTest(u=u,e=e):
                with self.assertRaises((TypeError,ValueError)):
                    enumerate_diagnoses(u,e)

    def test_private_certificate_cannot_be_overclaimed(self):
        with self.assertRaises(AssertionError):
            private_certificates(frozenset({0,1}), (frozenset({0,1}),))
        self.assertEqual(private_certificates(frozenset({0,1}),
                                              (frozenset({0}),frozenset({1}))),
                         ((0,0),(1,1)))

    def test_dossier_fail_closed_mutations(self):
        d=json.loads(DOSSIER.read_text(encoding="utf-8"))
        inv=json.loads(D10.read_text(encoding="utf-8"))
        lower=json.loads(D1D9.read_text(encoding="utf-8"))
        validate_dossier(d,inv,lower)
        mutants=[
          lambda x:x["candidate"].update(selected=True),
          lambda x:x["candidate"].update(ratified=True),
          lambda x:x["candidate"].update(coordinate="1000000000"),
          lambda x:x["candidate"].update(width=9),
          lambda x:x["candidate"].update(semantic_name="CHECK-CONFLICT"),
          lambda x:x["candidate"].update(falsifiers=[]),
          lambda x:x["history"][0].update(doi="10.0000/unproved"),
          lambda x:x["history"][1].update(year=1970),
          lambda x:x["ledger_effect"].update(selected_additions=1),
          lambda x:x["candidate"].update(proposal_status="ratified"),
          lambda x:x.update(status="SELECTED"),
          lambda x:x["history"][0].update(url="https://example.invalid")
        ]
        for i,mutate in enumerate(mutants):
            new=copy.deepcopy(d)
            mutate(new)
            with self.subTest(mutant=i):
                with self.assertRaises(AssertionError):
                    validate_dossier(new,inv,lower)
        print("D10 REITER: 12/12 adversarial dossier mutants BLOCKED")


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    dossier=json.loads(DOSSIER.read_text(encoding="utf-8"))
    inv=json.loads(D10.read_text(encoding="utf-8"))
    foundation=json.loads(D1D9.read_text(encoding="utf-8"))
    validate_dossier(dossier,inv,foundation)
    if args.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(DiagnosisLawTests)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
