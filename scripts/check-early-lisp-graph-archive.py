#!/usr/bin/env python3
"""Fail-closed archival guard for the early-Lisp graph research corpus."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "knowledge/early-lisp-graph-historical-evidence-v1.json"
FOUND = ROOT / "knowledge/d1-d9-foundation.json"
D10 = ROOT / "knowledge/d10-v1-semantic-inventory.json"
D3 = ROOT / "lib/domains/d3.lisp"
TRANSITIONS = ROOT / "knowledge/d10-selection-transition-history.json"
BASELINE_D10_BLOB = "73dd518469f972c55411e004b70b054ba8b3ec86"
CAPACITY = 1024
LAW_FORCED_COORDINATES = 256


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    rel = str(path.relative_to(ROOT))
    return subprocess.run(
        ["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, check=True,
        capture_output=True, text=True
    ).stdout.strip()


def git_blob(data):
    """SHA-1 of canonical repo JSON, matching the D10 inventory Git blob."""
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload).hexdigest()


def norm(v):
    s = str(v).strip().upper().replace("()", "EMPTY-LIST")
    return re.sub(r"[^A-Z0-9?!+*/<>=.-]", "", s)


def expected_crosswalk():
    return {
        "()": {"historical_code": "000", "current_d3_code": "000", "current_name": "()"},
        "QUOTE": {"historical_code": "001", "current_d3_code": "001", "current_name": "QUOTE"},
        "ATOM": {"historical_code": "010", "current_d3_code": "010", "current_name": "ATOM"},
        "EQ": {"historical_code": "011", "current_d3_code": "101", "current_name": "EQ"},
        "CONS": {"historical_code": "100", "current_d3_code": "111", "current_name": "CONS"},
        "CAR": {"historical_code": "101", "current_d3_code": "100", "current_name": "CAR"},
        "CDR": {"historical_code": "110", "current_d3_code": "011", "current_name": "CDR"},
        "COND": {"historical_code": "111", "current_d3_code": "110", "current_name": "COND"},
    }


def fail(condition, message):
    if not condition:
        raise ValueError(message)


def _verify_appended_rows(rows, transition):
    added_ids = transition.get("added_stable_ids")
    delta = transition.get("delta_selected")
    fail(isinstance(added_ids, list) and bool(added_ids), "transition missing added_stable_ids")
    fail(len(added_ids) == len(set(added_ids)), "transition duplicates added stable IDs")
    fail(delta == len(added_ids) == len(rows), "transition append count mismatch")
    fail([r.get("stable_id") for r in rows] == added_ids, "D10 tail differs from explicit transition IDs")
    for row in rows:
        fail(bool(row.get("semantic_name")) and bool(row.get("behavior")), "appended D10 row lacks name/law")
        has_inline_source = bool(row.get("provenance"))
        has_primary_reference = bool(row.get("primary_url")) and bool(row.get("source_section") or row.get("source_path") or row.get("historical_source"))
        has_pinned_source_path = bool(row.get("source_path")) and bool(row.get("source_sha") or row.get("source_line"))
        fail(has_inline_source or has_primary_reference or has_pinned_source_path,
             "appended D10 row lacks inline provenance or explicit source pointer")
        fail(row.get("status") == "SELECTED-RESEARCH-CANDIDATE", "appended row is not a selected research candidate")
        fail(row.get("coordinate") is None, "append event assigned a coordinate")
        fail(row.get("ratified_resident") is False, "append event ratified a resident")
        fail(row.get("coordinate_basis") in (None, "UNPLACED"), "append event forged coordinate basis")
        fail(row.get("language_visible") is not False, "append event includes non-language-visible row")
        fail(row.get("mechanism_only") is not True, "append event includes mechanism-only row")
        fail(row.get("falsified") is not True, "append event includes falsified row")


def _compatibility_historical_view(current, expected_blob):
    """Accept one exact, independently checked known-batch compatibility witness."""
    helper = ROOT / "scripts/d10_historical_snapshot_compat.py"
    batch = ROOT / "knowledge/d10-historical-primary-selected-20261009.json"
    if not helper.exists() or not batch.exists():
        raise ValueError("D10 differs from pinned archival snapshot without explicit transition history")
    spec = importlib.util.spec_from_file_location("d10_historical_snapshot_compat", helper)
    fail(spec is not None and spec.loader is not None, "cannot import D10 historical compatibility witness")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    historic = module.historic_view(copy.deepcopy(current), expected_blob)
    fail(git_blob(historic) == expected_blob, "compatibility witness failed to reconstruct the archived D10 blob")
    return historic


def historical_d10_view(current, expected_blob=BASELINE_D10_BLOB, transition_history=None):
    """Reconstruct the pinned 625-row archive only from hash-linked append events."""
    fail(expected_blob == BASELINE_D10_BLOB, "unsupported D10 archive baseline SHA")
    work = copy.deepcopy(current)
    if git_blob(work) == expected_blob:
        return work

    history = transition_history
    if history is None and TRANSITIONS.exists():
        history = load(TRANSITIONS)
    if history is None:
        return _compatibility_historical_view(work, expected_blob)

    fail(history.get("schema") == "d10-selection-transition-history/v1", "wrong D10 transition schema")
    fail(history.get("status") == "RESEARCH-ONLY-NO-RATIFICATION", "transition history may not ratify D10")
    base = history.get("baseline", {})
    fail(base.get("inventory_blob_sha") == expected_blob, "transition baseline SHA differs from historical archive")
    fail(base.get("selected_count") == 625, "transition baseline count drift")
    fail(base.get("selector_coordinates") == LAW_FORCED_COORDINATES, "transition selector-law count drift")
    fail(base.get("ratified_d10_residents") == 0, "transition baseline claims D10 ratification")

    transitions = history.get("transitions")
    fail(isinstance(transitions, list), "transition history missing transitions list")
    ids = [t.get("id") for t in transitions]
    fail(all(isinstance(i, str) and i for i in ids) and len(ids) == len(set(ids)),
         "transition history has missing/duplicate event IDs")
    for t in transitions:
        fail(t.get("coordinates_added") == 0 and t.get("ratified_added") == 0,
             "transition event assigns coordinates or ratification")
        fail(t.get("previous_selected", -1) + t.get("delta_selected", -1) == t.get("resulting_selected", -2),
             "transition count arithmetic mismatch")

    visited = set()
    while git_blob(work) != expected_blob:
        current_blob = git_blob(work)
        fail(current_blob not in visited, "cycle in append-transition history")
        visited.add(current_blob)
        events = [t for t in transitions if t.get("resulting_inventory_blob_sha") == current_blob]
        if not events:
            # A second, narrowly scoped compatibility witness may validate its
            # own exact append batch. It never accepts an arbitrary SHA/count.
            return _compatibility_historical_view(work, expected_blob)
        fail(len(events) == 1, "multiple events claim the same resulting D10 blob")
        event = events[0]
        selected = event.get("resulting_selected")
        prior = event.get("previous_selected")
        delta = event.get("delta_selected")
        fail(selected == len(work.get("rows", [])), "transition resulting count differs from live D10")
        fail(prior + delta == selected and delta == len(event.get("added_stable_ids", [])),
             "transition row-count arithmetic mismatch")
        fail(work.get("accounting", {}).get("selected_semantic_candidates") == selected,
             "live D10 accounting differs from transition")
        fail(work.get("accounting", {}).get("law_forced_coordinates") == LAW_FORCED_COORDINATES,
             "append transition changed the 256 law-forced selector coordinates")
        fail(work.get("accounting", {}).get("ratified_d10_residents") == 0,
             "D10 ratification appeared during an archival-only transition")

        added_ids = event["added_stable_ids"]
        _verify_appended_rows(work["rows"][-len(added_ids):], event)
        previous_blob = event.get("previous_inventory_blob_sha")
        fail(isinstance(previous_blob, str) and len(previous_blob) == 40, "transition missing previous SHA")
        sources = event.get("appended_sources", [])
        fail(isinstance(sources, list), "transition appended_sources must be a list")
        if sources:
            fail(work.get("sources", [])[-len(sources):] == sources, "D10 source tail differs from transition")
            del work["sources"][-len(sources):]
        del work["rows"][-len(added_ids):]
        work["accounting"]["selected_semantic_candidates"] = prior
        work["accounting"]["unplaced_selected_candidates"] = prior - LAW_FORCED_COORDINATES
        work["accounting"]["remaining_semantic_inventory"] = CAPACITY - prior
        work["accounting"]["ratified_d10_residents"] = 0
        fail(git_blob(work) == previous_blob, "append reversal did not reproduce previous inventory SHA")

    fail(len(work["rows"]) == 625, "archive reconstruction did not recover 625 baseline rows")
    return work


def validate(d, f, d10, d3, transition_history=None):
    errors = []
    if d.get("schema") != "early-lisp-graph-historical-evidence/v1":
        errors.append("wrong schema")
    if d.get("status") != "RESEARCH-ARCHIVE-NOT-CANONICAL-SEMANTIC-AUTHORITY":
        errors.append("status must remain archive-only")
    snap = d.get("current_authority_snapshot", {})
    for key, path in (("d1_d9_foundation_blob_sha", FOUND), ("d3_table_blob_sha", D3)):
        if snap.get(key) != sha(path):
            errors.append("stale authority hash: " + key)
    if snap.get("d10_inventory_blob_sha") != BASELINE_D10_BLOB:
        errors.append("archive D10 baseline SHA was rewritten")
    try:
        archived = historical_d10_view(d10, snap.get("d10_inventory_blob_sha"), transition_history)
        if git_blob(archived) != snap.get("d10_inventory_blob_sha"):
            errors.append("D10 archive view SHA mismatch")
        if len(archived.get("rows", [])) != snap.get("d10_selected"):
            errors.append("D10 archive selected count mismatch")
        if archived.get("accounting", {}).get("ratified_d10_residents") != snap.get("d10_ratified"):
            errors.append("D10 archive ratification snapshot mismatch")
    except (ValueError, KeyError, IndexError, TypeError, AssertionError) as error:
        errors.append("D10 append-only history invalid: " + str(error))

    live_count = len(d10.get("rows", []))
    accounting = d10.get("accounting", {})
    if accounting.get("selected_semantic_candidates") != live_count:
        errors.append("live D10 selected count mismatch")
    if live_count < snap.get("d10_selected", 0) or live_count > CAPACITY:
        errors.append("live D10 count is outside monotonic research bounds")
    if accounting.get("law_forced_coordinates") != LAW_FORCED_COORDINATES:
        errors.append("live selector-law coordinate count changed")
    if accounting.get("unplaced_selected_candidates") != live_count - LAW_FORCED_COORDINATES:
        errors.append("live D10 unplaced count mismatch")
    if accounting.get("remaining_semantic_inventory") != CAPACITY - live_count:
        errors.append("live D10 remaining count mismatch")
    if accounting.get("ratified_d10_residents") != 0:
        errors.append("live D10 ratified count must remain zero")

    if d.get("current_d3_crosswalk") != expected_crosswalk():
        errors.append("D3 crosswalk mismatch")
        return errors
    for code, name in [("000", "()"), ("001", "QUOTE"), ("010", "ATOM"), ("011", "CDR"),
                       ("100", "CAR"), ("101", "EQ"), ("110", "COND"), ("111", "CONS")]:
        if f"({code} " not in d3:
            errors.append("canonical D3 row missing: " + code + " " + name)
    counts = d.get("dataset_counts", {})
    expected = {"nodes": 34, "edges": 129, "falsifications": 10, "equivalence_evidence": 3,
                "bija3_pressure": 16, "selector_relation_kernel": 4}
    if counts != expected:
        errors.append("dataset counts mismatch")
    sets = d.get("datasets", {})
    for key, total in (("nodes", 34), ("edges", 129), ("falsification_ledger", 10),
                       ("equivalence_evidence", 3), ("bija3_pressure", 16), ("selector_relation_kernel", 4)):
        rows = sets.get(key, [])
        if len(rows) != total:
            errors.append(key + " row count mismatch")
        for row in rows:
            if row.get("coordinate", "MISSING") is not None:
                errors.append(key + ": active coordinate must be null")
            if row.get("selected_d10_candidate") is not False:
                errors.append(key + ": D10 selected flag must be false")
            if row.get("ratified") is not False:
                errors.append(key + ": ratified flag must be false")
    for node in sets.get("nodes", []):
        snaprow = node.get("historical_snapshot", {})
        if not snaprow:
            errors.append("node lost historical code snapshot: " + node.get("historical_id", "?"))
        for match in node.get("current_exact_name_matches", {}).get("d10_selected", []):
            if match.get("coordinate") is not None:
                errors.append("node D10 match imported coordinate")
    if any(n.get("current_d3_crosswalk") and n["current_d3_crosswalk"].get("current_d3_code")
           != expected_crosswalk()[n["current_d3_crosswalk"]["current_name"]]["current_d3_code"]
           for n in sets.get("nodes", [])):
        errors.append("node crosswalk mismatch")
    if any(row.get("status") not in {"falsified", "superseded-premise"} for row in sets.get("falsification_ledger", [])):
        errors.append("falsification ledger introduced non-falsified premise status")
    return errors


def _synthetic_transition(d10):
    current = copy.deepcopy(d10)
    row = copy.deepcopy(current["rows"][-1])
    row.update({
        "stable_id": "d10.test.archive-transition.v1",
        "semantic_name": "TEST-ARCHIVE-APPEND",
        "behavior": "synthetic row used only to exercise a transition validator",
        "provenance": ["synthetic test fixture"],
        "coordinate": None,
        "coordinate_basis": "UNPLACED",
        "ratified_resident": False,
        "status": "SELECTED-RESEARCH-CANDIDATE",
    })
    source = "knowledge/d10-test-archive-transition.json"
    current["rows"].append(row)
    current["sources"].append(source)
    current["accounting"]["selected_semantic_candidates"] += 1
    current["accounting"]["unplaced_selected_candidates"] += 1
    current["accounting"]["remaining_semantic_inventory"] -= 1
    event = {
        "id": "test.archive.append",
        "previous_inventory_blob_sha": git_blob(d10),
        "resulting_inventory_blob_sha": git_blob(current),
        "added_stable_ids": [row["stable_id"]],
        "appended_sources": [source],
        "coordinates_added": 0,
        "ratified_added": 0,
        "delta_selected": 1,
        "previous_selected": len(d10["rows"]),
        "resulting_selected": len(current["rows"]),
    }
    history = {
        "schema": "d10-selection-transition-history/v1",
        "status": "RESEARCH-ONLY-NO-RATIFICATION",
        "baseline": {
            "inventory_blob_sha": git_blob(d10),
            "selected_count": len(d10["rows"]),
            "selector_coordinates": LAW_FORCED_COORDINATES,
            "ratified_d10_residents": 0,
        },
        "transitions": [event],
    }
    return current, history


def main():
    d, f, d10 = load(ART), load(FOUND), load(D10)
    d3 = D3.read_text(encoding="utf-8")
    history = load(TRANSITIONS) if TRANSITIONS.exists() else None
    errors = validate(d, f, d10, d3, history)
    if errors:
        for error in errors:
            print("FAIL:", error, file=sys.stderr)
        return 1
    print(
        f"Early-Lisp graph archive: {d['dataset_counts']['nodes']} nodes, "
        f"{d['dataset_counts']['edges']} edges, corrected D3 crosswalk; "
        f"historical D10={d['current_authority_snapshot']['d10_selected']}, "
        f"live D10={len(d10['rows'])} PASS"
    )
    if "--self-test" in sys.argv:
        cases = []
        bad = copy.deepcopy(d)
        bad["datasets"]["nodes"][0]["coordinate"] = "011"
        cases.append(("coordinate", bad))
        bad = copy.deepcopy(d)
        bad["datasets"]["nodes"][0]["selected_d10_candidate"] = True
        cases.append(("selected", bad))
        bad = copy.deepcopy(d)
        bad["current_d3_crosswalk"]["CAR"]["current_d3_code"] = "101"
        cases.append(("crosswalk", bad))
        failures = [label for label, item in cases if not validate(item, f, d10, d3, history)]
        if failures:
            print("FAIL: negative controls accepted: " + ", ".join(failures), file=sys.stderr)
            return 1

        try:
            baseline_for_test = historical_d10_view(
                d10, d["current_authority_snapshot"]["d10_inventory_blob_sha"], history
            )
            synthetic, synthetic_history = _synthetic_transition(baseline_for_test)
            reconstructed = historical_d10_view(
                synthetic, d["current_authority_snapshot"]["d10_inventory_blob_sha"], synthetic_history
            )
            if git_blob(reconstructed) != git_blob(baseline_for_test):
                failures.append("append-history-reconstruction")
        except (ValueError, KeyError, IndexError, TypeError, AssertionError):
            failures.append("append-history-reconstruction")

        # An empty explicit ledger must never turn synthetic growth into a pass,
        # even if another compatibility helper exists for a different exact batch.
        empty_history = {
            "schema": "d10-selection-transition-history/v1",
            "status": "RESEARCH-ONLY-NO-RATIFICATION",
            "baseline": {
                "inventory_blob_sha": d["current_authority_snapshot"]["d10_inventory_blob_sha"],
                "selected_count": d["current_authority_snapshot"]["d10_selected"],
                "selector_coordinates": LAW_FORCED_COORDINATES,
                "ratified_d10_residents": 0,
            },
            "transitions": [],
        }
        try:
            baseline_for_test = historical_d10_view(
                d10, d["current_authority_snapshot"]["d10_inventory_blob_sha"], history
            )
            unrecorded, _ = _synthetic_transition(baseline_for_test)
            errs = validate(d, f, unrecorded, d3, empty_history)
            if not any("D10 append-only history invalid" in e for e in errs):
                failures.append("unrecorded-growth-control")
        except (ValueError, KeyError, IndexError, TypeError, AssertionError):
            # Rejection is the expected result for unrecorded growth.
            pass
        try:
            baseline_for_test = historical_d10_view(
                d10, d["current_authority_snapshot"]["d10_inventory_blob_sha"], history
            )
            mutated, mutant_history = _synthetic_transition(baseline_for_test)
            mutated["rows"][0]["behavior"] = "mutated historical law"
            mutant_history["transitions"][0]["resulting_inventory_blob_sha"] = git_blob(mutated)
            historical_d10_view(
                mutated, d["current_authority_snapshot"]["d10_inventory_blob_sha"], mutant_history
            )
            failures.append("old-row-mutation-control")
        except (ValueError, KeyError, IndexError, TypeError, AssertionError):
            pass
        # A new D10 row without inline provenance or an explicit source pointer
        # must fail closed even if the transition hash is updated to match it.
        try:
            baseline_for_test = historical_d10_view(
                d10, d["current_authority_snapshot"]["d10_inventory_blob_sha"], history
            )
            source_free, source_free_history = _synthetic_transition(baseline_for_test)
            appended = source_free["rows"][-1]
            for field in (
                "provenance", "primary_url", "source_section", "source_path",
                "source_file", "source_sha", "source_line", "historical_source",
            ):
                appended.pop(field, None)
            source_free_history["transitions"][0]["resulting_inventory_blob_sha"] = git_blob(source_free)
            historical_d10_view(
                source_free, d["current_authority_snapshot"]["d10_inventory_blob_sha"], source_free_history
            )
            failures.append("appended-row-source-provenance-control")
        except (ValueError, KeyError, IndexError, TypeError, AssertionError):
            pass

        if failures:
            print("FAIL: negative archive/authority controls: " + ", ".join(failures), file=sys.stderr)
            return 1
        print("archive authority controls + explicit append-transition reconstruction PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
