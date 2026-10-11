#!/usr/bin/env python3
"""#3750 — INTEGERP/RATIONALP × sign-axis D8 falsifier."""

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
    assert by_name["INTEGERP"] == "111110"
    assert by_name["RATIONALP"] == "111111"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "integerp": by_name["INTEGERP"],
        "rationalp": by_name["RATIONALP"],
    }


def corpus() -> list[Fraction]:
    values = {
        Fraction(n, d)
        for n in range(-8, 9)
        for d in range(1, 9)
    }
    out = sorted(values)
    assert len(out) == 87
    return out


def integerp(x: Fraction) -> bool:
    return x.denominator == 1


def rationalp(x: Fraction) -> bool:
    # Bounded lane is exact-Q by construction.
    return True


def run() -> dict[str, object]:
    authority = load_authority()
    values = corpus()

    integer_count = sum(integerp(x) for x in values)
    noninteger_rational_count = len(values) - integer_count

    neg_involution = sum(-(-x) == x for x in values)
    value_sign_observable = sum((-x) != x for x in values)
    integerp_sign_invariant = sum(integerp(-x) == integerp(x) for x in values)
    rationalp_sign_invariant = sum(rationalp(-x) == rationalp(x) for x in values)
    integerp_sign_observable = sum(integerp(-x) != integerp(x) for x in values)
    rationalp_sign_observable = sum(rationalp(-x) != rationalp(x) for x in values)

    assert integer_count == 17
    assert noninteger_rational_count == 70
    assert neg_involution == 87
    assert value_sign_observable == 86
    assert integerp_sign_invariant == 87
    assert rationalp_sign_invariant == 87
    assert integerp_sign_observable == 0
    assert rationalp_sign_observable == 0

    return {
        "schema": "d8-integerp-rationalp-sign/v1",
        "status": "UNOBSERVABLE-AXIS-REJECTED",
        "authority": {
            "d6": authority,
            "exact_type_law": "#3355",
            "d8": "#3281 research",
            "task": "#3750",
        },
        "carrier": {
            "exact_q_values": len(values),
            "exact_integers": integer_count,
            "exact_noninteger_rationals": noninteger_rational_count,
            "numerator_min": -8,
            "numerator_max": 8,
            "denominator_min": 1,
            "denominator_max": 8,
            "zero_included": True,
        },
        "witness": {
            "neg_involution_pass": neg_involution,
            "value_sign_observable_cases": value_sign_observable,
            "integerp_sign_invariant_pass": integerp_sign_invariant,
            "rationalp_sign_invariant_pass": rationalp_sign_invariant,
            "integerp_sign_observable_cases": integerp_sign_observable,
            "rationalp_sign_observable_cases": rationalp_sign_observable,
        },
        "result": {
            "axis_independent": False,
            "axis_observable_to_family": False,
            "analyzed_d8_coordinates": 0,
            "candidate_footprint": [],
            "reason": (
                "NEG changes 86/87 carrier values but changes neither INTEGERP "
                "nor RATIONALP output on any exact-Q witness."
            ),
        },
        "non_conclusions": [
            "This rejects only sign as a second D8 axis for INTEGERP/RATIONALP.",
            "It does not reject the current D6 INTEGERP/RATIONALP family.",
            "It does not prove that no other independent refinement exists.",
            "No D8 coordinate, resident, or callability is admitted.",
            "No D7 ancestry or historical D8 donor is used.",
        ],
    }


def render(report: dict[str, object]) -> str:
    c = report["carrier"]
    w = report["witness"]
    return "\n".join([
        "# D8 INTEGERP/RATIONALP × sign screen — #3750",
        "",
        "Result: **UNOBSERVABLE-AXIS-REJECTED**.",
        "",
        f"- exact-Q values: {c['exact_q_values']}",
        f"- exact integers: {c['exact_integers']}",
        f"- noninteger rationals: {c['exact_noninteger_rationals']}",
        f"- NEG involution: {w['neg_involution_pass']}/{c['exact_q_values']}",
        f"- sign changes value: {w['value_sign_observable_cases']} cases",
        f"- INTEGERP sign invariant: {w['integerp_sign_invariant_pass']}/{c['exact_q_values']}",
        f"- RATIONALP sign invariant: {w['rationalp_sign_invariant_pass']}/{c['exact_q_values']}",
        "- INTEGERP sign-observable outputs: 0",
        "- RATIONALP sign-observable outputs: 0",
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
