#!/usr/bin/env python3
"""#3752 — EXPT reciprocal-base × exponent-sign D8 collapse witness."""

from __future__ import annotations

import argparse
import hashlib
import json
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"


def load_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coord for coord, name in doc["residents"].items()}
    assert by_name["RECIP"] == "010110"
    assert by_name["EXPT"] == "010111"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "recip": by_name["RECIP"],
        "expt": by_name["EXPT"],
    }


def bases() -> list[Fraction]:
    values = {
        Fraction(n, d)
        for n in range(-4, 5)
        if n != 0
        for d in range(1, 5)
    }
    out = sorted(values)
    assert len(out) == 22
    return out


EXPONENTS = tuple(range(-4, 5))


def recip(x: Fraction) -> Fraction:
    assert x != 0
    return Fraction(x.denominator, x.numerator)


def expt(x: Fraction, n: int) -> Fraction:
    return x ** n


def table(fn, carrier):
    return tuple(str(fn(x, n)) for x in carrier for n in EXPONENTS)


def run() -> dict[str, object]:
    authority = load_authority()
    carrier = bases()

    recip_involution = sum(recip(recip(x)) == x for x in carrier)
    exponent_sign_involution = sum(-(-n) == n for n in EXPONENTS)

    observations = 0
    collapse_a_eq_b = 0
    collapse_ab_eq_id = 0
    axis_observable = 0

    for x in carrier:
        for n in EXPONENTS:
            observations += 1
            base = expt(x, n)
            a = expt(recip(x), n)
            b = expt(x, -n)
            ab = expt(recip(x), -n)

            collapse_a_eq_b += a == b
            collapse_ab_eq_id += ab == base
            axis_observable += a != base

    assert observations == 198
    assert recip_involution == 22
    assert exponent_sign_involution == 9
    assert collapse_a_eq_b == observations
    assert collapse_ab_eq_id == observations
    assert axis_observable > 0

    transforms = {
        "ID": table(lambda x, n: expt(x, n), carrier),
        "RECIP-BASE": table(lambda x, n: expt(recip(x), n), carrier),
        "NEG-EXPONENT": table(lambda x, n: expt(x, -n), carrier),
        "RECIP-BASE+NEG-EXPONENT": table(
            lambda x, n: expt(recip(x), -n), carrier
        ),
    }
    unique_global_tables = len(set(transforms.values()))
    assert unique_global_tables == 2
    assert transforms["RECIP-BASE"] == transforms["NEG-EXPONENT"]
    assert transforms["ID"] == transforms["RECIP-BASE+NEG-EXPONENT"]

    return {
        "schema": "d8-expt-recip-exponent-sign/v1",
        "status": "DEPENDENT-AXES-REJECTED",
        "authority": {
            "d6": authority,
            "d8": "#3281 research",
            "task": "#3752",
        },
        "carrier": {
            "nonzero_exact_q_bases": len(carrier),
            "integer_exponents": len(EXPONENTS),
            "observations": observations,
            "numerator_min": -4,
            "numerator_max": 4,
            "denominator_min": 1,
            "denominator_max": 4,
            "exponent_min": min(EXPONENTS),
            "exponent_max": max(EXPONENTS),
        },
        "witness": {
            "recip_involution_pass": recip_involution,
            "exponent_sign_involution_pass": exponent_sign_involution,
            "reciprocal_base_equals_negative_exponent_pass": collapse_a_eq_b,
            "both_axes_equal_identity_pass": collapse_ab_eq_id,
            "one_axis_observable_cases": axis_observable,
            "putative_product_tables": 4,
            "unique_global_tables": unique_global_tables,
        },
        "collapse": {
            "RECIP-BASE": "NEG-EXPONENT",
            "RECIP-BASE+NEG-EXPONENT": "ID",
            "law": "(1/x)^n = x^(-n)",
        },
        "result": {
            "axes_independent": False,
            "analyzed_d8_coordinates": 0,
            "candidate_footprint": [],
            "reason": (
                "Reciprocal-base and exponent-sign refinements are extensionally "
                "the same transformation of EXPT semantics; their product has "
                "two global tables, not four."
            ),
        },
        "non_conclusions": [
            "This does not reject D6 RECIP or EXPT.",
            "This rejects only reciprocal-base × exponent-sign as independent D8 axes.",
            "No D8 coordinate, resident, or callability is admitted.",
            "No D7 ancestry or historical D8 donor is used.",
        ],
    }


def render(report: dict[str, object]) -> str:
    c = report["carrier"]
    w = report["witness"]
    return "\n".join([
        "# D8 EXPT reciprocal-base × exponent-sign screen — #3752",
        "",
        "Result: **DEPENDENT-AXES-REJECTED**.",
        "",
        f"- exact nonzero bases: {c['nonzero_exact_q_bases']}",
        f"- integer exponents: {c['integer_exponents']}",
        f"- observations: {c['observations']}",
        f"- RECIP involution: {w['recip_involution_pass']}/22",
        f"- exponent-sign involution: {w['exponent_sign_involution_pass']}/9",
        (
            "- (1/x)^n = x^(-n): "
            f"{w['reciprocal_base_equals_negative_exponent_pass']}/{c['observations']}"
        ),
        (
            "- (1/x)^(-n) = x^n: "
            f"{w['both_axes_equal_identity_pass']}/{c['observations']}"
        ),
        f"- putative product tables: {w['putative_product_tables']}",
        f"- unique global tables: {w['unique_global_tables']}",
        "",
        "D8 coordinates allocated: **0**.",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    report = run()
    text = render(report)

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "witness.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
