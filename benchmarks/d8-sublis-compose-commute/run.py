#!/usr/bin/env python3
"""#3767 — SUBLIS/COMPOSE generic second-substitution D8 commutativity falsifier.

Research-only D8 screen. The candidate second axis is a second independently
chosen substitution/tree-transformer stage. A uniform D8 commuting-square law
would require the two stages to commute. This witness exhaustively tests the
smallest nontrivial three-atom substitution carrier and rejects that generic
axis when order is observably significant.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D6_AUTHORITY_PATH = REPO / "knowledge" / "d6-ratified.json"

ATOMS = ("a", "b", "c")
SUBSTITUTIONS = tuple(product(ATOMS, repeat=len(ATOMS)))
TREES = ATOMS + tuple((left, right) for left in ATOMS for right in ATOMS)


def load_authority() -> dict[str, object]:
    raw = D6_AUTHORITY_PATH.read_bytes()
    doc = json.loads(raw)
    assert doc["schema"] == "d6-ratified/v1"
    assert doc["status"] == "owner-ratified"
    assert doc["authority"] == "#3393"
    by_name = {name: coord for coord, name in doc["residents"].items()}
    assert by_name["SUBLIS"] == "001010"
    assert by_name["COMPOSE"] == "001011"
    return {
        "path": str(D6_AUTHORITY_PATH.relative_to(REPO)),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "authority": doc["authority"],
        "sublis": by_name["SUBLIS"],
        "compose": by_name["COMPOSE"],
    }


def apply_substitution(substitution: tuple[str, ...], tree):
    if isinstance(tree, str):
        return substitution[ATOMS.index(tree)]
    left, right = tree
    return (
        apply_substitution(substitution, left),
        apply_substitution(substitution, right),
    )


def apply_two(first: tuple[str, ...], second: tuple[str, ...], tree):
    """Apply first stage, then second stage."""
    return apply_substitution(second, apply_substitution(first, tree))


def as_mapping(substitution: tuple[str, ...]) -> dict[str, str]:
    return dict(zip(ATOMS, substitution, strict=True))


def run() -> dict[str, object]:
    authority = load_authority()

    assert len(SUBSTITUTIONS) == 27
    assert len(TREES) == 12

    ordered_pairs = 0
    commuting_pairs = 0
    noncommuting_pairs = 0
    first_counterexample = None

    for sigma in SUBSTITUTIONS:
        for tau in SUBSTITUTIONS:
            ordered_pairs += 1
            sigma_then_tau = tuple(apply_two(sigma, tau, tree) for tree in TREES)
            tau_then_sigma = tuple(apply_two(tau, sigma, tree) for tree in TREES)

            if sigma_then_tau == tau_then_sigma:
                commuting_pairs += 1
                continue

            noncommuting_pairs += 1
            if first_counterexample is None:
                for tree, st, ts in zip(
                    TREES, sigma_then_tau, tau_then_sigma, strict=True
                ):
                    if st != ts:
                        first_counterexample = {
                            "sigma": as_mapping(sigma),
                            "tau": as_mapping(tau),
                            "tree": tree,
                            "sigma_then_tau": st,
                            "tau_then_sigma": ts,
                        }
                        break

    assert ordered_pairs == 729
    assert commuting_pairs == 141
    assert noncommuting_pairs == 588
    assert commuting_pairs + noncommuting_pairs == ordered_pairs
    assert first_counterexample is not None

    return {
        "schema": "d8-sublis-compose-commutativity/v1",
        "status": "GENERIC-COMMUTING-AXIS-REJECTED",
        "authority": {
            "d6": authority,
            "d8": "#3281 research",
            "parent": "#3618",
            "task": "#3767",
            "semantic_donor": "#2348 post-D4 SUBLIS structural recursion",
        },
        "carrier": {
            "atoms": list(ATOMS),
            "substitutions": len(SUBSTITUTIONS),
            "ordered_substitution_pairs": ordered_pairs,
            "trees": len(TREES),
            "tree_shape": "3 atoms + all 9 ordered depth-1 pairs",
        },
        "witness": {
            "commuting_pairs": commuting_pairs,
            "noncommuting_pairs": noncommuting_pairs,
            "commuting_fraction": f"{commuting_pairs}/{ordered_pairs}",
            "noncommuting_fraction": f"{noncommuting_pairs}/{ordered_pairs}",
            "first_counterexample": first_counterexample,
        },
        "law": {
            "candidate": "S_sigma(S_tau(tree)) = S_tau(S_sigma(tree))",
            "holds_uniformly": False,
            "reason": (
                "SUBLIS-style tree substitutions form a composition system in "
                "which independently chosen stages are generally order-sensitive."
            ),
        },
        "result": {
            "generic_second_substitution_axis": False,
            "analyzed_d8_coordinates": 0,
            "candidate_footprint": [],
            "classification": "FALSIFIED",
        },
        "non_conclusions": [
            "This does not reject D6 SUBLIS or COMPOSE.",
            "This rejects only a generic order-independent second-substitution D8 axis.",
            "Restricted commuting substitution families may still be researched separately.",
            "No D8 coordinate, resident, or callability is admitted.",
            "No D7 ancestry or historical D8 donor map is used.",
        ],
    }


def render(report: dict[str, object]) -> str:
    c = report["carrier"]
    w = report["witness"]
    ex = w["first_counterexample"]
    return "\n".join([
        "# D8 SUBLIS/COMPOSE commutativity screen — #3767",
        "",
        "Result: **GENERIC-COMMUTING-AXIS-REJECTED**.",
        "",
        f"- atom substitutions: {c['substitutions']}",
        f"- ordered substitution pairs: {c['ordered_substitution_pairs']}",
        f"- shallow trees: {c['trees']}",
        f"- commuting pairs: {w['commuting_pairs']}",
        f"- noncommuting pairs: {w['noncommuting_pairs']}",
        "",
        "First counterexample:",
        f"- sigma: {ex['sigma']}",
        f"- tau: {ex['tau']}",
        f"- tree: {ex['tree']}",
        f"- sigma then tau: {ex['sigma_then_tau']}",
        f"- tau then sigma: {ex['tau_then_sigma']}",
        "",
        "D8 coordinates allocated: **0**.",
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
