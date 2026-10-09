#!/usr/bin/env python3
"""Fail-closed validation for the historical Lisp 1.5 D10 reconciliation.

The reconciliation records the exact D10 inventory visible on 2026-10-09.
Later research-only additions must not falsify that snapshot, and they may be
accepted only through an explicit, hash-linked append-only transition ledger.
No inventory, coordinates, or ratification are written by this checker.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "knowledge/d10-historical-lisp15-reconciliation-20261009.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
TRANSITIONS = ROOT / "knowledge/d10-selection-transition-history.json"
BASELINE_D10_BLOB = "73dd518469f972c55411e004b70b054ba8b3ec86"
BASELINE_FOUNDATION_BLOB = "09d1d71c39d1484dfd005a5068dbb18b76f0f0d4"
CAPACITY = 1024
LAW_FORCED_COORDINATES = 256


def git_blob(data: dict) -> str:
    """Git SHA-1 of the repo's canonical UTF-8, two-space JSON serialization."""
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    header = b"blob " + str(len(payload)).encode("ascii") + b"\0"
    return hashlib.sha1(header + payload).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _verify_appended_rows(rows: list[dict], transition: dict) -> None:
    added_ids = transition.get("added_stable_ids")
    delta = transition.get("delta_selected")
    _check(isinstance(added_ids, list) and added_ids, "transition has no explicit added_stable_ids")
    _check(len(added_ids) == len(set(added_ids)), "transition duplicates stable IDs")
    _check(delta == len(added_ids), "transition delta does not match explicit stable IDs")
    _check(len(rows) == delta, "transition appended row count mismatch")
    for row in rows:
        _check(row.get("stable_id") in added_ids, "unlisted stable ID in appended tail")
        _check(bool(row.get("semantic_name")), "appended row has no semantic name")
        _check(bool(row.get("behavior")), "appended row has no behavior law")
        _check(bool(row.get("provenance")), "appended row has no provenance")
        _check(row.get("status") == "SELECTED-RESEARCH-CANDIDATE", "appended row is not a selected research candidate")
        _check(row.get("coordinate") is None, "append transition assigned a coordinate")
        _check(row.get("ratified_resident") is False, "append transition ratified a resident")
        _check(row.get("coordinate_basis") in ("UNPLACED", None), "append transition forged coordinate basis")
        _check(row.get("language_visible") is not False, "append transition includes a non-language-visible row")
        _check(row.get("mechanism_only") is not True, "append transition includes mechanism-only row")
        _check(row.get("falsified") is not True, "append transition includes a falsified row")
    _check([row["stable_id"] for row in rows] == added_ids,
           "appended tail order differs from the explicit transition record")


