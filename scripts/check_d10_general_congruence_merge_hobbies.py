#!/usr/bin/env python3
"""Research ONLY: exact generalized congruence merging and conflict evidence.

Not a SENS resident, encoding, D10 slot, or authority to publish .sens.
Primary donors: SymPy solve_congruence and SageMath CRT_list docs.
"""
from __future__ import annotations

import argparse
import json
from itertools import permutations, product
from math import gcd, lcm
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-general-congruence-merge-hobbies-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"

class InvalidCongruence(ValueError):
    """Bad input is different from mathematically incompatible inputs."""


def merge_congruences(pairs: list[tuple[int, int]]) -> dict:
    """Exact (residue,positive modulus) constraints; indices are zero-based.

    The earliest incompatible ORIGINAL pair is an independently checkable
    certificate. The unique successful result is (r,L), 0 <= r < L.
    """
    if not isinstance(pairs, (list, tuple)):
        raise InvalidCongruence("expected finite ordered pairs")
    normalized = []
    for i, item in enumerate(pairs):
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise InvalidCongruence(f"bad pair at index {i}")
        a, m = item
        if type(a) is not int or type(m) is not int or m < 1:
            raise InvalidCongruence(f"integer residue/positive modulus required at {i}")
        normalized.append((a % m, m))

    # For integer congruences, pairwise gcd-compatibility is sufficient.
    # Inspect ORIGINAL order, to make the failure witness deterministic.
    for i, (a, m) in enumerate(normalized):
        for j in range(i + 1, len(normalized)):
            b, n = normalized[j]
            g = gcd(m, n)
            if (a - b) % g:
                return {"status": "CONFLICT", "i": i, "j": j,
                        "gcd": g, "difference_mod_gcd": (a - b) % g,
                        "left": [a, m], "right": [b, n]}
    r, modulus = 0, 1
    for a, m in normalized:
        g = gcd(modulus, m)
        q = m // g
        # gcd(modulus/g, q) == 1; q==1 needs no inverse.
        inverse = pow(modulus // g, -1, q) if q > 1 else 0
        k = (((a - r) // g) * inverse) % q if q > 1 else 0
        r = (r + modulus * k) % (modulus * q)
        modulus *= q
    return {"status": "SOLUTION", "residue": r, "modulus": modulus}


def brute_force(pairs: list[tuple[int, int]]) -> dict:
    """Independent exhaustive finite mathematical oracle, not extended GCD."""
    if not pairs:
        return {"status": "SOLUTION", "residue": 0, "modulus": 1}
    modulus = lcm(*(m for _, m in pairs))
    for candidate in range(modulus):
        if all(candidate % m == a % m for a, m in pairs):
            return {"status": "SOLUTION", "residue": candidate, "modulus": modulus}
    return {"status": "CONFLICT"}


def validate_dossier() -> dict:
    report = json.loads(DOSSIER.read_text(encoding="utf-8"))
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert report["schema"] == "sens-d10-general-congruence-hobbies/v1"
    assert report["proposal"]["semantic_name"] == "MERGE-CONGRUENCE-CONSTRAINTS"
    assert report["proposal"]["status"] == "HOLD-DERIVABILITY-CORE-VS-LIBRARY"
    assert report["proposal"]["coordinate"] is None
    assert report["proposal"]["selected"] is False
    assert report["proposal"]["ratified"] is False
    assert report["proposal"]["source_era"] == "research-only-no-binary"
    assert len(report["primary_sources"]) >= 2
    assert all(s["url"].startswith("https://") for s in report["primary_sources"])
    assert inv["capacity"] == 1024
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert inv["accounting"]["selected_semantic_candidates"] >= 630
    # An exact-name collision must stop intake; a behavioral duplicate
    # requires a deeper human review not inferred by this test.
    assert not any(row.get("semantic_name") == report["proposal"]["semantic_name"]
                   for row in inv["rows"])
    assert report["baseline"]["D1_D9_foundation_git_blob"] == (
        "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4"
    )
    assert report["scope"]["selected_delta"] == 0
    assert report["scope"]["ratified_delta"] == 0
    assert report["scope"]["modifies_canonical_inventory"] is False
    assert report["scope"]["writes_binary_sens"] is False
    return report


def run_checks() -> dict:
    doc = validate_dossier()
    cases = 0
    compatible = 0
    conflicts = 0
    # 6084 pair systems, includes non-coprime, modulus 1 and repeats.
    for m in range(1, 13):
        for n in range(1, 13):
            for a in range(m):
                for b in range(n):
                    system = [(a, m), (b, n)]
                    got = merge_congruences(system)
                    expected = brute_force(system)
                    assert got["status"] == expected["status"], system
                    if got["status"] == "SOLUTION":
                        assert got == expected, system
                        compatible += 1
                    else:
                        assert got["i"] == 0 and got["j"] == 1
                        assert got["difference_mod_gcd"] != 0
                        assert (a - b) % got["gcd"] == got["difference_mod_gcd"]
                        conflicts += 1
                    cases += 1
    # Three coupled congruences, pairwise compatibility iff soluble.
    for m, n, k in product(range(1, 6), repeat=3):
        for a, b, c in product(range(3), repeat=3):
            system = [(a, m), (b, n), (c, k)]
            got = merge_congruences(system)
            expected = brute_force(system)
            assert got["status"] == expected["status"], system
            if got["status"] == "SOLUTION":
                assert got == expected, system
            else:
                failures = [(i, j) for i in range(3)
                            for j in range(i + 1, 3)
                            if (system[i][0] - system[j][0])
                            % gcd(system[i][1], system[j][1])]
                assert (got["i"], got["j"]) == min(failures)
            cases += 1

    assert merge_congruences([]) == {"status": "SOLUTION", "residue": 0, "modulus": 1}
    assert merge_congruences([(2, 6), (5, 9)]) == (
        {"status": "SOLUTION", "residue": 14, "modulus": 18})
    assert merge_congruences([(2, 3), (3, 5), (2, 7)]) == (
        {"status": "SOLUTION", "residue": 23, "modulus": 105})
    assert merge_congruences([(6, 10), (0, 4)]) == (
        {"status": "SOLUTION", "residue": 16, "modulus": 20})
    assert merge_congruences([(7, 5), (2, 5)]) == (
        {"status": "SOLUTION", "residue": 2, "modulus": 5})
    for system in ([(2, 3), (4, 6)], [(2, 6), (4, 9)]):
        assert merge_congruences(system)["status"] == "CONFLICT"
    for system in ([(-1, 6), (3, 4)], [(1, 1), (5, 9)], [(0, 2), (1, 3)]):
        assert merge_congruences(system) == brute_force(system)
    for v in ([(1, 0)], [(1, -2)], [(True, 2)], [(1.0, 2)], [[1]], "1,2"):
        try:
            merge_congruences(v)
        except InvalidCongruence:
            pass
        else:
            raise AssertionError(f"invalid input not rejected: {v!r}")
    # Mutation guards: mathematically plausible but WRONG claims.
    assert merge_congruences([(2, 3), (4, 6)])["status"] != "SOLUTION"
    assert merge_congruences([(2, 6), (5, 9)])["modulus"] != 54
    assert merge_congruences([(2, 6), (5, 9)])["residue"] != 32
    assert merge_congruences([(1, 4), (3, 6)])["residue"] != 3
    assert merge_congruences([(0, 4), (0, 6), (1, 2)])["i"] == 0
    assert merge_congruences([(0, 4), (0, 6), (1, 2)])["j"] == 2
    # Prove order-free solution, not order-free earliest conflict indices.
    for case in doc["positive_witnesses"]:
        src = [tuple(pair) for pair in case["input"]]
        assert merge_congruences(src) == case["expected"]
        if len(src) <= 3:
            for p in permutations(src):
                assert merge_congruences(list(p)) == case["expected"]
    for case in doc["negative_witnesses"]:
        src = [tuple(pair) for pair in case["input"]]
        got = merge_congruences(src)
        assert got["status"] == "CONFLICT"
        assert [got["i"], got["j"]] == case["conflict_indices"]

    return {"schema": doc["schema"], "source": "exact-integers+brute-force",
            "independently_exhausted_systems": cases,
            "pair_compatible": compatible, "pair_incompatible": conflicts,
            "semantic_name": doc["proposal"]["semantic_name"],
            "D10_selected_delta": 0, "ratified_delta": 0,
            "oracle": "partial-math-only; current-SENS-runtime-NOT-PROVEN"}


def sympy_donor() -> dict:
    """A REAL external mathematics donor, not a home-grown fake 'oracle'."""
    from sympy.ntheory.modular import solve_congruence
    total = 0
    for m in range(1, 16):
        for n in range(1, 16):
            for a in range(m):
                for b in range(n):
                    pairs = [(a, m), (b, n)]
                    got = merge_congruences(pairs)
                    donor = solve_congruence(*pairs)
                    if donor is None:
                        assert got["status"] == "CONFLICT", (pairs, got)
                    else:
                        residue, period = map(int, donor)
                        assert got == {"status": "SOLUTION",
                                       "residue": residue % period,
                                       "modulus": period}, (pairs, got, donor)
                    total += 1
    return {"real_donor": "SymPy.solve_congruence", "observations": total,
            "status": "PASS", "D10_admission": "HOLD"}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sympy-donor", action="store_true")
    args = p.parse_args()
    result = run_checks()
    if args.sympy_donor:
        result["external_oracle"] = sympy_donor()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
