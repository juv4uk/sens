#!/usr/bin/env python3
"""#3374 — exact-Q constant bootstrap.

Ground layer:
    {-1, 0, 1}

Current function numbers under test:
    01010, 01011, 10110, 10111

Human names are validation projections only.  All arithmetic uses exact
fractions; no float enters the witness.
"""

from __future__ import annotations

from fractions import Fraction
import itertools
import json


FUNCTIONS = {
    "01010": "PLUS",
    "01011": "DIFFERENCE",
    "10110": "TIMES",
    "10111": "QUOTIENT",
}

SEEDS = (Fraction(-1, 1), Fraction(0, 1), Fraction(1, 1))
TARGET_CORPUS = (
    Fraction(-2, 1),
    Fraction(-1, 1),
    Fraction(-1, 2),
    Fraction(0, 1),
    Fraction(1, 2),
    Fraction(1, 1),
    Fraction(2, 1),
)


def q2(value: Fraction) -> str:
    n = value.numerator
    d = value.denominator
    if n == 0:
        nbits = "0"
    else:
        mag = format(abs(n), "b")
        nbits = ("-" if n < 0 else "") + mag
    return f"#q2:{nbits}/{format(d, 'b')}"


def apply(code: str, a: Fraction, b: Fraction) -> Fraction | None:
    if code == "01010":
        return a + b
    if code == "01011":
        return a - b
    if code == "10110":
        return a * b
    if code == "10111":
        return None if b == 0 else a / b
    raise KeyError(code)


def serialize(v: Fraction | None) -> str:
    return "UNDEFINED-MATHEMATICALLY" if v is None else q2(v)


def seed_signatures() -> dict:
    pairs = tuple(itertools.product(SEEDS, repeat=2))
    signatures = {
        code: tuple(serialize(apply(code, a, b)) for a, b in pairs)
        for code in FUNCTIONS
    }
    assert len(set(signatures.values())) == len(FUNCTIONS)

    # Find the smallest seed-pair probe set that distinguishes the four
    # current function numbers. Partiality is a mathematical behavior and may
    # contribute to the signature.
    minimal = None
    for k in range(1, len(pairs) + 1):
        for subset in itertools.combinations(range(len(pairs)), k):
            projected = {
                code: tuple(signatures[code][i] for i in subset)
                for code in FUNCTIONS
            }
            if len(set(projected.values())) == len(FUNCTIONS):
                minimal = subset
                break
        if minimal is not None:
            break
    assert minimal is not None

    return {
        "pair_order": [[q2(a), q2(b)] for a, b in pairs],
        "signatures": {
            code: {
                "validation_projection": FUNCTIONS[code],
                "outputs": list(sig),
            }
            for code, sig in signatures.items()
        },
        "all_four_distinct_on_seed_grid": True,
        "minimal_distinguishing_probe_count": len(minimal),
        "minimal_distinguishing_probes": [
            [q2(pairs[i][0]), q2(pairs[i][1])] for i in minimal
        ],
    }


def bootstrap_corpus() -> dict:
    minus_one, zero, one = SEEDS

    two = apply("01010", one, one)
    minus_two = apply("01010", minus_one, minus_one)
    assert two == Fraction(2, 1)
    assert minus_two == Fraction(-2, 1)

    half = apply("10111", one, two)
    minus_half = apply("10111", minus_one, two)
    assert half == Fraction(1, 2)
    assert minus_half == Fraction(-1, 2)

    generated = tuple(sorted(set(SEEDS + (two, minus_two, half, minus_half))))
    assert generated == TARGET_CORPUS

    return {
        "stage0_seeds": [q2(x) for x in SEEDS],
        "stage1": [
            {
                "result": q2(two),
                "equation": "01010(#q2:1/1,#q2:1/1)",
            },
            {
                "result": q2(minus_two),
                "equation": "01010(#q2:-1/1,#q2:-1/1)",
            },
        ],
        "stage2": [
            {
                "result": q2(half),
                "equation": "10111(#q2:1/1,#q2:10/1)",
            },
            {
                "result": q2(minus_half),
                "equation": "10111(#q2:-1/1,#q2:10/1)",
            },
        ],
        "generated_corpus": [q2(x) for x in generated],
        "target_corpus_recovered": True,
        "independent_seed_constants": 3,
        "generated_nonseed_constants": 4,
    }


