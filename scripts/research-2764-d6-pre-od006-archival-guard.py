#!/usr/bin/env python3
"""#2764 — cross-era D6 authority guard.

Current occupancy authority is OD-006 (64/64, UNKNOWN=0).
Selected sparse-model tools remain executable only as PRE-OD006 theorem
snapshots. This guard prevents either side from silently impersonating the
other.
"""

from __future__ import annotations

import runpy
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

CURRENT = REPO / "scripts/research-2764-d6-owner-baseline.py"
FRONTIER = REPO / "benchmarks/d6-unknown-frontier/run.py"
READINESS = REPO / "scripts/research-2619-d6-residency-readiness.py"
NONCONTAGION = REPO / "benchmarks/d6-ratification-noncontagion/run.py"


def load(path: Path) -> dict:
    return runpy.run_path(str(path))


def main() -> int:
    current_ns = load(CURRENT)
    current = current_ns["build_result"]()

    assert current["authority"] == "#2753/OD-006"
    assert current["capacity"] == 64
    assert current["resident_count"] == 64
    assert current["unallocated_count"] == 0
    assert current["selector_count"] == 16
    assert current["historical_nonselector_count"] == 48
    assert current["coordinate_001111_owner_name"] == "DEFVAR"
    assert current["legacy_sparse_16_plus_48_current_authority"] is False
    assert current["legacy_pure_unknown_current_authority"] is False
    assert current["former_setq_001111_current_claim"] is False

    frontier_ns = load(FRONTIER)
    frontier = frontier_ns["build"]()
    assert frontier["era"] == "PRE-OD006"
    assert frontier["current_occupancy_authority"] is False
    assert frontier["superseded_by"] == "OD-006/#2764/#2777"
    assert frontier["canonical"]["scope"] == "historical-sparse-snapshot-only"
    assert frontier["canonical"]["generated_members"] == 16
    assert frontier["canonical"]["unknown_free"] == 48

    readiness = load(READINESS)
    assert readiness["ERA"] == "PRE-OD006"
    assert readiness["CURRENT_OCCUPANCY_AUTHORITY"] is False
    assert readiness["SUPERSEDED_BY"] == "OD-006/#2764/#2777"

    noncontagion = load(NONCONTAGION)
    assert noncontagion["ERA"] == "PRE-OD006"
    assert noncontagion["CURRENT_OCCUPANCY_AUTHORITY"] is False
    assert noncontagion["SUPERSEDED_BY"] == "OD-006/#2764/#2777"

    print("D6-CROSS-ERA-AUTHORITY=PASS")
    print("current=OD-006:64/64:unknown=0")
    print("current-001111=DEFVAR")
    print("historical-frontier=PRE-OD006:16+48")
    print("historical-readiness=current-authority=false")
    print("historical-noncontagion=current-authority=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
