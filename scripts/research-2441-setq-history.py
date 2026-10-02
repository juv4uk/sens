#!/usr/bin/env python3
"""#2441 — validate historical Lisp 1.5 SET/SETQ classification.

Research-only. This validates the evidence record; it implements no mutation
and allocates no SENS identity.
"""

import json
from pathlib import Path

PATH = Path("docs/research/2441-setq-history.json")

def fail(msg: str) -> None:
    raise SystemExit(f"SETQ-HISTORY=FAIL\n{msg}")

def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    obs = {row["id"]: row for row in data["observations"]}
    required = {
        "setq-updates-existing-pair",
        "nearest-most-recent-binding-wins",
        "higher-level-binding-remains-mutated",
        "missing-binding-errors",
        "setq-quotes-target",
        "assignment-returns-new-value",
        "higher-level-alist-variables-are-settable",
    }
    missing = sorted(required - obs.keys())
    if missing:
        fail(f"missing observations: {missing}")
    for key in required:
        if obs[key]["status"] != "confirmed":
            fail(f"{key}: not confirmed")
    rows = dict(data["comparison_to_2402"]["rows"])
    required_true = (
        "updates existing location",
        "nearest existing binding selected",
        "no fresh binding on miss",
        "higher-level observers using same binding subsequently see new value",
        "computed SET target distinct from SETQ quoted target",
    )
    for key in required_true:
        if rows.get(key) is not True:
            fail(f"lower-bound mismatch: {key}")
    if rows.get("modern lexical-closure cell specifically required by source") is not False:
        fail("historical source overstated as modern lexical-cell semantics")
    decision = data["comparison_to_2402"]["classification"]
    if decision != "HISTORICAL-SETQ=SHARED-LOCATION-UPDATE":
        fail(f"unexpected classification: {decision}")
    print("SETQ-HISTORY=PASS")
    print(decision)
    print("TARGET=nearest-existing-a-list-binding")
    print("MISS-POLICY=error-no-fresh-binding")
    print("SET-TARGET=evaluated")
    print("SETQ-TARGET=quoted")
    print("CAVEAT=dynamic-a-list-not-modern-lexical-cell")

if __name__ == "__main__":
    main()
