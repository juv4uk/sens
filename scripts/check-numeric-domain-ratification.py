#!/usr/bin/env python3
"""Core-only, fail-closed check for owner-ratified D24/D48/... peer domains.

Verifies domain names, rank and growth; not runtime callability or full occupancy.
"""
import argparse
import json
import re
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
    for name in ("integer versus rational field layout",
                 "decimal literal lowering law",
                 "mixed-domain implicit coercion and general widening",
                 "overflow for other operations beyond same-domain natural ADD/MUL",
                 "binary opcode and production encoding for signed and rational compositions",
                 "canonical physical NEG/RATIO composition reader and transport and source macro projection"):
        need(name in policy.get("not_yet_ratified", []), "deferred law: " + name)
    need("signedness" not in policy.get("not_yet_ratified", []), "NEG composition law must not be marked wholly deferred")
    signed = policy.get("current_integer_extension", {})
    need(signed.get("status") == "owner-ratified", "current signed-integer extension status")
    need(signed.get("date") == "2026-10-18", "current signed-integer extension date")
    need(signed.get("supersedes_2026_10_11_integer_polarity") is True,
         "2026-10-11 unsigned integer polarity must be historical")
    need(signed.get("supersedes_2026_10_11_integer_word_and_arithmetic_interpretation") is True,
         "2026-10-11 natural-word interpretation must be historical")
    need(signed.get("encoding", "").startswith("For an exact n-bit Dn word u"), "two's-complement encoding")
    need("-2^(n-1)..2^(n-1)-1" in signed.get("range", ""), "signed range")
    need(signed.get("every_word_has_one_integer") is True, "one integer per Dn word")
    need(signed.get("has_negative_zero") is False, "no negative zero")
    need("widen" in signed.get("same_domain_arithmetic", ""), "signed overflow widening")
    need("unsigned numerator magnitude" in signed.get("fractions", ""),
         "existing exact fraction composition remains unchanged")
    need("opaque exact-width transport" in signed.get("t5m", "").lower(), "T5M remains opaque transport")
    extended = policy.get("extended_number_laws", {})
    need(extended.get("status") == "owner-ratified", "extended D24+ laws status")
    need(extended.get("no_new_domains") is True, "new domains forbidden")
    need(extended.get("no_negative_zero") is True, "negative zero forbidden")
    need(extended.get("denominator_zero_is_error") is True, "denominator zero must fail")
    need(extended.get("rounding_forbidden") is True, "rational rounding forbidden")
    need("gcd(abs(p),q)=1" in extended.get("rational", ""), "gcd canonical ratio law")
    need("q=1 collapses to integer" in extended.get("rational", ""), "unit denominator law")
    need("p=0 collapses" in extended.get("rational", ""), "zero numerator law")
    need(extended.get("binary_composition_opcode") == "deferred", "binary opcode still deferred")
    need(extended.get("wire_fasl_and_physical_encoding") == "deferred", "composite wire layout still deferred")
    need("Core-executable" in extended.get("callability_and_signed_rational_arithmetic", ""), "signed/rational Core runtime must execute")
    natural = policy.get("natural_arithmetic", {})
    need(natural.get("date") == "2026-10-11", "natural arithmetic source")
    need("same Dn" in natural.get("scope", ""), "same-domain operand scope")
    need("D(2n)" in natural.get("mul", ""), "multiplication result domain")
    need("if a>=b" in natural.get("sub", ""), "subtraction nonnegative guard")
    need("a=b*q+r" in natural.get("div_rem", ""), "Euclidean division identity")
    need(natural.get("no_implicit_mixed_domain_coercion") is True, "mixed domain must fail closed")
    need(natural.get("no_rounding_or_wraparound") is True, "no rounding/wraparound")
    need("Core-executable" in natural.get("signed_and_rational_runtime", ""), "signed/rational Core Value must execute")
    composite = policy.get("numeric_composition_runtime", {})
    need("Core-executable" in composite.get("status", ""), "composite Core runtime status")
    need(composite.get("physical_composite_codec") == "deferred", "physical composite codec remains deferred")
    need(composite.get("unqualified_or_mixed_numeric_coercion") is False, "no numeric domain coercion")
    need(composite.get("float_rounding") is False, "exact rational no floats")
    need("smallest" in composite.get("domain_growth", ""), "explicit rational result width growth")
    for n in (24, 48, 96, 192, 384):
        biggest = (1 << n)-1
        full_product = biggest*biggest
        need(full_product.bit_length() == 2*n, "full-width multiplication lost bits")
        need(full_product < 1<<(2*n), "D(2n) product capacity")
        need(biggest-biggest == 0, "exact subtraction")
        need(biggest == (biggest//3)*3 + (biggest%3), "Euclidean quotient remainder")
        signed_max = (1 << (n - 1)) - 1
        signed_min = -(1 << (n - 1))
        positive_overflow = signed_max + 1
        negative_overflow = signed_min - 1
        need(not signed_min <= positive_overflow <= signed_max,
             "signed positive boundary must exceed Dn")
        need(not signed_min <= negative_overflow <= signed_max,
             "signed negative boundary must exceed Dn")
        successor_min, successor_max = -(1 << (2 * n - 1)), (1 << (2 * n - 1)) - 1
        need(successor_min <= positive_overflow <= successor_max,
             "positive boundary must fit the next D24+ rung")
        need(successor_min <= negative_overflow <= successor_max,
             "negative boundary must fit the next D24+ rung")
        # Signed Dn is a two's-complement integer, not the old unsigned
        # interpretation of the same transport bits. This checks the
        # owner-ratified bit law; it does NOT execute the SENS math runtime.
        sign_bit, word_modulus = 1 << (n - 1), 1 << n
        signed_witnesses = (
            (0, 0),
            (1, 1),
            (sign_bit - 1, signed_max),
            (sign_bit, signed_min),
            (word_modulus - 1, -1),
        )
        for raw_word, expected_value in signed_witnesses:
            actual_value = (
                raw_word if raw_word < sign_bit else raw_word - word_modulus
            )
            need(actual_value == expected_value, "D24+ signed word interpretation")
            need(actual_value % word_modulus == raw_word,
                 "D24+ two's-complement roundtrip lost exact bits")
        need(-signed_min > signed_max,
             "minimum-negative magnitude cannot be positive in the same Dn")

    transport = policy.get("numeric_composition_transport", {})
    need("Core-only" in transport.get("status", ""), "transport is Core-only")
    need(transport.get("confirmed_domains") == [24,48,96,192,384], "numeric frame tested domains")
    need(transport.get("old_natural_frame_stable") is True, "legacy natural frame stability")
    need(transport.get("legacy_unqualified_number_not_implicitly_admitted") is True, "unqualified numeric no admission")
    need("deferred" in transport.get("physical_t5_program_numeric_composites", ""), "T5 physical composition boundary")
    need("deferred" in transport.get("ast_fasl_wire_expression_composites", ""), "FASL/AST numeric composition boundary")
    need("PackedBitstream" in transport.get("physical_bytes", ""), "existing packed byte transport")
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
        "(schema . numeric-domains-ratification-1)",
        "(schema . numeric-d24-signed-extension-1)",
        "(status . owner-ratified)", "(family . numeric)",
        "(rank . peer-of-D1-D9)", "(first-domain . D24)",
        "(initial-width . #d24)", "(next-width . double)",
        "(canonical-domain-names . (D24 D48 D96 D192))",
        '(domain-rule . "D(24 * 2^n), n >= 0")',
        "(same-domain-natural-addition", "(add-carry-preservation",
        "(addition-bridge-scope",
        "(same-domain-natural-multiplication", "(same-domain-natural-subtraction",
        "(same-domain-natural-division",
        "(numeric-composition-runtime", "(composite-growth",
        "(base-natural-occupancy", "(signed-composition", "(rational-composition",
        "(composite-identity", "(canonicalization",
        "(arithmetic-exclusivity",
    ):
        need(needle in ratification, "contract: " + needle)
    for needle in (
        "(numeric-domain-current-signed-integer-law-20261018",
        "(numeric-domains-peer-ratified",
        "(numeric-domain-natural-add-carry",
        "(numeric-domain-natural-mul-sub-exact-div",
        "(numeric-domain-signed-reduced-ratio-composition",
        "(numeric-domain-composition-runtime",
        "(binary-domain-words-not-arithmetic-operands",
        "D24, D48, D96, D192",
        "contracts/numeric-domains-ratification.lisp",
        "ontological domain rank",
        "Cross-domain reuse requires an explicit independently proved bridge law",
    ):
        need(needle in lang, "language: " + needle)


def validate_zig_numeric_prefix(policy, zig_source):
    """Mechanical width-profile parity only: no Zig authority or semantic admission.

    The SENS-ratified JSON supplies the expected prefix. Zig provides merely
    opaque fixed-width transport support for the listed four rungs.
    """
    declarations = re.findall(r"\bWIDE_WIDTHS\s*=", zig_source)
    need(len(declarations) == 1, "Zig WIDE_WIDTHS must have one declaration")
    match = re.search(
        r"(?m)^[ \t]*pub[ \t]+const[ \t]+WIDE_WIDTHS[ \t]*="
        r"[ \t]*\[_\]u16[ \t]*\{(?P<cells>[^{}]*)\}[ \t]*;",
        zig_source,
    )
    need(match is not None, "Zig WIDE_WIDTHS has no explicit u16 literal profile")
    cells = re.sub(r"//[^\n]*", "", match.group("cells"))
    parts = [part.strip() for part in cells.split(",")]
    if parts and not parts[-1]:
        parts.pop()
    need(bool(parts) and all(re.fullmatch(r"(?:0|[1-9][0-9]*)", part)
                                 for part in parts),
         "Zig WIDE_WIDTHS must contain literal physical widths")
    widths = [int(part) for part in parts]
    need(widths == policy["ratified_prefix_bits"],
         f"Zig physical prefix {widths} differs from SENS-ratified {policy['ratified_prefix_bits']}")


def selftest_zig_numeric_prefix(policy, zig_source):
    validate_zig_numeric_prefix(policy, zig_source)
    match = re.search(
        r"(?m)^[ \t]*pub[ \t]+const[ \t]+WIDE_WIDTHS[ \t]*="
        r"[ \t]*\[_\]u16[ \t]*\{(?P<cells>[^{}]*)\}[ \t]*;",
        zig_source,
    )
    need(match is not None, "Zig numeric witness declaration missing")
    original = match.group("cells")
    expected = policy["ratified_prefix_bits"]
    variants = (
        zig_source.replace("pub const WIDE_WIDTHS", "pub const OTHER_WIDTHS", 1),
        zig_source[:match.start("cells")] + ", ".join(map(str, [expected[0] + 1, *expected[1:]]))
        + zig_source[match.end("cells"):],
        zig_source[:match.start("cells")] + original.rstrip() + ", 384 "
        + zig_source[match.end("cells"):],
        zig_source + "\npub const WIDE_WIDTHS = [_]u16{ 24 };\n",
    )
    for index, damaged in enumerate(variants):
        try:
            validate_zig_numeric_prefix(policy, damaged)
        except ValueError:
            continue
        raise ValueError(f"NUMERIC-DOMAIN-RATIFICATION: Zig mutant {index} was admitted")

def validate_runtime_boundary(arithmetic, d6):
    """Assert that every Core math entry point checks explicit D24+ admission.

    This is a static CI backstop; behavioral Rust integration witnesses are
    crates/sens/tests/math_domain_exclusivity.rs. Never count a text check as
    proof that those runtime tests have actually executed.
    """
    spans = (
        ("arithmetic_on_values", "pub(super) fn arithmetic_on_values(", "pub(super) fn division_on_values("),
        ("division_on_values", "pub(super) fn division_on_values(", "pub(super) fn comparison_on_values("),
        ("comparison_on_values", "pub(super) fn comparison_on_values(", "#[cfg(test)]"),
    )
    for name, start, end in spans:
        need(arithmetic.count(start) == 1, name + " entry missing or duplicated")
        tail = arithmetic.split(start, 1)[1]
        need(end in tail, name + " next boundary missing")
        body = tail.split(end, 1)[0]
        need(body.count("require_math_domain(values, span)?;") == 1, name + " must enforce D24+ admission")
    need("!domain_numeric::is_domain_value(value)" in arithmetic, "unqualified/functional values must be refused")
    # Historical Number/Rational/floating point branches were removed from the
    # mathematical evaluator. Reader and JSON presentation may still retain
    # legacy data, but the Core arithmetic source may not gain a second path.
    for legacy in (
        "small_rational_fast_path",
        "numeric_value(",
        "enum Numeric",
        "if values.iter().any(domain_numeric::is_domain_value)",
        "if values.iter().any(|value| matches!(value, Value::BinaryNumber(_)))",
    ):
        need(legacy not in arithmetic, "legacy literal math path returned: " + legacy)
    need("values.is_empty()" in arithmetic, "no zero-arity generic Number operations")
    need("Value::NumericComposition(composition) => Some(composition.domain_width())" in d6,
         "D6 must accept canonical D24+ composite width")
    need("Value::BinaryNumber(number) => number.numeric_domain_width()" in d6,
         "D6 must require an exact D24+ numeric natural")
    need("BinaryNumber::from_numeric_domain_bits(width, &constant_bits)" in d6,
         "D6 unit must preserve the exact operand domain")
    need("Value::BinaryNumber(constant)" in d6, "D6 must not insert unqualified Rational(1)")
    need("Value::Rational(Rational::integer(1))" not in d6,
         "D6 historical unqualified one was reintroduced")


def selftest_runtime(arithmetic, d6):
    validate_runtime_boundary(arithmetic, d6)
    for damaged in (
        arithmetic.replace("require_math_domain(values, span)?;", "", 1),
        arithmetic.replace("!domain_numeric::is_domain_value(value)", "false", 1),
        arithmetic + "\nfn small_rational_fast_path() {}\n",
    ):
        try:
            validate_runtime_boundary(damaged, d6)
        except ValueError:
            pass
        else:
            raise ValueError("NUMERIC-DOMAIN-RATIFICATION: invalid runtime boundary admitted")
    try:
        validate_runtime_boundary(arithmetic, d6.replace(
            "Value::BinaryNumber(constant)", "Value::Rational(Rational::integer(1))", 1))
    except ValueError:
        pass
    else:
        raise ValueError("NUMERIC-DOMAIN-RATIFICATION: unqualified D6 unit admitted")


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
        ({"current_integer_extension": dict(policy["current_integer_extension"], encoding="unsigned")}, "two's-complement encoding"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], no_negative_zero=False)}, "negative zero forbidden"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], denominator_zero_is_error=False)}, "denominator zero must fail"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], rational="not reduced")}, "gcd canonical ratio law"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], wire_fasl_and_physical_encoding="unconditionally executable")}, "composite wire layout still deferred"),
        ({"natural_arithmetic": dict(policy["natural_arithmetic"], mul="truncate high bits")}, "multiplication result domain"),
        ({"natural_arithmetic": dict(policy["natural_arithmetic"], no_rounding_or_wraparound=False)}, "no rounding/wraparound"),
        ({"natural_arithmetic": dict(policy["natural_arithmetic"], signed_and_rational_runtime="disabled")}, "signed/rational Core Value must execute"),
        ({"numeric_composition_runtime": dict(policy["numeric_composition_runtime"], physical_composite_codec="complete")}, "physical composite codec remains deferred"),
        ({"numeric_composition_runtime": dict(policy["numeric_composition_runtime"], float_rounding=True)}, "exact rational no floats"),
        ({"numeric_composition_transport": dict(policy["numeric_composition_transport"], physical_t5_program_numeric_composites="complete")}, "T5 physical composition boundary"),
        ({"numeric_composition_transport": dict(policy["numeric_composition_transport"], old_natural_frame_stable=False)}, "legacy natural frame stability"),
        ({"numeric_composition_runtime": dict(policy["numeric_composition_runtime"], status="research")}, "composite Core runtime status"),
        ({"extended_number_laws": dict(policy["extended_number_laws"], callability_and_signed_rational_arithmetic="deferred")}, "signed/rational Core runtime must execute"),
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
        arithmetic = (ROOT / "crates/sens/src/eval/arithmetic.rs").read_text(encoding="utf-8")
        d6 = (ROOT / "crates/sens/src/eval/d6_arithmetic.rs").read_text(encoding="utf-8")
        zig_profile = (ROOT / "research/zig-codecs/numeric_domains.zig").read_text(encoding="utf-8")
        (selftest if args.self_test else validate)(policy, ratification, lang)
        (selftest_zig_numeric_prefix if args.self_test else validate_zig_numeric_prefix)(
            policy, zig_profile)
        (selftest_runtime if args.self_test else validate_runtime_boundary)(arithmetic, d6)
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("NUMERIC-DOMAIN-RATIFICATION: PASS contract + Zig physical width-prefix parity + static D24+-only Core entry guards (Rust/Zig runtime execution requires separate tests); composite physical codec deferred")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
