#!/usr/bin/env python3
"""#2479 — finite-signature goal search must pass a proof gate.

Stacked on #2474/#2465.  Finite semantic signatures are search evidence only.

This witness:
1. enumerates the current depth<=3 autonomous closure;
2. finds all finite-signature collision classes on the inherited 7-point corpus;
3. attacks them on held-out exact rationals;
4. replays a small exact-Q polynomial equality fragment for total add/mul trees;
5. includes a mandatory x^3 vs x finite-sample falsifier.

Research only.
"""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import importlib.util
import itertools
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
AUTO_PATH = ROOT / "benchmarks" / "core-math-autonomous-closure" / "run.py"
DONOR_PATH = ROOT / "scripts" / "research-2433-core-math-neutral-growth.py"
SPEC_PATH = ROOT / "benchmarks" / "core-math-autonomous-closure" / "spec.json"

HELD_OUT = (
    "-3/1", "3/1", "-3/2", "3/2", "-2/3", "2/3",
    "-1/3", "1/3", "4/1", "5/2",
)


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def eval_outputs(auto, donor, op, corpus: tuple[str, ...], model):
    constants = {
        "neg_one": model.parse("-1/1"),
    }
    outputs = []
    for combo in itertools.product(corpus, repeat=op.arity):
        argv = tuple(model.parse(x) for x in combo)
        value = auto.eval_expr(donor, model, op.expression, argv, constants)
        outputs.append(model.render(value))
    return outputs


Polynomial = dict[tuple[str, ...], Fraction]


class OutsidePolynomial(RuntimeError):
    pass


def poly_clean(poly: Polynomial) -> Polynomial:
    return {m: c for m, c in poly.items() if c != 0}


def poly_add(a: Polynomial, b: Polynomial) -> Polynomial:
    out = dict(a)
    for m, c in b.items():
        out[m] = out.get(m, Fraction(0)) + c
    return poly_clean(out)


def poly_mul(a: Polynomial, b: Polynomial) -> Polynomial:
    out: Polynomial = {}
    for lm, lc in a.items():
        for rm, rc in b.items():
            monomial = tuple(sorted(lm + rm))
            out[monomial] = out.get(monomial, Fraction(0)) + lc * rc
    return poly_clean(out)


def polynomial(node: dict[str, Any]) -> Polynomial:
    if "arg" in node:
        return {(f"x{node['arg']}",): Fraction(1)}
    if "const" in node:
        if node["const"] == "neg_one":
            return {(): Fraction(-1)}
        raise OutsidePolynomial(f"unknown-const:{node['const']}")
    op = node["call"]
    args = node["args"]
    if op == "add" and len(args) == 2:
        return poly_add(polynomial(args[0]), polynomial(args[1]))
    if op == "mul" and len(args) == 2:
        return poly_mul(polynomial(args[0]), polynomial(args[1]))
    raise OutsidePolynomial(op)


def partiality_is_total(node: dict[str, Any]) -> bool:
    return bool(node.get("true") is True)


def proof_status(group) -> tuple[str, str]:
    if not all(partiality_is_total(op.partiality) for op in group):
        return "OBSERVATIONALLY-EQUAL-BUT-UNKNOWN", "partial/outside-total-polynomial-proof"
    polys = []
    try:
        for op in group:
            polys.append(polynomial(op.expression))
    except OutsidePolynomial as exc:
        return "OBSERVATIONALLY-EQUAL-BUT-UNKNOWN", f"outside-polynomial-fragment:{exc}"
    first = polys[0]
    if all(poly == first for poly in polys[1:]):
        proof = canonical_json({
            "model": "replay-of-2458-exact-q-polynomial-fragment",
            "normal_form": [
                {
                    "monomial": list(m),
                    "coefficient": f"{c.numerator}/{c.denominator}",
                }
                for m, c in sorted(first.items())
            ],
        })
        return "PROVED-EQUIVALENT", proof
    return "REFUTED", "distinct-polynomial-normal-forms"


def first_heldout_counterexample(auto, donor, group):
    model_a = donor.FractionModel()
    model_b = donor.PairModel()

    outputs_a = [eval_outputs(auto, donor, op, HELD_OUT, model_a) for op in group]
    outputs_b = [eval_outputs(auto, donor, op, HELD_OUT, model_b) for op in group]
    assert outputs_a == outputs_b

    combos = list(itertools.product(HELD_OUT, repeat=group[0].arity))
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            for k, combo in enumerate(combos):
                if outputs_a[i][k] != outputs_a[j][k]:
                    return {
                        "left_identity": group[i].identity,
                        "right_identity": group[j].identity,
                        "input": list(combo),
                        "left_output": outputs_a[i][k],
                        "right_output": outputs_a[j][k],
                    }
    return None


