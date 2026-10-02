#!/usr/bin/env python3
"""#2390 bounded remove-one attack for the selector semantic basis.

Research-only. The experiment works on symbolic pair/list behavior, not code
arithmetic. It asks whether CAR/CDR can be reconstructed from the other
projection under a bounded projection-composition grammar, and whether the two
selector extension laws collapse to one parameterized composition schema.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

FAIL = ("FAIL",)


def atom(name: str):
    return ("ATOM", name)


def pair(a, d):
    return ("PAIR", a, d)


def project(value, op: str):
    if not isinstance(value, tuple) or not value or value[0] != "PAIR":
        return FAIL
    return value[1] if op == "A" else value[2]


def eval_selector(value, descriptor: str):
    out = value
    # Descriptor "AD" denotes A after D (CADR): apply appended actions first.
    for op in reversed(descriptor):
        out = project(out, op)
        if out == FAIL:
            return FAIL
    return out


def corpus():
    # Unique leaves make projection paths observationally distinguishable.
    a,b,c,d,e,f,g,h = [atom(x) for x in "abcdefgh"]
    return [
        pair(a,b),
        pair(pair(a,b), pair(c,d)),
        pair(pair(pair(a,b),c), pair(d,pair(e,f))),
        pair(a, pair(b, pair(c,d))),
        pair(pair(a, pair(b,c)), pair(pair(d,e), pair(f,g))),
        pair(pair(pair(a,b), pair(c,d)), pair(pair(e,f), pair(g,h))),
        atom("z"),
    ]


def signature(descriptor: str):
    return [eval_selector(value, descriptor) for value in corpus()]


def remove_one(target: str, remaining: str, max_depth: int):
    target_sig = signature(target)
    candidates = []
    for depth in range(1, max_depth + 1):
        descriptor = remaining * depth
        candidates.append(descriptor)
        if signature(descriptor) == target_sig:
            return {
                "status": "synthesized",
                "path": descriptor,
                "depth": depth,
                "tested": len(candidates),
            }
    # Smallest explicit witness separating target from every remaining-only path.
    for i, value in enumerate(corpus()):
        target_value = eval_selector(value, target)
        values = [eval_selector(value, path) for path in candidates]
        if all(v != target_value for v in values):
            return {
                "status": "bounded-negative",
                "path": None,
                "depth": max_depth,
                "tested": len(candidates),
                "counterexample_index": i,
                "target_value": repr(target_value),
                "candidate_values": [repr(v) for v in values],
            }
    return {
        "status": "unresolved",
        "path": None,
        "depth": max_depth,
        "tested": len(candidates),
    }


def extension_schema(max_depth: int):
    checked = 0
    for depth in range(1, max_depth + 1):
        # All A/D descriptors at this depth.
        for bits in range(1 << depth):
            path = "".join("D" if bits & (1 << (depth - 1 - i)) else "A" for i in range(depth))
            for projection in ("A", "D"):
                child = path + projection
                for value in corpus():
                    direct = eval_selector(value, child)
                    # Generic law: extend(current, p) = current after p.
                    staged = eval_selector(project(value, projection), path)
                    if direct != staged:
                        return {
                            "status": "falsified",
                            "checked": checked,
                            "path": path,
                            "projection": projection,
                            "value": repr(value),
                        }
                    checked += 1
    return {
        "status": "bounded-confirmed",
        "checked": checked,
        "schema": "extend(selector, projection) = selector after projection",
        "projection_domain": ["A", "D"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-depth", type=int, default=6)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.max_depth < 1:
        ap.error("--max-depth must be positive")
    args.out.mkdir(parents=True, exist_ok=True)

    car = remove_one("A", "D", args.max_depth)
    cdr = remove_one("D", "A", args.max_depth)
    schema = extension_schema(args.max_depth)

    assert car["status"] == "bounded-negative"
    assert cdr["status"] == "bounded-negative"
    assert schema["status"] == "bounded-confirmed"

    rows = [
        {
            "fact": "CAR/first-projection",
            "attack": "remove-CAR; CDR-only composition grammar",
            "status": car["status"],
            "search_bound": args.max_depth,
            "effect": "locally-necessary-under-declared-grammar",
        },
        {
            "fact": "CDR/rest-projection",
            "attack": "remove-CDR; CAR-only composition grammar",
            "status": cdr["status"],
            "search_bound": args.max_depth,
            "effect": "locally-necessary-under-declared-grammar",
        },
        {
            "fact": "extend-A + extend-D",
            "attack": "replace two laws by one projection-parameterized composition schema",
            "status": schema["status"],
            "search_bound": args.max_depth,
            "effect": "upper-bound 2 laws -> 1 schema",
        },
        {
            "fact": "selector-family carrier premise",
            "attack": "derive from more general pair/list carrier",
            "status": "unknown",
            "search_bound": 0,
            "effect": "requires external pair/list premise accounting",
        },
    ]

    with (args.out / "attacks.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    result = {
        "schema": "selector-basis-minimality/v1",
        "authority": "research-only",
        "grammar": {
            "remove_one": "composition of the single remaining projection only",
            "max_depth": args.max_depth,
            "corpus_size": len(corpus()),
            "generic_extension": "one composition schema parameterized by admitted projection choice",
        },
        "car_remove_one": car,
        "cdr_remove_one": cdr,
        "extension_schema": schema,
        "carrier_premise": {
            "status": "unknown",
            "reason": "whether selector typing is implied by a more general pair/list carrier is outside this bounded grammar",
        },
        "intervals": {
            "validated_current_global": [0, 5],
            "bounded_selector_projection_grammar": [2, 4],
            "explanation": [
                "CAR and CDR have bounded remove-one evidence only within the declared projection-composition grammar",
                "extend-A/extend-D collapse to one generic composition schema",
                "carrier premise and generic-schema independence remain unknown",
                "do not promote CAR/CDR to globally independent roots without broader #2019 evidence",
            ],
        },
        "non_conclusions": [
            "bounded-negative is not metaphysical impossibility",
            "this does not prove CAR/CDR globally independent from all admitted SENS operations",
            "one generic extension schema is not free; it remains a charged candidate law",
            "no bit-coordinate relation is used as evidence",
        ],
    }
    (args.out / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = f"""# Selector basis minimality — #2390

Search grammar: projection-only composition, maximum depth **{args.max_depth}**.

| attacked fact | result |
|---|---|
| CAR without CAR | {car['status']} |
| CDR without CDR | {cdr['status']} |
| two extension laws -> one parameterized composition schema | {schema['status']} |
| selector-family carrier premise | UNKNOWN |

## Bounded interpretation

- CAR and CDR are observationally necessary within the declared projection-only grammar.
- extend-A and extend-D are both instances of one semantic composition schema parameterized by projection choice.
- therefore the **bounded local** selector interval tightens from [0,5] to **[2,4]**.
- the validated global/accounting interval remains **[0,5]** until broader #2019/remove-one evidence and ledger review adopt the stronger result.

No code-bit arithmetic participates in this proof.
"""
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
