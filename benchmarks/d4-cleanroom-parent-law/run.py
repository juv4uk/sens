#!/usr/bin/env python3
"""#3244 — clean-room D4 parent-law placement gate.

A D4 coordinate under prefix p is admitted only by a two-child generator
certificate G(p,0), G(p,1). Single-capability placement is fail-closed.

Research/policy witness only; no new capability placement is created here.
"""

from __future__ import annotations
import argparse, csv, json
from pathlib import Path

PARENTS = {
    "000": "EMPTY",
    "001": "QUOTE",
    "010": "ATOM",
    "011": "CDR",
    "100": "CAR",
    "101": "EQ",
    "110": "COND",
    "111": "CONS",
}

REQUIRED = {
    "parent_invariant",
    "bit_meaning",
    "child0_semantics",
    "child1_semantics",
    "generator_equation",
    "parent_recovery",
    "falsifier",
}

def classify(claim: dict) -> str:
    if claim.get("refuted"):
        return "REFUTED"
    present={k for k in REQUIRED if claim.get(k)}
    if present == REQUIRED:
        return "PROVED-GENERATOR"
    return "UNKNOWN"

def selector_claim(parent: str) -> dict:
    # Positive control only for the two selector roots.
    if parent=="011":
        return {
            "parent":parent,
            "family":"selector",
            "parent_invariant":"rest projection followed by one selector choice",
            "bit_meaning":"0=first projection;1=rest projection",
            "child0_semantics":"rest then first",
            "child1_semantics":"rest then rest",
            "generator_equation":"G(p,b)=compose(p, selector_b)",
            "parent_recovery":"drop final selector choice bit",
            "falsifier":"swap only one child meaning while keeping bit fixed",
        }
    if parent=="100":
        return {
            "parent":parent,
            "family":"selector",
            "parent_invariant":"first projection followed by one selector choice",
            "bit_meaning":"0=first projection;1=rest projection",
            "child0_semantics":"first then first",
            "child1_semantics":"first then rest",
            "generator_equation":"G(p,b)=compose(p, selector_b)",
            "parent_recovery":"drop final selector choice bit",
            "falsifier":"swap only one child meaning while keeping bit fixed",
        }
    return {"parent":parent,"family":"selector","refuted":True}

def unknown_claim(parent: str, family: str) -> dict:
    return {
        "parent":parent,
        "family":family,
        "parent_invariant":"",
        "bit_meaning":"",
        "child0_semantics":"",
        "child1_semantics":"",
        "generator_equation":"",
        "parent_recovery":"",
        "falsifier":"",
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)

    rows=[]

    # Selector positive control.
    for p in PARENTS:
        c=selector_claim(p)
        status=classify(c)
        if p in {"011","100"}:
            assert status=="PROVED-GENERATOR"
        else:
            assert status=="REFUTED"
        rows.append({
            "family":"selector",
            "parent_bits":p,
            "parent_surface":PARENTS[p],
            "status":status,
            "single_capability_slot_allowed":False,
            "generator_equation":c.get("generator_equation",""),
            "bit_meaning":c.get("bit_meaning",""),
        })

    # Two clean-room capability requirements. No parent-law certificate exists yet.
    for family in ("late-bound-executable","unbounded-semantic-reentry"):
        for p in PARENTS:
            c=unknown_claim(p,family)
            assert classify(c)=="UNKNOWN"
            rows.append({
                "family":family,
                "parent_bits":p,
                "parent_surface":PARENTS[p],
                "status":"UNKNOWN",
                "single_capability_slot_allowed":False,
                "generator_equation":"",
                "bit_meaning":"",
            })

    # Pair hypothesis: the two new capabilities as siblings under one parent.
    pair_rows=[]
    for p in PARENTS:
        claim=unknown_claim(p,"late-binding-vs-reentry-sibling-pair")
        status=classify(claim)
        assert status=="UNKNOWN"
        pair_rows.append({
            "parent_bits":p,
            "parent_surface":PARENTS[p],
            "status":status,
            "reason":"no independent shared generator law / sibling bit meaning / parent recovery certificate",
        })

    # Negative gate: a one-child proposal can never classify as PROVED-GENERATOR.
    one_child={
        "parent":"001",
        "family":"synthetic-single-child",
        "parent_invariant":"some relation",
        "bit_meaning":"0 means candidate",
        "child0_semantics":"one capability",
        "child1_semantics":"",
        "generator_equation":"partial G(p,0)",
        "parent_recovery":"drop bit",
        "falsifier":"present",
    }
    assert classify(one_child)=="UNKNOWN"

    with (args.out/"parent-tournament.tsv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0].keys()),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    with (args.out/"pair-hypothesis.tsv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(pair_rows[0].keys()),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(pair_rows)

    result={
        "schema":"d4-cleanroom-parent-law-gate/v1",
        "authority":"research-only",
        "rule":"D4 placement requires a complete two-child generator certificate under a D3 parent",
        "required_certificate_fields":sorted(REQUIRED),
        "selector_positive_control":{
            "proved_parents":["011","100"],
            "other_parents_refuted":6,
        },
        "late_bound_parent_statuses":{"UNKNOWN":8},
        "reentry_parent_statuses":{"UNKNOWN":8},
        "pair_hypothesis_statuses":{"UNKNOWN":8},
        "single_child_proposal_status":"UNKNOWN",
        "new_d4_coordinates_assigned":0,
        "non_conclusions":[
            "UNKNOWN is not refutation",
            "semantic resemblance is not a generator law",
            "an empty coordinate is not placement evidence",
            "historical D4 identities are not premises",
        ],
    }
    (args.out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report="""# D4 clean-room parent-law gate — #3244

Placement rule:
a D4 child is admitted only through a complete two-child generator certificate G(parent,0/1).

Positive control:
- selector parent 011: PROVED-GENERATOR
- selector parent 100: PROVED-GENERATOR
- other six D3 parents for selector family: REFUTED

New clean-room capabilities:
- late-bound executable construction: UNKNOWN under all 8 D3 parents
- unbounded semantic re-entry: UNKNOWN under all 8 D3 parents
- sibling-pair hypothesis between them: UNKNOWN under all 8 D3 parents

Single-child proposal control: UNKNOWN, never PROVED-GENERATOR.

New D4 coordinates assigned: **0**.

Interpretation:
a capability proof is not a placement proof. Placement waits for a semantic two-child generator law.
"""
    (args.out/"report.md").write_text(report,encoding="utf-8")
    print(report)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
