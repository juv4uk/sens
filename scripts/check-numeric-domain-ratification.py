#!/usr/bin/env python3
"""Core-only, fail-closed check for owner-ratified D24/D48/... peer domains.

Verifies domain names, rank and growth; not runtime callability or full occupancy.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def need(ok, why):
    if not ok:
        raise ValueError("NUMERIC-DOMAIN-RATIFICATION: BLOCKED: " + why)

def validate(policy, ratification, lang):
    need(policy.get("status") == "owner-ratified", "owner status")
    need(policy.get("domain_family") == "numeric", "family")
    need(policy.get("domain_rank") == "same-semantic-domain-rank-as-D1-D9", "domain rank")
    need(policy.get("domain_name_law") == "D(24 * 2^n), n >= 0", "name/growth law")
    need(policy.get("first_width_bits") == 24, "initial width")
    need(policy.get("growth_law") == "width(n) = 24 * 2^n", "width law")
    need(policy.get("no_literal_dependency") is True, "no literal dependency")
    need(policy.get("ratified_prefix_bits") == [24, 48, 96, 192], "prefix widths")
    need(policy.get("ratified_domains") == ["D24", "D48", "D96", "D192"], "peer domain names")
    for n in range(20):
        need(24 * (1 << (n + 1)) == 2 * (24 * (1 << n)), "doubling")
    need("D1-D8" in policy.get("separate_from", []), "function domain boundary")
    for name in ("two's-complement or other polarity encoding",
                 "integer versus rational field layout",
                 "decimal literal lowering law",
                 "mixed-domain implicit coercion and general widening",
                 "multiplication and other-operation overflow policy",
                 "binary opcode and production encoding for signed and rational compositions",
                 "signed and rational arithmetic runtime admission and conformance"):
        need(name in policy.get("not_yet_ratified", []), "deferred law: " + name)
    need("signedness" not in policy.get("not_yet_ratified", []), "NEG composition law must not be marked wholly deferred")
    extended = policy.get("extended_number_laws", {})
    need(extended.get("status") == "owner-ratified", "extended D24+ laws status")
    need(extended.get("no_new_domains") is True, "new domains forbidden")
    need(extended.get("no_reserved_natural_bits") is True, "natural Dn atom range must be preserved")
    need(extended.get("no_negative_zero") is True, "negative zero forbidden")
    need(extended.get("denominator_zero_is_error") is True, "denominator zero must fail")
    need(extended.get("rounding_forbidden") is True, "rational rounding forbidden")
    need("NEG(nonzero Dn magnitude)" in extended.get("sign", ""), "NEG positive magnitude law")
    need("gcd(abs(p),q)=1" in extended.get("rational", ""), "gcd canonical ratio law")
    need("q=1 collapses to integer" in extended.get("rational", ""), "unit denominator law")
    need("p=0 collapses" in extended.get("rational", ""), "zero numerator law")
    need(extended.get("binary_composition_opcode") == "deferred", "binary opcode still deferred")
    need(extended.get("wire_fasl_and_physical_encoding") == "deferred", "composite wire layout still deferred")
    need(extended.get("callability_and_signed_rational_arithmetic") == "deferred", "signed/rational runtime still deferred")
    addition = policy.get("addition_widening", {})
    need(addition.get("status") == "owner-ratified", "addition promotion status")
    need(addition.get("required_successor") == "D(2n)", "addition successor")
    need(addition.get("max_sum_bits") == "n+1", "addition carry upper bound")
    need(addition.get("no_wraparound") is True, "addition carry must not wrap")
    need(addition.get("no_unqualified_number_identity") is True, "unqualified result is forbidden")
    for width in (24, 48, 96, 192, 384):
        full = (1 << width) - 1
        summed = full + full
        need(summed.bit_length() == width + 1, "full-width addition loses carry")
        next_width = 2 * width
        need(summed < (1 << next_width), "next admitted domain cannot carry exact sum")
        need(summed >= (1 << width), "overflow must be detected")
    need(((1 << 24) - 2) + 1 < (1 << 24), "non-overflow example unexpectedly widened")
    for needle in (
        "(schema . numeric-domains-ratification/1)",
        "(status . owner-ratified)", "(family . numeric)",
        "(rank . peer-of-D1-D9)", "(first-domain . D24)",
        "(initial-width . #d24)", "(next-width . double)",
        "(canonical-domain-names . (D24 D48 D96 D192))",
        '(domain-rule . "D(24 * 2^n), n >= 0")',
        "(same-domain-natural-addition", "(add-carry-preservation",
        "(addition-bridge-scope",
        "(base-natural-occupancy", "(signed-composition", "(rational-composition",
        "(composite-identity", "(canonicalization",
    ):
        need(needle in ratification, "contract: " + needle)
    for needle in (
        "(numeric-domains-peer-ratified",
        "(numeric-domain-natural-add-carry",
        "(numeric-domain-signed-reduced-ratio-composition",
        "D24, D48, D96, D192",
        "contracts/numeric-domains-ratification.lisp",
        "ontological domain rank",
        "Cross-domain reuse requires an explicit independently proved bridge law",
    ):
        need(needle in lang, "language: " + needle)

def selftest(policy, ratification, lang):
    validate(policy, ratification, lang)
    edits = [
        ({"ratified_domains": ["Number24", "D48", "D96", "D192"]}, "peer domain names"),
        ({"ratified_prefix_bits": [24, 48, 96, 193]}, "prefix widths"),
        ({"domain_rank": "storage-only"}, "domain rank"),
        ({"no_literal_dependency": False}, "no literal dependency"),
        ({"not_yet_ratified": []}, "deferred law"),
        ({"addition_widening": {"status": "research"}}, "addition promotion status"),
        ({"addition_widening": dict(policy["addition_widening"], no_wraparound=False)}, "addition carry must not wrap"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], no_reserved_natural_bits=False)}, "natural Dn atom range must be preserved"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], no_negative_zero=False)}, "negative zero forbidden"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], denominator_zero_is_error=False)}, "denominator zero must fail"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], rational="not reduced")}, "gcd canonical ratio law"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], wire_fasl_and_physical_encoding="unconditionally executable")}, "composite wire layout still deferred"),
    ]
    for change, why in edits:
        try:
            validate(dict(policy, **change), ratification, lang)
        except ValueError as exc:
            need(why in str(exc), "unexpected negative witness: " + str(exc))
        else:
            raise ValueError("invalid ratification admitted: " + repr(change))
    for damaged in (
        ratification.replace("(first-domain . D24)", "(first-domain . Number24)"),
        ratification.replace("(rank . peer-of-D1-D9)", "(rank . storage-only)"),
    ):
        try:
            validate(policy, damaged, lang)
        except ValueError:
            continue
        raise ValueError("invalid ratification contract admitted")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        policy = json.loads((ROOT / "knowledge/number-width-ratified.json").read_text(encoding="utf-8"))
        ratification = (ROOT / "contracts/numeric-domains-ratification.lisp").read_text(encoding="utf-8")
        lang = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")
        (selftest if args.self_test else validate)(policy, ratification, lang)
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("NUMERIC-DOMAIN-RATIFICATION: PASS D24+ full-natural atoms, NEG/RATIO composition laws and carry-safe ADD; signed/rational runtime deferred")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
