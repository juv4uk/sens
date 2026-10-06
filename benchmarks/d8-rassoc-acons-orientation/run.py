#!/usr/bin/env python3
"""#3741 — RASSOC/ACONS × association-orientation D8 research witness.

Research only. No D8 resident is admitted or made callable.

The semantic product is typed:

    role        = query | extend
    orientation = value | key

Current lower-domain/current-domain meanings:
- D6 RASSOC: query association list by value;
- D6 ACONS: prepend (key . value);
- D5 ASSOC: query association list by key.

The independent orientation action is pair transposition:
    tau((k,v)) = (v,k)
    tau(A) = map(tau, A)

Required conjugations:
    tau(RASSOC(q,A)) = ASSOC(q,tau(A))
    tau(ACONS(k,v,A)) = ACONS(v,k,tau(A))

No historical D8 donor participates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import permutations, product
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[2]
D5_AUTHORITY_PATH = REPO / "knowledge" / "d5-ratified.json"
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"
D3_SELECTOR_ROOTS = ("011", "100")

ATOMS = (0, 1, 2)
PAIR_UNIVERSE = tuple(product(ATOMS, repeat=2))
MAX_ALIST_LENGTH = 2

Pair = tuple[int, int]
Alist = tuple[Pair, ...]


def load_authority() -> dict[str, object]:
    d5_raw = D5_AUTHORITY_PATH.read_bytes()
    d5 = json.loads(d5_raw)
    assert d5["schema"] == "d5-ratified/v1"
    assert d5["status"] == "owner-ratified"
    assert d5["authority"] == "#3305"
    d5_by_name = {name: coord for coord, name in d5["residents"].items()}
    assert d5_by_name["ASSOC"] == "11100"

    d6_raw = D6_AUTHORITY_PATH.read_bytes()
    d6 = json.loads(d6_raw)
    assert d6["schema"] == "d6-ratified/v1"
    assert d6["status"] == "owner-ratified"
    assert d6["authority"] == "#3393"
    d6_by_name = {name: coord for coord, name in d6["residents"].items()}
    assert d6_by_name["RASSOC"] == "001100"
    assert d6_by_name["ACONS"] == "001101"

    return {
        "d5": {
            "path": str(D5_AUTHORITY_PATH.relative_to(REPO)),
            "sha256": hashlib.sha256(d5_raw).hexdigest(),
            "authority": d5["authority"],
            "assoc": d5_by_name["ASSOC"],
        },
        "d6": {
            "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
            "sha256": hashlib.sha256(d6_raw).hexdigest(),
            "authority": d6["authority"],
            "rassoc": d6_by_name["RASSOC"],
            "acons": d6_by_name["ACONS"],
        },
    }


def pair_tau(pair: Pair) -> Pair:
    k, v = pair
    return (v, k)


def alist_tau(alist: Alist) -> Alist:
    return tuple(pair_tau(pair) for pair in alist)


def optional_pair_tau(pair: Optional[Pair]) -> Optional[Pair]:
    return None if pair is None else pair_tau(pair)


def assoc(query: int, alist: Alist) -> Optional[Pair]:
    for pair in alist:
        if pair[0] == query:
            return pair
    return None


def rassoc(query: int, alist: Alist) -> Optional[Pair]:
    for pair in alist:
        if pair[1] == query:
            return pair
    return None


def acons(key: int, value: int, alist: Alist) -> Alist:
    return ((key, value),) + alist


def alists() -> list[Alist]:
    out: list[Alist] = [()]
    for length in range(1, MAX_ALIST_LENGTH + 1):
        out.extend(permutations(PAIR_UNIVERSE, length))
    assert len(out) == 82
    return out


def selector_d8_candidates() -> set[str]:
    d6_parents = {
        root + "".join(suffix)
        for root in D3_SELECTOR_ROOTS
        for suffix in product("01", repeat=3)
    }
    assert len(d6_parents) == 16
    out = {
        parent + "".join(suffix)
        for parent in d6_parents
        for suffix in product("01", repeat=2)
    }
    assert len(out) == 64
    return out


def coordinate_gauge(authority: dict[str, object]) -> dict[str, object]:
    d6 = authority["d6"]
    parent = str(d6["rassoc"])
    sibling = str(d6["acons"])
    assoc_d5 = str(authority["d5"]["assoc"])

    family = {parent + suffix for suffix in ("00", "01", "10", "11")}
    assert family.isdisjoint(selector_d8_candidates())

    return {
        "d6_parent": parent,
        "d6_role_sibling": sibling,
        "d5_orientation_sibling": assoc_d5,
        "d8_family_coordinates": sorted(family),
        "selector_collision": False,
        "axis_order_role_then_orientation": {
            "00": "RASSOC",
            "01": "ASSOC",
            "10": "ACONS",
            "11": "ACONS-SWAPPED",
        },
        "axis_order_orientation_then_role": {
            "00": "RASSOC",
            "01": "ACONS",
            "10": "ASSOC",
            "11": "ACONS-SWAPPED",
        },
        "invariants": {
            parent + "00": "RASSOC / D6 lower-domain duplicate",
            parent + "11": "ACONS-SWAPPED / generated typed candidate",
        },
        "middle_gauge_orbit": {
            "coordinates": [parent + "01", parent + "10"],
            "meanings": [
                "ASSOC / D5 lower-domain duplicate",
                "ACONS / D6 lower-domain duplicate",
            ],
            "absolute_assignment": "UNRESOLVED",
        },
    }


def run() -> dict[str, object]:
    authority = load_authority()
    corpus = alists()

    tau_involution = 0
    query_conjugation = 0
    query_orientation_observable = 0
    query_no_match_cases = 0
    query_no_match_preserved = 0

    extension_conjugation = 0
    extension_orientation_observable = 0

    normal_rassoc_after_acons = 0
    normal_assoc_after_acons = 0
    swapped_rassoc_after_acons = 0
    swapped_assoc_after_acons = 0

    reverse_control_cases = 0
    reverse_control_failures = 0

    for alist in corpus:
        tau_involution += alist_tau(alist_tau(alist)) == alist

        for q in ATOMS:
            r = rassoc(q, alist)
            a = assoc(q, alist_tau(alist))
            query_conjugation += optional_pair_tau(r) == a
            query_orientation_observable += rassoc(q, alist) != assoc(q, alist)
            if r is None:
                query_no_match_cases += 1
                query_no_match_preserved += a is None

        for key, value in PAIR_UNIVERSE:
            normal = acons(key, value, alist)
            transposed = acons(value, key, alist_tau(alist))

            extension_conjugation += alist_tau(normal) == transposed
            extension_orientation_observable += (
                acons(key, value, alist) != acons(value, key, alist)
            )

            normal_rassoc_after_acons += rassoc(value, normal) == (key, value)
            normal_assoc_after_acons += assoc(key, normal) == (key, value)
            swapped_rassoc_after_acons += (
                rassoc(key, transposed) == (value, key)
            )
            swapped_assoc_after_acons += (
                assoc(value, transposed) == (value, key)
            )

            if alist:
                reverse_control_cases += 1
                reverse_of_extension = tuple(reversed(normal))
                extension_of_reverse = acons(
                    key, value, tuple(reversed(alist))
                )
                reverse_control_failures += (
                    reverse_of_extension != extension_of_reverse
                )

    alist_count = len(corpus)
    query_cases = alist_count * len(ATOMS)
    extension_cases = alist_count * len(PAIR_UNIVERSE)

    assert alist_count == 82
    assert query_cases == 246
    assert extension_cases == 738

    assert tau_involution == alist_count
    assert query_conjugation == query_cases
    assert query_no_match_preserved == query_no_match_cases
    assert query_orientation_observable == 156

    assert extension_conjugation == extension_cases
    assert extension_orientation_observable == 492

    assert normal_rassoc_after_acons == extension_cases
    assert normal_assoc_after_acons == extension_cases
    assert swapped_rassoc_after_acons == extension_cases
    assert swapped_assoc_after_acons == extension_cases

    assert reverse_control_cases == 729
    assert reverse_control_failures == 720
    reverse_control_degenerate_equal = (
        reverse_control_cases - reverse_control_failures
    )
    assert reverse_control_degenerate_equal == 9

    gauge = coordinate_gauge(authority)
    parent = str(authority["d6"]["rassoc"])

    return {
        "schema": "d8-rassoc-acons-orientation/v1",
        "status": "PRODUCT-CANDIDATE-TYPED",
        "authority": {
            "d5_assoc": "#3305",
            "d6_rassoc_acons": "#3393 / #3384 f04",
            "sources": authority,
            "d8": "#3281 research",
            "task": "#3741",
        },
        "carrier": {
            "atoms": list(ATOMS),
            "ordered_pair_universe": len(PAIR_UNIVERSE),
            "max_alist_length": MAX_ALIST_LENGTH,
            "alist_distinct_entries": True,
            "alists": alist_count,
            "query_cases": query_cases,
            "extension_cases": extension_cases,
        },
        "orientation_law": {
            "pair_tau": "tau((k,v))=(v,k)",
            "alist_tau": "tau(A)=map(tau,A)",
            "query_conjugation": "tau(RASSOC(q,A))=ASSOC(q,tau(A))",
            "extension_conjugation": (
                "tau(ACONS(k,v,A))=ACONS(v,k,tau(A))"
            ),
        },
        "witness": {
            "tau_involution_pass": tau_involution,
            "query_conjugation_pass": query_conjugation,
            "query_no_match_cases": query_no_match_cases,
            "query_no_match_preserved": query_no_match_preserved,
            "query_orientation_observable_cases": (
                query_orientation_observable
            ),
            "extension_conjugation_pass": extension_conjugation,
            "extension_orientation_observable_cases": (
                extension_orientation_observable
            ),
            "normal_rassoc_after_acons_pass": normal_rassoc_after_acons,
            "normal_assoc_after_acons_pass": normal_assoc_after_acons,
            "swapped_rassoc_after_acons_pass": swapped_rassoc_after_acons,
            "swapped_assoc_after_acons_pass": swapped_assoc_after_acons,
        },
        "negative_control": {
            "axis": "alist order reversal",
            "nonempty_extension_cases": reverse_control_cases,
            "commutation_failures": reverse_control_failures,
            "degenerate_equal_cases": reverse_control_degenerate_equal,
            "status": "ORDERED-ONLY-REJECTED",
        },
        "semantic_corners": {
            "rassoc": "current D6 parent; lower-domain duplicate",
            "assoc": "current D5 meaning; lower-domain duplicate",
            "acons": "current D6 role sibling; lower-domain duplicate",
            "acons_swapped": "generated typed semantic candidate",
        },
        "coordinate_gauge": gauge,
        "result": {
            "generated_novel_semantics": 1,
            "invariant_coordinate_candidate": parent + "11",
            "invariant_coordinate_meaning": "ACONS-SWAPPED",
            "middle_orbit": [parent + "01", parent + "10"],
            "middle_meanings": ["ASSOC", "ACONS"],
            "orientation_theorem_missing": True,
        },
        "non_conclusions": [
            "No D8 resident or primitive is admitted.",
            "ASSOC and ACONS appearing in the D8 square are lower-domain duplicates.",
            "The two middle absolute coordinates remain gauge-unresolved.",
            "RASSOC/ACONS runtime mechanism availability is not inferred from semantic residency.",
            "No D7 ancestry is used.",
            "No historical D8 donor row is input.",
        ],
    }


def render(report: dict[str, object]) -> str:
    c = report["carrier"]
    w = report["witness"]
    n = report["negative_control"]
    g = report["coordinate_gauge"]
    r = report["result"]

    return "\n".join([
        "# D8 RASSOC/ACONS × association orientation — #3741",
        "",
        "Status: **PRODUCT-CANDIDATE-TYPED** (research only).",
        "",
        f"- alists: {c['alists']}",
        f"- query cases: {c['query_cases']}",
        f"- extension cases: {c['extension_cases']}",
        "",
        "Positive witnesses:",
        f"- tau involution: {w['tau_involution_pass']}/{c['alists']}",
        f"- RASSOC/ASSOC conjugation: {w['query_conjugation_pass']}/{c['query_cases']}",
        f"- no-match preservation: {w['query_no_match_preserved']}/{w['query_no_match_cases']}",
        f"- query orientation observable: {w['query_orientation_observable_cases']} cases",
        f"- ACONS conjugation: {w['extension_conjugation_pass']}/{c['extension_cases']}",
        f"- extension orientation observable: {w['extension_orientation_observable_cases']} cases",
        f"- normal RASSOC after ACONS: {w['normal_rassoc_after_acons_pass']}/{c['extension_cases']}",
        f"- normal ASSOC after ACONS: {w['normal_assoc_after_acons_pass']}/{c['extension_cases']}",
        f"- swapped RASSOC after ACONS: {w['swapped_rassoc_after_acons_pass']}/{c['extension_cases']}",
        f"- swapped ASSOC after ACONS: {w['swapped_assoc_after_acons_pass']}/{c['extension_cases']}",
        "",
        "Negative control:",
        f"- reverse-axis failures: {n['commutation_failures']}/{n['nonempty_extension_cases']}",
        f"- explicit degenerate equal cases: {n['degenerate_equal_cases']}",
        "",
        "Coordinate/gauge:",
        f"- D6 anchor: {g['d6_parent']} (RASSOC)",
        f"- family: {' '.join(g['d8_family_coordinates'])}",
        f"- selector collision: {g['selector_collision']}",
        f"- invariant 11 candidate: {r['invariant_coordinate_candidate']} = ACONS-SWAPPED",
        f"- middle gauge orbit: {' / '.join(r['middle_orbit'])} = ASSOC / ACONS",
        "",
        "No D8 admission follows from this witness.",
        "",
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    report = run()
    text = render(report)

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "witness.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
