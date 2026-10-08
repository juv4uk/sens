#!/usr/bin/env python3
from fractions import Fraction
import json

SELECTORS = {
    "D3": {
        "011": "CDR",
        "100": "CAR",
    },
    "D4": {
        "0110": "CDAR",
        "0111": "CDDR",
        "1000": "CAAR",
        "1001": "CADR",
    },
    "D5": {
        "01100": "CDAAR",
        "01101": "CDADR",
        "01110": "CDDAR",
        "01111": "CDDDR",
        "10000": "CAAAR",
        "10001": "CAADR",
        "10010": "CADAR",
        "10011": "CADDR",
    },
}

SEMANTIC_DUAL = {
    "CDR": "CAR",
    "CAR": "CDR",
    "CDAR": "CADR",
    "CADR": "CDAR",
    "CDDR": "CAAR",
    "CAAR": "CDDR",
    "CDAAR": "CADDR",
    "CADDR": "CDAAR",
    "CDADR": "CADAR",
    "CADAR": "CDADR",
    "CDDAR": "CAADR",
    "CAADR": "CDDAR",
    "CDDDR": "CAAAR",
    "CAAAR": "CDDDR",
}

def falling_odd_product(n, pairs):
    out = 1
    for i in range(pairs):
        out *= n - (2*i + 1)
    return out

rows=[]
xor1_fail=0
msb_fail=0
for domain, residents in SELECTORS.items():
    w=int(domain[1:])
    mask=(1<<w)-1
    by_value={int(bits,2):(bits,name) for bits,name in residents.items()}
    by_name={name:(bits,int(bits,2)) for bits,name in residents.items()}
    for bits,name in residents.items():
        x=int(bits,2)
        y=x ^ mask
        target_bits,target_name=by_value[y]
        expected=SEMANTIC_DUAL[name]
        match=(target_name==expected)
        involutive=((y ^ mask)==x)
        xor1_target=by_value.get(x^1)
        xor1_ok=(xor1_target is not None and xor1_target[1]==expected)
        msb_target=by_value.get(x^(1<<(w-1)))
        msb_ok=(msb_target is not None and msb_target[1]==expected)
        xor1_fail += (not xor1_ok)
        msb_fail += (not msb_ok)
        rows.append({
            "domain":domain,
            "bits":bits,
            "resident":name,
            "semantic_dual":expected,
            "coordinate_dual_bits":target_bits,
            "coordinate_dual_resident":target_name,
            "match":match,
            "involutive":involutive,
            "xor1_negative_control_match":xor1_ok,
            "msb_only_negative_control_match":msb_ok,
        })

pair_counts={"D3":1,"D4":2,"D5":4}
space_sizes={"D3":8,"D4":16,"D5":32}
per_domain={}
combined=Fraction(1,1)
for d,k in pair_counts.items():
    p=Fraction(1,falling_odd_product(space_sizes[d],k))
    per_domain[d]={"fraction":f"{p.numerator}/{p.denominator}","decimal":float(p)}
    combined*=p

report={
    "authority":"#3331",
    "issue":"#3345",
    "law":"dual_w(x)=x XOR (2^w-1)",
    "semantic_law":"toggle CAR<->CDR at every selector choice",
    "tested_residents":len(rows),
    "semantic_matches":sum(r["match"] for r in rows),
    "involution_matches":sum(r["involutive"] for r in rows),
    "xor1_negative_control_failures":xor1_fail,
    "msb_only_negative_control_failures":msb_fail,
    "rows":rows,
    "anti_numerology":{
        "per_domain_random_pairing_probability":per_domain,
        "combined_all_D3_D5_selector_pairs":{
            "fraction":f"{combined.numerator}/{combined.denominator}",
            "decimal":float(combined),
        }
    },
    "classification":"PROVED-BOUNDED-HOMOMORPHISM",
    "scope":"current ratified selector family D3-D5 only",
}
assert len(rows)==14
assert report["semantic_matches"]==14
assert report["involution_matches"]==14
assert xor1_fail==14
assert msb_fail==14
assert combined==Fraction(1,828316125)
print(json.dumps(report,indent=2,sort_keys=True))
