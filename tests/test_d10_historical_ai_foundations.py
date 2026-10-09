#!/usr/bin/env python3
"""Exact finite ATMS/STRIPS mathematical oracles. RESEARCH; not binary SENS execution."""
import copy
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "knowledge/d10-historical-atms-strips-law-intake-20261009.json"
NAMES = ("ATMS-MINIMAL-SUPPORT-LABEL", "STRIPS-GOAL-REGRESSION")

def support_label(antecedents, nogoods):
    """Independent operational algorithm: Cartesian support join + strict antichain."""
    choices = [tuple(frozenset(x) for x in label) for label in antecedents]
    prohibited = tuple(frozenset(g) for g in nogoods)
    if any(not label for label in choices):
        return []
    candidates = set()
    for product in itertools.product(*choices):
        environment = frozenset().union(*product)
        if any(ng.issubset(environment) for ng in prohibited):
            continue
        candidates.add(environment)
    minimal = [env for env in candidates
               if not any(other < env for other in candidates)]
    return [list(sorted(x)) for x in sorted(minimal, key=lambda x:(len(x), tuple(sorted(x))))]

def label_semantic_oracle(antecedents, nogoods, output, universe):
    """No Cartesian join: enumerate contexts and compare supported propositions."""
    returned = [frozenset(x) for x in output]
    forbidden = [frozenset(x) for x in nogoods]
    for mask in range(1 << len(universe)):
        context = {name for k, name in enumerate(universe) if mask & (1 << k)}
        if any(ng <= context for ng in forbidden):
            continue
        expected = all(any(set(option) <= context for option in label)
                       for label in antecedents)
        observed = any(env <= context for env in returned)
        assert observed == expected, ("ATMS incomplete/unsound context",context)
    assert len(set(map(frozenset,returned))) == len(returned)
    for a, b in itertools.permutations(returned, 2):
        assert not a.issubset(b), "ATMS label not inclusion-minimal"
    assert all(not any(ng <= env for ng in forbidden) for env in returned)

def regress(goal, pre, added, deleted):
    """Classical ground-positive STRIPS backward goal preimage, not world execution."""
    goal,pre,added,deleted = map(frozenset,(goal,pre,added,deleted))
    if added & deleted:
        raise ValueError("add/delete must be disjoint")
    if (goal - added) & deleted:
        return None
    return sorted((goal - added) | pre)

def progress(world, pre, added, deleted):
    """Independent world-state reference (not invoked from regress)."""
    assert not (set(added) & set(deleted))
    if not set(pre).issubset(world):
        return None
    return (set(world)-set(deleted))|set(added)

def check_source(d):
    assert d["schema"]=="d10-historical-symbolic-ai-foundations/v1"
    assert d["status"]=="SOURCE-GROUNDED-PENDING-REVIEW-UNSELECTED"
    assert d["snapshot"]["selected"]==634
    assert d["snapshot"]["ratified"]==0
    assert d["snapshot"]["inventory_git_blob"]=="65014431ac3e64633cd0be3630cfafc5e7a9aea3"
    assert d["impact"]=={
        "d10_selected_delta":0,"d10_coordinate_delta":0,"d10_ratified_delta":0,
        "d2_control_delta":0,"existing_ledger_preservation":True}
    assert [x["semantic_name"] for x in d["candidates"]]==list(NAMES)
    assert [x["proposal_id"] for x in d["candidates"]]==["D10P-0912","D10P-0913"]
    assert len(d["holds"])>=4 and len(d["background"])>=4
    for c in d["candidates"]:
        assert c["decision"]=="PENDING-REVIEW-NOT-SELECTED"
        assert c["coordinate"] is None and c["ratified_resident"] is False
        assert c["width"]==10
        assert c["stable_id"] and c["surface_uk"] and c["surface_ukr"]
        assert len(c["positives"])>=4 and len(c["falsifiers"])>=3
        assert c["sources"] and all(v["url"].startswith("https://") for v in c["sources"])
    return d["candidates"]

def witnesses(candidates):
    atms,strips=candidates
    count=0
    for v in atms["positives"]:
        observed=support_label(v["antecedent_labels"],v["nogoods"])
        assert observed==v["expected"], ("ATMS sample",v,observed)
        count+=1
    for v in strips["positives"]:
        observed=regress(v["goal"],v["pre"],v["add"],v["del"])
        if "error" in v:
            assert observed is None
        else:
            assert observed==v["expected"], ("STRIPS sample",v,observed)
        count+=1
    return count

def stress_atms():
    rng = random.Random(1979_1986)
    universe=tuple("ABCDE")
    count=0
    for _ in range(2400):
        labels=[]
        for _k in range(rng.randrange(0,4)):
            label=[]
            for _ in range(rng.randrange(0,5)):
                label.append([x for x in universe if rng.randrange(2)])
            labels.append(label)
        nogoods=[]
        for _k in range(rng.randrange(0,4)):
            nogoods.append([x for x in universe if rng.randrange(2)])
        out=support_label(labels,nogoods)
        label_semantic_oracle(labels,nogoods,out,universe)
        assert support_label([out],nogoods)==out, "ATMS antichain not idempotent"
        count+=1
    return count

def stress_strips():
    universe=tuple("ABC")
    subsets=[frozenset(x for i,x in enumerate(universe) if mask & (1<<i))
             for mask in range(1<<len(universe))]
    count=0
    for g,p,a,d in itertools.product(subsets,repeat=4):
        if a & d:
            try:
                regress(g,p,a,d)
            except ValueError:
                count+=1
                continue
            raise AssertionError("STRIPS invalid add/delete overlap accepted")
        predecessor=regress(g,p,a,d)
        for world in subsets:
            next_world=progress(set(world),p,a,d)
            forward=(next_world is not None and g.issubset(next_world))
            backward=(predecessor is not None and
                      set(predecessor).issubset(world))
            assert forward==backward,(g,p,a,d,world,predecessor)
            count+=1
    return count

def rejects_invalid(d):
    mutations=[
        lambda x:x["candidates"][0].update(coordinate="0"*10),
        lambda x:x["candidates"][1].update(ratified_resident=True),
        lambda x:x["candidates"][0].update(decision="SELECTED"),
        lambda x:x["impact"].update(d10_selected_delta=2),
        lambda x:x["impact"].update(d2_control_delta=1),
        lambda x:x["snapshot"].update(inventory_git_blob="0"*40),
        lambda x:x["candidates"][0]["positives"].clear(),
        lambda x:x["candidates"][1]["falsifiers"].clear(),
        lambda x:x["candidates"][1].update(proposal_id="D10P-0912"),
        lambda x:x["candidates"][1]["sources"].clear(),
        lambda x:x["candidates"][0].update(width=11),
    ]
    for idx, mutate in enumerate(mutations):
        changed=copy.deepcopy(d)
        mutate(changed)
        try:check_source(changed)
        except (AssertionError,KeyError,TypeError):continue
        raise AssertionError("unblocked source mutation "+str(idx))
    return len(mutations)

def main():
    data=json.loads(PATH.read_text(encoding="utf-8"))
    cs=check_source(data)
    samples=witnesses(cs)
    atms=stress_atms()
    strips=stress_strips()
    mutations=rejects_invalid(data)
    print(f"D10 AI 1959–1986: PASS witnesses={samples}, context_oracles={atms}, STRIPS world-relations={strips}, mutations={mutations}")
    print("ATMS minimal support joins and exact STRIPS regression, selected_delta=0, coords=0, ratified=0")
    print("No SENS runtime parity or owner admission claimed.")

if __name__=="__main__":
    main()
