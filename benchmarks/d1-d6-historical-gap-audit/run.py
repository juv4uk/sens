#!/usr/bin/env python3
"""#2718 — D1-D6 historical gap / ratification-readiness audit.

This gate joins existing authorities. It does not allocate a coordinate,
invent a domain law, or ratify occupancy.

Question:
    what did early Lisp actually have that the already-ratified domains do not
    yet explain, and which surviving rows are genuinely owner-ready?
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs/research/2344-post-d4-historical-ledger.json"
PLACEMENT = ROOT / "benchmarks/post-d4-semantic-placement/placement.json"
D5_GUARD = ROOT / "scripts/research-2689-d5-ratified-baseline.py"
D6_FRONTIER = ROOT / "benchmarks/d6-unknown-frontier/run.py"
ARITHMETIC_LEDGER = ROOT / "docs/research/2709-lisp15-arithmetic-ledger.json"
MEMO24_CHRONOLOGY = ROOT / "docs/research/2715-memo24-arithmetic-comparison.json"

# This table is not new semantic authority. It is the smallest explicit
# projection of the merged #2705 placement evidence into the question
# "which earliest ratified domain already explains the historical capability?"
EARLIEST_EXPLAINING_DOMAIN = {
    "LABEL": "D4",
    "FUNCTION": "D4",
    "FUNARG": "D4",
    "EVALQUOTE": "D4",
    "APPEND": "D3",
    "PAIR": "D3",
    "PAIRLIS": "D3",
    "ASSOC": "D3",
    "SUBST": "D3",
    "SUBLIS": "D3",
    "MAPLIST": "D4",
    "GO": "D4",
}

SURVIVING_DELTAS = {
    "SET": "shared-location-update",
    "SETQ": "shared-location-update+quoted-target-policy",
    "RETURN": "non-local-exit-root",
    "FEXPR": "raw-operands+explicit-caller-env",
    "FSUBR": "raw-operands+explicit-caller-env",
    "TRANSFORMER": "raw-form+returned-form-reevaluation",
}

EXPECTED_OPS = [
    "LABEL", "FUNCTION", "FUNARG", "EVALQUOTE",
    "APPEND", "PAIR", "PAIRLIS", "ASSOC", "SUBST", "SUBLIS", "MAPLIST",
    "SET", "SETQ", "PROG", "GO", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER",
]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(f"D1-D6 historical gap audit drift: {message}")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> dict[str, Any]:
    ledger = load_json(LEDGER)
    placement = load_json(PLACEMENT)
    arithmetic = load_json(ARITHMETIC_LEDGER)
    memo24 = load_json(MEMO24_CHRONOLOGY) if MEMO24_CHRONOLOGY.exists() else None
    d5 = runpy.run_path(str(D5_GUARD))["build_result"]()
    d6 = runpy.run_path(str(D6_FRONTIER))["build"]()

    require(ledger["authority"] == "historical-evidence-ledger-not-language-semantic-authority",
            "historical ledger authority changed")
    require(ledger["phase"] == "HISTORICAL-INGEST", "historical phase changed")
    require(placement["authority"].startswith("aggregation of merged historical"),
            "placement aggregation authority changed")

    historical = {row["operation"]: row for row in ledger["rows"]}
    placed = {row["operation"]: row for row in placement["rows"]}
    require(list(historical) == EXPECTED_OPS, "historical operation/order set changed")
    require(set(placed) == set(EXPECTED_OPS), "placement operation set changed")
    require(len(historical) == placement["invariants"]["historical_rows"] == 19,
            "19-row merged historical baseline changed")

    # Arithmetic is a historical completeness input, not Core residency
    # authority. Keep every historical numeric row explicitly outside the
    # Core D5/D6 allocation question until a typed Core-Math bridge exists.
    require(arithmetic["phase"] == "HISTORICAL-INGEST", "arithmetic phase changed")
    require(arithmetic["counts"]["rows"] == 26, "1962 arithmetic row count changed")
    require(len(arithmetic["rows"]) == 26, "1962 arithmetic ledger length changed")
    require(all(row["binary_object"] == "UNPLACED" for row in arithmetic["rows"]),
            "historical arithmetic allocated a binary object")
    require(all(row["current_domain_candidate"] == "unresolved" for row in arithmetic["rows"]),
            "historical arithmetic entered a Core domain without bridge proof")

    memo24_status: dict[str, Any]
    if memo24 is None:
        memo24_status = {
            "status": "PENDING-MERGE",
            "ref": "#2715/#2722",
            "note": "audit will consume Memo 24 automatically once the chronology sidecar lands",
        }
    else:
        require(memo24["phase"] == "HISTORICAL-INGEST", "Memo 24 phase changed")
        require(memo24["counts"]["rows"] == 26, "Memo 24 row count changed")
        require(len(memo24["rows"]) == 26, "Memo 24 chronology length changed")
        require(all(row["binary_object"] == "UNPLACED" for row in memo24["rows"]),
                "Memo 24 chronology allocated a binary object")
        require(all(row["current_domain_candidate"] == "unresolved" for row in memo24["rows"]),
                "Memo 24 chronology entered a Core domain without bridge proof")
        memo24_status = {
            "status": "CONSUMED",
            "ref": "#2715/#2722",
            "attested_1961": memo24["counts"]["attested"],
            "not_attested_1961": memo24["counts"]["not_attested"],
            "changed_by_1962": memo24["counts"]["changed"],
            "unresolved_relation": memo24["counts"]["unresolved_relation"],
        }

    require(d5["domain_ratified"] is True, "D5 domain lost ratification")
    require(d5["baseline_ratified"] is True, "D5 baseline lost ratification")
    require(d5["generated_count"] == 8, "D5 generated count changed")
    require(d5["unknown_count"] == 24, "D5 protected UNKNOWN count changed")
    require(d5["manual_nonselector_count"] == 0, "D5 gained manual resident")

    require(d6["canonical"]["generated_members"] == 16, "D6 selector closure changed")
    require(d6["canonical"]["ratified_manual_residents"] == 1, "D6 manual resident count drifted")
    require(d6["canonical"]["unknown_free"] == 47, "D6 canonical UNKNOWN count changed")
    require(d6["canonical"]["occupancy_mutations"] == 0, "D6 research mutated occupancy")
    target = d6["ratified_target"]
    require(target["coordinate"] == "001111", "ratified D6 target moved")
    require(target["research_evidence_class"] == "RATIFIED-MANUAL-RESIDENT",
            "001111 ratified evidence class changed")
    require(target["semantic_member"] is True,
            "001111 lost owner-ratified D6 membership")

    rows: list[dict[str, Any]] = []
    for op in EXPECTED_OPS:
        h = historical[op]
        p = placed[op]
        require(h["phase_status"] == "complete", f"{op}: historical ingest not complete")
        require(h["binary_object"] == "unplaced", f"{op}: historical ingest allocated bits")

        earliest = EARLIEST_EXPLAINING_DOMAIN.get(op, "NONE")
        delta = SURVIVING_DELTAS.get(op, "NONE")

        if op in EARLIEST_EXPLAINING_DOMAIN:
            readiness = "ALREADY-EXPLAINED"
            capability_status = "EXPLAINED-BY-RATIFIED-DOMAIN"
            domain_gap = "NONE"
            placement_gap = "NONE"
            missing = "NONE"
            require(p["resident_required"] == "NO", f"{op}: explained row now requires resident")
            require(p["coordinate"] == "NONE", f"{op}: explained row gained coordinate")
        elif op == "SET":
            readiness = "NEEDS-DOMAIN"
            capability_status = "PROVEN-SHARED-LOCATION-CARRIER"
            domain_gap = "EXACT-DOMAIN-UNRESOLVED"
            placement_gap = "BLOCKED-BY-DOMAIN"
            missing = "exact-domain theorem + residency/coordinate theorem; do not re-prove mutation lower bound"
        elif op == "SETQ":
            readiness = "RATIFIED"
            capability_status = "PROVEN-POLICY-OVER-SHARED-LOCATION-CARRIER"
            domain_gap = "RESOLVED-D6"
            placement_gap = "NONE-RATIFIED"
            missing = "NONE; owner decision #2538 OD-001 applied by #2723"
            require(p["placement_kind"] == "RATIFIED-RESIDENT",
                    "SETQ ratified placement kind drift")
            require(p["exact_domain"] == "D6" and p["coordinate"] == "001111",
                    "SETQ ratified D6 coordinate drift")
            require(p["candidate_coordinate"] is None,
                    "SETQ must not remain a candidate after ratification")
        elif op == "PROG":
            readiness = "COMPOSITE"
            capability_status = "COMPOSITE-GO+RETURN"
            domain_gap = "NONE-AS-RESIDENT"
            placement_gap = "NONE-AS-RESIDENT"
            missing = "NONE-as-resident; decompose GO + RETURN"
            require(p["resident_required"] == "NO-AS-COMPOSITE", "PROG composite status drift")
        elif op == "RETURN":
            readiness = "NEEDS-DOMAIN"
            capability_status = "PROVEN-NON-LOCAL-EXIT-ROOT"
            domain_gap = "EXACT-DOMAIN-UNRESOLVED"
            placement_gap = "BLOCKED-BY-DOMAIN"
            missing = "domain-selection theorem; proven roothood does not determine width; do not re-prove roothood"
            require(p["placement_kind"] == "PROVEN-ROOT-UNPLACED", "RETURN root status drift")
        elif op in {"FEXPR", "FSUBR"}:
            readiness = "NEEDS-DOMAIN"
            capability_status = "PROVEN-RAW+CALLER-ENV-PROTOCOL"
            domain_gap = "EXACT-DOMAIN-UNRESOLVED"
            placement_gap = "BLOCKED-BY-DOMAIN"
            missing = "exact-domain/width theorem; protocol axes are already factored by #2522/#2591"
        elif op == "TRANSFORMER":
            readiness = "NEEDS-DOMAIN"
            capability_status = "PROVEN-MULTI-DELTA-SPECIAL-CALL-PROTOCOL"
            domain_gap = "EXACT-DOMAIN-UNRESOLVED"
            placement_gap = "BLOCKED-BY-DOMAIN"
            missing = "exact-domain/width theorem; #2616 already rejects D5 one-delta child"
        else:
            raise AssertionError(f"unclassified historical row: {op}")

        rows.append({
            "historical_capability": op,
            "first_attested_lineage": h["first_attested_lineage"],
            "historical_evidence": h["source_provenance"],
            "earliest_ratified_domain_that_explains_it": earliest,
            "explanation_region": p["semantic_region"],
            "explanation_owner": p["primary_owner"],
            "surviving_observable_delta": delta,
            "capability_evidence_status": capability_status,
            "current_domain_status": p["exact_domain"],
            "domain_gap": domain_gap,
            "placement_gap": placement_gap,
            "binary_object": h["binary_object"],
            "ratification_readiness": readiness,
            "missing_evidence": missing,
            "placement_kind": p["placement_kind"],
            "candidate_coordinate": p["candidate_coordinate"],
            "falsifier_guard": "chronology!=residency; #2508 domain firewall; no free-slot search",
        })

    already = [r for r in rows if r["ratification_readiness"] == "ALREADY-EXPLAINED"]
    needs_law = [r for r in rows if r["ratification_readiness"] == "NEEDS-LAW"]
    needs_domain = [r for r in rows if r["ratification_readiness"] == "NEEDS-DOMAIN"]
    needs_placement = [r for r in rows if r["ratification_readiness"] == "NEEDS-PLACEMENT"]
    owner_ready = [r for r in rows if r["ratification_readiness"] == "OWNER-READY"]
    ratified = [r for r in rows if r["ratification_readiness"] == "RATIFIED"]
    composite = [r for r in rows if r["ratification_readiness"] == "COMPOSITE"]

    require(owner_ready == [], "owner-ready set must be empty after OD-001")
    require([r["historical_capability"] for r in ratified] == ["SETQ"],
            "ratified set changed; review required")
    require(needs_law == [], "audit is trying to re-open already-proved capability laws")
    require(set(r["historical_capability"] for r in needs_domain) ==
            {"SET", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"},
            "surviving NEEDS-DOMAIN set changed; review required")
    require(needs_placement == [], "placement-only queue changed; review required")
    require([r["historical_capability"] for r in composite] == ["PROG"],
            "composite set changed")

    return {
        "schema": "d1-d6-historical-gap-audit/v1",
        "issue": 2718,
        "authority": "joined evidence / ratification-readiness report; not residency authority",
        "phase": "HISTORICAL-INGEST -> STRUCTURAL-DISCOVERY -> RATIFICATION-READINESS",
        "rows": rows,
        "domain_summary": {
            "D1-D4": {
                "status": "RATIFIED-FOUNDATION",
                "historical_rows_explained": len(already),
                "note": "derived historical names remain in the ledger; explanation does not erase history",
            },
            "D5": {
                "status": "RATIFIED-BASELINE",
                "generated_residents": d5["generated_count"],
                "protected_unknown": d5["unknown_count"],
                "manual_nonselector_residents": d5["manual_nonselector_count"],
                "missing": "new same-domain law, not occupancy",
            },
            "D6": {
                "status": "RATIFIED-WIDTH / LAW-DRIVEN-OCCUPANCY",
                "generated_residents": d6["canonical"]["generated_members"],
                "canonical_unknown": d6["canonical"]["unknown_free"],
                "pure_unknown_not_search_space": d6["frontier_counts"]["PURE-UNKNOWN"],
                "ratified_manual_residents": ["001111"],
                "missing": "new theorem for any additional resident",
            },
        },
        "missing_from_previous_domains": [
            "shared-location update carrier/policy",
            "non-local exit root",
            "raw-operands + explicit caller environment special-call carrier",
            "returned-form re-evaluation / transformer staging policy",
        ],
        "foreign_or_pending_ingest": {
            "lisp15_arithmetic": {
                "status": "HISTORICAL-INGEST-FOREIGN-TO-CORE-RESIDENCY",
                "refs": ["#2697", "#2710", "#2715", "#2720", "#2721", "#2722"],
                "rows_1962": arithmetic["counts"]["rows"],
                "all_binary_objects": "UNPLACED",
                "all_current_domain_candidates": "unresolved",
                "memo24_chronology": memo24_status,
                "domain_rule": "typed Core-Math bridge required; historical spelling/count cannot populate Core D5/D6",
            }
        },
        "owner_facing": {
            "ready_now": [],
            "decided": [
                {
                    "decision": "OD-001",
                    "binary_object": "D6:001111",
                    "status": "RATIFIED-RESIDENT",
                    "meaning": "shared-location / SETQ binding-policy product",
                    "authority": "#2538/#2723",
                }
            ],
            "not_ready": [r["historical_capability"] for r in needs_law + needs_domain + needs_placement],
            "do_not_ratify_as_resident": [r["historical_capability"] for r in already + composite],
        },
        "summary": {
            "historical_rows": len(rows),
            "already_explained": len(already),
            "needs_new_law": len(needs_law),
            "needs_domain": len(needs_domain),
            "needs_placement": len(needs_placement),
            "owner_ready": len(owner_ready),
            "ratified": len(ratified),
            "composite": len(composite),
            "new_d5_manual_residents": 0,
            "new_d6_admissions": 1,
        },
        "guards": [
            "historical presence != resident necessity",
            "free coordinate != candidate",
            "roothood != width",
            "factor count != domain",
            "same name != same semantic law",
            "Core-Math/mechanism cannot donate Core residency",
            "D6 PURE-UNKNOWN coordinates are not enumerated as search targets",
        ],
    }


def render_md(result: dict[str, Any]) -> str:
    lines = [
        "# D1-D6 historical gap audit — #2718",
        "",
        "This report asks what the already-ratified domains fail to explain. It does not allocate bits.",
        "",
        "| historical row | earliest explaining domain | surviving delta | readiness | missing |",
        "|---|---|---|---|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['historical_capability']} | "
            f"{row['earliest_ratified_domain_that_explains_it']} | "
            f"{row['surviving_observable_delta']} | "
            f"**{row['ratification_readiness']}** | {row['missing_evidence']} |"
        )

    lines += [
        "",
        "## What previous domains still do not explain",
        "",
    ]
    lines += [f"- {item}" for item in result["missing_from_previous_domains"]]
    lines += [
        "",
        "## Domain state",
        "",
        f"- D1-D4: {result['domain_summary']['D1-D4']['historical_rows_explained']} historical rows already explained.",
        f"- D5: {result['domain_summary']['D5']['generated_residents']} generated / "
        f"{result['domain_summary']['D5']['protected_unknown']} protected UNKNOWN / 0 manual.",
        f"- D6: {result['domain_summary']['D6']['generated_residents']} generated / "
        f"{result['domain_summary']['D6']['canonical_unknown']} canonical UNKNOWN; "
        f"{result['domain_summary']['D6']['pure_unknown_not_search_space']} PURE-UNKNOWN are not a search space.",
        "",
        "## Owner decision applied",
        "",
        "- OD-001: D6:001111 is RATIFIED for SETQ/shared-location under #2538/#2723.",
        "- No other historical row is owner-ready; additional residents still require a new theorem.",
        "",
        "## Arithmetic",
        "",
        f"- Lisp 1.5 arithmetic: {result['foreign_or_pending_ingest']['lisp15_arithmetic']['rows_1962']} historical rows, all UNPLACED.",
        f"- Memo 24 chronology: {result['foreign_or_pending_ingest']['lisp15_arithmetic']['memo24_chronology']['status']}.",
        "- Arithmetic cannot populate Core D5/D6 by shared spelling, row count or spare capacity.",
        "",
        "## Non-conclusion",
        "",
        "Historical completeness is not domain density. Empty coordinates are a valid result.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = build()
    print("D1-D6-HISTORICAL-GAP-AUDIT=PASS")
    for key, value in result["summary"].items():
        print(f"{key}={value}")
    print("ratified=D6:001111")
    print("RULE=fill-history-not-free-slots")

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "result.json").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (args.out / "report.md").write_text(render_md(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