def historical_inventory_view(
    current: dict,
    expected_blob: str = BASELINE_D10_BLOB,
    transition_history: dict | None = None,
) -> dict:
    """Reconstruct a pinned historical inventory by reversing approved append events.

    This fails closed if the live inventory differs from the historical SHA but
    has no explicit hash-linked transition manifest. Existing rows are never
    rewritten, and all added rows must remain selected-but-unplaced/unratified.
    """
    _check(expected_blob == BASELINE_D10_BLOB, "unsupported historical D10 baseline SHA")
    manifest = transition_history
    if manifest is None and TRANSITIONS.exists():
        manifest = load(TRANSITIONS)

    work = copy.deepcopy(current)
    actual_blob = git_blob(work)
    if actual_blob == expected_blob:
        if manifest is not None:
            _check(manifest.get("baseline", {}).get("inventory_blob_sha") == expected_blob,
                   "transition manifest baseline does not match historical audit")
        return work

    # Alternate current-main replay of the 625 -> 629 primary-law batch. It has
    # its own exact append witness and SHA reconstruction. Never use it to
    # accept arbitrary inventory drift.
    if manifest is None:
        compatibility = ROOT / "scripts/d10_historical_snapshot_compat.py"
        if compatibility.exists():
            spec = importlib.util.spec_from_file_location("d10_historical_snapshot_compat", compatibility)
            _check(spec is not None and spec.loader is not None, "cannot load historical snapshot compatibility helper")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            view = module.historic_view(work, expected_blob)
            _check(git_blob(view) == expected_blob, "compatibility helper did not reconstruct the pinned D10 blob")
            return view
        raise ValueError("D10 differs from historical SHA without an explicit append-only transition ledger")

    _check(manifest.get("schema") == "d10-selection-transition-history/v1",
           "wrong D10 transition manifest schema")
    _check(manifest.get("status") == "RESEARCH-ONLY-NO-RATIFICATION",
           "transition manifest can only record research-only additions")
    _check(manifest.get("baseline", {}).get("inventory_blob_sha") == expected_blob,
           "transition baseline does not match historical audit")
    _check(manifest.get("baseline", {}).get("selected_count") == 625,
           "transition baseline selected count drift")
    _check(manifest.get("baseline", {}).get("selector_coordinates") == LAW_FORCED_COORDINATES,
           "transition baseline selector-law count drift")
    _check(manifest.get("baseline", {}).get("ratified_d10_residents") == 0,
           "transition baseline claims D10 ratification")

    transitions = manifest.get("transitions")
    _check(isinstance(transitions, list), "transition history is not a list")
    seen_transition_ids: set[str] = set()
    for transition in transitions:
        transition_id = transition.get("id")
        _check(isinstance(transition_id, str) and transition_id,
               "transition lacks stable identity")
        _check(transition_id not in seen_transition_ids, "duplicate transition identity")
        seen_transition_ids.add(transition_id)
        _check(transition.get("coordinates_added") == 0, "transition claims coordinate additions")
        _check(transition.get("ratified_added") == 0, "transition claims ratification")
        _check(transition.get("previous_selected", 0) + transition.get("delta_selected", 0)
               == transition.get("resulting_selected", -1),
               "transition count arithmetic is inconsistent")

    visited: set[str] = set()
    while git_blob(work) != expected_blob:
        current_blob = git_blob(work)
        _check(current_blob not in visited, "cycle in D10 transition history")
        visited.add(current_blob)
        candidates = [t for t in transitions if t.get("resulting_inventory_blob_sha") == current_blob]
        _check(len(candidates) == 1, "live D10 blob has no unique explicit append event")
        transition = candidates[0]

        resulting_count = transition.get("resulting_selected")
        previous_count = transition.get("previous_selected")
        delta = transition.get("delta_selected")
        _check(resulting_count == len(work.get("rows", [])), "transition resulting count != live row count")
        _check(previous_count == resulting_count - delta, "transition previous count arithmetic drift")
        _check(work.get("accounting", {}).get("selected_semantic_candidates") == resulting_count,
               "live inventory selected accounting differs from transition")
        _check(work.get("accounting", {}).get("law_forced_coordinates") == LAW_FORCED_COORDINATES,
               "transition altered the 256 law-forced selector coordinates")
        _check(work.get("accounting", {}).get("ratified_d10_residents") == 0,
               "live D10 has ratified residents during research-only transition")

        added_ids = transition.get("added_stable_ids", [])
        _verify_appended_rows(work["rows"][-len(added_ids):], transition)
        previous_blob = transition.get("previous_inventory_blob_sha")
        _check(isinstance(previous_blob, str) and len(previous_blob) == 40,
               "transition has no previous inventory blob SHA")

        appended_sources = transition.get("appended_sources", [])
        _check(isinstance(appended_sources, list), "appended_sources must be a list")
        if appended_sources:
            _check(work.get("sources", [])[-len(appended_sources):] == appended_sources,
                   "inventory source tail differs from transition")
            del work["sources"][-len(appended_sources):]

        del work["rows"][-len(added_ids):]
        work["accounting"]["selected_semantic_candidates"] = previous_count
        work["accounting"]["unplaced_selected_candidates"] = previous_count - LAW_FORCED_COORDINATES
        work["accounting"]["remaining_semantic_inventory"] = CAPACITY - previous_count
        work["accounting"]["ratified_d10_residents"] = 0
        _check(git_blob(work) == previous_blob, "append-only reversal did not reproduce previous inventory SHA")

    historic = work
    _check(historic["accounting"]["selected_semantic_candidates"] == 625,
           "reconstructed historical inventory is not 625 rows")
    _check(len(historic["rows"]) == 625, "reconstructed historical row count is not 625")
    return historic


