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

EVEN_NAME = "EVENP"
ODD_NAME = "ODDP"


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


def verify_current_residents(path: Path | None = None) -> dict[str, dict[str, Any]]:
    """Read current D6 identity only from the owner-ratified #3393 map."""
    if path is None:
        path = Path(__file__).resolve().parents[2] / "knowledge" / "d6-ratified.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "d6-ratified/v1":
        raise AssertionError("current D6 authority schema mismatch")
    if data.get("status") != "owner-ratified" or data.get("authority") != "#3393":
        raise AssertionError("current D6 authority must be owner-ratified #3393")
    if data.get("width") != 6 or data.get("capacity") != 64:
        raise AssertionError("D6 exact width/capacity mismatch")
    if data.get("occupancy") != 64 or data.get("distinct_residents") != 64:
        raise AssertionError("current D6 authority must remain dense 64/64")

    residents = data.get("residents")
    expected_coordinates = {format(i, "06b") for i in range(64)}
    if not isinstance(residents, dict) or set(residents) != expected_coordinates:
        raise AssertionError(
            "ratified D6 map must contain all exact six-bit coordinates"
        )
    if len(set(residents.values())) != 64:
        raise AssertionError("ratified D6 residents must be unique")

    rows = data.get("rows")
    if not isinstance(rows, list):
        raise AssertionError("ratified D6 map lacks its evidence rows")
    by_name: dict[str, dict[str, Any]] = {}
    for name in (EVEN_NAME, ODD_NAME):
        matches = [row for row in rows if row.get("resident") == name]
        if len(matches) != 1:
            raise AssertionError(
                f"current #3393 D6 map must contain exactly one {name} row"
            )
        row = matches[0]
        coordinate = row.get("coordinate")
        if (
            not isinstance(coordinate, str)
            or len(coordinate) != 6
            or set(coordinate) - {"0", "1"}
            or residents.get(coordinate) != name
        ):
            raise AssertionError(
                f"{name} row disagrees with the authoritative resident map"
            )
        if row.get("status") != "OWNER-RATIFIED":
            raise AssertionError(f"{name} is not owner-ratified")
        by_name[name] = {
            "name": name,
            "domain": "D6",
            "current_bits": coordinate,
            "authority": "#3393",
            "status": row["status"],
            "law_status": row.get("law_status", "UNSPECIFIED"),
            "evidence": row.get("evidence", []),
        }
    return by_name




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


def geometry_accounting(current: dict[str, dict[str, Any]]) -> dict[str, Any]:
    even_bits = current[EVEN_NAME]["current_bits"]
    odd_bits = current[ODD_NAME]["current_bits"]
    if len(even_bits) != 6 or len(odd_bits) != 6:
        raise AssertionError("current D6 coordinates must preserve exact width")
    hamming = sum(a != b for a, b in zip(even_bits, odd_bits, strict=True))
    shared_prefix = even_bits[:-1] if even_bits[:-1] == odd_bits[:-1] else None
    current_axis_payload_bits = 6 if shared_prefix is not None else None

    # Coordinate geometry is a property of the ratified presentation, not a
    # derivation of the parity law. #3393 explicitly marks this axis as candidate.
    law_statuses = {current[EVEN_NAME]["law_status"], current[ODD_NAME]["law_status"]}
    geometry_status = (
        "NEIGHBORHOOD-CANDIDATE"
        if law_statuses == {"NEIGHBORHOOD-CANDIDATE"}
        else "BLOCKED-OWNER-LAW-REVIEW"
    )
    return {
        "current_ratified_projection": {
            EVEN_NAME: even_bits,
            ODD_NAME: odd_bits,
            "authority": "#3393",
            "hamming_distance": hamming,
            "law_statuses": {
                EVEN_NAME: current[EVEN_NAME]["law_status"],
                ODD_NAME: current[ODD_NAME]["law_status"],
            },
        },
        "semantic_geometry_status": geometry_status,
        "one_bit_axis_is_semantically_proved": False,
        "coordinate_accounting": {
            "arbitrary_pair_direct_coordinate_bits": 12,
            "current_shared_prefix_plus_orientation_bits": current_axis_payload_bits,
            "note": (
                "coordinate/certificate accounting only; "
                "does not prove a semantic law"
            ),
        },
        "reencoding_guard": (
            "the exact-integer complement law survives coordinate re-encoding; "
            "current adjacency is only an owner-ratified presentation candidate"
        ),
    }




def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    current = verify_current_residents()
    values = corpus()
    witness = semantic_witness(values)
    geometry = geometry_accounting(current)

    witness_path = args.out / "integer-witness.tsv"
    with witness_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(witness["rows"][0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(witness["rows"])

    relation = {
        "schema": "d6-parity-duality/v2",
        "authority": "research-only; current resident projection from #3393",
        "resident_projection": {
            EVEN_NAME: current[EVEN_NAME],
            ODD_NAME: current[ODD_NAME],
        },
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
            "geometry": geometry["semantic_geometry_status"],
        },
        "non_conclusions": [
            "exact-integer parity proof does not derive D6 coordinate placement",
            "the one-bit axis is a ratified candidate, not a proved semantic law",
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
        f"Current owner-ratified residents checked: **{EVEN_NAME} = "
        f"{current[EVEN_NAME]['current_bits']}**, **{ODD_NAME} = "
        f"{current[ODD_NAME]['current_bits']}** (#3393).",
        f"Exact integer cases: **{len(values)}**.",
        f"Period-2 checks: **{witness['period2_checks']}**.",
        "Predicate results: exact **D1 1/0**.",
        "",
        "Semantic result:",
        "- complementarity PASS;",
        "- mutual exclusivity PASS;",
        "- exhaustiveness on exact integers PASS;",
        "- period-2 invariance PASS;",
        "- false period-1 law REFUTED;",
        "- false even=odd law REFUTED;",
        "- non-integers fail OUT-OF-SCOPE in this witness.",
        "",
        "Current coordinate observation:",
        f"- ratified coordinates are {current[EVEN_NAME]['current_bits']} "
        f"and {current[ODD_NAME]['current_bits']};",
        f"- observed Hamming distance = "
        f"**{geometry['current_ratified_projection']['hamming_distance']}**;",
        f"- owner law status = **{geometry['semantic_geometry_status']}**, "
        "not semantic proof;",
        "- the parity theorem does not depend on these coordinates.",
        "",
        "Handoff: exact-integer duality is confirmed within this bounded witness; "
        "coordinate neighborhood remains a candidate only.",
        "",
    ]
    rendered = "\n".join(report)
    (args.out / "report.md").write_text(rendered, encoding="utf-8")
    print(rendered)
    return 0




if __name__ == "__main__":
    raise SystemExit(main())
