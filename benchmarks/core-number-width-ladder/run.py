#!/usr/bin/env python3
"""#2512 — Core Number width-ladder model tournament.

Research-only.  Tests whether D24/D48 can earn semantic Number-domain status
independently of FPGA limb implementation.

Models:
A. exact bounded signed integers with partial overflow;
B. lawful widening/narrowing ladder between A domains;
C. exact dyadic mantissa/exponent candidate with canonical normalization;
D. mechanism-only Limb24 negative control.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class IntDomain:
    name: str
    width: int

    @property
    def lo(self) -> int:
        return -(1 << (self.width - 1))

    @property
    def hi(self) -> int:
        return (1 << (self.width - 1)) - 1

    def contains(self, value: int) -> bool:
        return self.lo <= value <= self.hi

    def encode(self, value: int) -> str:
        if not self.contains(value):
            raise OverflowError(f"{value} outside {self.name}")
        raw = value if value >= 0 else (1 << self.width) + value
        return format(raw, f"0{self.width}b")

    def decode(self, bits: str) -> int:
        if len(bits) != self.width or any(c not in "01" for c in bits):
            raise ValueError("exact-width binary object required")
        raw = int(bits, 2)
        sign = 1 << (self.width - 1)
        return raw - (1 << self.width) if raw & sign else raw

    def add(self, a: int, b: int) -> Optional[int]:
        out = a + b
        return out if self.contains(out) else None

    def mul(self, a: int, b: int) -> Optional[int]:
        out = a * b
        return out if self.contains(out) else None


D24 = IntDomain("Core-Number-D24Z-candidate", 24)
D48 = IntDomain("Core-Number-D48Z-candidate", 48)


def widen(value: int, src: IntDomain, dst: IntDomain) -> int:
    if src.width >= dst.width:
        raise ValueError("widen requires strictly wider destination")
    if not src.contains(value):
        raise OverflowError("source membership failure")
    assert dst.contains(value)
    return value


def narrow(value: int, src: IntDomain, dst: IntDomain) -> Optional[int]:
    if src.width <= dst.width:
        raise ValueError("narrow requires strictly narrower destination")
    if not src.contains(value):
        raise OverflowError("source membership failure")
    return value if dst.contains(value) else None


@dataclass(frozen=True)
class DyadicDomain:
    name: str
    width: int
    mantissa_bits: int
    exponent_bits: int

    def __post_init__(self):
        if self.mantissa_bits + self.exponent_bits != self.width:
            raise ValueError("dyadic field widths must sum to total width")

    @staticmethod
    def signed_range(bits: int) -> tuple[int, int]:
        return (-(1 << (bits - 1)), (1 << (bits - 1)) - 1)

    def normalize(self, mantissa: int, exponent: int) -> tuple[int, int]:
        if mantissa == 0:
            return (0, 0)
        while mantissa % 2 == 0:
            mantissa //= 2
            exponent += 1
        mlo, mhi = self.signed_range(self.mantissa_bits)
        elo, ehi = self.signed_range(self.exponent_bits)
        if not (mlo <= mantissa <= mhi and elo <= exponent <= ehi):
            raise OverflowError("canonical dyadic outside domain")
        return mantissa, exponent

    def value(self, mantissa: int, exponent: int) -> Fraction:
        m, e = self.normalize(mantissa, exponent)
        return Fraction(m * (1 << e), 1) if e >= 0 else Fraction(m, 1 << (-e))

    def encode(self, mantissa: int, exponent: int) -> str:
        m, e = self.normalize(mantissa, exponent)
        return signed_bits(m, self.mantissa_bits) + signed_bits(e, self.exponent_bits)


DY24 = DyadicDomain("Core-Number-D24Dyadic-candidate", 24, 16, 8)
DY48 = DyadicDomain("Core-Number-D48Dyadic-candidate", 48, 32, 16)


def signed_bits(value: int, width: int) -> str:
    lo = -(1 << (width - 1))
    hi = (1 << (width - 1)) - 1
    if not lo <= value <= hi:
        raise OverflowError
    raw = value if value >= 0 else (1 << width) + value
    return format(raw, f"0{width}b")


def limb24_encode_unsigned(value: int) -> list[int]:
    """Mechanism-only base-2^24 magnitude limbs, little endian."""
    if value < 0:
        raise ValueError("magnitude only")
    base = 1 << 24
    if value == 0:
        return [0]
    limbs = []
    while value:
        limbs.append(value % base)
        value //= base
    while len(limbs) > 1 and limbs[-1] == 0:
        limbs.pop()
    return limbs


def limb24_decode_unsigned(limbs: list[int]) -> int:
    base = 1 << 24
    if not limbs or any(not 0 <= x < base for x in limbs):
        raise ValueError("invalid Limb24")
    out = 0
    for limb in reversed(limbs):
        out = out * base + limb
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    # A — exact bounded integer semantics.
    for domain in (D24, D48):
        probes = [domain.lo, -1, 0, 1, domain.hi]
        for value in probes:
            assert domain.decode(domain.encode(value)) == value

    # Explicit overflow: exact Number semantics never wraps.
    assert D24.add(D24.hi, 1) is None
    assert D24.add(D24.lo, -1) is None
    assert D24.mul(1 << 12, 1 << 12) is None  # 2^24 does not fit signed D24.
    assert D48.mul(1 << 12, 1 << 12) == 1 << 24

    # B — directed widening ladder.
    boundary = D24.hi
    widened = widen(boundary, D24, D48)
    assert widened == boundary
    assert D48.decode(D48.encode(widened)) == boundary
    assert narrow(widened, D48, D24) == boundary

    just_outside = D24.hi + 1
    assert D48.contains(just_outside)
    assert narrow(just_outside, D48, D24) is None

    negative_boundary = D24.lo
    assert narrow(widen(negative_boundary, D24, D48), D48, D24) == negative_boundary

    # Widening commutes with exact operations whenever D24 result is defined.
    sample = [-100, -1, 0, 1, 7, 1024]
    for a in sample:
        for b in sample:
            r24 = D24.add(a, b)
            if r24 is not None:
                assert D48.add(widen(a, D24, D48), widen(b, D24, D48)) == widen(r24, D24, D48)
            r24m = D24.mul(a, b)
            if r24m is not None:
                assert D48.mul(widen(a, D24, D48), widen(b, D24, D48)) == widen(r24m, D24, D48)

    # C — exact dyadic candidate.
    # Different non-canonical pairs representing the same exact value collapse.
    assert DY24.normalize(2, -1) == (1, 0)
    assert DY24.value(2, -1) == Fraction(1, 1)
    assert DY24.encode(2, -1) == DY24.encode(1, 0)
    assert DY24.value(1, -1) + DY24.value(1, -2) == Fraction(3, 4)
    assert DY24.value(3, -2) == Fraction(3, 4)

    # The dyadic candidate is exact but intentionally not general Q.
    one_third = Fraction(1, 3)
    dyadic_one_third_representable = one_third.denominator & (one_third.denominator - 1) == 0
    assert not dyadic_one_third_representable

    # D — Limb24 mechanism control.
    cross = (1 << 24) - 1
    limbs_before = limb24_encode_unsigned(cross)
    limbs_after = limb24_encode_unsigned(cross + 1)
    assert limbs_before == [cross]
    assert limbs_after == [0, 1]
    assert limb24_decode_unsigned(limbs_after) == 1 << 24

    # Same exact integer can be represented with another mechanism (single Python bigint);
    # hence Limb24 layout cannot be semantic authority.
    assert limb24_decode_unsigned(limb24_encode_unsigned((1 << 70) + 3)) == (1 << 70) + 3

    model_rows = [
        {
            "model": "A-fixed-signed-integer",
            "domain": D24.name,
            "status": "VIABLE-SEMANTIC-CANDIDATE",
            "canonical": True,
            "exact": True,
            "closure": "partial-on-overflow",
            "widening": "D24->D48 total embedding",
            "general_Q": False,
            "mechanism_only": False,
        },
        {
            "model": "A-fixed-signed-integer",
            "domain": D48.name,
            "status": "VIABLE-SEMANTIC-CANDIDATE",
            "canonical": True,
            "exact": True,
            "closure": "partial-on-overflow",
            "widening": "to wider tier pending",
            "general_Q": False,
            "mechanism_only": False,
        },
        {
            "model": "B-directed-width-ladder",
            "domain": "D24Z->D48Z",
            "status": "VIABLE-LAWFUL-EMBEDDING",
            "canonical": True,
            "exact": True,
            "closure": "operations commute with widening when source-defined",
            "widening": "total injective; narrowing partial",
            "general_Q": False,
            "mechanism_only": False,
        },
        {
            "model": "C-exact-dyadic",
            "domain": DY24.name,
            "status": "VIABLE-SUBSET-CANDIDATE",
            "canonical": True,
            "exact": True,
            "closure": "exact dyadic only; bounded fields may overflow",
            "widening": "candidate to D48Dyadic",
            "general_Q": False,
            "mechanism_only": False,
        },
        {
            "model": "D-Limb24",
            "domain": "mechanism-private",
            "status": "MECHANISM-ONLY",
            "canonical": False,
            "exact": True,
            "closure": "unbounded via limb chains",
            "widening": "more limbs, not semantic D24->D48",
            "general_Q": False,
            "mechanism_only": True,
        },
    ]

    with (args.out / "model-tournament.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(model_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(model_rows)

    hardware_rows = [
        {
            "candidate": "D24Z",
            "semantic_payload_bits": 24,
            "add_geometry_bits": 24,
            "full_product_bits": 48,
            "cross_width_target": "D48Z",
            "device_specific_DSP_fit": "UNKNOWN-pending-fpga-lisp#39",
        },
        {
            "candidate": "D48Z",
            "semantic_payload_bits": 48,
            "add_geometry_bits": 48,
            "full_product_bits": 96,
            "cross_width_target": "wider-tier",
            "device_specific_DSP_fit": "UNKNOWN-pending-fpga-lisp#39",
        },
        {
            "candidate": "Limb24",
            "semantic_payload_bits": "mechanism-only",
            "add_geometry_bits": 25,
            "full_product_bits": 48,
            "cross_width_target": "next-limb carry",
            "device_specific_DSP_fit": "UNKNOWN-pending-fpga-lisp#39",
        },
    ]
    with (args.out / "hardware-geometry.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(hardware_rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(hardware_rows)

    artifact = {
        "schema": "core-number-width-ladder/v1",
        "authority": "research-only",
        "ontology_ref": "#2490",
        "semantic_results": {
            "D24Z": {
                "carrier": [D24.lo, D24.hi],
                "encoding": "canonical exact-width signed two's-complement coordinate",
                "add_mul": "exact when result is in carrier; otherwise undefined/needs widening",
                "silent_wrap": False,
            },
            "D48Z": {
                "carrier": [D48.lo, D48.hi],
                "encoding": "canonical exact-width signed two's-complement coordinate",
                "add_mul": "exact when result is in carrier; otherwise undefined/needs widening",
                "silent_wrap": False,
            },
            "widen_D24_D48": {
                "total": True,
                "injective": True,
                "value_preserving": True,
                "operation_commuting_on_defined_source_cases": True,
            },
            "narrow_D48_D24": {
                "partial": True,
                "proof_condition": "decoded exact integer lies in D24 carrier",
            },
            "D24Dyadic": {
                "exact": True,
                "canonical_normalization": "mantissa odd unless zero; exponent adjusted",
                "general_Q": False,
                "counterexample": "1/3 is not dyadic",
            },
            "Limb24": {
                "semantic_domain": False,
                "role": "mechanism-private unbounded magnitude representation",
                "first_carry_witness": "(2^24-1)+1 -> limbs [0,1]",
            },
        },
        "hardware_geometry": hardware_rows,
        "separation": {
            "semantic_width_choice_requires_math": True,
            "device_specific_resource_fit_is_semantics": False,
            "resource_source": "fpga-lisp#39",
        },
        "non_conclusions": [
            "D24Z/D48Z are candidates, not owner-ratified Core domains",
            "two's-complement polarity/encoding is a candidate coordinate choice, not yet uniquely forced by number theory",
            "D24Dyadic is not general exact rational Q",
            "Limb24 hardware convenience does not admit semantic D24",
            "no FPGA DSP/LUT count is claimed without device-specific synthesis evidence",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core Number width ladder — #2512",
        "",
        "Semantic tournament:",
        "",
        "| model | result |",
        "|---|---|",
        "| D24Z fixed exact signed integer | viable candidate; overflow is undefined/widening, never wrap |",
        "| D48Z fixed exact signed integer | viable candidate; same law at wider carrier |",
        "| D24Z -> D48Z | total injective value-preserving embedding |",
        "| D48Z -> D24Z | partial narrowing with explicit fit proof |",
        "| exact D24 dyadic | viable exact subset candidate, but not general Q (1/3 falsifier) |",
        "| Limb24 | mechanism-only control; not semantic authority |",
        "",
        "Key witnesses:",
        f"- D24 range: [{D24.lo}, {D24.hi}];",
        f"- D48 range: [{D48.lo}, {D48.hi}];",
        f"- D24 max + 1: undefined in D24, exactly representable in D48;",
        "- 2^12 * 2^12: undefined in signed D24, exact 2^24 in D48;",
        "- widening commutes with sampled defined add/mul cases;",
        "- canonical dyadic normalization: (2,-1) == (1,0);",
        "- 1/3 rejects the dyadic-as-general-Q hypothesis;",
        "- Limb24 carry: (2^24-1)+1 -> [0,1].",
        "",
        "Hardware geometry is reported separately; device-specific DSP/LUT fit remains",
        "UNKNOWN pending fpga-lisp#39 rather than becoming semantic evidence.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