def verify(
    review: dict,
    foundation: dict,
    inventory: dict,
    transition_history: dict | None = None,
) -> dict:
    if review.get("schema") != "d10-historical-lisp15-reconciliation/v1":
        raise ValueError("wrong reconciliation schema")
    if review.get("status") != "RESEARCH-ONLY-NO-RESIDENTS":
        raise ValueError("unexpected review authority")

    rows = review.get("rows")
    if not isinstance(rows, list) or len(rows) != 31 or review["snapshot"]["rows_reconciled"] != 31:
        raise ValueError("expected 30 recovered families plus one MAPATOMS/OBARRAY review lead")
    if review["snapshot"]["selected_added"] or review["snapshot"]["coordinates_added"] or review["snapshot"]["ratifications_added"]:
        raise ValueError("a historical audit must not change semantic authority")

    snapshot = review["snapshot"]
    historic = historical_inventory_view(inventory, snapshot["d10_inventory_blob"], transition_history)
    if git_blob(historic) != snapshot["d10_inventory_blob"]:
        raise ValueError("historical D10 snapshot SHA mismatch")
    if snapshot["d10_selected"] != historic["accounting"]["selected_semantic_candidates"]:
        raise ValueError("historical selected count drift")
    if snapshot["d10_unplaced"] != historic["accounting"]["unplaced_selected_candidates"]:
        raise ValueError("historical unplaced count drift")
    if snapshot["d10_remaining"] != historic["accounting"]["remaining_semantic_inventory"]:
        raise ValueError("historical remaining count drift")
    if snapshot["d10_ratified"] != historic["accounting"]["ratified_d10_residents"]:
        raise ValueError("historical ratification count drift")
    if git_blob(foundation) != snapshot["foundation_blob"] or snapshot["foundation_blob"] != BASELINE_FOUNDATION_BLOB:
        raise ValueError("ratified D1-D9 foundation changed from the historical audit baseline")

    if inventory["accounting"]["selected_semantic_candidates"] != len(inventory["rows"]):
        raise ValueError("live selected accounting differs from current rows")
    live_count = len(inventory["rows"])
    if live_count < snapshot["d10_selected"] or live_count > CAPACITY:
        raise ValueError("live D10 count is outside append-only research bounds")
    live_accounting = inventory["accounting"]
    if live_accounting["law_forced_coordinates"] != LAW_FORCED_COORDINATES:
        raise ValueError("live selector-law coordinate count changed")
    if live_accounting["unplaced_selected_candidates"] != live_count - LAW_FORCED_COORDINATES:
        raise ValueError("live unplaced accounting drift")
    if live_accounting["remaining_semantic_inventory"] != CAPACITY - live_count:
        raise ValueError("live remaining accounting drift")
    if live_accounting["ratified_d10_residents"] != 0:
        raise ValueError("live D10 ratified residents must stay zero")

    if len({row.get("review_id") for row in rows}) != len(rows):
        raise ValueError("duplicate review_id")
    for row in rows:
        if row.get("selected_d10") is not False or row.get("coordinate") is not None or row.get("ratified") is not False:
            raise ValueError(f"authority leak in {row.get('review_id')}")

    current_names = [str(row.get("semantic_name", "")).upper() for row in inventory["rows"]]
    current_ids = [row.get("stable_id") for row in inventory["rows"]]
    if len(set(current_names)) != len(current_names):
        raise ValueError("duplicate D10 semantic name")
    if len(set(current_ids)) != len(current_ids):
        raise ValueError("duplicate D10 stable_id")

    ob = next((r for r in rows if r.get("review_id") == "L15-31"), None)
    if (
        not ob
        or ob.get("exact_d1_d9_name_matches")
        or not any(x.get("name", "").upper() == "MAPATOMS" for x in ob.get("exact_selected_d10_name_matches", []))
        or ob.get("exact_name_residuals") != ["OBARRAY", "OBLIST"]
    ):
        raise ValueError("MAPATOMS must be deduplicated against selected D10; only OBARRAY/OBLIST remains on HOLD")

    current_set = set(current_names)
    lower_names = {
        str(name).upper()
        for dom in foundation["domains"].values()
        for name in dom["residents"].values()
    }
    if "MAPATOMS" not in current_set:
        raise ValueError("expected existing selected D10 MAPATOMS row was not found")
    if current_set & lower_names:
        raise ValueError("live D10 contains an exact-name duplicate of ratified D1-D9")
    if "OBARRAY" in current_set or "OBLIST" in current_set or "OBARRAY" in lower_names or "OBLIST" in lower_names:
        raise ValueError("OBARRAY/OBLIST now has an exact-name collision: update hold disposition before review")

    return {
        "rows_reconciled": len(rows),
        "d10_historical_selected": snapshot["d10_selected"],
        "d10_live_selected": live_count,
        "d10_live_unplaced": live_accounting["unplaced_selected_candidates"],
        "d10_live_remaining": live_accounting["remaining_semantic_inventory"],
        "selected_added_by_historical_audit": 0,
        "coordinates_added_by_historical_audit": 0,
        "ratifications_added_by_historical_audit": 0,
    }


def main() -> int:
    review = load(REVIEW)
    foundation = load(FOUNDATION)
    inventory = load(INVENTORY)
    transition_history = load(TRANSITIONS) if TRANSITIONS.exists() else None
    try:
        print(json.dumps(verify(review, foundation, inventory, transition_history), ensure_ascii=False, sort_keys=True))
    except ValueError as error:
        print("D10-HISTORICAL-LISP15: FAIL " + str(error))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
