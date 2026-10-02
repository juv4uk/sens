#!/usr/bin/env python3
"""#2344 — validate the executable Lisp I -> Lisp 1.5 capability ledger.

Research-only. The ledger records evidence and chronology; cited executable
witnesses remain the semantic evidence owners. This checker allocates no code.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ALLOWED_CLASSIFICATIONS = {
    "ALREADY-REPRESENTED",
    "DERIVED-D1-D4",
    "HISTORICAL-MECHANISM",
    "NEW-OBSERVABLE-CAPABILITY",
    "HOST-MECHANISM",
    "UNRESOLVED",
}
ALLOWED_PHASE_STATUS = {"complete", "active", "blocked", "later"}
PHASE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}
HEX40 = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_FIELDS = {
    "order",
    "phase",
    "operation",
    "historical_era",
    "source_provenance",
    "observable_role",
    "d1_d4_equivalent",
    "derivation_witness",
    "host_mechanism",
    "hidden_state_needed",
    "first_class_value",
    "raw_operands",
    "caller_env_access",
    "mutation",
    "non_local_control",
    "result_is_form",
    "strongest_parent",
    "one_new_delta",
    "classification",
    "issue",
    "evidence_sha",
    "address",
    "phase_status",
}

BOOL_OR_NULL = {
    "hidden_state_needed",
    "caller_env_access",
    "one_new_delta",
}
BOOL_ONLY = {
    "host_mechanism",
    "first_class_value",
    "raw_operands",
    "mutation",
    "non_local_control",
    "result_is_form",
}


def fail(message: str) -> None:
    raise SystemExit(f"HISTORICAL-LEDGER=FAIL\n{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def commit_exists(sha: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def validate_row(row: dict[str, Any], previous_phase_rank: int) -> int:
    missing = sorted(REQUIRED_FIELDS - row.keys())
    require(not missing, f"{row.get('operation', '<unknown>')}: missing fields {missing}")

    op = row["operation"]
    require(isinstance(row["order"], int) and row["order"] > 0, f"{op}: invalid order")
    require(row["phase"] in PHASE_ORDER, f"{op}: invalid phase {row['phase']}")
    phase_rank = PHASE_ORDER[row["phase"]]
    require(phase_rank >= previous_phase_rank, f"{op}: phase order regressed")

    require(
        row["classification"] in ALLOWED_CLASSIFICATIONS,
        f"{op}: invalid classification {row['classification']}",
    )
    require(
        row["phase_status"] in ALLOWED_PHASE_STATUS,
        f"{op}: invalid phase_status {row['phase_status']}",
    )
    require(isinstance(row["issue"], int) and row["issue"] > 0, f"{op}: invalid issue")

    for field in BOOL_ONLY:
        require(isinstance(row[field], bool), f"{op}: {field} must be boolean")
    for field in BOOL_OR_NULL:
        require(
            isinstance(row[field], bool) or row[field] is None,
            f"{op}: {field} must be boolean or null",
        )

    for field in (
        "operation",
        "historical_era",
        "source_provenance",
        "observable_role",
        "d1_d4_equivalent",
        "derivation_witness",
        "strongest_parent",
    ):
        require(isinstance(row[field], str) and row[field].strip(), f"{op}: empty {field}")

    # Historical research ledger v1 is deliberately allocation-free.
    require(row["address"] == "none", f"{op}: address allocation is forbidden in #2344")

    resolved = row["classification"] != "UNRESOLVED"
    if row["phase_status"] == "complete":
        require(resolved, f"{op}: complete row cannot remain UNRESOLVED")
    else:
        require(not resolved, f"{op}: non-complete row cannot claim a final classification")

    if resolved:
        sha = row["evidence_sha"]
        require(HEX40.match(sha) is not None, f"{op}: resolved row needs full evidence SHA")
        require(commit_exists(sha), f"{op}: evidence commit {sha} is absent from git history")
        require(row["one_new_delta"] is not None, f"{op}: resolved row needs one_new_delta verdict")
        require(
            row["hidden_state_needed"] is not None,
            f"{op}: resolved row needs hidden_state_needed verdict",
        )
        require(
            row["caller_env_access"] is not None,
            f"{op}: resolved row needs caller_env_access verdict",
        )
    else:
        require(row["evidence_sha"] == "none", f"{op}: unresolved row must not claim merged evidence")

    if row["classification"] == "NEW-OBSERVABLE-CAPABILITY":
        require(
            row["one_new_delta"] is not None,
            f"{op}: new capability must state whether one delta is sufficient",
        )

    return phase_rank


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ledger",
        nargs="?",
        default="docs/research/2344-post-d4-historical-ledger.json",
    )
    parser.add_argument("--summary-json", default="")
    args = parser.parse_args()

    path = Path(args.ledger)
    raw = path.read_text(encoding="utf-8")
    require("#undefined" not in raw, "stale #undefined reference is forbidden")
    data = json.loads(raw)

    require(data.get("schema") == "post-d4-historical-ledger/1", "unsupported schema")
    require(
        data.get("authority") == "research-evidence-ledger-not-language-semantic-authority",
        "ledger must not claim language semantic authority",
    )

    rows = data.get("rows")
    require(isinstance(rows, list) and rows, "ledger rows missing")

    operations: set[str] = set()
    issues: set[int] = set()
    orders: list[int] = []
    previous_phase_rank = -1

    for row in rows:
        require(isinstance(row, dict), "row must be object")
        previous_phase_rank = validate_row(row, previous_phase_rank)
        op = row["operation"]
        require(op not in operations, f"duplicate operation {op}")
        operations.add(op)
        issues.add(row["issue"])
        orders.append(row["order"])

    require(orders == list(range(1, len(rows) + 1)), "orders must be contiguous 1..N")

    required_operations = {
        "LABEL",
        "FUNCTION",
        "FUNARG",
        "EVALQUOTE",
        "APPEND",
        "PAIR",
        "PAIRLIS",
        "ASSOC",
        "SUBST",
        "SUBLIS",
        "MAPLIST",
        "SET",
        "SETQ",
        "PROG",
        "GO",
        "RETURN",
        "FEXPR",
        "FSUBR",
        "TRANSFORMER",
    }
    missing_ops = sorted(required_operations - operations)
    require(not missing_ops, f"missing required historical rows {missing_ops}")

    first_new = next(
        (row for row in rows if row["classification"] == "NEW-OBSERVABLE-CAPABILITY"),
        None,
    )
    earliest_unresolved = next(
        (row for row in rows if row["classification"] == "UNRESOLVED"),
        None,
    )

    placement_search_may_start = False
    if first_new is not None:
        prior = [row for row in rows if row["order"] < first_new["order"]]
        placement_search_may_start = all(
            row["classification"] != "UNRESOLVED" for row in prior
        )

    complete = [row for row in rows if row["phase_status"] == "complete"]
    unresolved = [row for row in rows if row["classification"] == "UNRESOLVED"]

    summary = {
        "schema": data["schema"],
        "row_count": len(rows),
        "complete_rows": len(complete),
        "unresolved_rows": len(unresolved),
        "first_new_observable_capability": (
            first_new["operation"] if first_new is not None else "NONE-YET"
        ),
        "earliest_unresolved": (
            earliest_unresolved["operation"] if earliest_unresolved is not None else "NONE"
        ),
        "placement_search_may_start": placement_search_may_start,
        "resolved": [
            {
                "operation": row["operation"],
                "classification": row["classification"],
                "evidence_sha": row["evidence_sha"],
            }
            for row in complete
        ],
    }

    if args.summary_json:
        target = Path(args.summary_json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("HISTORICAL-LEDGER=PASS")
    print(f"rows={len(rows)} complete={len(complete)} unresolved={len(unresolved)}")
    print(
        "first-new-observable-capability="
        + summary["first_new_observable_capability"]
    )
    print("earliest-unresolved=" + summary["earliest_unresolved"])
    print(
        "placement-search-may-start="
        + ("yes" if placement_search_may_start else "no")
    )
    for row in complete:
        print(
            f"resolved\t{row['order']:02d}\t{row['operation']}\t"
            f"{row['classification']}\t{row['evidence_sha'][:12]}"
        )


if __name__ == "__main__":
    main()
