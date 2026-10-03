#!/usr/bin/env python3
"""#2516 — exact rational product-width ladder.

Stacked on #2514.

Candidate law:
  Q(2w) = normalize(signed Z(w), positive U(w))

First instances:
  D48Q = 24-bit signed numerator || 24-bit positive denominator
  D96Q = 48-bit signed numerator || 48-bit positive denominator

Research only; no Core owner ratification.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from fractions import Fraction
from math import gcd
from pathlib import Path
from typing import Optional

VALUE = "VALUE"
NEEDS_WIDENING = "NEEDS-WIDENING"
UNDEFINED_MATHEMATICALLY = "UNDEFINED-MATHEMATICALLY"


def signed_range(width: int) -> tuple[int, int]:
    return (-(1 << (width - 1)), (1 << (width - 1)) - 1)


def signed_bits(value: int, width: int) -> str:
    lo, hi = signed_range(width)
    if not lo <= value <= hi:
        raise OverflowError("signed factor overflow")
    raw = value if value >= 0 else (1 << width) + value
    return format(raw, f"0{width}b")


def signed_decode(bits: str) -> int:
    width = len(bits)
    raw = int(bits, 2)
    sign = 1 << (width - 1)
    return raw - (1 << width) if raw & sign else raw


def unsigned_bits(value: int, width: int) -> str:
    if not 0 <= value < (1 << width):
        raise OverflowError("unsigned factor overflow")
    return format(value, f"0{width}b")


@dataclass(frozen=True)
class RationalDomain:
    name: str
    factor_width: int

    @property
    def total_width(self) -> int:
        return 2 * self.factor_width

    @property
    def numerator_range(self) -> tuple[int, int]:
        return signed_range(self.factor_width)

    @property
    def denominator_hi(self) -> int:
        return (1 << self.factor_width) - 1

    def normalize(self, numerator: int, denominator: int) -> tuple[int, int]:
        if denominator == 0:
            raise ZeroDivisionError("zero denominator")
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        if numerator == 0:
            numerator, denominator = 0, 1
        else:
            g = gcd(abs(numerator), denominator)
            numerator //= g
            denominator //= g

        lo, hi = self.numerator_range
        if not lo <= numerator <= hi:
            raise OverflowError("normalized numerator outside domain")
        if not 1 <= denominator <= self.denominator_hi:
            raise OverflowError("normalized denominator outside domain")
        return numerator, denominator

    def contains(self, numerator: int, denominator: int) -> bool:
        try:
            self.normalize(numerator, denominator)
        except (OverflowError, ZeroDivisionError):
            return False
        return True

    def encode(self, numerator: int, denominator: int) -> str:
        n, d = self.normalize(numerator, denominator)
        return signed_bits(n, self.factor_width) + unsigned_bits(d, self.factor_width)

    def decode(self, bits: str) -> tuple[int, int]:
        if len(bits) != self.total_width or any(ch not in "01" for ch in bits):
            raise ValueError("exact-width binary rational required")
        nbits = bits[: self.factor_width]
        dbits = bits[self.factor_width :]
        n = signed_decode(nbits)
        d = int(dbits, 2)
        if d == 0:
            raise ValueError("zero denominator coordinate")
        normalized = self.normalize(n, d)
        if normalized != (n, d):
            raise ValueError("non-canonical rational coordinate")
        return normalized

    def value(self, numerator: int, denominator: int) -> Fraction:
        n, d = self.normalize(numerator, denominator)
        return Fraction(n, d)

    def add(self, a: tuple[int, int], b: tuple[int, int]) -> Optional[tuple[int, int]]:
        an, ad = a
        bn, bd = b
        try:
            return self.normalize(an * bd + bn * ad, ad * bd)
        except OverflowError:
            return None

    def mul(self, a: tuple[int, int], b: tuple[int, int]) -> Optional[tuple[int, int]]:
        an, ad = a
        bn, bd = b
        try:
            return self.normalize(an * bn, ad * bd)
        except OverflowError:
            return None

    def recip_classified(
        self, a: tuple[int, int]
    ) -> tuple[str, Optional[tuple[int, int]]]:
        an, ad = a
        if an == 0:
            return UNDEFINED_MATHEMATICALLY, None
        try:
            return VALUE, self.normalize(ad, an)
        except OverflowError:
            return NEEDS_WIDENING, None

    def recip(self, a: tuple[int, int]) -> Optional[tuple[int, int]]:
        status, value = self.recip_classified(a)
        return value if status == VALUE else None

    def div_classified(
        self, a: tuple[int, int], b: tuple[int, int]
    ) -> tuple[str, Optional[tuple[int, int]]]:
        an, ad = a
        bn, bd = b
        if bn == 0:
            return UNDEFINED_MATHEMATICALLY, None

        # Decide residency from the final exact quotient after cancellation.
        # Do not require the intermediate reciprocal of b to fit this tier.
        try:
            return VALUE, self.normalize(an * bd, ad * bn)
        except OverflowError:
            return NEEDS_WIDENING, None

    def div(self, a: tuple[int, int], b: tuple[int, int]) -> Optional[tuple[int, int]]:
        status, value = self.div_classified(a, b)
        return value if status == VALUE else None


D48Q = RationalDomain("Core-Number-D48Q-candidate", 24)
D96Q = RationalDomain("Core-Number-D96Q-candidate", 48)


def embed_integer_d24(value: int) -> tuple[int, int]:
    lo, hi = signed_range(24)
    if not lo <= value <= hi:
        raise OverflowError("not a D24Z value")
    return D48Q.normalize(value, 1)


def widen_q(value: tuple[int, int], src: RationalDomain, dst: RationalDomain) -> tuple[int, int]:
    if src.factor_width >= dst.factor_width:
        raise ValueError("widen requires larger factor width")
    n, d = src.normalize(*value)
    return dst.normalize(n, d)


def narrow_q(value: tuple[int, int], src: RationalDomain, dst: RationalDomain) -> Optional[tuple[int, int]]:
    if src.factor_width <= dst.factor_width:
        raise ValueError("narrow requires smaller target")
    n, d = src.normalize(*value)
    try:
        return dst.normalize(n, d)
    except OverflowError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # Canonical normalization controls.
    half = D48Q.normalize(2, 4)
    assert half == (1, 2)
    assert D48Q.normalize(-2, -4) == (1, 2)
    assert D48Q.normalize(0, 999) == (0, 1)
    assert D48Q.encode(2, 4) == D48Q.encode(1, 2)
    assert D48Q.value(*half) == Fraction(1, 2)

    # Non-canonical raw coordinate is rejected on decode.
    raw_noncanonical = signed_bits(2, 24) + unsigned_bits(4, 24)
    try:
        D48Q.decode(raw_noncanonical)
    except ValueError as exc:
        noncanonical_rejected = "non-canonical" in str(exc)
    else:
        noncanonical_rejected = False
    assert noncanonical_rejected

    # Exact arithmetic witnesses.
    third = D48Q.normalize(1, 3)
    sixth = D48Q.normalize(1, 6)
    assert D48Q.add(third, sixth) == (1, 2)
    assert D48Q.mul(D48Q.normalize(2, 3), D48Q.normalize(3, 5)) == (2, 5)
    assert D48Q.recip(third) == (3, 1)
    assert D48Q.recip((0, 1)) is None
    assert D48Q.recip_classified((0, 1)) == (UNDEFINED_MATHEMATICALLY, None)
    assert D48Q.div(D48Q.normalize(2, 3), D48Q.normalize(4, 5)) == (5, 6)
    assert D48Q.div((1, 2), (0, 1)) is None
    assert D48Q.div_classified((1, 2), (0, 1)) == (
        UNDEFINED_MATHEMATICALLY,
        None,
    )

    # Final-fit DIV falsifier from #2516/#2519 review.
    # The reciprocal of 1/(2^24-1) does not fit signed-24, but the exact
    # quotient of the value by itself is 1 and must stay in D48Q.
    d48_den_max = D48Q.denominator_hi
    cancel = D48Q.normalize(1, d48_den_max)
    assert D48Q.recip_classified(cancel) == (NEEDS_WIDENING, None)
    assert D48Q.div_classified(cancel, cancel) == (VALUE, (1, 1))
    assert D48Q.div(cancel, cancel) == (1, 1)

    # Integer embedding: every D24Z point maps to n/1 in D48Q.
    d24_lo, d24_hi = signed_range(24)
    for value in [d24_lo, -1, 0, 1, d24_hi]:
        embedded = embed_integer_d24(value)
        assert embedded == (value, 1)
        assert D48Q.value(*embedded) == Fraction(value, 1)

    # D48Q -> D96Q is total by factor-width inclusion.
    samples = [
        D48Q.normalize(1, 3),
        D48Q.normalize(-7, 11),
        D48Q.normalize(d24_hi, 1),
        D48Q.normalize(d24_lo, D48Q.denominator_hi),
    ]
    for q in samples:
        wide = widen_q(q, D48Q, D96Q)
        assert Fraction(*q) == Fraction(*wide)
        assert narrow_q(wide, D96Q, D48Q) == q

    # A real widening-required arithmetic case:
    # max * max is exact but its normalized numerator exceeds signed-24.
    max_q = D48Q.normalize(d24_hi, 1)
    assert D48Q.mul(max_q, max_q) is None
    wide_max = widen_q(max_q, D48Q, D96Q)
    wide_product = D96Q.mul(wide_max, wide_max)
    assert wide_product is not None
    assert Fraction(*wide_product) == Fraction(d24_hi * d24_hi, 1)
    assert narrow_q(wide_product, D96Q, D48Q) is None

    # Denominator-growth widening case.
    a = D48Q.normalize(1, d24_hi)
    b = D48Q.normalize(1, d24_hi - 1)
    sum48 = D48Q.add(a, b)
    assert sum48 is None
    sum96 = D96Q.add(widen_q(a, D48Q, D96Q), widen_q(b, D48Q, D96Q))
    assert sum96 is not None
    assert Fraction(*sum96) == Fraction(1, d24_hi) + Fraction(1, d24_hi - 1)

    # Same-width domain separation control.
    # A 48-bit D48Z coordinate and a D48Q coordinate are not interchangeable.
    d48z_bits_for_one = format(1, "048b")
    d48q_bits_for_one = D48Q.encode(1, 1)
    assert len(d48z_bits_for_one) == len(d48q_bits_for_one) == 48
    assert d48z_bits_for_one != d48q_bits_for_one

    # Field-swap attack generally changes meaning.
    encoded_third = D48Q.encode(1, 3)
    swapped = encoded_third[24:] + encoded_third[:24]
    try:
        swapped_pair = D48Q.decode(swapped)
        swapped_value = D48Q.value(*swapped_pair)
    except (ValueError, OverflowError):
        swapped_value = None
    assert swapped_value != Fraction(1, 3)

    # Signed denominator / no-normalization would create duplicates; canonical law rejects them.
    assert D48Q.normalize(-1, -2) == (1, 2)
    assert D48Q.normalize(10, 20) == (1, 2)

    model_rows = [
        {
            "domain": D48Q.name,
            "factor_width": 24,
            "total_width": 48,
            "carrier": "reduced signed numerator / positive denominator",
            "status": "VIABLE-SEMANTIC-CANDIDATE",
            "widen_to": D96Q.name,
            "general_exact_Q_subset": True,
        },
        {
            "domain": D96Q.name,
            "factor_width": 48,
            "total_width": 96,
            "carrier": "reduced signed numerator / positive denominator",
            "status": "VIABLE-WIDER-CANDIDATE",
            "widen_to": "wider Q tier",
            "general_exact_Q_subset": True,
        },
    ]
    with (args.out / "q-product-ladder.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(model_rows[0].keys()), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(model_rows)

    artifact = {
        "schema": "core-number-q-product-ladder/v1",
        "authority": "research-only",
        "candidate_law": "Q(2w)=normalize(signed-Z(w), positive-U(w))",
        "domains": {
            "D48Q": {
                "factor_width": 24,
                "total_width": 48,
                "normalization": "denominator>0; gcd=1; zero=0/1",
                "coordinate": "signed numerator bits || unsigned positive denominator bits",
            },
            "D96Q": {
                "factor_width": 48,
                "total_width": 96,
                "normalization": "same law at wider factors",
                "coordinate": "signed numerator bits || unsigned positive denominator bits",
            },
        },
        "relations": {
            "D24Z_to_D48Q": {
                "mapping": "n -> n/1",
                "total": True,
                "injective": True,
                "exact": True,
            },
            "D48Q_to_D96Q": {
                "total": True,
                "injective": True,
                "value_preserving": True,
            },
            "D96Q_to_D48Q": {
                "partial": True,
                "condition": "normalized numerator/denominator fit 24-bit factors",
            },
        },
        "witnesses": {
            "one_third_plus_one_sixth": "1/2",
            "two_fourths_normalizes": "1/2",
            "negative_sign_normalizes": "1/2",
            "zero_normalizes": "0/1",
            "reciprocal_zero": UNDEFINED_MATHEMATICALLY,
            "reciprocal_out_of_tier": NEEDS_WIDENING,
            "division_by_zero": UNDEFINED_MATHEMATICALLY,
            "division_final_fit_cancellation": "VALUE 1/1",
            "d24_integer_embedding_max": f"{d24_hi}/1",
            "numerator_widening_required": f"{d24_hi}^2 requires D96Q",
            "denominator_widening_required": "1/max + 1/(max-1) requires D96Q",
        },
        "attacks": {
            "noncanonical_decode_rejected": noncanonical_rejected,
            "field_swap_preserves_semantics": False,
            "signed_denominator_duplicate_allowed": False,
            "skip_gcd_duplicate_allowed": False,
            "D48Z_equals_D48Q_by_width": False,
        },
        "non_conclusions": [
            "D48Q/D96Q are candidates, not owner-ratified Core domains",
            "24/24 factorization is justified here by composition over the D24 integer factor candidate; uniqueness among all possible D48 rational coordinates is not proved",
            "same total width does not identify D48Z with D48Q",
            "Limb24 may implement factors but is not semantic authority",
            "Core-Math exact-Q convergence still requires separate cross-proof",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = [
        "# Core Number rational product ladder — #2516",
        "",
        "Candidate law:",
        "",
        "    Q(2w) = normalize(signed Z(w), positive U(w))",
        "",
        "| candidate | result |",
        "|---|---|",
        "| D48Q over 24+24 factors | viable exact rational subset candidate |",
        "| D96Q over 48+48 factors | viable wider candidate under same law |",
        "| D24Z -> D48Q | total exact embedding n -> n/1 |",
        "| D48Q -> D96Q | total injective value-preserving widening |",
        "| D96Q -> D48Q | partial narrowing by normalized factor fit |",
        "",
        "Exact witnesses PASS:",
        "- 1/3 + 1/6 = 1/2;",
        "- 2/4 and -2/-4 canonicalize to 1/2;",
        "- zero canonicalizes to 0/1;",
        "- reciprocal/division by zero are UNDEFINED-MATHEMATICALLY;",
        "- out-of-tier reciprocal is NEEDS-WIDENING, not mathematically undefined;",
        "- DIV final-fit cancellation keeps (1/d)/(1/d)=1 inside D48Q even when recip(1/d) needs widening;",
        "- D24Z max embeds as max/1;",
        "- max^2 overflows D48Q factor width but is exact in D96Q;",
        "- denominator-growth example also requires D96Q.",
        "",
        "Falsifiers PASS:",
        "- non-canonical raw coordinates are rejected;",
        "- numerator/denominator field swap does not preserve the law;",
        "- signed denominator duplicates are normalized away;",
        "- gcd duplicates are normalized away;",
        "- same total width does not identify D48Z with D48Q.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
