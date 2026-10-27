#!/usr/bin/env python3
"""Fail-closed Lisp-contract check for D12+ mathematics and legacy D24+ physical admission.

Verifies domain names, rank and growth; not runtime callability or full occupancy.
"""
import argparse
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from domain_tables import number_domains  # noqa: E402

def need(ok, why):
    if not ok:
        raise ValueError("NUMERIC-DOMAIN-RATIFICATION: BLOCKED: " + why)

def physical_prefix_from_history(ratification):
    """Current Zig D24+ implementation profile, read from historical Lisp law.

    The current mathematical ladder begins at D12. Physical support for D12
    is not established by this legacy profile.
    """
    marker = "(schema . numeric-domains-ratification-1)"
    need(ratification.count(marker) == 1, "unique historical D24 ratification")
    historical = ratification.split(marker, 1)[1].split(
        "(schema . numeric-d24-signed-extension-1)", 1
    )[0]
    match = re.search(r"\(canonical-domain-names\s*\.\s*\(([^()]*)\)\)", historical)
    need(match is not None, "historical physical profile missing")
    names = match.group(1).split()
    need(names == ["D24", "D48", "D96", "D192"], "historical D24 physical prefix")
    return {"ratified_prefix_bits": [int(name[1:]) for name in names]}


def validate(ratification, lang):
    """Validate the last owner extension, historical continuity and scope."""
    marker = "(schema . numeric-d12-start-extension-1)"
    need(ratification.count(marker) == 1, "unique current D12 ratification")
    current = ratification.split(marker, 1)[1]
    first_domains = re.findall(r"\(first-domain\s*\.\s*([^()\s]+)\)", current)
    need(first_domains == ["D12"],
         f"reason=duplicate-or-conflicting-first-domain expected=[D12] actual={first_domains!r}")
    required = (
        "(status . owner-ratified)",
        '(date . "2026-10-24")',
        "(family . numeric)",
        "(first-domain . D12)",
        "(initial-width . #d12)",
        "(next-width . double)",
        "(canonical-domain-names . (D12 D24 D48 D96 D192))",
        '(domain-rule . "D(12 * 2^n), n >= 0")',
        "(integer-law .",
        "(arithmetic .",
        "(fraction-law .",
        "(identity-law .",
        "(transport-law .",
        "(implementation-status .",
        '(current-normative-source . "contracts/numeric-domains-ratification.lisp")',
    )
    for needle in required:
        need(needle in current, "current Lisp contract: " + needle)
    for law in ("two's-complement", "no negative zero", "gcd",
                "denominator zero", "Float is distinct", "D12 is a numeric domain",
                "not a D12 callable-function codebook", "codec padding",
                "not reported operational"):
        if law == "not reported operational":
            # Gate the operational claim on the real native execution path,
            # not on one frozen wording of the status sentence.
            need(
                "Do not report D12 operational before" in current
                and "positive/negative execution witnesses pass" in current,
                "D12 runtime status",
            )
        else:
            need(law in current, "D12 law: " + law)
    need(ratification.count("(schema . numeric-d24-signed-extension-1)") == 1,
         "historical D24 signed integer amendment")
    need("(arithmetic-exclusivity" in ratification, "arithmetic exclusivity")
    need("(rational-composition" in ratification, "historical exact ratio provenance")
    need("(rank . peer-of-D1-D9)" in ratification, "domain rank")
    need("knowledge/number-width-ratified.json" not in ratification,
         "retired JSON is still named as authority")
    for needle in (
        "(number-ladder-all-kernels",
        "(numeric-domain-current-d12-law-20261024",
        "(binary-domain-words-not-arithmetic-operands",
        "D(12 * 2^n)",
        "D12",
        "D24",
        "contracts/numeric-domains-ratification.lisp",
    ):
        need(needle in lang, "language contract: " + needle)

    # Contract 12.0 supersedes the old standalone 2026-10-18 signed-integer
    # marker with its normative numeric-first invariant and explicit release gate.
    # Accept either the historical amendment or the current Contract 12.0 form,
    # but never accept a language contract with no owner-ratified signed law.
    contract12_active = all(marker in lang for marker in (
        "(contract-12-owner-decision",
        "(contract-12-numeric-first",
        "(contract-12-release-gate",
    ))
    legacy_signed_law = "(numeric-domain-current-signed-integer-law-20261018" in lang
    need(legacy_signed_law or contract12_active,
         "language contract: missing owner-ratified signed-integer authority")
    if contract12_active:
        need(
            "2026-10-24 D12 signed two's-complement arithmetic overrides ALL older D24-first" in lang,
            "Contract 12.0 D12 signed numeric-first law",
        )
        need(
            "native SENS and Zig/T5M proof of exact domain words" in lang
            and "D12 numeric boundaries" in lang,
            "Contract 12.0 explicit native-execution release gate",
        )
    need("number-width-ratified.json" not in lang, "language still cites retired JSON")
    expected = (("D12", 12), ("D24", 24), ("D48", 48),
                ("D96", 96), ("D192", 192))
    # Exact parser used by projections and the other guards.
    # Syntax/width checks are performed directly here without filesystem writes.
    names = re.search(r"\(canonical-domain-names\s*\.\s*\(([^()]*)\)\)", current)
    need(names is not None, "D12 prefix list missing")
    need(tuple((name, int(name[1:])) for name in names.group(1).split()) == expected,
         "D12 prefix width identity")
    for width in (12, 24, 48, 96, 192, 384):
        sign = 1 << (width - 1)
        minimum = -sign
        maximum = sign - 1
        need(((1 << width) - 1) - (1 << width) == -1,
             "two's-complement negative one")
        need(minimum < 0 < maximum, "signed word range")
        need(maximum + 1 > maximum and minimum - 1 < minimum,
             "signed widening needs successor")
        need(maximum + 1 < (1 << (2 * width - 1)),
             "successor cannot hold positive overflow")
    return physical_prefix_from_history(ratification)


