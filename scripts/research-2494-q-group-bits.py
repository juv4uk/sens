#!/usr/bin/env python3
"""#2494 — exact-Q group-factor binary-coordinate witness.

Research tooling only. Canonical objects under test are binary numbers in an
explicit candidate domain. Human names are validation projections only.
"""

from __future__ import annotations
import argparse
from fractions import Fraction
from itertools import permutations, product
import json
from pathlib import Path
from typing import Optional

CORPUS = (
    Fraction(-2, 1), Fraction(-1, 1), Fraction(-1, 2),
    Fraction(0, 1), Fraction(1, 2), Fraction(1, 1), Fraction(2, 1),
)

PROJECTION = {
    "0": "ADD", "00": "NEG", "01": "SUB",
    "1": "MUL", "10": "RECIP", "11": "DIV",
}

def bits(value: int, width: int) -> str:
    return format(value, f"0{width}b")

def combine(family: int, left: Fraction, right: Fraction) -> Fraction:
    if family == 0:
        return left + right
    if family == 1:
        return left * right
    raise ValueError(f"unknown family bit: {family}")

def identity(family: int) -> Fraction:
    if family == 0:
        return Fraction(0, 1)
    if family == 1:
        return Fraction(1, 1)
    raise ValueError(f"unknown family bit: {family}")

def inverse(family: int, value: Fraction) -> Optional[Fraction]:
    if family == 0:
        return -value
    if family == 1:
        if value == 0:
            return None
        return Fraction(value.denominator, value.numerator)
    raise ValueError(f"unknown family bit: {family}")

def semantic_role(
    family: int,
    role: int,
    left: Fraction,
    right: Optional[Fraction] = None,
) -> Optional[Fraction]:
    if role == 0:
        return inverse(family, left)
    if role == 1:
        if right is None:
            raise ValueError("quotient role requires two operands")
        right_inverse = inverse(family, right)
        if right_inverse is None:
            return None
        return combine(family, left, right_inverse)
    raise ValueError(f"unknown role bit: {role}")

def child_code(family: int, role: int) -> tuple[int, int]:
    if family not in (0, 1) or role not in (0, 1):
        raise ValueError("family and role must each be one bit")
    return (family << 1) | role, 2

def semantic_witness() -> dict:
    defined_cases = 0
    undefined_cases = 0
    rows = []
    for family in (0, 1):
        for role in (0, 1):
            code, width = child_code(family, role)
            code_bits = bits(code, width)
            assert code == 2 * family + role
            assert code_bits == bits(family, 1) + bits(role, 1)
            local_defined = 0
            local_undefined = 0
            if role == 0:
                for value in CORPUS:
                    result = semantic_role(family, role, value)
                    if result is None:
                        local_undefined += 1
                        assert family == 1 and value == 0
                        continue
                    assert combine(family, value, result) == identity(family)
                    local_defined += 1
            else:
                for left, right in product(CORPUS, repeat=2):
                    result = semantic_role(family, role, left, right)
                    if result is None:
                        local_undefined += 1
                        assert family == 1 and right == 0
                        continue
                    assert combine(family, result, right) == left
                    local_defined += 1
            defined_cases += local_defined
            undefined_cases += local_undefined
            rows.append({
                "root_bits": bits(family, 1),
                "role_bits": bits(role, 1),
                "child_bits": code_bits,
                "binary_equation": f"{code}=2*{family}+{role}",
                "validation_projection": PROJECTION[code_bits],
                "defined_cases": local_defined,
                "undefined_cases": local_undefined,
            })
    return {
        "rows": rows,
        "defined_cases": defined_cases,
        "undefined_cases": undefined_cases,
    }

def mapping_from_permutation(perm: tuple[int, ...]) -> dict[tuple[int, int], int]:
    pairs = ((0, 0), (0, 1), (1, 0), (1, 1))
    return dict(zip(pairs, perm, strict=True))

def exact_polarity(mapping: dict[tuple[int, int], int]) -> bool:
    return all(
        mapping[(family, role)] == 2 * family + role
        for family in (0, 1)
        for role in (0, 1)
    )

def family_prefix_preserved(mapping: dict[tuple[int, int], int]) -> bool:
    return all(
        mapping[(family, role)] >> 1 == family
        for family in (0, 1)
        for role in (0, 1)
    )

def one_global_role_orientation(mapping: dict[tuple[int, int], int]) -> bool:
    for role_map in ({0: 0, 1: 1}, {0: 1, 1: 0}):
        if all(
            mapping[(family, role)] == 2 * family + role_map[role]
            for family in (0, 1)
            for role in (0, 1)
        ):
            return True
    return False

def anti_numerology() -> dict:
    mappings = [
        mapping_from_permutation(perm)
        for perm in permutations((0, 1, 2, 3))
    ]
    exact = [m for m in mappings if exact_polarity(m)]
    family_preserving = [m for m in mappings if family_prefix_preserved(m)]
    global_role = [m for m in mappings if one_global_role_orientation(m)]

    local_swap = {
        (0, 0): 1, (0, 1): 0,
        (1, 0): 2, (1, 1): 3,
    }
    assert family_prefix_preserved(local_swap)
    assert not one_global_role_orientation(local_swap)

    global_swap = {
        (0, 0): 1, (0, 1): 0,
        (1, 0): 3, (1, 1): 2,
    }
    assert family_prefix_preserved(global_swap)
    assert one_global_role_orientation(global_swap)
    assert not exact_polarity(global_swap)

    family_swapped = {
        (0, 0): 2, (0, 1): 3,
        (1, 0): 0, (1, 1): 1,
    }
    assert all(
        (family_swapped[(family, role)] >> 1) == (1 - family)
        and (family_swapped[(family, role)] & 1) == role
        for family in (0, 1)
        for role in (0, 1)
    )

    return {
        "all_width2_slot_permutations": len(mappings),
        "exact_original_polarity": len(exact),
        "family_prefix_preserving_permutations": len(family_preserving),
        "single_global_role_orientation_permutations": len(global_role),
        "arbitrary_permutations_rejected_by_global_factor_law": len(mappings) - len(global_role),
        "local_one_family_role_swap": "REJECTED",
        "global_role_bit_reversal": "PRESERVES-FACTOR-STRUCTURE",
        "global_family_bit_reversal": "PRESERVES-FACTOR-STRUCTURE-WITH-CONSISTENT-ROOT-RELABEL",
    }

