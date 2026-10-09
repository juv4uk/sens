#!/usr/bin/env python3
"""D10 symbolic AI research: Dung grounded argument labelling.

Independent witness models:
  (1) synchronous IN/OUT/UNDEC propagation (unattacked and defeated attackers)
  (2) Dung characteristic operator F(S) iterated from the empty extension.
No SENS evaluator, truth-domain, T5, or machine opcode is altered.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
import copy
import json
from pathlib import Path
import random
import unittest
import argparse

ROOT=Path(__file__).resolve().parents[1]
DOSSIER=ROOT/"knowledge/d10-dung-grounded-argumentation-20261009.json"
INVENTORY=ROOT/"knowledge/d10-v1-semantic-inventory.json"
LOWER=ROOT/"knowledge/d1-d9-foundation.json"
NAME="GROUNDED-ARGUMENT-LABELING"


def validate(nodes,attacks):
    if not isinstance(nodes,(list,tuple)) or not isinstance(attacks,(list,tuple)):
        raise TypeError("finite node and attack sequences required")
    if any(not isinstance(n,str) or not n for n in nodes):
        raise ValueError("opaque test labels must be nonempty strings")
    if len(set(nodes))!=len(nodes):
        raise ValueError("duplicate argument identity")
    identities=set(nodes)
    normalized=[]
    seen=set()
    for edge in attacks:
        if not isinstance(edge,(tuple,list)) or len(edge)!=2:
            raise ValueError("every attack must contain exactly two ids")
        a,b=edge
        if not isinstance(a,str) or not isinstance(b,str) or a not in identities or b not in identities:
            raise ValueError("attack endpoints must be declared arguments")
        if (a,b) in seen:
            raise ValueError("duplicate ATTACK edge")
        seen.add((a,b))
        normalized.append((a,b))
    return tuple(nodes),tuple(normalized)


def grounded_labelling(nodes,attacks):
    """Simultaneous propagation of IN/OUT; UNDEC remains explicit."""
    nodes,attacks=validate(nodes,attacks)
    attackers={a:set() for a in nodes}
    targets={a:set() for a in nodes}
    for attacker,target in attacks:
        attackers[target].add(attacker)
        targets[attacker].add(target)
    accepted=set()
    rejected=set()
    while True:
        new_in={n for n in nodes if n not in accepted and n not in rejected
                and attackers[n] <= rejected}
        proposed_in=accepted|new_in
        new_out={n for n in nodes if n not in proposed_in and n not in rejected
                 and bool(attackers[n]&proposed_in)}
        proposed_out=rejected|new_out
        if proposed_in==accepted and proposed_out==rejected:
            break
        accepted,rejected=proposed_in,proposed_out
    undecided=set(nodes)-accepted-rejected
    assert not (accepted&rejected) and len(accepted|rejected|undecided)==len(nodes)
    return {
        "IN":[a for a in nodes if a in accepted],
        "OUT":[a for a in nodes if a in rejected],
        "UNDEC":[a for a in nodes if a in undecided],
    }


def characteristic_oracle(nodes,attacks):
    """Separate formal Dung least fixed point by defense over edge relation."""
    nodes,attacks=validate(nodes,attacks)
    attacks=set(attacks)
    selected=frozenset()
    def defended(n,selected):
        all_attackers={u for (u,v) in attacks if v==n}
        return all(any((s,u) in attacks for s in selected) for u in all_attackers)
    while True:
        new=frozenset(n for n in nodes if defended(n,selected))
        if new==selected:
            break
        assert selected<=new
        selected=new
    defeated={v for (u,v) in attacks if u in selected}
    assert not(selected & defeated)
    return {
        "IN":[n for n in nodes if n in selected],
        "OUT":[n for n in nodes if n in defeated],
        "UNDEC":[n for n in nodes if n not in selected and n not in defeated],
    }


def check_dossier(data,inventory,foundation):
    c=data["candidate"]
    assert data["schema"]=="d10-symbolic-ai-grounded-argumentation-v1"
    assert data["status"]=="RESEARCH-PENDING-OWNER-REVIEW"
    assert data["source"]["author"]=="Phan Minh Dung"
    assert data["source"]["doi"]=="10.1016/0004-3702(94)00041-X"
    assert data["source"]["url"].startswith("https://doi.org/")
    assert data["owner_donors"][0]["blob_sha"]=="dadc52a2f40f2f30ad77642898afb81980044c08"
    assert c["semantic_name"]==NAME and c["proposal_id"]=="D10P-4971"
    assert c["width"]==10 and c["coordinate"] is None
    assert c["selected"] is False and c["ratified"] is False
    assert c["proposal_status"]=="pending-review"
    assert c["surface_uk"] and c["surface_ukr"] and c["law"]
    assert len(c["witnesses"])==9 and len(c["falsifiers"])>=8
    assert len(c["neighbors"])>=7 and c["derivability"]
    assert c["upper_boundary"].startswith("Three output partitions")
    assert data["accounting"]=={
        "selected_additions":0,"ratification_additions":0,
        "coordinate_additions":0,"pending_ledger_rows":1}
    assert inventory["domain"]=="D10" and inventory["capacity"]==1024
    assert inventory["accounting"]["selected_semantic_candidates"]>=634
    assert inventory["accounting"]["ratified_d10_residents"]==0
    assert len(inventory["rows"])==inventory["accounting"]["selected_semantic_candidates"]
    names={row["semantic_name"] for row in inventory["rows"]}
    assert {"JTMS-STATE-SUBST", "PROVE-RULE"} <= names
    assert "PROVE-RULE" in names and NAME not in names
    assert foundation["status"]=="owner-ratified"
    lower={str(n).upper() for d in foundation["domains"].values()
           for n in d["residents"].values()}
    assert "REASON" in lower and NAME not in lower
    assert data["snapshot"]["selected"]==634
    assert data["snapshot"]["inventory_sha"]=="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    for row in c["witnesses"]:
        actual=grounded_labelling(row["nodes"],row["attacks"])
        assert actual==row["result"],(row,actual)
        assert characteristic_oracle(row["nodes"],row["attacks"])==actual
    print("D10 DUNG grounded dossier: PASS source law, +0 selected, no new coordinates")


class DungFiniteTests(unittest.TestCase):
    def test_source_examples(self):
        data=json.loads(DOSSIER.read_text(encoding="utf-8"))
        for row in data["candidate"]["witnesses"]:
            self.assertEqual(grounded_labelling(row["nodes"],row["attacks"]),row["result"])

    def test_exhaustive_all_directed_graphs_up_to_four(self):
        tested=0
        for n in range(0,5):
            nodes=[f"a{i}" for i in range(n)]
            edge_pool=[(a,b) for a in nodes for b in nodes]
            for word in range(1<<len(edge_pool)):
                edges=[edge_pool[k] for k in range(len(edge_pool)) if word>>k&1]
                got=grounded_labelling(nodes,edges)
                expected=characteristic_oracle(nodes,edges)
                self.assertEqual(got,expected, (nodes,edges))
                tested+=1
        self.assertEqual(tested,66067)
        print(f"D10 DUNG: {tested} complete directed graphs cross-checked with independent fixed point")

    def test_random_six_to_eight_argument_graphs(self):
        rng=random.Random(20261009)
        for n in range(5,9):
            nodes=[f"v{i}" for i in range(n)]
            for _ in range(750):
                attacks=[(a,b) for a in nodes for b in nodes if rng.random()<.32]
                self.assertEqual(grounded_labelling(nodes,attacks),
                                 characteristic_oracle(nodes,attacks))

    def test_invariance_under_input_reordering_as_sets(self):
        rng=random.Random(63100)
        for _ in range(300):
            nodes=[str(i) for i in range(rng.randint(0,8))]
            attacks=[(a,b) for a in nodes for b in nodes if rng.random()<.30]
            orig=grounded_labelling(nodes,attacks)
            rev=grounded_labelling(list(reversed(nodes)),list(reversed(attacks)))
            for name in ("IN","OUT","UNDEC"):
                self.assertEqual(set(orig[name]),set(rev[name]))

    def test_mutual_and_self_attack_stay_undecided(self):
        self.assertEqual(grounded_labelling(["a","b"],[("a","b"),("b","a")]),
                         {"IN":[],"OUT":[],"UNDEC":["a","b"]})
        self.assertEqual(grounded_labelling(["a"],[("a","a")]),
                         {"IN":[],"OUT":[],"UNDEC":["a"]})

    def test_external_grounding_defeats_cycle(self):
        actual=grounded_labelling(["a","b","c","d"],
             [("a","b"),("b","c"),("c","a"),("d","a")])
        self.assertEqual(actual,{"IN":["b","d"],"OUT":["a","c"],"UNDEC":[]})

    def test_reject_untrusted_graph_shapes(self):
        invalid=[
            (["a","a"],[]),
            (["a"],[("a","b")]),
            (["a"],[("b","a")]),
            (["a"],[("a","a"),("a","a")]),
            (["a"],[("a",)]),
            (["a"],[("a","a","a")]),
            ([3],[]),
            (["a"],[(1,"a")]),
            ("a",[]),
            ([],[("a","a")]),
            ([""],[])
        ]
        for nodes,edges in invalid:
            with self.subTest(input=(nodes,edges)):
                with self.assertRaises((TypeError,ValueError)):
                    grounded_labelling(nodes,edges)

    def test_dossier_and_negative_mutations(self):
        data=json.loads(DOSSIER.read_text(encoding="utf-8"))
        inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
        low=json.loads(LOWER.read_text(encoding="utf-8"))
        check_dossier(data,inv,low)
        mutations=[
            lambda z:z["candidate"].update(selected=True),
            lambda z:z["candidate"].update(ratified=True),
            lambda z:z["candidate"].update(coordinate="1000000000"),
            lambda z:z["candidate"].update(width=9),
            lambda z:z["candidate"].update(semantic_name="PROVE-RULE"),
            lambda z:z["candidate"].update(witnesses=[]),
            lambda z:z["candidate"].update(falsifiers=[]),
            lambda z:z["source"].update(url="unverified"),
            lambda z:z["source"].update(doi="invented"),
            lambda z:z["owner_donors"][0].update(blob_sha="unverified"),
            lambda z:z["accounting"].update(selected_additions=1),
            lambda z:z.update(status="SELECTED"),
            lambda z:z["candidate"].update(proposal_status="ratified")
        ]
        for idx,fn in enumerate(mutations):
            bad=copy.deepcopy(data)
            fn(bad)
            with self.subTest(mutant=idx):
                with self.assertRaises(AssertionError):
                    check_dossier(bad,inv,low)
        print(f"D10 DUNG: {len(mutations)} source/ratification mutations rejected")


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--self-test",action="store_true")
    opts=ap.parse_args()
    dossier=json.loads(DOSSIER.read_text(encoding="utf-8"))
    inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
    lower=json.loads(LOWER.read_text(encoding="utf-8"))
    check_dossier(dossier,inv,lower)
    if opts.self_test:
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(DungFiniteTests)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise SystemExit(1)
