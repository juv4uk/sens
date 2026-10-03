#!/usr/bin/env python3
"""#2679 — D6 PURE-UNKNOWN domain firewall.

Research-only.

For every canonical D6 PURE-UNKNOWN coordinate, attack Core D6 membership
with four foreign lookalike sources:

1. selector-path semantic domain;
2. exact-Q factor semantic domain;
3. HUMAN-WIRE transport/framing mechanism;
4. GC/runtime mechanism metadata.

Equal raw bits or a shared low-level bit transform never authorize Core D6
semantics. A separately proved bridge is the only admitted escape hatch.
"""

from __future__ import annotations

import argparse
import json
import runpy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
FRONTIER = REPO / "benchmarks" / "d6-unknown-frontier" / "run.py"
SEPARATION = REPO / "benchmarks" / "binary-domain-separation" / "run.py"

CORE_D6 = "core-d6"
SELECTOR = "selector-path"
QGROUP = "q-group-factor"

DOMAIN_MISMATCH = "DOMAIN-MISMATCH"
MECHANISM_NONAUTHORITY = "MECHANISM-NONAUTHORITY"
BRIDGE_REQUIRED = "BRIDGE-REQUIRED"
BRIDGE_ACCEPTABLE = "BRIDGE-ACCEPTABLE"


@dataclass(frozen=True)
class ForeignEvidence:
    source_id: str
    source_kind: str  # semantic-domain | mechanism
    source_domain: str | None
    raw_bits: str
    semantic_authority: bool
    shared_mechanism: str | None = None


@dataclass(frozen=True)
class BridgeClaim:
    source_domain: str
    target_domain: str
    same_semantic_object: bool
    same_law: bool
    cross_proof: bool
    witness: str


def adjudicate_core_d6(
    target_bits: str,
    evidence: ForeignEvidence,
    bridge: BridgeClaim | None = None,
) -> str:
    assert len(target_bits) == 6 and set(target_bits) <= {"0", "1"}
    assert evidence.raw_bits == target_bits

    if evidence.source_kind == "mechanism":
        assert evidence.semantic_authority is False
        return MECHANISM_NONAUTHORITY

    assert evidence.source_kind == "semantic-domain"
    assert evidence.semantic_authority is True
    assert evidence.source_domain is not None

    if evidence.source_domain == CORE_D6:
        raise AssertionError("foreign-evidence control accidentally used Core D6")

    if bridge is None:
        return DOMAIN_MISMATCH

    if (
        bridge.source_domain == evidence.source_domain
        and bridge.target_domain == CORE_D6
        and bridge.same_semantic_object
        and bridge.same_law
        and bridge.cross_proof
        and bridge.witness
    ):
        return BRIDGE_ACCEPTABLE

    return BRIDGE_REQUIRED


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    frontier_ns = runpy.run_path(str(FRONTIER))
    frontier = frontier_ns["build"]()
    pure = sorted(
        row["coordinate"]
        for row in frontier["frontier"]
        if row["research_evidence_class"] == frontier_ns["PURE_UNKNOWN"]
    )
    assert len(pure) == 44

    separation_ns = runpy.run_path(str(SEPARATION))
    # Reuse the authoritative donor constants/functions to prove this lane
    # consumes the same domain distinction as #2508.
    assert separation_ns["SELECTOR"] == SELECTOR
    assert separation_ns["QGROUP"] == QGROUP
    assert separation_ns["SELECTOR_LAW"].domain == SELECTOR
    assert separation_ns["QGROUP_LAW"].domain == QGROUP

    return frontier, separation_ns, pure