def result() -> dict:
    witness = semantic_witness()
    attacks = anti_numerology()
    assert witness["defined_cases"] == 104
    assert witness["undefined_cases"] == 8
    assert attacks["all_width2_slot_permutations"] == 24
    assert attacks["exact_original_polarity"] == 1
    assert attacks["family_prefix_preserving_permutations"] == 4
    assert attacks["single_global_role_orientation_permutations"] == 2
    assert attacks["arbitrary_permutations_rejected_by_global_factor_law"] == 22
    return {
        "schema": "core-math-q-group-bits/v1",
        "authority": "research-only",
        "domain": {
            "name": "exact-Q-group-factor-coordinate",
            "root_width_bits": 1,
            "child_width_bits": 2,
            "root_count": 2,
            "role_count": 2,
        },
        "binary_objects": {
            "roots": ["0", "1"],
            "children": ["00", "01", "10", "11"],
            "coordinate_law": "child=(root<<1)|role = 2*root+role",
        },
        "semantic_law": {
            "inverse": "inverse_F(x)=unique y such that x circle y = identity_F, where defined",
            "quotient": "quotient_F(x,y)=x circle inverse_F(y), where defined",
            "multiplicative_partiality": "inverse(0) and quotient(x,0) are undefined",
        },
        "witness": witness,
        "anti_numerology": attacks,
        "classification": {
            "inverse_quotient_semantics": "SEMANTIC-LAW",
            "two_factor_binary_layout": "CANONICAL-FACTOR-COORDINATE-LAW",
            "specific_family_bit_polarity": "NOT-FORCED-BY-THIS-LAW",
            "specific_role_bit_polarity": "NOT-FORCED-BY-THIS-LAW",
        },
        "accounting": {
            "family_roots_or_premises": 2,
            "generic_role_laws": 2,
            "explicit_partiality_facts": 1,
            "binary_factor_coordinate_laws": 1,
            "per_result_lookup_rows": 0,
        },
        "relation": {
            "status": "CORE-MATH-ONLY",
            "core_bridge": "NONE-CLAIMED",
            "convergence": "NONE-CLAIMED",
        },
        "non_conclusions": [
            "the inverse/quotient laws do not force the 0/1 polarity of either factor",
            "the experiment does not admit these coordinates into Core",
            "the two-bit factor law does not prove every future Core-Math domain has the same shape",
            "human operation names are validation projections only",
        ],
    }

def render_markdown(data: dict) -> str:
    lines = [
        "# #2494 exact-Q binary group-factor witness",
        "",
        "root bit: 0 / 1; role bit: 0 / 1; child = root*2 + role",
        "",
        "| root | role | child | human projection | defined | undefined |",
        "|---:|---:|---:|---|---:|---:|",
    ]
    for row in data["witness"]["rows"]:
        lines.append(
            f"| {row['root_bits']} | {row['role_bits']} | {row['child_bits']} | "
            f"{row['validation_projection']} | {row['defined_cases']} | {row['undefined_cases']} |"
        )
    attacks = data["anti_numerology"]
    cls = data["classification"]
    lines += [
        "",
        f"Exact-Q cases: {data['witness']['defined_cases']} defined, "
        f"{data['witness']['undefined_cases']} intentionally undefined.",
        "",
        "Anti-numerology:",
        f"- all width-2 slot permutations: {attacks['all_width2_slot_permutations']}",
        f"- exact original polarity: {attacks['exact_original_polarity']}",
        f"- family-prefix preserving: {attacks['family_prefix_preserving_permutations']}",
        f"- one global role orientation: {attacks['single_global_role_orientation_permutations']}",
        f"- rejected by global factor law: {attacks['arbitrary_permutations_rejected_by_global_factor_law']}",
        "- local one-family role swap: REJECTED",
        "- global role-bit reversal: preserves factor structure",
        "- global family-bit reversal with consistent root relabel: preserves factor structure",
        "",
        "Classification:",
        f"- semantic inverse/quotient law: {cls['inverse_quotient_semantics']}",
        f"- binary [family][role] layout: {cls['two_factor_binary_layout']}",
        f"- family polarity: {cls['specific_family_bit_polarity']}",
        f"- role polarity: {cls['specific_role_bit_polarity']}",
        "",
        "Interpretation:",
        "one generic factor law covers both families without per-result lookup rows.",
        "The factorization is real; this experiment does not prove that mathematics uniquely chooses the 0/1 polarity of either factor.",
        "",
    ]
    return "\\n".join(lines)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = result()
    report = render_markdown(data)
    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "result.json").write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(report, encoding="utf-8")
    print(json.dumps(data, indent=2, sort_keys=True) if args.json else report)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
