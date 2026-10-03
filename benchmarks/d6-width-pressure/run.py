#!/usr/bin/env python3
"""#2573 — conservative post-D4/D6 structural width-pressure classifier.

Consumes the completed #2344 historical ledger. It does not allocate coordinates.

A local D5/D6 width verdict is admitted only when a capability has:
1. a proved observable delta count;
2. a proved same-base local parent;
3. an explicit placement/lower-bound theorem.

Axis count without a local parent theorem remains UNKNOWN.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "docs/research/2344-post-d4-historical-ledger.json"

DERIVED = {
    "LABEL", "EVALQUOTE", "APPEND", "PAIR", "PAIRLIS", "ASSOC",
    "SUBST", "SUBLIS", "MAPLIST", "GO",
}
MECHANISM_ONLY = {"FUNCTION", "FUNARG"}


def decision(row: dict[str, Any]) -> dict[str, Any]:
    op = row["operation"]
    base = {
        "operation": op,
        "historical_classification": row["later_SENS_classification"],
        "independent_observable_axes": [],
        "strongest_local_parent": "NONE",
        "local_parent_proof": "none",
        "local_minimum_width": "UNKNOWN",
        "width_verdict_scope": "none",
        "evidence": [],
        "placement": "UNPLACED",
    }

    if op in DERIVED:
        base.update(
            local_minimum_width="NONE",
            width_verdict_scope="no-post-D4-resident-required",
            evidence=[f"ledger:{row['issue']}"],
        )
        return base

    if op in MECHANISM_ONLY:
        base.update(
            local_minimum_width="NONE",
            width_verdict_scope="historical-mechanism-not-semantic-resident",
            evidence=[f"ledger:{row['issue']}"],
        )
        return base

    if op == "SETQ":
        base.update(
            independent_observable_axes=[
                "binding-target: current/new vs nearest-existing",
                "missing-binding-policy: create vs fail",
            ],
            strongest_local_parent="D4 DEFINE / 0011",
            local_parent_proof="#2518 with #2526/#2537 parent attacks",
            local_minimum_width="D6",
            width_verdict_scope="LOCAL parent+two-delta placement only",
            evidence=["#2492", "#2511", "#2518", "#2527/#2541", "#2508"],
        )
        return base

    if op == "SET":
        base.update(
            independent_observable_axes=["shared-location update"],
            strongest_local_parent="UNKNOWN",
            local_parent_proof="no independent local placement theorem for SET row",
            local_minimum_width="UNKNOWN",
            width_verdict_scope="mutation capability observed; coordinate not inherited from SETQ",
            evidence=["#2314", "#2344", "#2508"],
        )
        return base

    if op == "RETURN":
        base.update(
            independent_observable_axes=["non-local exit"],
            strongest_local_parent="UNKNOWN",
            local_parent_proof="new observable capability, but no one-delta same-base placement theorem",
            local_minimum_width="UNKNOWN",
            width_verdict_scope="capability lower bound only",
            evidence=["#2315/#2403", "#2344"],
        )
        return base

    if op == "PROG":
        base.update(
            independent_observable_axes=["derived GO state", "non-local RETURN capability"],
            strongest_local_parent="COMPOSITE",
            local_parent_proof="whole form decomposes; no single-resident placement theorem",
            local_minimum_width="UNKNOWN",
            width_verdict_scope="composite structure; do not assign width from surface form",
            evidence=["#2315/#2403", "#2344"],
        )
        return base

    if op in {"FEXPR", "FSUBR"}:
        base.update(
            independent_observable_axes=["raw operands", "explicit caller environment"],
            strongest_local_parent="UNKNOWN",
            local_parent_proof="two capabilities proved, but no same-base D4 parent/placement theorem",
            local_minimum_width="UNKNOWN",
            width_verdict_scope="NEGATIVE CONTROL: two axes do not imply D6",
            evidence=["#2522/#2528", "#2530", "#2508"],
        )
        return base

    if op == "TRANSFORMER":
        base.update(
            independent_observable_axes=["raw form input", "returned-form replacement/re-evaluation"],
            strongest_local_parent="UNKNOWN",
            local_parent_proof="Hart/SENS protocol alignment is chronology/protocol evidence, not placement",
            local_minimum_width="UNKNOWN",
            width_verdict_scope="protocol-aligned historical row; width unresolved",
            evidence=["#2557/#2571", "Hart-AIM-57", "#2508"],
        )
        return base

    raise AssertionError(f"unclassified historical row: {op}")


def build() -> dict[str, Any]:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = data["rows"]
    if len(rows) != 19:
        raise AssertionError(f"expected completed 19-row historical sample, got {len(rows)}")
    active = [r["operation"] for r in rows if r["phase_status"] != "complete"]
    if active:
        raise AssertionError(f"historical ingest not complete: {active}")

    out = [decision(row) for row in rows]
    if any(row["placement"] != "UNPLACED" for row in out):
        raise AssertionError("structural discovery must not allocate coordinates")

    d6 = [r for r in out if r["local_minimum_width"] == "D6"]
    if [r["operation"] for r in d6] != ["SETQ"]:
        raise AssertionError(f"only proved local D6 positive control is SETQ, got {d6}")

    for op in ("FEXPR", "FSUBR", "TRANSFORMER"):
        row = next(r for r in out if r["operation"] == op)
        if row["local_minimum_width"] != "UNKNOWN":
            raise AssertionError(f"{op}: protocol axes must not auto-assign width")

    return {
        "schema": "d6-width-pressure-map/v1",
        "phase": "STRUCTURAL-DISCOVERY",
        "authority": "research-only-no-placement",
        "source": "docs/research/2344-post-d4-historical-ledger.json",
        "rules": [
            "chronology never allocates width",
            "axis count without same-base local parent theorem remains UNKNOWN",
            "D6 means local placement minimum, not global information minimum",
            "DOMAIN-MISMATCH guard #2508 applies to reused transforms",
        ],
        "counts": {
            "rows": len(out),
            "D6-local-minimum": sum(r["local_minimum_width"] == "D6" for r in out),
            "D5-local-minimum": sum(r["local_minimum_width"] == "D5" for r in out),
            "NONE": sum(r["local_minimum_width"] == "NONE" for r in out),
            "UNKNOWN": sum(r["local_minimum_width"] == "UNKNOWN" for r in out),
            "allocated": 0,
        },
        "rows": out,
    }


def report(data: dict[str, Any]) -> str:
    c = data["counts"]
    lines = [
        "# D6 structural width-pressure map — #2573",
        "",
        "This is STRUCTURAL-DISCOVERY, not placement authority.",
        "",
        f"- historical rows: {c['rows']}",
        f"- proved local D6 minima: {c['D6-local-minimum']}",
        f"- proved local D5 minima: {c['D5-local-minimum']}",
        f"- no post-D4 resident required: {c['NONE']}",
        f"- width still UNKNOWN: {c['UNKNOWN']}",
        f"- coordinates allocated: {c['allocated']}",
        "",
        "Positive control:",
        "- SETQ: local D6 minimum only under D4 DEFINE + two independent commuting deltas (#2518).",
        "",
        "Negative controls:",
        "- FEXPR/FSUBR: two capabilities, but width UNKNOWN without same-base parent theorem.",
        "- TRANSFORMER: protocol axes do not imply a width.",
        "- standalone 2-bit product representation from #2527 is a different domain, not a refutation of local D6 placement.",
        "",
        "NON-CONCLUSION: this report does not admit 001111 or any other D6 resident.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    data = build()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "d6-width-pressure.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.out / "report.md").write_text(report(data), encoding="utf-8")
    print(report(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
