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
    for name in ("signedness", "integer versus rational field layout",
                 "decimal literal lowering law",
                 "mixed-domain implicit coercion and general widening",
                 "multiplication and other-operation overflow policy"):
        need(name in policy.get("not_yet_ratified", []), "deferred law: " + name)
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
    ):
        need(needle in ratification, "contract: " + needle)
    for needle in (
        "(numeric-domains-peer-ratified",
        "(numeric-domain-natural-add-carry",
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
    print("NUMERIC-DOMAIN-RATIFICATION: PASS D24 D48 D96 D192 ... peer-of-D1-D9")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