def x3_vs_x_control() -> dict[str, Any]:
    train = (Fraction(-1), Fraction(0), Fraction(1))
    held = Fraction(2)
    left = [x * x * x for x in train]
    right = list(train)
    assert left == right
    assert held * held * held != held
    return {
        "training": [f"{x.numerator}/{x.denominator}" for x in train],
        "training_signature_equal": True,
        "held_out_input": "2/1",
        "x3": "8/1",
        "x": "2/1",
        "status": "REFUTED",
        "lesson": "finite-signature-match-is-not-universal-identity",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    auto = load_module(AUTO_PATH, "core_math_auto_2479")
    donor = load_module(DONOR_PATH, "core_math_growth_2479")
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    spec["max_depth"] = 3

    ops, metrics = auto.run_closure(spec, donor)
    generated = [op for op in ops if op.depth > 0]
    assert len(generated) == 76

    groups: dict[tuple[int, str], list[Any]] = {}
    for op in generated:
        groups.setdefault((op.arity, op.signature_sha256), []).append(op)

    collisions = [
        group for group in groups.values()
        if len(group) > 1
    ]
    assert len(groups) == 62
    assert sum(len(g) - 1 for g in collisions) == 14

    rows = []
    counts = {
        "REFUTED": 0,
        "PROVED-EQUIVALENT": 0,
        "OBSERVATIONALLY-EQUAL-BUT-UNKNOWN": 0,
    }

    for idx, group in enumerate(
        sorted(collisions, key=lambda g: (g[0].arity, g[0].signature_sha256))
    ):
        held_counterexample = first_heldout_counterexample(auto, donor, group)

        if held_counterexample is not None:
            status = "REFUTED"
            proof = "held-out-counterexample"
            counterexample = canonical_json(held_counterexample)
        else:
            status, proof = proof_status(group)
            counterexample = ""

        counts[status] += 1
        rows.append({
            "collision_class": idx,
            "arity": group[0].arity,
            "training_signature_sha256": group[0].signature_sha256,
            "identity_count": len(group),
            "identities": "|".join(sorted(op.identity for op in group)),
            "training_equal": True,
            "held_out_equal": held_counterexample is None,
            "first_counterexample": counterexample,
            "equivalence_status": status,
            "proof_or_reason": proof,
            "expressions": canonical_json([
                auto.normalize_expr(op.expression) for op in group
            ]),
        })

    with (args.out / "collision-classes.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    control = x3_vs_x_control()

    artifact = {
        "schema": "core-math-goal-proof-gate/v1",
        "authority": "research-only",
        "training_corpus": list(auto.CORPUS),
        "held_out_corpus": list(HELD_OUT),
        "depth3_generated_identities": len(generated),
        "training_signature_classes": len(groups),
        "observational_duplicate_identities": len(generated) - len(groups),
        "collision_class_count": len(collisions),
        "classification_counts": counts,
        "collision_classes": rows,
        "mandatory_finite_signature_falsifier": control,
        "search_contract": {
            "signature_match_means": "candidate-only",
            "acceptable_terminal_statuses": [
                "PROVED-EQUIVALENT",
                "REFUTED",
                "OBSERVATIONALLY-EQUAL-BUT-UNKNOWN",
            ],
            "identity_authority": "proof/equivalence-theory-not-finite-signature",
        },
        "non_conclusions": [
            "held-out equality is still not proof",
            "the polynomial proof fragment is intentionally incomplete",
            "UNKNOWN is preserved outside admitted proof fragments",
            "bounded signatures remain useful for candidate discovery",
        ],
    }
    (args.out / "proof-gate.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core-Math goal proof gate — #2479",
        "",
        f"Depth-3 generated identities: **{len(generated)}**",
        f"Training semantic-signature classes: **{len(groups)}**",
        f"Observational duplicate identities: **{len(generated) - len(groups)}**",
        f"Collision classes: **{len(collisions)}**",
        "",
        "| classification | classes |",
        "|---|---:|",
        f"| REFUTED | {counts['REFUTED']} |",
        f"| PROVED-EQUIVALENT | {counts['PROVED-EQUIVALENT']} |",
        f"| OBSERVATIONALLY-EQUAL-BUT-UNKNOWN | {counts['OBSERVATIONALLY-EQUAL-BUT-UNKNOWN']} |",
        "",
        "Mandatory finite-signature falsifier:",
        "- x^3 and x are equal on {-1,0,1};",
        "- at x=2 they are 8 and 2;",
        "- therefore finite-signature equality cannot be semantic identity authority.",
        "",
        "Search contract:",
        "signature match -> candidate; candidate must be proved, refuted, or remain UNKNOWN.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
