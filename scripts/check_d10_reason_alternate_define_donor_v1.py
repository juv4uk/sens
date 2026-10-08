#!/usr/bin/env python3
"""Fail-closed audit of a source-era DEFINE donor, not a D10 allocator."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/d10-reason-alternate-define-donor-v1.json"
SOURCE = ROOT / "lib/reason.lisp"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"
CANONICAL = ROOT / "knowledge/d10-library-harvest-v1.json"
RAW_EXISTING = ROOT / "knowledge/d10-library-source-symbols-v1.json"
DEFINE = re.compile(r"^\s*\(00001011\s+([^\s()]+)")


def blob_sha(content: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()


def expected_class(name: str, selected: set[str]) -> str:
    if name.upper() in selected:
        return "ALREADY_SELECTED_NAME"
    if name.startswith("*") and name.endswith("*"):
        return "SCHEMA_OR_CONSTANT"
    if name in {"reason-index-mode", "reason-index-rules", "reason-index-buckets"}:
        return "ACCESSOR_ALIAS_BINDING"
    return "RESEARCH_UNREVIEWED"


def verify(ledger: dict, original: bytes, inventory: dict, state: dict,
           canonical: dict, existing_raw: dict) -> dict:
    if ledger.get("schema") != "d10-reason-alternate-define-donor-v1/v1" or (
        ledger.get("authority") != "#4013"
        or ledger.get("scope") != "RESEARCH-ONLY-NO-SEMANTIC-PROMOTION"
        or ledger.get("historical_define_head") != "00001011"
    ):
        raise ValueError("unratified source-era donor authority drift")
    if ledger.get("source") != {
        "path": "lib/reason.lisp", "git_blob_sha1": blob_sha(original)
    }:
        raise ValueError("source bytes/SHA changed; historical 00001011 evidence invalid")
    if ledger.get("proposed_routing") != {
        "selected_d10_delta": 0, "ratified_d10_delta": 0,
        "assigned_coordinates": 0, "original_executable_t5_migrations": 0,
    }:
        raise ValueError("research source syntax cannot mint D10 residents or .sens")
    if (inventory.get("domain") != "D10" or inventory.get("status") != "RESEARCH-UNRATIFIED-PARTIAL"
            or state.get("status") != "RESEARCH-UNRATIFIED"):
        raise ValueError("D10 research authority drift")
    selected_names = {str(row["semantic_name"]).upper() for row in inventory["rows"]}
    actual_count = state["target"]["selected_semantic_candidates"]
    if (len(inventory["rows"]) != actual_count or len(selected_names) != actual_count
            or actual_count + state["target"]["remaining_semantic_candidates"] != 1024
            or state["target"]["ratified_residents"] != 0):
        raise ValueError("selected D10 accounting must not change via donor research")
    if (canonical.get("schema") != "d10-library-harvest-v1/v1"
            or len(canonical.get("rows", [])) != 39
            or canonical["accounting"]["selected_d10_candidates"] != 39
            or existing_raw.get("count") != 102
            or len(existing_raw.get("candidates", [])) != 102):
        raise ValueError("39 reviewed vs 102 RAW historical evidence must remain separate")

    lines = original.decode("utf-8").splitlines()
    observed = []
    for line_no, line in enumerate(lines, 1):
        match = DEFINE.match(line)
        if match:
            observed.append((line_no, match.group(1)))
    if len(observed) != 37:
        raise ValueError("unexpected number of historical DEFINE records")
    if len({name for _, name in observed}) != 37:
        raise ValueError("source has duplicate historical definitions")

    rows = ledger.get("rows")
    if not isinstance(rows, list) or len(rows) != len(observed):
        raise ValueError("missing/extra donor evidence")
    accounting: dict[str, int] = {}
    for actual, item in zip(observed, rows, strict=True):
        line_no, name = actual
        category = expected_class(name, selected_names)
        if item != {
            "path": "lib/reason.lisp", "line": line_no, "head": "00001011",
            "name": name, "source_git_blob_sha1": blob_sha(original),
            "classification": category, "coordinate": None,
            "ratified": False, "semantic_law_verified": False,
        }:
            raise ValueError(f"donor mismatch line {line_no}, name {name}; never retag W8 to D10")
        accounting[category] = accounting.get(category, 0) + 1
    if ledger.get("counts") != {"total": 37, "by_classification": accounting}:
        raise ValueError("raw donor count or classification drift")
    return {
        "historical_source_defs": 37,
        "already_selected_names_not_promoted": accounting["ALREADY_SELECTED_NAME"],
        "schema_or_constants": accounting["SCHEMA_OR_CONSTANT"],
        "binding_aliases": accounting["ACCESSOR_ALIAS_BINDING"],
        "needs_behavioral_dedup": accounting["RESEARCH_UNREVIEWED"],
        "selected_added": 0,
        "ratified_added": 0,
        "original_executable_t5_migrations": 0,
    }


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run() -> dict:
    return verify(read(LEDGER), SOURCE.read_bytes(), read(INVENTORY), read(STATE),
                  read(CANONICAL), read(RAW_EXISTING))


if __name__ == "__main__":
    print("D10-REASON-ALTERNATE-HEAD PASS " + json.dumps(run(), sort_keys=True))
