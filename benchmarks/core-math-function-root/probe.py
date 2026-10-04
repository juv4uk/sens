#!/usr/bin/env python3
"""#3023 function-root law probe.

Current semantic authority: #3331 (D1-D5 ratified; D6-D8 research).

This probe does two things:
1. exhaustively enumerates perfect-square coordinates in the current D1-D5
   foundation and all exact-domain residents whose numeric coordinate equals
   the integer square root;
2. runs the selector-family semantic falsifier and the affine append positive
   control.

Arithmetic never creates semantics here.  Semantic witnesses are stated
independently from the selector law already ratified in #3202/#3272/#3331.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
import json


FOUNDATION = {
    "D1": {
        "0": "NO",
        "1": "YES",
    },
    "D2": {
        "00": "SEPARATOR",
        "01": "CLOSE",
        "10": "OPEN",
        "11": "DOT",
    },
    "D3": {
        "000": "EMPTY",
        "001": "QUOTE",
        "010": "ATOM",
        "011": "CDR",
        "100": "CAR",
        "101": "EQ",
        "110": "COND",
        "111": "CONS",
    },
    "D4": {
        "0000": "APPLY",
        "0001": "EVAL",
        "0010": "LAMBDA",
        "0011": "DEFINE",
        "0100": "NOT",
        "0101": "NULL",
        "0110": "CDAR",
        "0111": "CDDR",
        "1000": "CAAR",
        "1001": "CADR",
        "1010": "LOOKUP",
        "1011": "BIND",
        "1100": "EVCON",
        "1101": "EVLIS",
        "1110": "LIST",
        "1111": "APPEND",
    },
    "D5": {
        "00000": "EVALQUOTE",
        "00001": "FUNCTION",
        "00010": "FEXPR",
        "00011": "MACRO",
        "00100": "LABEL",
        "00101": "PROG",
        "00110": "SET",
        "00111": "SETQ",
        "01000": "ZEROP",
        "01001": "NUMBERP",
        "01010": "PLUS",
        "01011": "DIFFERENCE",
        "01100": "CDAAR",
        "01101": "CDADR",
        "01110": "CDDAR",
        "01111": "CDDDR",
        "10000": "CAAAR",
        "10001": "CAADR",
        "10010": "CADAR",
        "10011": "CADDR",
        "10100": "REVERSE",
        "10101": "REVERSE-ONTO",
        "10110": "TIMES",
        "10111": "QUOTIENT",
        "11000": "GO",
        "11001": "RETURN",
        "11010": "LESSP",
        "11011": "GREATERP",
        "11100": "ASSOC",
        "11101": "MEMBER",
        "11110": "PAIRLIS",
        "11111": "SUBST",
    },
}


def coord(domain: str, name: str) -> tuple[str, int]:
    for bits, resident in FOUNDATION[domain].items():
        if resident == name:
            return bits, int(bits, 2)
    raise KeyError((domain, name))


def resident_at(domain: str, value: int) -> tuple[str, str] | None:
    width = int(domain[1:])
    if value >= 1 << width:
        return None
    bits = format(value, f"0{width}b")
    name = FOUNDATION[domain].get(bits)
    if name is None:
        return None
    return bits, name


def falling(n: int, k: int) -> int:
    out = 1
    for x in range(n, n - k, -1):
        out *= x
    return out


def perfect_square_scan() -> list[dict]:
    rows: list[dict] = []
    for source_domain, residents in FOUNDATION.items():
        for source_bits, source_name in residents.items():
            n = int(source_bits, 2)
            r = isqrt(n)
            if r * r != n:
                continue
            roots = []
            for candidate_domain in FOUNDATION:
                hit = resident_at(candidate_domain, r)
                if hit is None:
                    continue
                bits, name = hit
                roots.append(
                    {
                        "domain": candidate_domain,
                        "bits": bits,
                        "resident": name,
                    }
                )
            rows.append(
                {
                    "source_domain": source_domain,
                    "source_bits": source_bits,
                    "source_resident": source_name,
                    "source_value": n,
                    "root_value": r,
                    "root_candidates": roots,
                }
            )
    return rows


def selector_falsifier() -> list[dict]:
    # Independent semantic facts from the admitted selector law:
    # CAR∘CAR = CAAR; CDR∘CDR = CDDR.
    semantic_pairs = [
        ("D3", "CAR", "D4", "CAAR"),
        ("D3", "CDR", "D4", "CDDR"),
    ]
    rows = []
    for root_domain, root_name, semantic_domain, semantic_name in semantic_pairs:
        root_bits, root_value = coord(root_domain, root_name)
        semantic_bits, semantic_value = coord(semantic_domain, semantic_name)
        square_value = root_value * root_value

        predicted = []
        for domain in FOUNDATION:
            hit = resident_at(domain, square_value)
            if hit is not None:
                bits, name = hit
                predicted.append(
                    {"domain": domain, "bits": bits, "resident": name}
                )

        rows.append(
            {
                "root": {
                    "domain": root_domain,
                    "bits": root_bits,
                    "resident": root_name,
                    "value": root_value,
                },
                "semantic_self_composition": {
                    "domain": semantic_domain,
                    "bits": semantic_bits,
                    "resident": semantic_name,
                    "value": semantic_value,
                },
                "coordinate_square_value": square_value,
                "coordinate_square_targets": predicted,
                "match": any(
                    x["domain"] == semantic_domain
                    and x["bits"] == semantic_bits
                    for x in predicted
                ),
            }
        )
    return rows


def selector_append_witnesses() -> list[dict]:
    # child(parent,A) = 2*n+0; child(parent,D) = 2*n+1
    relations = [
        ("D3", "CDR", "D4", "CDAR", 0),
        ("D3", "CDR", "D4", "CDDR", 1),
        ("D3", "CAR", "D4", "CAAR", 0),
        ("D3", "CAR", "D4", "CADR", 1),
        ("D4", "CDAR", "D5", "CDAAR", 0),
        ("D4", "CDAR", "D5", "CDADR", 1),
        ("D4", "CDDR", "D5", "CDDAR", 0),
        ("D4", "CDDR", "D5", "CDDDR", 1),
        ("D4", "CAAR", "D5", "CAAAR", 0),
        ("D4", "CAAR", "D5", "CAADR", 1),
        ("D4", "CADR", "D5", "CADAR", 0),
        ("D4", "CADR", "D5", "CADDR", 1),
    ]
    out = []
    for parent_domain, parent_name, child_domain, child_name, bit in relations:
        parent_bits, parent_value = coord(parent_domain, parent_name)
        child_bits, child_value = coord(child_domain, child_name)
        predicted = 2 * parent_value + bit
        out.append(
            {
                "parent": {
                    "domain": parent_domain,
                    "bits": parent_bits,
                    "resident": parent_name,
                    "value": parent_value,
                },
                "selector_bit": bit,
                "child": {
                    "domain": child_domain,
                    "bits": child_bits,
                    "resident": child_name,
                    "value": child_value,
                },
                "predicted_value": predicted,
                "match": predicted == child_value,
            }
        )
    return out


def main() -> None:
    square_scan = perfect_square_scan()
    square_tests = selector_falsifier()
    append = selector_append_witnesses()

    d3_d4_append = [x for x in append if x["parent"]["domain"] == "D3"]
    d4_d5_append = [x for x in append if x["parent"]["domain"] == "D4"]

    # Exact random-placement controls.
    #
    # Square control:
    # CAR/CDR receive two distinct random D3 coordinates.  Both squares fit in
    # D4 only when both coordinates are in {0,1,2,3}: 4P2 / 8P2.
    # Given that, CAAR/CDDR must hit two exact D4 coordinates: 1 / 16P2.
    p_square_both = Fraction(falling(4, 2), falling(8, 2)) * Fraction(
        1, falling(16, 2)
    )

    # Append controls: conditional on arbitrary distinct parent positions,
    # every named child has one exact required coordinate.
    p_append_d3_d4_all = Fraction(1, falling(16, 4))
    p_append_d4_d5_all = Fraction(1, falling(32, 8))

    report = {
        "authority": "#3331",
        "current_domains": list(FOUNDATION),
        "current_resident_count": sum(len(x) for x in FOUNDATION.values()),
        "perfect_square_source_count": len(square_scan),
        "domain_qualified_root_candidate_count": sum(
            len(x["root_candidates"]) for x in square_scan
        ),
        "square_sources": square_scan,
        "selector_square_self_compose": square_tests,
        "selector_square_matches": sum(x["match"] for x in square_tests),
        "selector_square_tests": len(square_tests),
        "selector_append": append,
        "selector_append_matches": sum(x["match"] for x in append),
        "selector_append_tests": len(append),
        "anti_numerology": {
            "p_both_primitive_selector_square_hits_random_placement": {
                "fraction": f"{p_square_both.numerator}/{p_square_both.denominator}",
                "decimal": float(p_square_both),
            },
            "p_all_d3_d4_append_hits_random_placement": {
                "fraction": f"{p_append_d3_d4_all.numerator}/{p_append_d3_d4_all.denominator}",
                "decimal": float(p_append_d3_d4_all),
            },
            "p_all_d4_d5_append_hits_random_placement": {
                "fraction": f"{p_append_d4_d5_all.numerator}/{p_append_d4_d5_all.denominator}",
                "decimal": float(p_append_d4_d5_all),
            },
        },
        "classification": {
            "sqrt_self_composition_selector_family": "FALSIFIED",
            "affine_selector_append_law": "PROVED-BOUNDED-POSITIVE-CONTROL",
        },
        "scope_note": (
            "The coordinate scan is exhaustive for current D1-D5. "
            "Semantic self-composition is tested only where an independent "
            "composition law is already admitted. Other root candidates remain "
            "UNTESTED, never inferred from arithmetic."
        ),
    }

    assert report["current_resident_count"] == 62
    assert report["perfect_square_source_count"] == 17
    assert report["domain_qualified_root_candidate_count"] == 76
    assert report["selector_square_matches"] == 0
    assert report["selector_square_tests"] == 2
    assert report["selector_append_matches"] == 12
    assert report["selector_append_tests"] == 12
    assert p_square_both == Fraction(1, 1120)
    assert p_append_d3_d4_all == Fraction(1, 43680)
    assert p_append_d4_d5_all == Fraction(1, 424097856000)

    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
