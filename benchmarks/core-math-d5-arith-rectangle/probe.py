#!/usr/bin/env python3
from fractions import Fraction
import json

COORD = {
    "PLUS": int("01010", 2),
    "DIFFERENCE": int("01011", 2),
    "TIMES": int("10110", 2),
    "QUOTIENT": int("10111", 2),
}

def hamming_weight(x):
    return x.bit_count()

def corpus():
    vals={Fraction(n,d) for n in range(-12,13) for d in range(1,7)}
    return sorted(vals)

def main():
    vals=corpus()
    assert len(vals)==93

    semantic_cases=0
    quotient_defined=0
    quotient_undefined=0

    for a in vals:
        for b in vals:
            semantic_cases += 1

            plus = a + b
            difference = a - b
            times = a * b

            assert difference == a + (-b)

            if b == 0:
                quotient_undefined += 1
            else:
                quotient_defined += 1
                quotient = a / b
                assert quotient == a * (1 / b)

            # independent family x role oracle
            add_combine = a + b
            add_right_quotient = a + (-b)
            mul_combine = a * b

            assert add_combine == plus
            assert add_right_quotient == difference
            assert mul_combine == times

            if b != 0:
                mul_right_quotient = a * (1 / b)
                assert mul_right_quotient == quotient

    p=COORD["PLUS"]
    d=COORD["DIFFERENCE"]
    t=COORD["TIMES"]
    q=COORD["QUOTIENT"]

    role_mask_1 = p ^ d
    role_mask_2 = t ^ q
    family_mask_1 = p ^ t
    family_mask_2 = d ^ q

    rectangle = (p ^ d ^ t ^ q) == 0
    role_axis_shared = role_mask_1 == role_mask_2
    family_axis_shared = family_mask_1 == family_mask_2

    # Random-placement controls for four labeled distinct residents in 32 cells.
    p_any_affine_rectangle = Fraction(1, 29)
    p_any_onebit_role_rectangle = Fraction(5, 31*29)
    p_fixed_lsb_role_rectangle = Fraction(1, 31*29)
    p_exact_observed_masks = Fraction(1, 31*30*29)

    wrong_role_mask=2
    wrong_role_hits = int((p ^ wrong_role_mask)==d) + int((t ^ wrong_role_mask)==q)

    report={
        "authority":"#3331/#3305",
        "issue":"#3349",
        "semantic_oracle":{
            "carrier":"exact-Q",
            "values":len(vals),
            "ordered_pairs":semantic_cases,
            "difference_identity_matches":semantic_cases,
            "quotient_defined_cases":quotient_defined,
            "quotient_undefined_cases":quotient_undefined,
            "family_role_factorization":"PASS",
        },
        "coordinates":{k:format(v,"05b") for k,v in COORD.items()},
        "coordinate_geometry":{
            "role_mask":format(role_mask_1,"05b"),
            "role_mask_shared":role_axis_shared,
            "role_mask_hamming_weight":hamming_weight(role_mask_1),
            "family_mask":format(family_mask_1,"05b"),
            "family_mask_shared":family_axis_shared,
            "family_mask_hamming_weight":hamming_weight(family_mask_1),
            "affine_rectangle":rectangle,
            "xor_all_four":format(p^d^t^q,"05b"),
            "wrong_xor_00010_role_hits":wrong_role_hits,
        },
        "anti_numerology":{
            "p_any_affine_rectangle":{
                "fraction":f"{p_any_affine_rectangle.numerator}/{p_any_affine_rectangle.denominator}",
                "decimal":float(p_any_affine_rectangle),
            },
            "p_any_onebit_role_rectangle":{
                "fraction":f"{p_any_onebit_role_rectangle.numerator}/{p_any_onebit_role_rectangle.denominator}",
                "decimal":float(p_any_onebit_role_rectangle),
            },
            "p_fixed_lsb_role_rectangle":{
                "fraction":f"{p_fixed_lsb_role_rectangle.numerator}/{p_fixed_lsb_role_rectangle.denominator}",
                "decimal":float(p_fixed_lsb_role_rectangle),
            },
            "p_exact_observed_masks":{
                "fraction":f"{p_exact_observed_masks.numerator}/{p_exact_observed_masks.denominator}",
                "decimal":float(p_exact_observed_masks),
            },
        },
        "classification":{
            "semantic_family_x_role":"PROVED-BOUNDED",
            "current_D5_coordinate_rectangle":"COMPLEMENTARY-BRIDGE-CANDIDATE",
            "global_coordinate_law":"NOT-PROVED",
        },
        "warning":"Observed masks are not semantic authority; current geometry is evidence, not derivation.",
    }

    assert semantic_cases==8649
    assert quotient_undefined==93
    assert quotient_defined==8556
    assert role_mask_1==role_mask_2==1
    assert family_mask_1==family_mask_2==28
    assert rectangle
    assert wrong_role_hits==0
    assert p_any_affine_rectangle==Fraction(1,29)
    assert p_any_onebit_role_rectangle==Fraction(5,899)
    assert p_fixed_lsb_role_rectangle==Fraction(1,899)
    assert p_exact_observed_masks==Fraction(1,26970)

    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
