#!/usr/bin/env python3
"""#3420 — axiom-basis minimality / hidden-premise probe.

This is a research witness, not semantic authority.

It checks:
1. bounded exact-Q closure from candidate mathematical seed constants using
   exact current D5 arithmetic function numbers;
2. which subsets of {-1,0,1} are actually sufficient for the required seed
   closure under the declared operation set;
3. source-level dependency of current lib/si-derived.lisp entries on the
   seven exact SI defining constants, including remove-one impact.

No float is used.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations
from pathlib import Path
import json
import re


ROOT = Path(__file__).resolve().parents[2]

D5_OPS = {
    "01010": "PLUS",
    "01011": "DIFFERENCE",
    "10110": "TIMES",
    "10111": "QUOTIENT",
}

REQUIRED = {
    Fraction(-2), Fraction(-1), Fraction(-1, 2),
    Fraction(0), Fraction(1, 2), Fraction(1), Fraction(2),
}

WORLD_ROOTS = {
    "delta_nu_cs": "si:cesium-frequency",
    "c": "si:speed-of-light",
    "h": "si:planck-constant",
    "e": "si:elementary-charge",
    "k": "si:boltzmann-constant",
    "N_A": "si:avogadro-constant",
    "K_cd": "si:luminous-efficacy",
}

DEFINING_NAMES = {
    "delta_nu_cs": "si:defining-cesium-frequency",
    "c": "si:defining-speed-of-light",
    "h": "si:defining-planck-constant",
    "e": "si:defining-elementary-charge",
    "k": "si:defining-boltzmann-constant",
    "N_A": "si:defining-avogadro-constant",
    "K_cd": "si:defining-luminous-efficacy",
}


def apply(bits: str, a: Fraction, b: Fraction) -> Fraction | None:
    if bits == "01010":
        return a + b
    if bits == "01011":
        return a - b
    if bits == "10110":
        return a * b
    if bits == "10111":
        return None if b == 0 else a / b
    raise AssertionError(bits)


def bounded_closure(
    seeds: tuple[int, ...],
    rounds: int = 4,
    numerator_bound: int = 16,
    denominator_bound: int = 16,
) -> tuple[dict[Fraction, dict], int]:
    known: dict[Fraction, dict] = {
        Fraction(x): {"status": "AXIOM", "depth": 0, "value": str(Fraction(x))}
        for x in seeds
    }
    undefined = 0

    for depth in range(1, rounds + 1):
        values = list(known)
        new: dict[Fraction, dict] = {}
        for a in values:
            for b in values:
                for bits, name in D5_OPS.items():
                    out = apply(bits, a, b)
                    if out is None:
                        undefined += 1
                        continue
                    if abs(out.numerator) > numerator_bound or out.denominator > denominator_bound:
                        continue
                    if out in known or out in new:
                        continue
                    new[out] = {
                        "status": "DERIVED",
                        "depth": depth,
                        "value": str(out),
                        "function_bits": bits,
                        "function_projection": name,
                        "inputs": [str(a), str(b)],
                    }
        known.update(new)
        if not new:
            break

    return known, undefined


def all_seed_subsets() -> list[dict]:
    base = (-1, 0, 1)
    rows = []
    for size in range(1, len(base) + 1):
        for subset in combinations(base, size):
            known, undefined = bounded_closure(subset)
            sufficient = REQUIRED.issubset(known)
            rows.append({
                "seeds": list(subset),
                "seed_count": len(subset),
                "sufficient_for_required_closure": sufficient,
                "derived_count": sum(v["status"] == "DERIVED" for v in known.values()),
                "known_count": len(known),
                "undefined_branches": undefined,
                "required_depths": {
                    str(x): known[x]["depth"] if x in known else None
                    for x in sorted(REQUIRED)
                },
            })
    return rows


def strip_comments(text: str) -> str:
    return "\n".join(line.split(";", 1)[0] for line in text.splitlines())


def top_level_forms(text: str) -> list[str]:
    text = strip_comments(text)
    forms = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0 and start is not None:
                forms.append(text[start:i + 1])
                start = None
        if depth < 0:
            raise AssertionError("unbalanced close paren")
    if depth != 0:
        raise AssertionError("unbalanced open paren")
    return forms


def form_name(form: str) -> str | None:
    m = re.match(r"\(\s*[^\s()]+\s+([^\s()]+)", form)
    return None if m is None else m.group(1)


def world_dependency_report() -> dict:
    si = (ROOT / "lib" / "si.lisp").read_text(encoding="utf-8")
    derived = (ROOT / "lib" / "si-derived.lisp").read_text(encoding="utf-8")

    for defining in DEFINING_NAMES.values():
        assert defining in si, f"missing defining axiom record {defining}"

    roots = set(WORLD_ROOTS.values())
    dependency_by_derived: dict[str, list[str]] = {}

    for form in top_level_forms(derived):
        name = form_name(form)
        if not name or not name.startswith("si:"):
            continue
        deps = sorted(root for root in roots if root in form)
        dependency_by_derived[name] = deps

    assert len(dependency_by_derived) == 7, dependency_by_derived

    remove_one = {}
    for axiom_id, root in WORLD_ROOTS.items():
        affected = sorted(
            name for name, deps in dependency_by_derived.items()
            if root in deps
        )
        remove_one[axiom_id] = {
            "root_symbol": root,
            "affected_derived_count": len(affected),
            "affected_derived": affected,
            "current_corpus_status": "EXERCISED" if affected else "UNEXERCISED",
        }

    # Current corpus expectations, derived from lib/si-derived.lisp structure.
    assert remove_one["h"]["affected_derived_count"] == 5
    assert remove_one["e"]["affected_derived_count"] == 5
    assert remove_one["k"]["affected_derived_count"] == 1
    assert remove_one["N_A"]["affected_derived_count"] == 3
    assert remove_one["delta_nu_cs"]["affected_derived_count"] == 0
    assert remove_one["c"]["affected_derived_count"] == 0
    assert remove_one["K_cd"]["affected_derived_count"] == 0

    return {
        "defining_axiom_count": len(WORLD_ROOTS),
        "derived_entry_count": len(dependency_by_derived),
        "dependency_by_derived": dependency_by_derived,
        "remove_one": remove_one,
        "unexercised_world_axioms": sorted(
            axiom for axiom, row in remove_one.items()
            if row["current_corpus_status"] == "UNEXERCISED"
        ),
    }


def main() -> None:
    subset_rows = all_seed_subsets()
    sufficient = [r for r in subset_rows if r["sufficient_for_required_closure"]]
    min_size = min(r["seed_count"] for r in sufficient)
    minimal = [r["seeds"] for r in sufficient if r["seed_count"] == min_size]

    # Under CURRENT four D5 arithmetic operations, both {-1} and {1} are
    # sufficient singleton seeds; {0} is not.
    assert min_size == 1
    assert [-1] in minimal
    assert [1] in minimal
    assert [0] not in minimal

    minus_one_closure, _ = bounded_closure((-1,))
    assert minus_one_closure[Fraction(1)]["status"] == "DERIVED"
    assert minus_one_closure[Fraction(0)]["status"] == "DERIVED"
    assert minus_one_closure[Fraction(2)]["status"] == "DERIVED"
    assert minus_one_closure[Fraction(1, 2)]["status"] == "DERIVED"

    world = world_dependency_report()

    report = {
        "issue": "#3420",
        "classification": "BOUNDED AXIOM-BASIS / HIDDEN-PREMISE PROBE",
        "function_numbers": D5_OPS,
        "required_seed_closure": [str(x) for x in sorted(REQUIRED)],
        "mathematical_basis": {
            "candidate_seeds": [-1, 0, 1],
            "subset_results": subset_rows,
            "minimum_seed_count_under_current_D5_ops": min_size,
            "minimal_singleton_seeds_under_current_D5_ops": minimal,
            "important_boundary": (
                "This minimality is relative to the admitted operation set. "
                "If DIFFERENCE/QUOTIENT are themselves derived rather than roots, "
                "the constant basis must be recomputed to avoid circularity."
            ),
        },
        "world_basis": world,
        "world_application_gap": (
            "delta_nu_cs, c and K_cd have no consumers in current lib/si-derived.lisp; "
            "they are not thereby redundant. They need separate MODEL_LAW / observation "
            "witnesses to exercise their world-knowledge role."
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
