#!/usr/bin/env python3
"""#2409 phase A: can CAR/CDR emerge without any pair observer?

Research-only bounded attack.  The admitted grammar in this slice contains
whole-value identity, constants, ATOM, EQ, CONS and COND-like choice.  It
contains no primitive that can inspect a pair field.

The script combines:
1. a small semantic-signature BFS over heterogeneous/held-out pair trees; and
2. an authority audit showing that adding UNCONS immediately makes projection
   derivation circular because UNCONS already exposes both hidden fields.

This is not the full #2409 grammar: LAMBDA/recursion are follow-up phases.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

NIL = ("NIL",)
TRUE = ("TRUE",)
FALSE = NIL


def atom(name: str):
    return ("ATOM", name)


def pair(a, d):
    return ("PAIR", a, d)


def is_pair(v):
    return isinstance(v, tuple) and len(v) == 3 and v[0] == "PAIR"


def atom_p(v):
    return TRUE if not is_pair(v) else FALSE


def eq_p(a, b):
    return TRUE if a == b else FALSE


def truthy(v):
    return v != NIL


def target_car(v):
    return v[1] if is_pair(v) else ("FAIL",)


def target_cdr(v):
    return v[2] if is_pair(v) else ("FAIL",)


def corpus():
    a,b,c,d,e,f,g,h = [atom(x) for x in "abcdefgh"]
    # First four are search/training shapes, remainder are held-out and include
    # improper/asymmetric/repeated structures.
    return [
        pair(a,b),
        pair(pair(a,b),pair(c,d)),
        pair(a,pair(b,c)),
        pair(pair(a,b),c),
        pair(pair(pair(d,e),f),pair(g,h)),
        pair(pair(a,a),pair(b,b)),
        pair(atom("u"),pair(pair(atom("v"),atom("w")),atom("x"))),
        atom("outside-domain"),
    ]


VALUES = corpus()
TRAIN = tuple(range(4))
HELD_OUT = tuple(range(4, len(VALUES)))


@dataclass(frozen=True)
class Expr:
    text: str
    depth: int
    signature: tuple


def sig(fn):
    return tuple(fn(v) for v in VALUES)


def dedup(exprs):
    best = {}
    for expr in exprs:
        old = best.get(expr.signature)
        if old is None or (expr.depth, len(expr.text), expr.text) < (old.depth, len(old.text), old.text):
            best[expr.signature] = expr
    return list(best.values())


def bfs(max_depth: int, state_cap: int):
    # Constant set is deliberately corpus-independent.  No quoted leaf from the
    # target pair trees is admitted, preventing finite-corpus memorization.
    values = [
        Expr("x", 0, tuple(VALUES)),
        Expr("()", 0, tuple(NIL for _ in VALUES)),
        Expr("FAIL", 0, tuple(("FAIL",) for _ in VALUES)),
        Expr("k", 0, tuple(atom("k") for _ in VALUES)),
    ]
    predicates = []
    all_values = dedup(values)
    all_preds = []

    target_sigs = {
        "CAR": tuple(target_car(v) for v in VALUES),
        "CDR": tuple(target_cdr(v) for v in VALUES),
    }

    found = {}
    counts = []

    for depth in range(1, max_depth + 1):
        prior_values = list(all_values)
        new_preds = []

        # Unary ATOM.
        for a in prior_values:
            new_preds.append(
                Expr(f"(ATOM {a.text})", depth, tuple(atom_p(x) for x in a.signature))
            )

        # EQ over a bounded canonical subset of shortest value signatures.
        short_values = sorted(prior_values, key=lambda e:(e.depth,len(e.text),e.text))[:40]
        for i,a in enumerate(short_values):
            for b in short_values[i:]:
                new_preds.append(
                    Expr(
                        f"(EQ {a.text} {b.text})",
                        depth,
                        tuple(eq_p(x,y) for x,y in zip(a.signature,b.signature)),
                    )
                )
        all_preds = dedup(all_preds + new_preds)
        short_preds = sorted(all_preds, key=lambda e:(e.depth,len(e.text),e.text))[:40]

        new_values = []
        # CONS is a constructor, never a pair observer.
        for a in short_values[:20]:
            for b in short_values[:20]:
                new_values.append(
                    Expr(
                        f"(CONS {a.text} {b.text})",
                        depth,
                        tuple(pair(x,y) for x,y in zip(a.signature,b.signature)),
                    )
                )

        # COND-like choice. Limit combinations but preserve deterministic search.
        branches = short_values[:20]
        for p in short_preds[:20]:
            for a in branches[:10]:
                for b in branches[:10]:
                    new_values.append(
                        Expr(
                            f"(COND {p.text} {a.text} {b.text})",
                            depth,
                            tuple(x if truthy(q) else y for q,x,y in zip(p.signature,a.signature,b.signature)),
                        )
                    )

        all_values = dedup(all_values + new_values)
        if len(all_values) > state_cap:
            all_values = sorted(all_values, key=lambda e:(e.depth,len(e.text),e.text))[:state_cap]

        for name, target in target_sigs.items():
            if name in found:
                continue
            for expr in all_values:
                if expr.signature == target:
                    found[name] = expr
                    break

        counts.append({
            "depth": depth,
            "value_signatures": len(all_values),
            "predicate_signatures": len(all_preds),
        })

    return found, counts, all_values


def separating_witness(target_name: str, exprs):
    target = target_car if target_name == "CAR" else target_cdr
    # Find one held-out input where every retained expression differs from the
    # target. If none exists, return the strongest per-expression mismatch count.
    for idx in HELD_OUT:
        want = target(VALUES[idx])
        if all(expr.signature[idx] != want for expr in exprs):
            return {
                "held_out_index": idx,
                "input": repr(VALUES[idx]),
                "target": repr(want),
                "all_candidates_differ": True,
            }
    best = min(
        (
            sum(expr.signature[i] != target(VALUES[i]) for i in HELD_OUT),
            expr.text,
        )
        for expr in exprs
    )
    return {
        "all_candidates_differ": False,
        "best_held_out_mismatches": best[0],
        "best_candidate": best[1],
    }


def circular_control():
    # UNCONS exposes both hidden pair fields.  CAR/CDR can then be selected
    # immediately, but that is equivalent destructuring authority, not a
    # derivation from constructors/predicates/control.
    return {
        "basis": "UNCONS : Pair -> Pair(first,rest)",
        "CAR_path": "UNCONS -> first-output",
        "CDR_path": "UNCONS -> rest-output",
        "status": "circular",
        "authority_audit": "reject: primitive specification already exposes both pair fields",
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-depth",type=int,default=4)
    ap.add_argument("--state-cap",type=int,default=4000)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    if args.max_depth < 1 or args.state_cap < 100:
        ap.error("positive bounds required")
    args.out.mkdir(parents=True,exist_ok=True)

    found,counts,exprs=bfs(args.max_depth,args.state_cap)
    car_status="derived" if "CAR" in found else "bounded-negative"
    cdr_status="derived" if "CDR" in found else "bounded-negative"

    # Positive guard: the corpus itself must distinguish CAR from CDR.
    assert sig(target_car) != sig(target_cdr)
    # Negative expectation for the declared no-observer grammar.
    assert car_status == "bounded-negative"
    assert cdr_status == "bounded-negative"

    rows=[
        {
            "target":"CAR",
            "grammar":"identity+constants+ATOM+EQ+CONS+COND; no pair observer",
            "max_depth":args.max_depth,
            "status":car_status,
            "found_expr":found.get("CAR").text if "CAR" in found else "",
        },
        {
            "target":"CDR",
            "grammar":"identity+constants+ATOM+EQ+CONS+COND; no pair observer",
            "max_depth":args.max_depth,
            "status":cdr_status,
            "found_expr":found.get("CDR").text if "CDR" in found else "",
        },
        {
            "target":"CAR/CDR",
            "grammar":"UNCONS alternative observer control",
            "max_depth":1,
            "status":"circular",
            "found_expr":"UNCONS exposes target fields",
        },
    ]

    with (args.out/"results.tsv").open("w",newline="",encoding="utf-8") as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0]),delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

    result={
        "schema":"selector-root-global-attack/phase-a-v1",
        "authority":"research-only",
        "scope":"constructor+predicate+control grammar without LAMBDA/recursion",
        "bounds":{"max_depth":args.max_depth,"state_cap":args.state_cap},
        "corpus":{"size":len(VALUES),"train_indices":TRAIN,"held_out_indices":HELD_OUT},
        "search_counts":counts,
        "CAR":{
            "status":car_status,
            "separating_witness":separating_witness("CAR",exprs),
        },
        "CDR":{
            "status":cdr_status,
            "separating_witness":separating_witness("CDR",exprs),
        },
        "alternative_observer_control":circular_control(),
        "anti_smuggling":{
            "forbidden":["host tuple indexing","pattern field bind","iterator destructuring","helper specified as first/rest"],
            "reason":"these already carry pair-elimination authority",
        },
        "non_conclusions":[
            "bounded-negative does not prove global independence",
            "LAMBDA and structural recursion are not searched in phase A",
            "UNCONS control is circular, not a smaller independent derivation",
            "no binary coordinate relation is used as evidence",
        ],
    }
    (args.out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")

    report=f"""# Wider selector-root attack — #2409 phase A

Search grammar: whole-value identity + corpus-independent constants + ATOM + EQ + CONS + COND.
No pair observer is admitted.

| target | status |
|---|---|
| CAR | {car_status} |
| CDR | {cdr_status} |
| UNCONS alternative observer | circular |

Depth bound: **{args.max_depth}**. Retained semantic-signature cap: **{args.state_cap}**.

The result is a bounded negative for the constructor/predicate/control grammar only.
It does not yet cover LAMBDA or structural recursion.

The UNCONS control demonstrates the anti-smuggling boundary: once a primitive
already exposes both fields, CAR/CDR become trivial projections, but no semantic
independence has been reduced.
"""
    (args.out/"report.md").write_text(report,encoding="utf-8")
    print(report)


if __name__=="__main__":
    main()
