#!/usr/bin/env python3
"""#2524 — Core <-> Core-Math exact-Q complementary bridge.

Core side: bounded binary D48Q/D96Q coordinates from #2519.
Core-Math side: independent exact rational semantics using Fraction only.

The bridge compares mathematical value and partiality.  It does not identify
the two domains or copy Core binary identity into Core-Math.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import sys
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
CORE_PATH = ROOT / "benchmarks" / "core-number-q-product-ladder" / "run.py"


def load_core():
    spec = importlib.util.spec_from_file_location("core_q_2516_bridge", CORE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class CoreMathQ:
    """Independent unbounded exact-Q semantic object."""

    value: Fraction

    @staticmethod
    def from_pair(n: int, d: int) -> "CoreMathQ":
        if d == 0:
            raise ZeroDivisionError
        return CoreMathQ(Fraction(n, d))

    def add(self, other: "CoreMathQ") -> "CoreMathQ":
        return CoreMathQ(self.value + other.value)

    def mul(self, other: "CoreMathQ") -> "CoreMathQ":
        return CoreMathQ(self.value * other.value)

    def recip(self) -> Optional["CoreMathQ"]:
        if self.value == 0:
            return None
        return CoreMathQ(1 / self.value)

    def div(self, other: "CoreMathQ") -> Optional["CoreMathQ"]:
        inv = other.recip()
        return None if inv is None else self.mul(inv)


def core_to_cm(domain, bits: str) -> CoreMathQ:
    n, d = domain.decode(bits)
    return CoreMathQ.from_pair(n, d)


def cm_to_core(domain, value: CoreMathQ) -> Optional[str]:
    n = value.value.numerator
    d = value.value.denominator
    try:
        return domain.encode(n, d)
    except OverflowError:
        return None


def bridge_pair(domain, pair: tuple[int, int]) -> CoreMathQ:
    bits = domain.encode(*pair)
    return core_to_cm(domain, bits)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    core = load_core()
    D48Q = core.D48Q
    D96Q = core.D96Q

    # Core -> Core-Math is structurally total for every valid coordinate:
    # decode validates canonical Core membership; Fraction accepts every
    # nonzero-denominator normalized pair produced by the decoder.
    sample_pairs = [
        D48Q.normalize(0, 1),
        D48Q.normalize(1, 3),
        D48Q.normalize(-7, 11),
        D48Q.normalize(2, 5),
        D48Q.normalize((1 << 23) - 1, 1),
        D48Q.normalize(-(1 << 23), (1 << 24) - 1),
    ]
    for pair in sample_pairs:
        bits = D48Q.encode(*pair)
        cm = core_to_cm(D48Q, bits)
        assert cm.value == Fraction(*pair)
        assert cm_to_core(D48Q, cm) == bits

    # Exact named controls.
    third = bridge_pair(D48Q, D48Q.normalize(1, 3))
    sixth = bridge_pair(D48Q, D48Q.normalize(1, 6))
    assert third.add(sixth).value == Fraction(1, 2)

    a = bridge_pair(D48Q, D48Q.normalize(-7, 11))
    b = bridge_pair(D48Q, D48Q.normalize(22, 21))
    assert a.mul(b).value == Fraction(-2, 3)

    zero = bridge_pair(D48Q, D48Q.normalize(0, 1))
    assert zero.recip() is None
    assert D48Q.recip((0, 1)) is None

    # Commuting arithmetic square on a bounded corpus.
    corpus = [
        D48Q.normalize(0, 1),
        D48Q.normalize(1, 3),
        D48Q.normalize(-7, 11),
        D48Q.normalize(2, 5),
        D48Q.normalize(5, 6),
    ]
    commute_rows = []
    for op_name in ("add", "mul"):
        for left in corpus:
            for right in corpus:
                core_result = getattr(D48Q, op_name)(left, right)
                cm_left = bridge_pair(D48Q, left)
                cm_right = bridge_pair(D48Q, right)
                cm_result = getattr(cm_left, op_name)(cm_right)
                if core_result is not None:
                    bridged = bridge_pair(D48Q, core_result)
                    assert bridged.value == cm_result.value
                    status = "COMMUTES-D48Q"
                else:
                    bits96 = cm_to_core(D96Q, cm_result)
                    status = "NEEDS-WIDER-OR-BEYOND"
                    if bits96 is not None:
                        assert core_to_cm(D96Q, bits96).value == cm_result.value
                        status = "COMMUTES-VIA-D96Q"
                commute_rows.append({
                    "operation": op_name,
                    "left": str(Fraction(*left)),
                    "right": str(Fraction(*right)),
                    "status": status,
                })

    # Unary reciprocal parity and binary division parity.
    for value in corpus:
        cm = bridge_pair(D48Q, value)
        cr = D48Q.recip(value)
        mr = cm.recip()
        if cr is None:
            assert mr is None
        else:
            assert mr is not None
            assert bridge_pair(D48Q, cr).value == mr.value

    for left in corpus:
        for right in corpus:
            cr = D48Q.div(left, right)
            mr = bridge_pair(D48Q, left).div(bridge_pair(D48Q, right))
            if cr is None:
                if right[0] == 0:
                    assert mr is None
                else:
                    assert mr is not None
                    assert cm_to_core(D48Q, mr) is None
            else:
                assert mr is not None
                assert bridge_pair(D48Q, cr).value == mr.value

    # Required widening case: D48Q cannot hold max^2 but D96Q can.
    d24_hi = (1 << 23) - 1
    max48 = D48Q.normalize(d24_hi, 1)
    core_product48 = D48Q.mul(max48, max48)
    assert core_product48 is None
    cm_max = bridge_pair(D48Q, max48)
    cm_product = cm_max.mul(cm_max)
    bits96 = cm_to_core(D96Q, cm_product)
    assert bits96 is not None
    assert core_to_cm(D96Q, bits96).value == cm_product.value

    # Independent denominator-growth widening case.
    q1 = D48Q.normalize(1, d24_hi)
    q2 = D48Q.normalize(1, d24_hi - 1)
    assert D48Q.add(q1, q2) is None
    cm_sum = bridge_pair(D48Q, q1).add(bridge_pair(D48Q, q2))
    sum96 = cm_to_core(D96Q, cm_sum)
    assert sum96 is not None
    assert core_to_cm(D96Q, sum96).value == cm_sum.value

    # Malformed/noncanonical Core coordinate fails before bridge.
    raw_noncanonical = core.signed_bits(2, 24) + core.unsigned_bits(4, 24)
    try:
        core_to_cm(D48Q, raw_noncanonical)
    except ValueError:
        malformed_rejected = True
    else:
        malformed_rejected = False
    assert malformed_rejected

    # Core-Math stays exact even when no current Core tier can encode the value.
    outside = CoreMathQ(Fraction(1 << 47, 1))
    assert cm_to_core(D96Q, outside) is None
    assert outside.value == Fraction(1 << 47, 1)

    # The bridge never carries a claim of shared binary identity.
    one_core_bits = D48Q.encode(1, 1)
    one_cm = core_to_cm(D48Q, one_core_bits)
    assert one_cm.value == 1
    assert not hasattr(one_cm, "bits")

    with (args.out / "commuting-square.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(commute_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(commute_rows)

    counts = {
        status: sum(row["status"] == status for row in commute_rows)
        for status in sorted({row["status"] for row in commute_rows})
    }

    artifact = {
        "schema": "core-coremath-q-complementary-bridge/v1",
        "authority": "research-only",
        "classification": "COMPLEMENTARY-BOUNDED",
        "core_domains": ["Core-Number-D48Q-candidate", "Core-Number-D96Q-candidate"],
        "core_math_domain": "independent-unbounded-exact-Q-semantic-oracle",
        "bridge": {
            "core_to_coremath": "total for every valid Core Q coordinate by decode -> exact Fraction",
            "coremath_to_D48Q": "partial by normalized 24-bit factor fit",
            "coremath_to_D96Q": "partial by normalized 48-bit factor fit",
            "shared_binary_identity_claim": False,
        },
        "commuting_square_counts": counts,
        "widening_controls": {
            "max_squared_requires_D96Q": True,
            "denominator_growth_requires_D96Q": True,
            "exact_value_preserved": True,
        },
        "negative_controls": {
            "reciprocal_zero_undefined_both_sides": True,
            "noncanonical_core_bits_rejected": malformed_rejected,
            "outside_D96Q_coremath_value_remains_exact": str(outside.value),
            "outside_D96Q_core_encoding": "NOT-ENCODABLE",
        },
        "non_conclusions": [
            "COMPLEMENTARY does not mean CONVERGENT",
            "Core D48Q/D96Q bits are not Core-Math canonical identities",
            "Core-Math does not inherit Core width tiers",
            "Core D48Q/D96Q remain unratified candidates",
            "the independent Fraction oracle is a semantic witness, not a Core-Math production runtime",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core <-> Core-Math exact-Q bridge — #2524",
        "",
        "Bounded classification: **COMPLEMENTARY**",
        "",
        "Bridge properties:",
        "- valid Core D48Q/D96Q coordinate -> Core-Math exact Q: total/exact;",
        "- Core-Math exact Q -> Core tier: partial by normalized factor fit;",
        "- no shared binary identity is inferred.",
        "",
        "Commuting controls:",
        "- 1/3 + 1/6 = 1/2;",
        "- -7/11 * 22/21 = -2/3;",
        "- reciprocal/division zero partiality agrees;",
        "- bounded add/mul corpus commutes in D48Q or through D96Q when widening is sufficient;",
        "- max^2 and denominator-growth witnesses commute through D96Q.",
        "",
        "Fail-closed controls:",
        "- noncanonical Core coordinate rejected before bridge;",
        "- Core-Math value 2^47 remains exact but is NOT-ENCODABLE even in current D96Q.",
        "",
        "This proves value/operation complementarity only. It does not prove domain convergence.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
