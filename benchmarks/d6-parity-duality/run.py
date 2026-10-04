#!/usr/bin/env python3
"""#3078 — coordinate-independent D6 parity duality witness.

Semantic authority in this experiment is the exact integer parity relation.
CURRENT D6 coordinates are loaded only as report provenance and are not used to
compute or validate the law.

Predicate outputs are exact D1 bits 1/0.
"""

from __future__ import annotations

import argparse
import csv
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

EVEN_ID = "sr-qcstbceparwp"
ODD_ID = "sr-vnrkjfutjtyh"


def bit1(value: bool) -> int:
    return 1 if value else 0


def even_bit(n: int) -> int:
    if type(n) is not int:
        raise TypeError("OUT-OF-SCOPE: exact integer required")
    return bit1(n % 2 == 0)


def odd_bit(n: int) -> int:
    if type(n) is not int:
        raise TypeError("OUT-OF-SCOPE: exact integer required")
    return bit1(n % 2 != 0)


def corpus() -> list[int]:
    small = list(range(-33, 34))
    large = [
        -(2**127),
        -(2**127) + 1,
        -(10**60),
        -(10**60) + 1,
        10**60,
        10**60 + 1,
        2**127,
        2**127 + 1,
    ]
    return small + large


def verify_stable_rows(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = {row["stable_resident_id"]: row for row in data["rows"]}
    assert EVEN_ID in rows and ODD_ID in rows
    even = rows[EVEN_ID]
    odd = rows[ODD_ID]
    assert even["current_domain"] == odd["current_domain"] == "D6"
    assert even["semantic_status"] == odd["semantic_status"] == "RECOVERED"
    assert even["semantic_role"] == odd["semantic_role"] == "predicate"
    assert even["semantic_class"] == odd["semantic_class"] == "predicate"
    return {EVEN_ID: even, ODD_ID: odd}


def semantic_witness(values: list[int]) -> dict[str, Any]:
    rows = []
    period2_checks = 0
    false_period1_counterexamples = []
    false_equal_counterexamples = []

    for n in values:
        e = even_bit(n)
        o = odd_bit(n)
        assert e in {0, 1} and o in {0, 1}
        assert o == 1 - e
        assert e == 1 - o
        assert e + o == 1
        assert e * o == 0

        for k in (-17, -3, -1, 0, 1, 4, 19):
            assert even_bit(n + 2 * k) == e
            assert odd_bit(n + 2 * k) == o
            period2_checks += 2

        if even_bit(n + 1) != e:
            false_period1_counterexamples.append(n)
        if e != o:
            false_equal_counterexamples.append(n)

        rows.append({
            "integer": str(n),
            "even_d1": e,
            "odd_d1": o,
            "complement": o == 1 - e,
            "exclusive": e * o == 0,
            "exhaustive": e + o == 1,
        })

    assert false_period1_counterexamples
    assert false_equal_counterexamples

    nonintegers = [
        Fraction(1, 2),
        Fraction(-3, 2),
        "2",
        None,
    ]
    rejected = []
    for value in nonintegers:
        for fn_name, fn in [("even", even_bit), ("odd", odd_bit)]:
            try:
                fn(value)  # type: ignore[arg-type]
            except TypeError as exc:
                rejected.append({
                    "fn": fn_name,
                    "input": repr(value),
                    "status": "OUT-OF-SCOPE",
                    "reason": str(exc),
                })
            else:
                raise AssertionError("non-integer value unexpectedly admitted")

    return {
        "rows": rows,
        "period2_checks": period2_checks,
        "false_period1_first_counterexample": false_period1_counterexamples[0],
        "false_even_equals_odd_first_counterexample": false_equal_counterexamples[0],
        "noninteger_rejections": rejected,
    }


def geometry_accounting(stable: dict[str, dict[str, Any]]) -> dict[str, Any]:
    even_bits = stable[EVEN_ID]["current_bits"]
    odd_bits = stable[ODD_ID]["current_bits"]
    assert len(even_bits) == len(odd_bits) == 6
    current_hamming = sum(a != b for a, b in zip(even_bits, odd_bits, strict=True))

    # This is accounting, not a semantic theorem. A relation certificate can
    # name both arbitrary 6-bit coordinates directly (12 coordinate bits), or a
    # local one-bit-axis candidate can name one 5-bit prefix plus the fact that
    # both role bits are used (5 prefix bits + 1 orientation convention).
    shared_prefix = even_bits[:-1] if even_bits[:-1] == odd_bits[:-1] else None
    current_axis_payload_bits = 6 if shared_prefix is not None else None
    arbitrary_pair_payload_bits = 12

    return {
        "current_projection": {
            EVEN_ID: even_bits,
            ODD_ID: odd_bits,
            "hamming_distance": current_hamming,
        },
        "semantic_geometry_status": "NEIGHBORHOOD-CANDIDATE",
        "one_bit_axis_is_semantically_proved": False,
        "coordinate_accounting": {
            "arbitrary_pair_direct_coordinate_bits": arbitrary_pair_payload_bits,
            "current_shared_prefix_plus_orientation_bits": current_axis_payload_bits,
            "note": "mechanism/certificate accounting only; does not prove adjacency",
        },
        "reencoding_guard": (
            "semantic complement law remains true after arbitrary coordinate "
            "re-encoding; therefore CURRENT adjacency is not semantic authority"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    stable = verify_stable_rows(args.corpus)
    values = corpus()
    witness = semantic_witness(values)
    geometry = geometry_accounting(stable)

    with (args.out / "integer-witness.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(witness["rows"][0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(witness["rows"])

    relation = {
        "schema": "d6-parity-duality/v1",
        "authority": "research-only",
        "resident_ids": [EVEN_ID, ODD_ID],
        "carrier": "exact-integer",
        "output_domain": "D1-PredicateBit",
        "relation_type": "DUALITY-COMPLEMENT",
        "semantic_law": {
            "odd": "odd(n)=1-even(n)",
            "even": "even(n)=1-odd(n)",
            "exclusive": "even(n)*odd(n)=0",
            "exhaustive": "even(n)+odd(n)=1",
            "period": "parity(n+2k)=parity(n)",
        },
        "witness": {
            "integer_cases": len(values),
            "period2_checks": witness["period2_checks"],
            "negative_controls": {
                "false_period1_first_counterexample": witness[
                    "false_period1_first_counterexample"
                ],
                "false_even_equals_odd_first_counterexample": witness[
                    "false_even_equals_odd_first_counterexample"
                ],
            },
            "noninteger_rejections": witness["noninteger_rejections"],
        },
        "geometry": geometry,
        "status": {
            "semantic_relation": "BOUNDED-CONFIRMED-EXACT-INTEGER",
            "geometry": "CANDIDATE-NOT-PROVED",
        },
        "non_conclusions": [
            "CURRENT one-bit adjacency is not semantic authority",
            "the exact 0/1 coordinate orientation is not forced by complementarity",
            "behavior outside the exact-integer carrier is not claimed",
            "no production coordinate is changed",
        ],
    }
    (args.out / "relation.json").write_text(
        json.dumps(relation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D6 parity duality — #3078",
        "",
        f"Stable residents checked: **{EVEN_ID}**, **{ODD_ID}**.",
        f"Exact integer cases: **{len(values)}**.",
        f"Period-2 checks: **{witness['period2_checks']}**.",
        "Predicate results: exact **D1 1/0**.",
        "",
        "Semantic result:",
        "- complementarity PASS;",
        "- mutual exclusivity PASS;",
        "- exhaustiveness on integers PASS;",
        "- period-2 invariance PASS;",
        "- false period-1 law REFUTED;",
        "- false even=odd law REFUTED;",
        "- non-integers fail OUT-OF-SCOPE in this witness.",
        "",
        "Geometry result:",
        f"- CURRENT projection Hamming distance = **{geometry['current_projection']['hamming_distance']}**;",
        "- one-bit neighborhood = **CANDIDATE**, not semantic theorem;",
        "- complementarity survives arbitrary coordinate re-encoding.",
        "",
        "Handoff: relation type DUALITY-COMPLEMENT; geometry remains NEIGHBORHOOD-CANDIDATE.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
