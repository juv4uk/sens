#!/usr/bin/env python3
"""Fail-closed historical coverage evidence plus exact append-only D10 transitions."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/d10-historical-coverage-gap-audit-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
DIALECT = ROOT / "docs/DIALECT-COMPARISON.md"
BASELINE = ROOT / "knowledge/d10-growth-baseline-v1.json"
TRANSITIONS = ROOT / "knowledge/d10-historical-gap-transitions-v1.json"

PROTECTED_FIELDS = (
    "stable_id", "semantic_name", "source_class", "relation_class",
    "behavior", "coordinate", "coordinate_basis", "ratified_resident",
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def transition_index(manifest):
    require(manifest.get("schema") == "d10-historical-gap-transitions/v1",
            "wrong transition manifest schema")
    require(manifest.get("status") ==
            "TRANSITION-OBSERVATION-ALLOWLIST-NOT-SELECTION-AUTHORITY",
            "transition manifest has selection authority")
    snapshot = manifest.get("historical_snapshot", {})
    require(snapshot == {
        "inventory_blob": "73dd518469f972c55411e004b70b054ba8b3ec86",
        "selected": 625,
        "ratified": 0,
    }, "historical transition baseline changed")
    transitions = manifest.get("transitions")
    require(isinstance(transitions, list), "transitions must be a list")
    by_review = {}
    names = set()
    for item in transitions:
        review_id = item.get("review_id")
        name = str(item.get("semantic_name", "")).upper()
        require(review_id and name, "transition requires review_id and semantic_name")
        require(review_id not in by_review, f"duplicate transition review_id: {review_id}")
        require(name not in names, f"duplicate transition semantic name: {name}")
        require(item.get("selection_pr"), f"{review_id}: selection PR is not recorded")
        require(item.get("stable_id") and item.get("source_class"),
                f"{review_id}: stable_id/source_class required")
        require(item.get("required_provenance"),
                f"{review_id}: source provenance allowlist is empty")
        by_review[review_id] = item
        names.add(name)
    return by_review


def verify(ledger, inv, foundation, dialect, baseline, manifest):
    require(ledger.get("schema") == "d10-historical-coverage-gap-audit/v1",
            "wrong historical audit schema")
    require(ledger.get("status") == "RESEARCH-COVERAGE-GAPS-ONLY",
            "historical audit acquired authority")
    require(ledger.get("snapshot", {}).get("ratified") == 0,
            "historical snapshot is not unratified")

    rows = inv.get("rows")
    counts = inv.get("accounting", {})
    require(isinstance(rows, list), "live inventory rows must be a list")
    selected_count = counts.get("selected_semantic_candidates")
    require(len(rows) == selected_count, "inventory row/accounting mismatch")
    require(counts.get("ratified_d10_residents") == 0,
            "D10 must remain unratified")
    require(inv.get("width") == 10 and inv.get("capacity") == 1024,
            "unexpected D10 width/capacity")
    require(counts.get("law_forced_coordinates") == 256,
            "D10 law-forced selector count changed")
    require(counts.get("unplaced_selected_candidates") == selected_count - 256,
            "live unplaced count inconsistent")
    require(counts.get("remaining_semantic_inventory") == 1024 - selected_count,
            "live remaining count inconsistent")

    selected_by_name = {}
    selected_by_id = {}
    for row in rows:
        name = str(row.get("semantic_name", "")).upper()
        stable_id = row.get("stable_id")
        require(name and stable_id, "live inventory row lacks name/stable_id")
        require(name not in selected_by_name, f"duplicate current D10 name: {name}")
        require(stable_id not in selected_by_id, f"duplicate current D10 stable_id: {stable_id}")
        selected_by_name[name] = row
        selected_by_id[stable_id] = row

    lower = {
        str(name).upper()
        for domain in foundation.get("domains", {}).values()
        for name in domain.get("residents", {}).values()
    }

    # Immutable historical baseline protects all 625 old meanings as D10 grows.
    require(baseline.get("schema") == "d10-growth-baseline/v1",
            "wrong immutable baseline schema")
    require(baseline.get("origin_inventory_git_blob") ==
            "73dd518469f972c55411e004b70b054ba8b3ec86",
            "immutable 625 baseline origin changed")
    require(baseline.get("frozen_count") == 625,
            "immutable historical baseline size changed")
    require(tuple(baseline.get("protected_fields", ())) == PROTECTED_FIELDS,
            "baseline protected-field list changed")
    frozen_rows = baseline.get("rows")
    require(isinstance(frozen_rows, list) and len(frozen_rows) == 625,
            "immutable baseline rows missing or truncated")
    for frozen in frozen_rows:
        sid = frozen.get("stable_id")
        live = selected_by_id.get(sid)
        require(live is not None, f"historic D10 stable_id disappeared: {sid}")
        for field in PROTECTED_FIELDS:
            require(live.get(field) == frozen.get(field),
                    f"historic D10 row changed: {sid}.{field}")

    require(len({r["semantic_name"].upper() for r in rows}) == len(rows),
            "duplicate semantic name in selected D10")
    require(len(ledger.get("historic_family_coverage", [])) >= 10,
            "historical family census incomplete")
    gaps = ledger.get("exact_name_absent_research", [])
    require(len(gaps) >= 15, "historical exact-name gap census incomplete")
    require(len({r["review_id"] for r in gaps}) == len(gaps),
            "duplicate historical review_id")
    require(len({r["historical_spelling"].upper() for r in gaps}) == len(gaps),
            "duplicate historical spelling")
    transitions = transition_index(manifest)

    for family in ledger["historic_family_coverage"]:
        require(family.get("status") != "EXHAUSTIVE",
                "historical completeness was not proved")
        require(family.get("evidence") and
                str(family.get("historical_source", "")).startswith("https://"),
                "historical family missing source evidence")
        require(family.get("in_repo"), "historical family missing in-repo coverage note")

    for name in ("Franz Lisp", "ZetaLisp", "EuLisp", "ISLISP"):
        require(name in dialect, "historical omission lost from in-repo appendix")

    accepted_transitions = []
    for record in gaps:
        review_id = record.get("review_id")
        name = str(record.get("historical_spelling", "")).upper()

        # These fields intentionally describe the frozen 625-row historical audit.
        require(record.get("exact_name_in_d1_d10") is False,
                f"{review_id}: historical exact-name fact was rewritten")
        require(record.get("selected_in_inventory") is False,
                f"{review_id}: historical selected-at-audit fact was rewritten")
        require(record.get("semantically_novel") is None,
                f"{review_id}: novelty was asserted without review")
        require(record.get("coordinate") is None and record.get("ratified") is False,
                f"{review_id}: historical row acquired coordinate/ratification")
        require(record.get("physical_t5_authorized") is False,
                f"{review_id}: historical row acquired T5 authority")
        require(str(record.get("primary_url", "")).startswith("https://"),
                f"{review_id}: primary source URL missing")
        require(record.get("observable_question"),
                f"{review_id}: observable question missing")
        if record.get("status") in ("HOLD-D2-CONTROL", "HOLD-D2-SYNTAX"):
            require(record.get("coordinate") is None,
                    f"{review_id}: only D2 owns language control")

        live = selected_by_name.get(name)
        if live is None:
            require(name not in lower,
                    f"{review_id}: exact name now exists in D1-D9: {name}")
            require(str(record.get("status", "")).startswith("HOLD-"),
                    f"{review_id}: unresolved historical row lost HOLD status")
            continue

        # A present-day exact-name match is tolerated only for an explicitly
        # allowlisted append-only transition. The historical ledger stays intact.
        transition = transitions.get(review_id)
        require(transition is not None,
                f"{review_id}: exact name now selected without approved transition: {name}")
        require(name == str(transition["semantic_name"]).upper(),
                f"{review_id}: transition name mismatch")
        require(live.get("stable_id") == transition["stable_id"],
                f"{review_id}: selected row stable_id mismatch")
        require(live.get("source_class") == transition["source_class"],
                f"{review_id}: selected row source_class mismatch")
        require(live.get("coordinate") is None and
                live.get("coordinate_basis") == "UNPLACED",
                f"{review_id}: research candidate got a coordinate")
        require(live.get("ratified_resident") is False,
                f"{review_id}: research candidate was ratified")
        require(live.get("proposal_status") == "pending-owner-review",
                f"{review_id}: proposal status must remain pending-owner-review")
        require(live.get("status") == "SELECTED-RESEARCH-CANDIDATE",
                f"{review_id}: live row is not a research candidate")
        provenance = set(live.get("provenance", []))
        missing = set(transition["required_provenance"]) - provenance
        require(not missing,
                f"{review_id}: selected row missing provenance: {sorted(missing)}")
        require(name not in lower,
                f"{review_id}: selected candidate collides with D1-D9: {name}")
        accepted_transitions.append(review_id)

    for item in ledger.get("known_not_missing", []):
        name = str(item["name"]).upper()
        require(name in selected_by_name or name in lower,
                f"existing identity has disappeared: {name}")

    return {
        "historical_families": len(ledger["historic_family_coverage"]),
        "exact_name_gaps": len(gaps),
        "live_selected": len(selected_by_name),
        "newly_selected_by_this_checker": 0,
        "newly_ratified": 0,
        "accepted_historical_transitions": sorted(accepted_transitions),
        "ratified_d10_residents": counts["ratified_d10_residents"],
    }


def synthetic_selection(inv, transition):
    """Build a test-only current-inventory view with one allowlisted row."""
    tmp = copy.deepcopy(inv)
    row = {
        "stable_id": transition["stable_id"],
        "semantic_name": transition["semantic_name"],
        "source_class": transition["source_class"],
        "relation_class": "TEST-ONLY-TRANSITION-WITNESS",
        "behavior": "test-only; not persisted and not semantic authority",
        "coordinate": None,
        "coordinate_basis": "UNPLACED",
        "ratified_resident": False,
        "proposal_status": "pending-owner-review",
        "status": "SELECTED-RESEARCH-CANDIDATE",
        "provenance": list(transition["required_provenance"]),
    }
    tmp["rows"].append(row)
    tmp["accounting"]["selected_semantic_candidates"] += 1
    tmp["accounting"]["unplaced_selected_candidates"] += 1
    tmp["accounting"]["remaining_semantic_inventory"] -= 1
    return tmp, row


def self_test(ledger, inv, foundation, dialect, baseline, manifest):
    transitions = transition_index(manifest)
    baseline_result = verify(ledger, inv, foundation, dialect, baseline, manifest)

    # Prove the frozen historical result can remain unchanged while a listed
    # source-backed candidate appears in a later current inventory.
    for review_id in ("HIST-GAP-009", "HIST-GAP-011"):
        transition = transitions[review_id]
        synthetic_inv, _ = synthetic_selection(inv, transition)
        accepted = verify(ledger, synthetic_inv, foundation, dialect, baseline, manifest)
        require(review_id in accepted["accepted_historical_transitions"],
                f"{review_id}: valid append-only transition was not accepted")

        mutations = (
            ("stable_id", "invented.stable-id"),
            ("source_class", "UNVERIFIED"),
            ("coordinate", "0000000000"),
            ("coordinate_basis", "PLACED"),
            ("ratified_resident", True),
            ("proposal_status", "ratified"),
            ("status", "RATIFIED"),
        )
        for field, bad_value in mutations:
            bad_inv, bad_row = synthetic_selection(inv, transition)
            bad_row[field] = bad_value
            try:
                verify(ledger, bad_inv, foundation, dialect, baseline, manifest)
            except AssertionError:
                pass
            else:
                raise AssertionError(
                    f"unsafe {review_id} transition was not blocked: {field}={bad_value!r}"
                )
        bad_inv, bad_row = synthetic_selection(inv, transition)
        bad_row["provenance"] = []
        try:
            verify(ledger, bad_inv, foundation, dialect, baseline, manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"{review_id}: missing provenance was not blocked")

    # Historical claims themselves must remain immutable.
    for change in (
        {"coordinate": "0000000000"}, {"ratified": True},
        {"selected_in_inventory": True}, {"semantically_novel": True},
        {"historical_spelling": "CALL/CC"}, {"status": "RATIFIED"},
    ):
        tmp = copy.deepcopy(ledger)
        tmp["exact_name_absent_research"][0].update(change)
        try:
            verify(tmp, inv, foundation, dialect, baseline, manifest)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"unsafe historical mutation was not blocked: {change}")

    tmp = copy.deepcopy(ledger)
    tmp["historic_family_coverage"][0]["status"] = "EXHAUSTIVE"
    try:
        verify(tmp, inv, foundation, dialect, baseline, manifest)
    except AssertionError:
        pass
    else:
        raise AssertionError("false exhausted history not blocked")

    # An unlisted current candidate colliding with a historical HOLD must block.
    fake_ledger = copy.deepcopy(ledger)
    fake_record = copy.deepcopy(fake_ledger["exact_name_absent_research"][0])
    fake_record["historical_spelling"] = "UNLISTED-RESEARCH-NAME"
    fake_record["review_id"] = "HIST-GAP-FAKE"
    fake_ledger["exact_name_absent_research"].append(fake_record)
    fake_inv = copy.deepcopy(inv)
    fake_inv["rows"].append({
        "stable_id": "test.unlisted.transition",
        "semantic_name": "UNLISTED-RESEARCH-NAME",
        "source_class": "UNVERIFIED",
        "relation_class": "TEST-ONLY",
        "behavior": "test only",
        "coordinate": None,
        "coordinate_basis": "UNPLACED",
        "ratified_resident": False,
        "proposal_status": "pending-owner-review",
        "status": "SELECTED-RESEARCH-CANDIDATE",
        "provenance": ["test-only"],
    })
    fake_inv["accounting"]["selected_semantic_candidates"] += 1
    fake_inv["accounting"]["unplaced_selected_candidates"] += 1
    fake_inv["accounting"]["remaining_semantic_inventory"] -= 1
    try:
        verify(fake_ledger, fake_inv, foundation, dialect, baseline, manifest)
    except AssertionError:
        pass
    else:
        raise AssertionError("unlisted historical transition was not blocked")

    return baseline_result


def main():
    read = lambda path: json.loads(path.read_text(encoding="utf-8"))
    ledger = read(LEDGER)
    inventory = read(INVENTORY)
    foundation = read(FOUNDATION)
    dialect = DIALECT.read_text(encoding="utf-8")
    baseline = read(BASELINE)
    manifest = read(TRANSITIONS)
    result = (
        self_test(ledger, inventory, foundation, dialect, baseline, manifest)
        if "--self-test" in sys.argv
        else verify(ledger, inventory, foundation, dialect, baseline, manifest)
    )
    print("D10-HISTORICAL-GAPS PASS", json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
