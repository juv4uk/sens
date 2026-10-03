#!/usr/bin/env python3
"""#2344 — validate the historical-ingest ledger.

This is a chronology/evidence gate, not semantic or placement authority.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "historical-ingest-ledger/2"
PHASE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5}
PRESENCE = {"yes", "uncertain"}
PHASE_STATUS = {"complete", "active"}
PLACEMENT = {
    "not-required-derived",
    "not-required-historical-mechanism",
    "unplaced-new-capability",
    "unplaced-composite",
    "unplaced-two-axis-capability",
    "unplaced-active-comparison",
    "unplaced-transformer-protocol",
}
SENS_CLASS = {
    "DERIVED-D1-D4",
    "HISTORICAL-MECHANISM",
    "NEW-OBSERVABLE-CAPABILITY",
    "COMPOSITE",
    "RAW+ENV-TWO-CAPABILITIES",
    "FORM-TRANSFORMER-PROTOCOL",
    "UNRESOLVED",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")

REQUIRED = {
    "order",
    "phase",
    "operation",
    "historical_era",
    "first_attested_lineage",
    "source_provenance",
    "historical_presence",
    "historical_behavior",
    "historical_dependencies",
    "current_domain_candidate",
    "binary_object",
    "placement_status",
    "later_structural_classification",
    "later_SENS_classification",
    "protocol_axes",
    "issue",
    "evidence_sha",
    "phase_status",
    "notes",
}

REQUIRED_OPERATIONS = {
    "LABEL", "FUNCTION", "FUNARG", "EVALQUOTE",
    "APPEND", "PAIR", "PAIRLIS", "ASSOC", "SUBST", "SUBLIS", "MAPLIST",
    "SET", "SETQ", "PROG", "GO", "RETURN",
    "FEXPR", "FSUBR", "TRANSFORMER",
}

def fail(message: str) -> None:
    raise SystemExit(f"HISTORICAL-INGEST-LEDGER=FAIL\n{message}")

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

def validate_row(row: dict[str, Any], previous_phase: int) -> int:
    missing = sorted(REQUIRED - row.keys())
    require(not missing, f"{row.get('operation','<unknown>')}: missing fields {missing}")
    op = row["operation"]
    require(isinstance(row["order"], int) and row["order"] > 0, f"{op}: invalid order")
    require(row["phase"] in PHASE_ORDER, f"{op}: invalid phase")
    rank = PHASE_ORDER[row["phase"]]
    require(rank >= previous_phase, f"{op}: phase order regressed")
    require(row["historical_presence"] in PRESENCE, f"{op}: invalid historical_presence")
    require(row["phase_status"] in PHASE_STATUS, f"{op}: invalid phase_status")
    require(row["placement_status"] in PLACEMENT, f"{op}: invalid placement_status")
    require(row["later_SENS_classification"] in SENS_CLASS, f"{op}: invalid later_SENS_classification")
    require(row["binary_object"] == "unplaced", f"{op}: HISTORICAL-INGEST cannot allocate a binary object")
    require(isinstance(row["historical_dependencies"], list), f"{op}: dependencies must be list")
    require(isinstance(row["issue"], int) and row["issue"] > 0, f"{op}: invalid issue")
    axes = row["protocol_axes"]
    require(set(axes) == {"raw_operands","explicit_caller_env","result_reeval"}, f"{op}: malformed protocol_axes")
    require(all(isinstance(v, bool) for v in axes.values()), f"{op}: protocol axes must be booleans")
    for field in (
        "operation","historical_era","first_attested_lineage","source_provenance",
        "historical_behavior","current_domain_candidate","placement_status",
        "later_structural_classification","later_SENS_classification","notes",
    ):
        require(isinstance(row[field], str) and row[field].strip(), f"{op}: empty {field}")

    if row["phase_status"] == "complete":
        require(row["historical_presence"] == "yes", f"{op}: completed historical row must be present")
        require(row["later_SENS_classification"] != "UNRESOLVED", f"{op}: complete row cannot be unresolved")
        sha=row["evidence_sha"]
        require(HEX40.match(sha) is not None, f"{op}: complete row needs full evidence SHA")
        require(commit_exists(sha), f"{op}: evidence commit not in git history: {sha}")
    else:
        require(row["later_SENS_classification"] == "UNRESOLVED", f"{op}: active row must remain unresolved")
        require(row["evidence_sha"] == "pending", f"{op}: active row evidence must be pending")

    return rank

def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("ledger", nargs="?", default="docs/research/2344-post-d4-historical-ledger.json")
    parser.add_argument("--summary-json", default="")
    args=parser.parse_args()

    data=json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    require(data.get("schema") == SCHEMA, "unsupported schema")
    require(data.get("authority") == "historical-evidence-ledger-not-language-semantic-authority", "authority drift")
    require(data.get("phase") == "HISTORICAL-INGEST", "phase drift")
    baseline=data.get("selector_baseline",{})
    require(baseline.get("status") == "generated", "selector baseline must remain generated")
    require(len(baseline.get("binary_objects",[])) == 8, "selector baseline must contain exactly eight D5 descendants")

    rows=data.get("rows")
    require(isinstance(rows,list) and rows, "rows missing")
    ops=set()
    orders=[]
    rank=-1
    for row in rows:
        require(isinstance(row,dict), "row must be object")
        rank=validate_row(row,rank)
        require(row["operation"] not in ops, f"duplicate operation {row['operation']}")
        ops.add(row["operation"])
        orders.append(row["order"])
    require(orders == list(range(1,len(rows)+1)), "orders must be contiguous")
    require(not (REQUIRED_OPERATIONS-ops), f"missing rows {sorted(REQUIRED_OPERATIONS-ops)}")

    by={row["operation"]:row for row in rows}

    # Cross-row historical/semantic controls.
    require(by["SET"]["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY", "SET shared-location result drift")
    require(by["SETQ"]["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY", "SETQ shared-location result drift")
    require(by["GO"]["later_SENS_classification"] == "DERIVED-D1-D4", "GO derivation drift")
    require(by["RETURN"]["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY", "RETURN lower-bound drift")

    fexpr_axes={"raw_operands":True,"explicit_caller_env":True,"result_reeval":False}
    transformer_axes={"raw_operands":True,"explicit_caller_env":False,"result_reeval":True}
    require(by["FEXPR"]["protocol_axes"] == fexpr_axes, "FEXPR protocol-axis drift")
    require(by["FSUBR"]["protocol_axes"] == fexpr_axes, "FSUBR protocol-axis drift")
    require(by["TRANSFORMER"]["protocol_axes"] == transformer_axes, "TRANSFORMER comparison-axis drift")

    unresolved=[r for r in rows if r["phase_status"] != "complete"]
    first_new=next(
        (r for r in rows if r["later_SENS_classification"] == "NEW-OBSERVABLE-CAPABILITY"),
        None,
    )

    historical_ingest_complete = not unresolved
    structural_discovery_may_start = historical_ingest_complete
    placement_search_may_start = False  # #2533: placement is not a HISTORICAL-INGEST action.

    summary={
        "schema":SCHEMA,
        "row_count":len(rows),
        "complete_rows":len(rows)-len(unresolved),
        "active_rows":[r["operation"] for r in unresolved],
        "first_surviving_new_capability": first_new["operation"] if first_new else "NONE-YET",
        "historical_ingest_complete":historical_ingest_complete,
        "structural_discovery_may_start":structural_discovery_may_start,
        "placement_search_may_start":placement_search_may_start,
    }

    if args.summary_json:
        p=Path(args.summary_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")

    print("HISTORICAL-INGEST-LEDGER=PASS")
    print(f"rows={len(rows)} complete={summary['complete_rows']} active={len(unresolved)}")
    print("active-rows=" + (",".join(summary["active_rows"]) or "none"))
    print("first-surviving-new-capability=" + summary["first_surviving_new_capability"])
    print("historical-ingest-complete=" + ("yes" if historical_ingest_complete else "no"))
    print("structural-discovery-may-start=" + ("yes" if structural_discovery_may_start else "no"))
    print("placement-search-may-start=no")
    print("RULE=history-first-structure-second-sens-third")
    print("RULE=historical-presence-is-independent-of-derivability")
    print("RULE=no-binary-allocation-during-historical-ingest")

if __name__ == "__main__":
    main()