def derived_laws() -> dict:
    corpus = TARGET_CORPUS
    minus_one = Fraction(-1, 1)
    one = Fraction(1, 1)
    zero = Fraction(0, 1)

    neg_matches = 0
    recip_matches = 0
    recip_undefined = 0
    identity_counts = {
        "plus_right_zero": 0,
        "times_right_one": 0,
        "times_right_zero": 0,
        "difference_right_zero": 0,
        "quotient_right_one": 0,
    }

    for x in corpus:
        neg = apply("10110", minus_one, x)
        assert neg == -x
        neg_matches += 1

        rec = apply("10111", one, x)
        if x == 0:
            assert rec is None
            recip_undefined += 1
        else:
            assert rec == Fraction(1, 1) / x
            recip_matches += 1

        if apply("01010", x, zero) == x:
            identity_counts["plus_right_zero"] += 1
        if apply("10110", x, one) == x:
            identity_counts["times_right_one"] += 1
        if apply("10110", x, zero) == zero:
            identity_counts["times_right_zero"] += 1
        if apply("01011", x, zero) == x:
            identity_counts["difference_right_zero"] += 1
        if apply("10111", x, one) == x:
            identity_counts["quotient_right_one"] += 1

    sub_matches = 0
    div_defined_matches = 0
    div_undefined_matches = 0
    for x, y in itertools.product(corpus, repeat=2):
        derived_sub = apply("01010", x, apply("10110", minus_one, y))
        direct_sub = apply("01011", x, y)
        assert derived_sub == direct_sub
        sub_matches += 1

        recip_y = apply("10111", one, y)
        derived_div = None if recip_y is None else apply("10110", x, recip_y)
        direct_div = apply("10111", x, y)
        assert derived_div == direct_div
        if y == 0:
            div_undefined_matches += 1
        else:
            div_defined_matches += 1

    assert neg_matches == 7
    assert recip_matches == 6
    assert recip_undefined == 1
    assert sub_matches == 49
    assert div_defined_matches == 42
    assert div_undefined_matches == 7
    assert all(v == 7 for v in identity_counts.values())

    return {
        "NEG_from_constant_and_TIMES": {
            "equation": "NEG(x) = 10110(#q2:-1/1, x)",
            "matches": neg_matches,
        },
        "RECIP_from_constant_and_QUOTIENT": {
            "equation": "RECIP(x) = 10111(#q2:1/1, x)",
            "defined_matches": recip_matches,
            "undefined_zero_cases": recip_undefined,
        },
        "SUB_from_PLUS_TIMES_minus_one": {
            "equation": "SUB(x,y) = 01010(x, 10110(#q2:-1/1,y))",
            "matches": sub_matches,
        },
        "DIV_from_TIMES_QUOTIENT_one": {
            "equation": "DIV(x,y) = 10110(x, 10111(#q2:1/1,y))",
            "defined_matches": div_defined_matches,
            "undefined_zero_divisor_matches": div_undefined_matches,
        },
        "constant_anchor_laws": identity_counts,
    }


def main() -> None:
    report = {
        "issue": "#3374",
        "classification": "Q-CONSTANT-BOOTSTRAP-WITNESS",
        "seed_layer": {
            "values": [q2(x) for x in SEEDS],
            "human_projection": ["-1", "0", "1"],
            "ground_fact_count": 3,
        },
        "function_numbers": {
            code: {"validation_projection": name}
            for code, name in FUNCTIONS.items()
        },
        "seed_signatures": seed_signatures(),
        "bootstrap": bootstrap_corpus(),
        "derived_laws": derived_laws(),
        "result": {
            "seed_constants_anchor_function_behavior": True,
            "old_seven_point_Q_corpus_generated": True,
            "derived_operations_replay_current_arithmetic": True,
            "float_used": False,
        },
        "boundary": (
            "This is a semantic bootstrap witness over existing exact-Q values "
            "and current D5 function numbers. It does not allocate new domain "
            "residents or declare a final rational storage ontology."
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
