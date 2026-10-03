#!/usr/bin/env python3
"""#2663 — non-local-exit exact-domain falsifier.

Research only. No coordinate allocation, D5/D6 occupancy mutation, or owner decision.
"""

from __future__ import annotations

import argparse
import json
import runpy
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
D5 = REPO / "benchmarks/d5-sens-derivation-closeout/factor-eligibility.json"
ROOT_CLOSEOUT = REPO / "benchmarks/post-d4-root-min-closeout/run.py"
D6_CLOSEOUT = REPO / "benchmarks/d6-closure-map/run.py"
D6_FRONTIER = REPO / "benchmarks/d6-unknown-frontier/run.py"
RETURN_WITNESS = REPO / "scripts/research-2488-return-placement.py"


def load_inputs():
    d5 = json.loads(D5.read_text(encoding="utf-8"))
    root_ns = runpy.run_path(str(ROOT_CLOSEOUT))
    d6_ns = runpy.run_path(str(D6_CLOSEOUT))
    frontier_ns = runpy.run_path(str(D6_FRONTIER))
    ret_ns = runpy.run_path(str(RETURN_WITNESS))

    d5_row = next(row for row in d5["factors"] if row["factor_id"] == "non-local-exit")
    root_row = next(row for row in root_ns["ROWS"] if row["factor"] == "non-local-exit")
    d6_rows = d6_ns["build_map"]()
    frontier = frontier_ns["build"]()
    return d5_row, root_row, d6_rows, frontier, ret_ns


def observable_controls(ret_ns):
    Target = ret_ns["Target"]
    Context = ret_ns["Context"]
    Policy = ret_ns["Policy"]
    deliver = ret_ns["deliver"]

    policies = {
        "local-completion": Policy(Target.IMMEDIATE, Context.OPTIONAL),
        "nearest-prog-optional": Policy(Target.NEAREST_PROG, Context.OPTIONAL),
        "immediate-required": Policy(Target.IMMEDIATE, Context.REQUIRED),
        "historical-non-local-exit": Policy(Target.NEAREST_PROG, Context.REQUIRED),
    }

    traces = {
        name: {
            "outside-prog": deliver(policy, ()),
            "one-prog": deliver(policy, ("P0",)),
            "nested-prog": deliver(policy, ("P0", "P1")),
        }
        for name, policy in policies.items()
    }

    assert len({json.dumps(v, sort_keys=True) for v in traces.values()}) == 4
    assert traces["historical-non-local-exit"]["nested-prog"] == ("exit", "P1")
    assert traces["historical-non-local-exit"]["outside-prog"] == ("error", "no-active-prog")

    return {
        "independent_policy_axes": [
            "completion-target: immediate-caller vs nearest-active-PROG",
            "active-context-policy: optional/fallback vs required/fail-closed",
        ],
        "required_observations": [
            "ordinary local completion",
            "nearest-active-PROG exit",
            "nested nearest-scope selection",
            "fail outside active PROG",
        ],
        "traces": traces,
        "lower_bound_note": (
            "Two independently observable policy axes are facts to preserve. "
            "They are not a theorem that identity needs exactly two bits, "
            "nor that any existing D5/D6 coordinate is eligible."
        ),
    }


def validate_inputs(d5_row, root_row, d6_rows, frontier):
    assert d5_row["classification"] == "ROOT-RESIDUE"
    assert d5_row["root_theorem"] is True
    assert d5_row["d5_eligible"] == "NO"
    assert d5_row["strongest_same_base_parent"] is None

    assert root_row["root_status"] == "PROVEN-ROOT"
    assert root_row["width"] == "UNKNOWN"
    assert root_row["coordinate"] == "UNPLACED"

    generated = [r for r in d6_rows if r["status"] == "generated"]
    ratified = [r for r in d6_rows if r["status"] == "ratified-resident"]
    unknown = [r for r in d6_rows if r["status"] == "UNKNOWN/free"]
    assert len(generated) == 16
    assert len(ratified) == 1 and ratified[0]["coordinate"] == "001111"
    assert len(unknown) == 47
    assert all(not r["semantic_member_of_ratified_domain"] for r in unknown)

    assert frontier["canonical"]["generated_members"] == 16
    assert frontier["canonical"]["ratified_manual_residents"] == 1
    assert frontier["canonical"]["unknown_free"] == 47
    assert frontier["canonical"]["occupancy_mutations"] == 0
    assert frontier["frontier_counts"] == {
        "PURE-UNKNOWN": 44,
        "PARENT-DUPLICATE-NOT-EARNED": 1,
        "OVERLAY-CANDIDATE-NONADMITTED": 2,
    }
    return_rows = [
        row for row in frontier["historical_unplaced_sidecar"]
        if row["operation"] == "RETURN"
    ]
    assert len(return_rows) == 1
    assert return_rows[0]["d6_coordinate"] is None
    assert return_rows[0]["d6_membership_inferred"] is False

    return {
        "d5": {
            "eligible": "NO",
            "free_coordinates": 24,
            "reason": (
                "No honest same-base D4 parent exists, and #2616 admits only "
                "same-base-one-delta candidates into D5 placement search."
            ),
        },
        "d6": {
            "eligible": "UNRESOLVED",
            "generated_members": 16,
            "ratified_manual_residents": 1,
            "unknown_free": 47,
            "reason": (
                "D6 has one unrelated owner-ratified shared-location resident, while remaining "
                "UNKNOWN/free capacity is still not membership evidence. "
                "No domain-selection theorem maps non-local-exit into D6."
            ),
        },
    }