def build() -> dict[str, Any]:
    frontier, separation_ns, pure = load_inputs()

    shared_append = "child=2*parent+bit"
    assert separation_ns["append_mechanism"]("101", "0") == "1010"
    assert separation_ns["SELECTOR_LAW"].semantic_equation != separation_ns["QGROUP_LAW"].semantic_equation

    rows = []
    verdict_counts: dict[str, int] = {}

    for bits in pure:
        attacks = [
            ForeignEvidence(
                source_id="selector-same-bits",
                source_kind="semantic-domain",
                source_domain=SELECTOR,
                raw_bits=bits,
                semantic_authority=True,
                shared_mechanism=shared_append,
            ),
            ForeignEvidence(
                source_id="qgroup-same-bits",
                source_kind="semantic-domain",
                source_domain=QGROUP,
                raw_bits=bits,
                semantic_authority=True,
                shared_mechanism=shared_append,
            ),
            ForeignEvidence(
                source_id="human-wire-framing",
                source_kind="mechanism",
                source_domain=None,
                raw_bits=bits,
                semantic_authority=False,
                shared_mechanism="framing/transport",
            ),
            ForeignEvidence(
                source_id="gc-runtime-tag",
                source_kind="mechanism",
                source_domain=None,
                raw_bits=bits,
                semantic_authority=False,
                shared_mechanism="runtime-memory-management",
            ),
        ]

        for evidence in attacks:
            verdict = adjudicate_core_d6(bits, evidence)
            expected = (
                DOMAIN_MISMATCH
                if evidence.source_kind == "semantic-domain"
                else MECHANISM_NONAUTHORITY
            )
            assert verdict == expected
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
            rows.append(
                {
                    "target_domain": CORE_D6,
                    "target_bits": bits,
                    "target_frontier_class": "PURE-UNKNOWN",
                    "foreign_source": evidence.source_id,
                    "foreign_kind": evidence.source_kind,
                    "foreign_domain": evidence.source_domain,
                    "same_raw_bits": True,
                    "shared_mechanism": evidence.shared_mechanism,
                    "bridge_supplied": False,
                    "verdict": verdict,
                    "core_d6_membership_granted": False,
                }
            )

    assert len(rows) == 44 * 4 == 176
    assert verdict_counts == {
        DOMAIN_MISMATCH: 88,
        MECHANISM_NONAUTHORITY: 88,
    }

    # Escape-hatch self-test. This is NOT evidence that such a bridge exists.
    # It proves the firewall is conditional on #2490/#2508 bridge criteria
    # rather than hard-coded xenophobia against all foreign domains.
    synthetic = ForeignEvidence(
        source_id="synthetic-qgroup-bridge-control",
        source_kind="semantic-domain",
        source_domain=QGROUP,
        raw_bits=pure[0],
        semantic_authority=True,
        shared_mechanism=shared_append,
    )
    incomplete_bridge = BridgeClaim(
        source_domain=QGROUP,
        target_domain=CORE_D6,
        same_semantic_object=True,
        same_law=False,
        cross_proof=True,
        witness="#synthetic-control",
    )
    assert (
        adjudicate_core_d6(pure[0], synthetic, incomplete_bridge)
        == BRIDGE_REQUIRED
    )

    complete_bridge = BridgeClaim(
        source_domain=QGROUP,
        target_domain=CORE_D6,
        same_semantic_object=True,
        same_law=True,
        cross_proof=True,
        witness="#synthetic-control-only",
    )
    assert (
        adjudicate_core_d6(pure[0], synthetic, complete_bridge)
        == BRIDGE_ACCEPTABLE
    )

    # The synthetic positive bridge is a harness control only. It does not
    # mutate the frontier or count as real evidence.
    assert frontier["canonical"]["occupancy_mutations"] == 0

    return {
        "schema": "d6-pure-unknown-domain-firewall/v1",
        "issue": 2679,
        "domain": "Core D6",
        "pure_unknown_count": len(pure),
        "attack_rows": rows,
        "verdict_counts": verdict_counts,
        "bridge_escape_hatch_control": {
            "incomplete_bridge": BRIDGE_REQUIRED,
            "complete_synthetic_bridge": BRIDGE_ACCEPTABLE,
            "real_bridge_claimed": False,
        },
        "result": "NO-FOREIGN-AUTHORITY-FOR-D6-PURE-UNKNOWN",
        "new_candidates": 0,
        "occupancy_mutations": 0,
        "guards": [
            "same raw bits do not imply same semantic object",
            "shared 2*x+b mechanism does not imply shared semantic law",
            "transport/framing bits have no semantic-domain authority",
            "GC/runtime tags have no semantic-domain authority",
            "only a separately proved same-object+same-law+cross-proof bridge can cross the firewall",
            "synthetic bridge control is not a production bridge claim",
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    result = build()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print("D6-PURE-UNKNOWN-DOMAIN-FIREWALL=PASS")
    print("PURE-UNKNOWN=44")
    print("ATTACKS=176")
    print("DOMAIN-MISMATCH=88")
    print("MECHANISM-NONAUTHORITY=88")
    print("REAL-BRIDGES=0")
    print("NEW-CANDIDATES=0")
    print("OCCUPANCY-MUTATIONS=0")
    print("RESULT=NO-FOREIGN-AUTHORITY-FOR-D6-PURE-UNKNOWN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
