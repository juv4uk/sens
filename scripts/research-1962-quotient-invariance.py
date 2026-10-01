#!/usr/bin/env python3
"""#1962 research-only witness: quotient aliases + helper-refactoring invariance.

This script is deliberately tiny. It does not allocate codes or define language
authority. It tests two candidate laws from the #1962 beauty filter:

1. semantic aliases collapse before addressing;
2. a harmless helper name does not change normalized semantic form/cost.
"""

from __future__ import annotations

from collections import defaultdict

# Existing selector-path evidence from #1962.
SELECTOR_PATHS = {
    "second": "1011",      # CADR
    "cadr": "1011",
    "fourth": "101111",    # CADDDR
    "cadddr": "101111",
}

PRIMITIVES = {"car", "cdr"}


def quotient_by_path(named_paths):
    """Group spellings by already-proven canonical selector path."""
    classes = defaultdict(list)
    for name, path in named_paths.items():
        classes[path].append(name)
    return {path: tuple(sorted(names)) for path, names in sorted(classes.items())}


def substitute_arg(term, arg):
    """Substitute the single helper parameter marker $0."""
    if term == "$0":
        return arg
    if isinstance(term, tuple):
        fn, child = term
        return (fn, substitute_arg(child, arg))
    return term


def normalize(term, helpers):
    """Inline helper names until only the primitive semantic term remains."""
    if isinstance(term, str):
        return term

    fn, arg = term
    normalized_arg = normalize(arg, helpers)

    if fn in helpers:
        expanded = substitute_arg(helpers[fn], normalized_arg)
        return normalize(expanded, helpers)

    return (fn, normalized_arg)


def primitive_cost(term):
    """Count primitive selector steps after helper erasure."""
    if isinstance(term, str):
        return 0
    fn, arg = term
    return (1 if fn in PRIMITIVES else 0) + primitive_cost(arg)


def main():
    classes = quotient_by_path(SELECTOR_PATHS)

    assert classes["1011"] == ("cadr", "second")
    assert classes["101111"] == ("cadddr", "fourth")
    assert len(SELECTOR_PATHS) == 4
    assert len(classes) == 2

    direct = ("car", ("cdr", "x"))

    helpers_a = {"tail": ("cdr", "$0")}
    factored_a = ("car", ("tail", "x"))

    # Same helper semantics under a completely different spelling.
    helpers_b = {"q": ("cdr", "$0")}
    factored_b = ("car", ("q", "x"))

    canonical = normalize(direct, {})
    canonical_a = normalize(factored_a, helpers_a)
    canonical_b = normalize(factored_b, helpers_b)

    assert canonical == ("car", ("cdr", "x"))
    assert canonical_a == canonical
    assert canonical_b == canonical

    cost = primitive_cost(canonical)
    assert cost == 2
    assert primitive_cost(canonical_a) == cost
    assert primitive_cost(canonical_b) == cost

    print("quotient classes:")
    for path, names in classes.items():
        print(f"  {path}: {', '.join(names)}")

    print()
    print("refactoring fixture:")
    print(f"  direct:       {direct}")
    print(f"  helper tail:  {factored_a} -> {canonical_a}")
    print(f"  helper q:     {factored_b} -> {canonical_b}")
    print(f"  primitive cost: {cost}")
    print()
    print("PASS: alias spelling and harmless helper naming do not change canonical identity/cost.")
    print("Research-only: this proves the fixture, not a global allocation law.")


if __name__ == "__main__":
    main()