def models():
    return [
        {
            "model": "R0-smallest-free-domain",
            "domain_selection_rule": "choose the smallest ratified domain with free capacity",
            "minimum_width_theorem": False,
            "independent_semantic_facts_charged": 0,
            "carrier_premises_charged": 0,
            "d5_consequence": "would choose D5 because 24 rows are free",
            "d6_consequence": "not reached",
            "coordinate_assigned": "no",
            "falsifier": "D5 root row is d5_eligible=NO despite 24 free rows",
            "verdict": "FALSIFIED",
        },
        {
            "model": "R1-historical-stratum",
            "domain_selection_rule": "use first historical stratum where capability appears",
            "minimum_width_theorem": False,
            "independent_semantic_facts_charged": 0,
            "carrier_premises_charged": 0,
            "d5_consequence": "unsupported",
            "d6_consequence": "unsupported",
            "coordinate_assigned": "no",
            "falsifier": (
                "merged root evidence retains width UNKNOWN after historical capability "
                "identity is already known; chronology is provenance, not domain law"
            ),
            "verdict": "FALSIFIED-AS-DOMAIN-AUTHORITY",
        },
        {
            "model": "R2-semantic-fact-lower-bound",
            "domain_selection_rule": (
                "select only a domain whose admitted law preserves all irreducible observations "
                "without collision or hidden metadata"
            ),
            "minimum_width_theorem": False,
            "independent_semantic_facts_charged": 2,
            "carrier_premises_charged": 1,
            "d5_consequence": "NO under current same-base-one-delta law",
            "d6_consequence": "UNRESOLVED; needs an additional D6 domain theorem",
            "coordinate_assigned": "no",
            "falsifier": (
                "derive a valid lower-bound/domain theorem or exhibit a collision-free "
                "representation with fewer charged facts and no hidden channel"
            ),
            "verdict": "SURVIVES-AS-CRITERION-DOMAIN-UNRESOLVED",
        },
        {
            "model": "R3-independent-root-domain",
            "domain_selection_rule": "parentless roots join/start a separate exact root domain",
            "minimum_width_theorem": False,
            "independent_semantic_facts_charged": 2,
            "carrier_premises_charged": 1,
            "d5_consequence": "NO if a separate-root theorem is proved",
            "d6_consequence": "NO if a separate-root theorem is proved",
            "coordinate_assigned": "no",
            "falsifier": (
                "without a canonical non-tabular construction this only moves the arbitrary table"
            ),
            "verdict": "UNPROVEN-CANDIDATE",
        },
        {
            "model": "R4-proof-addressed-construction",
            "domain_selection_rule": "proof/certificate identity precedes execution projection",
            "minimum_width_theorem": False,
            "independent_semantic_facts_charged": 2,
            "carrier_premises_charged": 1,
            "d5_consequence": "UNRESOLVED",
            "d6_consequence": "UNRESOLVED",
            "coordinate_assigned": "no",
            "falsifier": (
                "proof identity cannot replace #2490 exact semantic domain; "
                "storage/execution projection must remain non-authoritative"
            ),
            "verdict": "INSUFFICIENT-AS-DOMAIN-LAW",
        },
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    d5_row, root_row, d6_rows, frontier, ret_ns = load_inputs()
    domain_status = validate_inputs(d5_row, root_row, d6_rows, frontier)
    observations = observable_controls(ret_ns)
    rows = models()

    assert all(row["minimum_width_theorem"] is False for row in rows)
    assert all(row["coordinate_assigned"] == "no" for row in rows)

    final = {
        "D5-ELIGIBLE": "NO",
        "D6-ELIGIBLE": "UNRESOLVED",
        "MINIMUM-EXACT-DOMAIN": "UNRESOLVED",
        "COORDINATE": "UNPLACED",
    }

    result = {
        "schema": "nonlocal-exit-domain-falsifier/v1",
        "issue": "#2663",
        "phase": "SENS-DERIVATION",
        "root": {
            "id": "non-local-exit",
            "status": "PROVEN-ROOT",
            "law": "dynamic non-local exit to nearest active PROG",
            "width": "UNKNOWN",
            "coordinate": "UNPLACED",
            "evidence": ["#2488", "#2504", "#2616", "#2655"],
        },
        "observations": observations,
        "domain_status": domain_status,
        "d6_frontier_control": {
            "frontier_counts": frontier["frontier_counts"],
            "return_membership_inferred": False,
            "occupancy_mutations": frontier["canonical"]["occupancy_mutations"],
            "evidence": "#2660/#2661",
        },
        "models": rows,
        "final": final,
        "guards": [
            "root != width",
            "width != coordinate",
            "free coordinate != evidence",
            "chronology != domain law",
            "independent fact count != bit width",
            "D6 ratification != UNKNOWN-row membership",
            "no Core-Math donation without #2508 bridge",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = f"""# Non-local-exit exact-domain falsifier — #2663

The sole post-D4 PROVEN-ROOT remains **domain-unresolved**.

- D5-ELIGIBLE = **{final['D5-ELIGIBLE']}**
- D6-ELIGIBLE = **{final['D6-ELIGIBLE']}**
- MINIMUM-EXACT-DOMAIN = **{final['MINIMUM-EXACT-DOMAIN']}**
- COORDINATE = **{final['COORDINATE']}**

Hard conclusions:
- free capacity does not select a semantic domain;
- chronology does not select a semantic domain;
- two independent RETURN policy facts do not imply a two-bit identity or an existing domain;
- D5 is excluded by its own placement law;
- D6 remains unresolved because ratified width plus UNKNOWN/free capacity is not membership evidence;
- no coordinate is allocated and no owner decision is made.

Handoff to #2662:
- R2 survives only as a reusable criterion; it still lacks a fact-to-domain theorem;
- R3 remains unproved until a canonical non-tabular root-domain construction exists;
- R4 may identify proofs/certificates but cannot replace #2490 semantic domain.
"""
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
