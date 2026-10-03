#!/usr/bin/env python3
"""#2508 — same binary mechanism must not collapse domain semantics.

Research-only witness for #2490.

Two admitted semantic laws currently share the same low-level bit mechanism:
append one bit / y = 2*x+b.

This script proves that the mechanism can be shared while law authority remains
explicitly domain-scoped.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

SELECTOR = "selector-path"
QGROUP = "q-group-factor"


@dataclass(frozen=True)
class BinaryObject:
    domain: str
    bits: str

    def __post_init__(self):
        if not self.bits or any(ch not in "01" for ch in self.bits):
            raise ValueError("binary object must be non-empty 0/1 bits")


@dataclass(frozen=True)
class Law:
    law_id: str
    domain: str
    semantic_equation: str


SELECTOR_LAW = Law(
    "selector.extend/v1",
    SELECTOR,
    "extend(selector,b)(x)=selector(project_b(x))",
)
QGROUP_LAW = Law(
    "q-group.role/v1",
    QGROUP,
    "inverse_F(x)=unique y:x∘y=e; quotient_F(x,y)=x∘inverse_F(y)",
)


def append_mechanism(parent: str, bit: str) -> str:
    if bit not in {"0", "1"}:
        raise ValueError("delta must be one bit")
    return parent + bit


def apply_law(law: Law, parent: BinaryObject, bit: str) -> BinaryObject:
    if parent.domain != law.domain:
        raise TypeError(f"DOMAIN-MISMATCH:{parent.domain}->{law.domain}")
    return BinaryObject(parent.domain, append_mechanism(parent.bits, bit))


FAIL = ("FAIL",)


def atom(name: str):
    return ("ATOM", name)


def pair(a, d):
    return ("PAIR", a, d)


def project(value, bit: str):
    if not isinstance(value, tuple) or len(value) != 3 or value[0] != "PAIR":
        return FAIL
    return value[1] if bit == "0" else value[2]


def selector_semantic_control():
    value = pair(pair(atom("a"), atom("b")), pair(atom("c"), atom("d")))
    # Core canonical selector root 101 = first projection.
    parent_result = project(value, "0")
    child_result = project(project(value, "0"), "0")
    staged = project(parent_result, "0")
    assert child_result == staged
    return {
        "parent_bits": "101",
        "delta": "0",
        "child_bits": "1010",
        "semantic_result": repr(child_result),
    }


def qgroup_semantic_control():
    corpus = [
        Fraction(-2, 1),
        Fraction(-1, 2),
        Fraction(0, 1),
        Fraction(1, 2),
        Fraction(2, 1),
    ]
    additive_inverse = [-x for x in corpus]
    additive_quotient = [x - y for x in corpus for y in corpus]
    multiplicative_inverse = [
        None if x == 0 else Fraction(1, 1) / x
        for x in corpus
    ]
    multiplicative_quotient = [
        None if y == 0 else x / y
        for x in corpus for y in corpus
    ]
    assert additive_inverse
    assert additive_quotient
    assert multiplicative_inverse.count(None) == 1
    assert sum(x is None for x in multiplicative_quotient) == len(corpus)
    return {
        "root_bits": ["0", "1"],
        "children": ["00", "01", "10", "11"],
        "undefined_reciprocal_cases": 1,
        "undefined_division_cases": len(corpus),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    selector_parent = BinaryObject(SELECTOR, "101")
    q_parent = BinaryObject(QGROUP, "1")

    selector_child = apply_law(SELECTOR_LAW, selector_parent, "0")
    q_child = apply_law(QGROUP_LAW, q_parent, "0")

    assert selector_child.bits == append_mechanism("101", "0") == "1010"
    assert q_child.bits == append_mechanism("1", "0") == "10"

    # Same low-level mechanism does not authorize cross-domain semantics.
    cross = []
    for law, obj in [
        (SELECTOR_LAW, q_parent),
        (QGROUP_LAW, selector_parent),
    ]:
        try:
            apply_law(law, obj, "0")
        except TypeError as exc:
            cross.append({
                "law": law.law_id,
                "object_domain": obj.domain,
                "status": "DOMAIN-MISMATCH",
                "reason": str(exc),
            })
        else:
            raise AssertionError("cross-domain law unexpectedly accepted")
    assert len(cross) == 2

    # A mechanism-only representation loses the semantic distinction.
    mechanism_only = {
        "factor": "10",
        "equation": "child=2*parent+bit",
    }
    assert SELECTOR_LAW.semantic_equation != QGROUP_LAW.semantic_equation

    # Equal bit strings may exist as mechanism values under different explicit
    # domains; domain is part of semantic identity even before validity rules.
    same_bits_selector = BinaryObject(SELECTOR, "10")
    same_bits_q = BinaryObject(QGROUP, "10")
    assert same_bits_selector.bits == same_bits_q.bits
    assert same_bits_selector != same_bits_q

    selector_control = selector_semantic_control()
    q_control = qgroup_semantic_control()

    rows = [
        {
            "domain": SELECTOR,
            "bits": selector_parent.bits,
            "law": SELECTOR_LAW.law_id,
            "semantic_equation": SELECTOR_LAW.semantic_equation,
            "mechanism_equation": mechanism_only["equation"],
            "cross_domain_apply": "DOMAIN-MISMATCH",
            "status": "DOMAIN-VALID",
        },
        {
            "domain": QGROUP,
            "bits": q_parent.bits,
            "law": QGROUP_LAW.law_id,
            "semantic_equation": QGROUP_LAW.semantic_equation,
            "mechanism_equation": mechanism_only["equation"],
            "cross_domain_apply": "DOMAIN-MISMATCH",
            "status": "DOMAIN-VALID",
        },
    ]

    with (args.out / "domain-separation.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    artifact = {
        "schema": "binary-domain-separation/v1",
        "authority": "research-only",
        "shared_mechanism": mechanism_only,
        "laws": rows,
        "cross_domain_controls": cross,
        "same_bits_control": {
            "bits": "10",
            "selector_object": {"domain": SELECTOR, "bits": "10"},
            "qgroup_object": {"domain": QGROUP, "bits": "10"},
            "semantic_objects_equal": False,
            "status_without_domain": "AMBIGUOUS-WITHOUT-DOMAIN",
        },
        "selector_semantic_control": selector_control,
        "qgroup_semantic_control": q_control,
        "non_conclusions": [
            "shared factor-2 mechanism is not a global semantic law ID",
            "synthetic same-bits control does not claim 10 is an admitted selector root",
            "domain tags are semantic authority, not display metadata",
            "this witness does not prove convergence between selector and Q-group domains",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Binary-domain separation — #2508",
        "",
        "Both tested laws reuse the same low-level mechanism:",
        "",
        "    child = 2*parent + bit",
        "",
        "But their semantic equations are different.",
        "",
        "| law domain | valid local apply | cross-domain apply |",
        "|---|---|---|",
        "| selector-path | PASS | DOMAIN-MISMATCH |",
        "| q-group-factor | PASS | DOMAIN-MISMATCH |",
        "",
        "Same-bits control: domain-qualified objects with bits 10 remain distinct.",
        "Erasing the domain yields AMBIGUOUS-WITHOUT-DOMAIN.",
        "",
        "Interpretation:",
        "the binary append/factor-2 mechanism is reusable implementation structure;",
        "semantic law identity remains domain-scoped.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
