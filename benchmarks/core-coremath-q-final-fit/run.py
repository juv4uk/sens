#!/usr/bin/env python3
"""#2610 — replay complementary Core <-> Core-Math Q bridge after DIV final-fit repair.

Current Core side:
- imports current-main #2516/#2582 D48Q/D96Q candidate witness.

Independent side:
- fractions.Fraction only;
- no Core codec/tier logic used to compute mathematical quotient.

This witness exists specifically because #2529 merged before the later DIV
final-fit falsifier/repair.
"""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "benchmarks" / "core-number-q-product-ladder" / "run.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_q_2610", CORE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def exact_div(left: tuple[int, int], right: tuple[int, int]) -> Optional[Fraction]:
    a = Fraction(*left)
    b = Fraction(*right)
    if b == 0:
        return None
    return a / b


def encode_exact(domain, value: Fraction) -> Optional[str]:
    try:
        return domain.encode(value.numerator, value.denominator)
    except OverflowError:
        return None


def bridge_value(domain, pair: tuple[int, int]) -> Fraction:
    bits = domain.encode(*pair)
    n, d = domain.decode(bits)
    return Fraction(n, d)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    core = load_core()
    D48Q = core.D48Q
    D96Q = core.D96Q

    rows: list[dict[str, object]] = []

    # 1. Final-fit cancellation: intermediate reciprocal needs widening,
    # but final exact quotient normalizes to 1/1 and fits D48Q.
    d = D48Q.denominator_hi
    cancel_left = D48Q.normalize(1, d)
    cancel_right = D48Q.normalize(1, d)

    recip_status, recip_value = D48Q.recip_classified(cancel_right)
    assert recip_status == core.NEEDS_WIDENING
    assert recip_value is None

    div_status, div_value = D48Q.div_classified(cancel_left, cancel_right)
    assert div_status == core.VALUE
    assert div_value == (1, 1)

    exact = exact_div(cancel_left, cancel_right)
    assert exact == Fraction(1, 1)
    exact_bits48 = encode_exact(D48Q, exact)
    assert exact_bits48 == D48Q.encode(1, 1)
    assert bridge_value(D48Q, div_value) == exact

    rows.append({
        "case": "final-fit-cancellation",
        "left": str(Fraction(*cancel_left)),
        "right": str(Fraction(*cancel_right)),
        "intermediate_recip_status": recip_status,
        "core_div_status": div_status,
        "independent_exact_result": str(exact),
        "D48Q_encodable": exact_bits48 is not None,
        "D96Q_encodable": encode_exact(D96Q, exact) is not None,
        "bridge_commutes": True,
    })

    # 2. Truly out-of-tier final result: mathematically defined and exact,
    # does not fit D48Q but does fit D96Q.
    max24 = D48Q.numerator_range[1]
    widen_left = D48Q.normalize(max24, 1)
    widen_right = D48Q.normalize(1, max24)

    widen_status48, widen_value48 = D48Q.div_classified(widen_left, widen_right)
    assert widen_status48 == core.NEEDS_WIDENING
    assert widen_value48 is None

    widen_exact = exact_div(widen_left, widen_right)
    assert widen_exact == Fraction(max24 * max24, 1)
    assert encode_exact(D48Q, widen_exact) is None
    bits96 = encode_exact(D96Q, widen_exact)
    assert bits96 is not None

    wide_left = core.widen_q(widen_left, D48Q, D96Q)
    wide_right = core.widen_q(widen_right, D48Q, D96Q)
    widen_status96, widen_value96 = D96Q.div_classified(wide_left, wide_right)
    assert widen_status96 == core.VALUE
    assert widen_value96 is not None
    assert Fraction(*widen_value96) == widen_exact
    assert bridge_value(D96Q, widen_value96) == widen_exact

    rows.append({
        "case": "true-needs-widening",
        "left": str(Fraction(*widen_left)),
        "right": str(Fraction(*widen_right)),
        "intermediate_recip_status": D48Q.recip_classified(widen_right)[0],
        "core_div_status": widen_status48,
        "independent_exact_result": str(widen_exact),
        "D48Q_encodable": False,
        "D96Q_encodable": True,
        "bridge_commutes": True,
    })

    # 3. Mathematical undefinedness: denominator operand is zero.
    zero_left = D48Q.normalize(1, 2)
    zero_right = D48Q.normalize(0, 1)

    undefined_status, undefined_value = D48Q.div_classified(zero_left, zero_right)
    assert undefined_status == core.UNDEFINED_MATHEMATICALLY
    assert undefined_value is None
    undefined_exact = exact_div(zero_left, zero_right)
    assert undefined_exact is None

    rows.append({
        "case": "division-by-zero",
        "left": str(Fraction(*zero_left)),
        "right": str(Fraction(*zero_right)),
        "intermediate_recip_status": D48Q.recip_classified(zero_right)[0],
        "core_div_status": undefined_status,
        "independent_exact_result": "UNDEFINED",
        "D48Q_encodable": False,
        "D96Q_encodable": False,
        "bridge_commutes": True,
    })

    # Hard separation of the three semantic/result classes.
    assert {
        row["core_div_status"] for row in rows
    } == {
        core.VALUE,
        core.NEEDS_WIDENING,
        core.UNDEFINED_MATHEMATICALLY,
    }

    with (args.out / "q-bridge-final-fit.tsv").open(
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

    artifact = {
        "schema": "core-coremath-q-bridge-final-fit/v1",
        "authority": "research-only",
        "classification": "COMPLEMENTARY-BOUNDED",
        "core_source": "current-main benchmarks/core-number-q-product-ladder/run.py",
        "independent_oracle": "python fractions.Fraction",
        "cases": rows,
        "three_way_status_separation": True,
        "old_bridge_regression_closed": True,
        "non_conclusions": [
            "Core D48Q/D96Q remain candidate domains unless separately ratified",
            "Core-Math does not adopt Core binary coordinates as identity",
            "COMPLEMENTARY does not mean CONVERGENT",
            "intermediate implementation fit is not semantic authority",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core <-> Core-Math Q bridge final-fit replay — #2610",
        "",
        "| case | Core D48Q classification | exact result | D48Q | D96Q |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        report.append(
            f"| {row['case']} | {row['core_div_status']} | "
            f"{row['independent_exact_result']} | "
            f"{'VALUE' if row['D48Q_encodable'] else 'NO'} | "
            f"{'VALUE' if row['D96Q_encodable'] else 'NO'} |"
        )

    report += [
        "",
        "Critical regression:",
        f"- recip(1/{d}) in D48Q = NEEDS-WIDENING;",
        f"- (1/{d}) / (1/{d}) = 1/1 and remains VALUE in D48Q;",
        "- final normalized quotient decides tier residency.",
        "",
        "The independent exact-Q oracle agrees in all three result classes.",
        "Bridge classification remains COMPLEMENTARY, not CONVERGENT.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
