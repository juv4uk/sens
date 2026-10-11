#!/usr/bin/env python3
"""Fail-closed audit for a pending CLASS-OF D10 proposal; never selects it."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "knowledge/d10-class-of-proposal-v1.json"
LEDGER = ROOT / "knowledge/d10-proposal-ledger.tsv"
FOUND = ROOT / "knowledge/d1-d9-foundation.json"
INV = ROOT / "knowledge/d10-v1-semantic-inventory.json"
HISTORY = ROOT / "knowledge/d10-selection-transition-history.json"
ORACLE = ROOT / "knowledge/d10-clos-slot-observation-v1.json"
ORACLE_LISP = ROOT / "tests/oracles/d10_clos_slot_states.lisp"
PROPOSAL_ID = "D10P-4870"
SEMANTIC_NAME = "CLASS-OF"
DONOR_COMMIT = "c67db6cdd820dea8d3a110caed359507c0a2d7a4"
DONOR_PROVENANCE = (
    f"juv4uk/sens@{DONOR_COMMIT}:knowledge/d10-clos-slot-observation-v1.json:38-43"
)
LEDGER_FIELDS = (
    "proposal_id", "surface_uk", "surface_ukr", "semantic_name",
    "semantic_law", "width", "donor_provenance", "dedup_check",
    "ownership_test", "blocked_source", "status", "ratified",
)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def read_ledger() -> list[dict[str, str]]:
    with LEDGER.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, delimiter="\t")
        if tuple(reader.fieldnames or ()) != LEDGER_FIELDS:
            raise ValueError("proposal ledger header drift")
        return list(reader)


def check(
    data: dict[str, Any],
    ledger: list[dict[str, str]],
    foundation: dict[str, Any],
    inventory: dict[str, Any],
    history: dict[str, Any],
    oracle: dict[str, Any],
    *,
    foundation_sha: str,
    inventory_sha: str,
    oracle_sha: str,
    oracle_lisp_sha: str,
    oracle_lisp: str,
) -> list[str]:
    errors: list[str] = []
    if data.get("schema") != "d10-class-of-proposal/v1":
        errors.append("wrong schema")
    if data.get("status") != "PENDING-OWNER-REVIEW":
        errors.append("status must stay pending")
    if data.get("semantic_name") != SEMANTIC_NAME:
        errors.append("semantic name mismatch")
    if data.get("selected_d10_candidate") is not False:
        errors.append("must not be selected")
    if data.get("ratified") is not False:
        errors.append("must not be ratified")
    if data.get("coordinate", "MISSING") is not None:
        errors.append("coordinate must be null")
    if data.get("physical_t5_authorized") is not False:
        errors.append("physical T5 must remain false")

    rows = [r for r in ledger if r.get("proposal_id") == PROPOSAL_ID]
    if len(rows) != 1:
        errors.append("ledger must contain exactly one D10P-4870 row")
    else:
        row = rows[0]
        expected = {
            "surface_uk": "безпосередній-клас",
            "surface_ukr": "клас-прямого-екземпляра",
            "semantic_name": SEMANTIC_NAME,
            "semantic_law": data.get("law", {}).get("statement", ""),
            "width": "D10",
            "donor_provenance": DONOR_PROVENANCE,
            "dedup_check": (
                f"D1-D9@{foundation_sha}=PENDING;D10@"
                f"{data.get('source_snapshot', {}).get('d10_inventory_blob_sha', '')}=PENDING"
            ),
            "blocked_source": "NOT-A-MIGRATION-BLOCK",
            "status": "pending-review",
            "ratified": "0",
        }
        for key, value in expected.items():
            if row.get(key) != value:
                errors.append(f"ledger mismatch: {key}")
        for key in LEDGER_FIELDS:
            if not row.get(key, "").strip():
                errors.append(f"ledger field empty: {key}")
        if not row.get("ownership_test", "").startswith("UNIVERSAL-BORDER: "):
            errors.append("ownership boundary must be explicit")

    low_names = {
        str(name).strip().upper()
        for domain in foundation.get("domains", {}).values()
        for name in domain.get("residents", {}).values()
    }
    high_names = {
        str(row.get("semantic_name", "")).strip().upper()
        for row in inventory.get("rows", [])
    }
    if SEMANTIC_NAME in low_names:
        errors.append("CLASS-OF now exact-name collides with D1-D9; re-review required")
    if SEMANTIC_NAME in high_names:
        errors.append("CLASS-OF has since been selected in D10; reconcile instead of double-counting")
    if "TYPE-OF" not in high_names:
        errors.append("expected neighboring selected TYPE-OF for behavioral comparison")

    historical = {row.get("name"): row for row in oracle.get("historical_functions", [])}
    if SEMANTIC_NAME not in historical:
        errors.append("SBCL CLOS oracle artifact lacks CLASS-OF")
    case_ids = set(oracle.get("observed_case_ids", []))
    for case in (
        "CLASS_OF_EXACT_CLASS_OBJECT",
        "CLASS_OF_NOT_CLASS_SYMBOL",
        "CLASS_OF_CHILD_NOT_PARENT",
    ):
        if case not in case_ids:
            errors.append(f"missing oracle case {case}")
        if case not in oracle_lisp:
            errors.append(f"live SBCL source lacks {case}")
    if oracle.get("geometry", {}).get("coordinate", "MISSING") is not None:
        errors.append("oracle artifact must not assign coordinate")

    snapshot = data.get("source_snapshot", {})
    expected_snapshot = {
        "checked_against_commit": DONOR_COMMIT,
        "d1_d9_foundation_blob_sha": foundation_sha,
        "d10_inventory_blob_sha": data.get("source_snapshot", {}).get("d10_inventory_blob_sha"),
        "selected_d10_candidates": data.get("source_snapshot", {}).get("selected_d10_candidates"),
        "exact_name_matches": {"d1_d9": False, "d10": False},
    }
    for key, value in expected_snapshot.items():
        if snapshot.get(key) != value:
            errors.append(f"source snapshot drift: {key}")
    # A proposal references the inventory at its historically checked donor
    # commit. That Git blob must remain in the append-only selection chain,
    # rather than being rewritten each time an unrelated D10 law is selected.
    source_sha = snapshot.get("d10_inventory_blob_sha")
    if source_sha != "7e13e929338baeef9b16c2139d24b78e23ea1e03" or snapshot.get("selected_d10_candidates") != 647:
        errors.append("original CLASS-OF donor snapshot must remain 647 at its exact historical SHA")
    archival = [transition for transition in history.get("transitions", [])
                if transition.get("resulting_inventory_blob_sha") == source_sha]
    if len(archival) != 1:
        errors.append("historical inventory snapshot missing from selection chain")
    elif archival[0].get("resulting_selected") != snapshot.get("selected_d10_candidates"):
        errors.append("historical snapshot candidate count mismatch")
    transitions = history.get("transitions", [])
    if not transitions or transitions[-1].get("resulting_inventory_blob_sha") != inventory_sha:
        errors.append("current inventory not anchored by terminal selection SHA")
    elif transitions[-1].get("resulting_selected") != inventory.get("accounting", {}).get("selected_semantic_candidates"):
        errors.append("current inventory count not anchored by terminal selection history")
    if data.get("source", {}).get("donor_commit") != DONOR_COMMIT:
        errors.append("donor source commit drift")
    if data.get("source", {}).get("observation_artifact_blob_sha") != oracle_sha:
        errors.append("CLOS observation artifact blob drift")
    if data.get("source", {}).get("oracle_lisp_blob_sha") != oracle_lisp_sha:
        errors.append("SBCL oracle source blob drift")
    return errors


def main() -> int:
    if "--self-test" in sys.argv and not __debug__:
        print(
            "CLASS-OF-PROPOSAL: BLOCKED — Python -O disables guarded self-test",
            file=sys.stderr,
        )
        return 1

    data = load(ART)
    ledger = read_ledger()
    foundation = load(FOUND)
    inventory = load(INV)
    oracle = load(ORACLE)
    history = load(HISTORY)
    pins = {
        "foundation_sha": git_blob_sha(FOUND),
        "inventory_sha": git_blob_sha(INV),
        "oracle_sha": git_blob_sha(ORACLE),
        "oracle_lisp_sha": git_blob_sha(ORACLE_LISP),
        "oracle_lisp": ORACLE_LISP.read_text(encoding="utf-8"),
    }
    errors = check(data, ledger, foundation, inventory, history, oracle, **pins)
    if errors:
        for error in errors:
            print(f"CLASS-OF-PROPOSAL: BLOCK {error}", file=sys.stderr)
        return 1
    print("CLASS-OF proposal guard PASS; pending/unselected/unplaced/unratified")

    if "--self-test" in sys.argv:
        mutants = []
        bad = copy.deepcopy(data); bad["selected_d10_candidate"] = True; mutants.append(("selection", bad))
        bad = copy.deepcopy(data); bad["coordinate"] = "1010101010"; mutants.append(("coordinate", bad))
        bad = copy.deepcopy(data); bad["ratified"] = True; mutants.append(("ratification", bad))
        bad = copy.deepcopy(data); bad["physical_t5_authorized"] = True; mutants.append(("T5 authorization", bad))
        missed = [
            name for name, mutant in mutants
            if not check(mutant, ledger, foundation, inventory, history, oracle, **pins)
        ]
        if missed:
            print(
                "CLASS-OF-PROPOSAL: FAIL unsafe mutations accepted: " + ", ".join(missed),
                file=sys.stderr,
            )
            return 1
        print("CLASS-OF-PROPOSAL: 4 no-admission negative controls PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
