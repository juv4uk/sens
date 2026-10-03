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
MEMO24 = ROOT / "docs/research/2715-memo24-arithmetic-comparison.json"

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
    d5 = runpy.run_path(str(D5_GUARD))["build_result"]()
    d6 = runpy.run_path(str(D6_FRONTIER))["build"]()
    memo24 = load_json(MEMO24)

    require(ledger["authority"] == "historical-evidence-ledger-not-language-semantic-authority",
            "historical ledger authority changed")
    require(ledger["phase"] == "HISTORICAL-INGEST", "historical phase changed")
    require(placement["authority"].startswith("aggregation of merged historical"),
            "placement aggregation authority changed")
    require(memo24["schema"] == "memo24-lisp15-arithmetic-chronology/v1",
            "Memo 24 chronology schema changed")
    require(memo24["phase"] == "HISTORICAL-INGEST",
            "Memo 24 chronology left historical-ingest phase")
    require(memo24["authority"].startswith("primary-source chronology/provenance only"),
            "Memo 24 chronology acquired placement authority")
    require(memo24["counts"] == {
        "rows": 26,
        "attested": 21,
        "not_attested": 5,
        "unresolved_presence": 0,
        "same": 15,
        "changed": 4,
        "extended": 5,
        "unresolved_relation": 2,
    }, "Memo 24 bounded chronology counts changed")
    memo_not_attested = [
        row["historical_name"] for row in memo24["rows"]
        if row["memo24_presence"] == "NOT-ATTESTED-IN-MEMO24"
    ]
    memo_changed = [
        row["historical_name"] for row in memo24["rows"]
        if row["manual1962_relation"] == "CHANGED"
    ]
    memo_unresolved = [
        row["historical_name"] for row in memo24["rows"]
        if row["manual1962_relation"] == "UNRESOLVED"
    ]
    require(memo_not_attested == ["QUOTIENT", "REMAINDER", "DIVIDE", "EXPT", "LEFTSHIFT"],
            "Memo 24 non-attested set changed")
    require(memo_changed == ["LESSP", "GREATERP", "ONEP", "EQUAL"],
            "1961->1962 changed-law set changed")
    require(memo_unresolved == ["ZEROP", "FLOATP"],
            "Memo 24 unresolved-law set changed")

    historical = {row["operation"]: row for row in ledger["rows"]}
    placed = {row["operation"]: row for row in placement["rows"]}
    require(list(historical) == EXPECTED_OPS, "historical operation/order set changed")
    require(set(placed) == set(EXPECTED_OPS), "placement operation set changed")
    require(len(historical) == placement["invariants"]["historical_rows"] == 19,
            "19-row merged historical baseline changed")

    require(d5["domain_ratified"] is True, "D5 domain lost ratification")
    require(d5["baseline_ratified"] is True, "D5 baseline lost ratification")
    require(d5["generated_count"] == 8, "D5 generated count changed")
    require(d5["unknown_count"] == 24, "D5 protected UNKNOWN count changed")
    require(d5["manual_nonselector_count"] == 0, "D5 gained manual resident")

    require(d6["canonical"]["generated_members"] == 16, "D6 selector closure changed")
    require(d6["canonical"]["unknown_free"] == 48, "D6 canonical UNKNOWN count changed")
    require(d6["canonical"]["occupancy_mutations"] == 0, "D6 research mutated occupancy")
    target = next(row for row in d6["frontier"] if row["coordinate"] == "001111")
    require(target["research_evidence_class"] == "OWNER-READY-NONADMITTED",
            "001111 owner-readiness changed")
    require(target["canonical_semantic_member"] is False,
            "001111 became admitted without audit update")

    rows: list[dict[str, Any]] = []
    for op in EXPECTED_OPS:
        h = historical[op]
        p = placed[op]
        require(h["phase_status"] == "complete", f"{op}: historical ingest not complete")
        require(h["binary_object"] == "unplaced", f"{op}: historical ingest allocated bits")

        earliest = EARLIEST_EXPLAINING_DOMAIN.get(op, "NONE")
        delta = SURVIVING_DELTAS.get(op, "NONE")

        needs_law = False
        needs_domain = False
        needs_placement = False
        owner_decision = False

        if op in EARLIEST_EXPLAINING_DOMAIN:
            readiness = "ALREADY-EXPLAINED"
            missing = "NONE"
            require(p["resident_required"] == "NO", f"{op}: explained row now requires resident")
            require(p["coordinate"] == "NONE", f"{op}: explained row gained coordinate")
        elif op == "SET":
            readiness = "NEEDS-DOMAIN"
            needs_domain = True
            needs_placement = True
            missing = "shared-location carrier is established; exact-domain + residency/coordinate theorem remain"
            require(p["placement_kind"] == "CARRIER-FAMILY", "SET carrier classification drift")
        elif op == "SETQ":
            readiness = "OWNER-READY"
            owner_decision = True
            missing = "owner decision only for candidate D6:001111; historical row remains UNPLACED"
            require(p["candidate_coordinate"] == "D6:001111 (OD-001 owner-ready only)",
                    "SETQ owner-ready candidate drift")
        elif op == "PROG":
            readiness = "COMPOSITE"
            missing = "NONE-as-resident; decompose GO + RETURN"
            require(p["resident_required"] == "NO-AS-COMPOSITE", "PROG composite status drift")
        elif op == "RETURN":
            readiness = "NEEDS-DOMAIN"
            needs_domain = True
            needs_placement = True
            missing = "non-local-exit root is proven; exact domain/width + placement theorem remain"
            require(p["placement_kind"] == "PROVEN-ROOT-UNPLACED", "RETURN root status drift")
        elif op in {"FEXPR", "FSUBR"}:
            readiness = "NEEDS-DOMAIN"
            needs_domain = True
            needs_placement = True
            missing = "raw/env protocol factorization is established; exact domain/width + placement theorem remain"
            require(p["placement_kind"] == "CARRIER-FAMILY", f"{op}: carrier classification drift")
        elif op == "TRANSFORMER":
            readiness = "NEEDS-LAW"
            needs_law = True
            needs_domain = True
            needs_placement = True
            missing = "carrier+returned-form+timing protocol still needs a canonical structural law before domain/placement"
            require(p["placement_kind"] == "POLICY-OVER-CARRIER",
                    "TRANSFORMER policy-over-carrier classification drift")
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
            "current_domain_status": p["exact_domain"],
            "binary_object": h["binary_object"],
            "ratification_readiness": readiness,
            "needs_law": needs_law,
            "needs_domain": needs_domain,
            "needs_placement": needs_placement,
            "owner_decision": owner_decision,
            "missing_evidence": missing,
            "placement_kind": p["placement_kind"],
            "candidate_coordinate": p["candidate_coordinate"],
            "falsifier_guard": "chronology!=residency; #2508 domain firewall; no free-slot search",
        })

    already = [r for r in rows if r["ratification_readiness"] == "ALREADY-EXPLAINED"]
    needs_law = [r for r in rows if r["needs_law"]]
    needs_domain = [r for r in rows if r["needs_domain"]]
    needs_placement = [r for r in rows if r["needs_placement"]]
    owner_ready = [r for r in rows if r["ratification_readiness"] == "OWNER-READY"]
    composite = [r for r in rows if r["ratification_readiness"] == "COMPOSITE"]

    require([r["historical_capability"] for r in owner_ready] == ["SETQ"],
            "owner-ready set changed; review required")
    require([r["historical_capability"] for r in needs_law] == ["TRANSFORMER"],
            "surviving NEEDS-LAW set changed; review required")
    require(set(r["historical_capability"] for r in needs_domain) ==
            {"SET", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"},
            "NEEDS-DOMAIN set changed; review required")
    require(set(r["historical_capability"] for r in needs_placement) ==
            {"SET", "RETURN", "FEXPR", "FSUBR", "TRANSFORMER"},
            "NEEDS-PLACEMENT set changed; review required")
    require([r["historical_capability"] for r in composite] == ["PROG"],
            "composite set changed")

    return {
        "schema": "d1-d6-historical-gap-audit/v2",
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
                "owner_ready_nonadmitted": ["001111"],
                "missing": "owner decision for 001111; new theorem for anything else",
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
                "status": "HISTORICAL-CHRONOLOGY-REFINED / OUTSIDE-CORE-RESIDENCY-DENOMINATOR",
                "refs": ["#2697", "#2710", "#2721", "#2715", "#2722"],
                "domain_rule": "Core-Math bridge required; historical spelling cannot populate Core D5/D6",
                "residency_denominator_rows": 0,
                "memo24_1961": {
                    "rows_compared": memo24["counts"]["rows"],
                    "attested": memo24["counts"]["attested"],
                    "not_attested": memo_not_attested,
                    "changed_by_1962_manual": memo_changed,
                    "unresolved_relation": memo_unresolved,
                    "stable_negative_control": "RECIP fixed-point -> 0 is not exact-Q reciprocal",
                },
            }
        },
        "reopen_on_change_inputs": [
            "docs/research/2344-post-d4-historical-ledger.json",
            "benchmarks/post-d4-semantic-placement/placement.json",
            "docs/research/2715-memo24-arithmetic-comparison.json",
            "scripts/research-2689-d5-ratified-baseline.py",
            "benchmarks/d6-unknown-frontier/run.py",
        ],
        "owner_facing": {
            "ready_now": [
                {
                    "decision": "OD-001",
                    "binary_object": "D6:001111",
                    "status": "OWNER-READY-NONADMITTED",
                    "meaning": "shared-location / SETQ binding-policy product candidate",
                    "authority": "#2538",
                }
            ],
            "not_ready": [r["historical_capability"] for r in rows if r["needs_domain"] or r["needs_law"]],
            "do_not_ratify_as_resident": [r["historical_capability"] for r in already + composite],
        },
        "summary": {
            "historical_rows": len(rows),
            "already_explained": len(already),
            "needs_new_law": len(needs_law),
            "needs_domain": len(needs_domain),
            "needs_placement": len(needs_placement),
            "owner_ready": len(owner_ready),
            "composite": len(composite),
            "memo24_arithmetic_rows": memo24["counts"]["rows"],
            "arithmetic_rows_in_core_residency_denominator": 0,
            "new_d5_manual_residents": 0,
            "new_d6_admissions": 0,
        },
        "guards": [
            "historical presence != resident necessity",
            "free coordinate != candidate",
            "roothood != width",
            "factor count != domain",
            "same name != same semantic law",
            "historical chronology delta != Core residency pressure",
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
        "| historical row | earliest explaining domain | surviving delta | readiness | law? | domain? | placement? | missing |",
        "|---|---|---|---|---:|---:|---:|---|",
    ]
    for row in result["rows"]:
        lines.append(
            f"| {row['historical_capability']} | "
            f"{row['earliest_ratified_domain_that_explains_it']} | "
            f"{row['surviving_observable_delta']} | "
            f"**{row['ratification_readiness']}** | "
            f"{'yes' if row['needs_law'] else 'no'} | "
            f"{'yes' if row['needs_domain'] else 'no'} | "
            f"{'yes' if row['needs_placement'] else 'no'} | "
            f"{row['missing_evidence']} |"
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
        "## Owner-ready now",
        "",
        "- OD-001: D6:001111 is owner-ready but nonadmitted. No other historical row is owner-ready.",
        "",
        "## Arithmetic chronology — outside the 19-row Core residency denominator",
        "",
        f"- Memo 24 (1961) directly attests {result['foreign_or_pending_ingest']['lisp15_arithmetic']['memo24_1961']['attested']}/26 rows.",
        "- Five 1962-manual rows are not attested in Memo 24: QUOTIENT, REMAINDER, DIVIDE, EXPT, LEFTSHIFT.",
        "- Four laws change from Memo 24 to the 1962 manual: LESSP, GREATERP, ONEP, EQUAL.",
        "- ZEROP and FLOATP remain source-level UNRESOLVED in the comparison.",
        "- RECIP fixed-point -> 0 is a stable #2508 negative control against exact-Q reciprocal identity.",
        "- Arithmetic chronology contributes 0 rows to the Core D5/D6 residency denominator.",
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
    print("owner-ready=D6:001111")
    print("needs-law=TRANSFORMER")
    print("needs-domain=SET,RETURN,FEXPR,FSUBR,TRANSFORMER")
    print("arithmetic-core-residency-denominator=0")
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