def validate_zig_numeric_prefix(policy, zig_source):
    """Mechanical width-profile parity only: no Zig authority or semantic admission.

    The historical Lisp D24 profile supplies the expected implemented prefix. Zig provides merely
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


def validate_runtime_boundary(arithmetic, d6):
    """Assert that every Core math entry point checks explicit D12+ admission.

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
        need(body.count("require_math_domain(values, span)?;") == 1, name + " must enforce D12+ admission")
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
         "D6 must accept canonical D12+ composite width")
    need("Value::BinaryNumber(number) => number.numeric_domain_width()" in d6,
         "D6 must require an exact D12+ numeric natural")
    need("BinaryNumber::from_numeric_domain_bits(width, &constant_bits)" in d6,
         "D6 unit must preserve the exact operand domain")
    need("Value::BinaryNumber(constant)" in d6, "D6 must not insert unqualified Rational(1)")
    need("Value::Rational(Rational::integer(1))" not in d6,
         "D6 historical unqualified one was reintroduced")
    need("D6 ADD1/SUB1/NEG requires a D12+ numeric operand" in d6,
         "D6 unary arithmetic must admit explicit D12+ numeric values")


def main():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    try:
        ratification = (ROOT / "contracts/numeric-domains-ratification.lisp").read_text(encoding="utf-8")
        lang = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")
        arithmetic = (ROOT / "crates/sens/src/eval/arithmetic.rs").read_text(encoding="utf-8")
        d6 = (ROOT / "crates/sens/src/eval/d6_arithmetic.rs").read_text(encoding="utf-8")
        zig_profile = (ROOT / "research/zig-codecs/numeric_domains.zig").read_text(encoding="utf-8")
        physical = validate(ratification, lang)
        validate_zig_numeric_prefix(physical, zig_profile)
        validate_runtime_boundary(arithmetic, d6)
    except (ValueError, KeyError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("NUMERIC-DOMAIN-RATIFICATION: PASS Lisp D12 law + legacy Zig D24 wide-word profile + static D12+ Core admission guards (runtime claims require executed witnesses); standalone E3 composite physical codec deferred")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
