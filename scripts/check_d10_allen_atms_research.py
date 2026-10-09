#!/usr/bin/env python3
"""Research-only, fail-closed exact semantics: historical Allen / ATMS.
These are behavioral reference witnesses, NOT admitted D10 machine opcodes.
"""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-allen-atms-research-20261009.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"

ALLEN_RELATIONS = frozenset({
    "BEFORE", "MEETS", "OVERLAPS", "STARTS", "DURING", "FINISHES",
    "EQUALS", "AFTER", "MET-BY", "OVERLAPPED-BY",
    "STARTED-BY", "CONTAINS", "FINISHED-BY"
})
ALLEN_INVERSE = {
    "BEFORE": "AFTER", "AFTER": "BEFORE",
    "MEETS": "MET-BY", "MET-BY": "MEETS",
    "OVERLAPS": "OVERLAPPED-BY", "OVERLAPPED-BY": "OVERLAPS",
    "STARTS": "STARTED-BY", "STARTED-BY": "STARTS",
    "DURING": "CONTAINS", "CONTAINS": "DURING",
    "FINISHES": "FINISHED-BY", "FINISHED-BY": "FINISHES",
    "EQUALS": "EQUALS",
}


def _exact_number(value: object) -> Fraction:
    if type(value) is int or isinstance(value, Fraction):
        return Fraction(value)
    raise TypeError("endpoints must be exact rational (no bool/float/string)")


def _interval(pair: object) -> tuple[Fraction, Fraction]:
    if not isinstance(pair, (tuple, list)) or len(pair) != 2:
        raise TypeError("interval must be a two-element pair")
    start, end = (_exact_number(value) for value in pair)
    if start >= end:
        raise ValueError("interval endpoints require start < end")
    return start, end


def allen_interval_relation(a: object, b: object) -> str:
    """One of exactly 13 qualitative relations; touching is MEETS, not BEFORE."""
    a0, a1 = _interval(a)
    b0, b1 = _interval(b)
    if a1 < b0:
        return "BEFORE"
    if a1 == b0:
        return "MEETS"
    if a0 > b1:
        return "AFTER"
    if a0 == b1:
        return "MET-BY"
    if a0 == b0:
        if a1 == b1:
            return "EQUALS"
        return "STARTS" if a1 < b1 else "STARTED-BY"
    if a1 == b1:
        return "FINISHED-BY" if a0 < b0 else "FINISHES"
    if a0 < b0:
        return "OVERLAPS" if a1 < b1 else "CONTAINS"
    return "OVERLAPPED-BY" if a1 > b1 else "DURING"


def _family(value: object) -> set[frozenset[int]]:
    if not isinstance(value, (list, tuple)):
        raise TypeError("support family must be a finite list/tuple")
    supports: set[frozenset[int]] = set()
    for group in value:
        if not isinstance(group, (tuple, list, frozenset, set)):
            raise TypeError("support must be a collection of assumption IDs")
        elements = tuple(group)
        if any(type(x) is not int or x < 0 for x in elements):
            raise TypeError("assumption IDs must be nonnegative exact integers")
        supports.add(frozenset(elements))
    return supports


def atms_consistent_label_join(
    left: object, right: object, nogoods: object
) -> tuple[tuple[int, ...], ...]:
    """Minimal pairwise support unions without any known inconsistent subset.

    Empty label [] = no alternative support, [[]] = unconditional support.
    Output ordering is cardinality first, then lexicographic ID order.
    """
    l, r, ng = _family(left), _family(right), _family(nogoods)
    unions = {a | b for a in l for b in r}
    consistent = {env for env in unions if not any(bad <= env for bad in ng)}
    minimal = {env for env in consistent
               if not any(other < env for other in consistent)}
    return tuple(sorted((tuple(sorted(env)) for env in minimal),
                        key=lambda x: (len(x), x)))


def verify_dossier(
    dossier: dict, foundation: dict, inventory: dict
) -> dict:
    assert dossier["schema"] == "sens-d10-historical-hobby-allen-atms-research/v1"
    assert dossier["status"] == "RESEARCH-UNRATIFIED-HOLD-NOT-SELECTED"
    assert dossier["invariants"] == {
        "selected_inventory_mutated": False,
        "d1_d9_changed": False,
        "d2_control_changed": False,
        "t5_changed": False,
        "coordinate_count_new": 0,
        "ratified_new": 0,
    }
    assert dossier["canonical_snapshot"]["main_selected_at_claim"] == 634
    assert inventory["accounting"]["selected_semantic_candidates"] == len(inventory["rows"])
    assert inventory["accounting"]["selected_semantic_candidates"] >= 634
    assert inventory["accounting"]["ratified_d10_residents"] == 0
    lower = {str(name).upper() for dom in foundation["domains"].values()
             for name in dom["residents"].values()}
    upper = {row["semantic_name"].upper() for row in inventory["rows"]}
    rows = dossier["rows"]
    assert len(rows) == 2
    assert {x["semantic_name"] for x in rows} == {
        "ALLEN-INTERVAL-RELATION", "ATMS-CONSISTENT-LABEL-JOIN"
    }
    assert len({x["proposal_id"] for x in rows}) == len(rows)
    for row in rows:
        name = row["semantic_name"].upper()
        assert name not in lower and name not in upper, "D1-D9/D10 collision"
        assert row["triage_status"].startswith("HOLD-")
        assert row["coordinate"] is None
        assert row["ratified_resident"] is False
        assert row["selected_in_canonical_inventory"] is False
        assert row["physical_t5_authorized"] is False
        assert row["owner_review_required"] is True
        assert row["historical_is_lisp_opcode"] is False
        assert row["source"]["primary_url"].startswith("https://doi.org/")
        assert len(row["positive_witnesses"]) >= 3
        assert len(row["falsifiers"]) >= 4
        assert row["signature"] and row["semantic_law"] and row["duplicate_review"]
        assert row["surface_uk"] and row["surface_ukr"]
    return {
        "checked": len(rows),
        "selected_from_dossier": 0,
        "ratified_from_dossier": 0,
        "current_selected": len(inventory["rows"]),
    }


def main() -> None:
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))
    outcome = verify_dossier(load(DOSSIER), load(FOUNDATION), load(INVENTORY))
    print("D10 historical Allen/ATMS research PASS", json.dumps(outcome, sort_keys=True))


if __name__ == "__main__":
    main()
