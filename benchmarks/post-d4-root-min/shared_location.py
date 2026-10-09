#!/usr/bin/env python3
"""#2628 — minimize shared-location-update against explicit immutable state.

SENS-DERIVATION only. No width, resident or coordinate allocation.

The bounded result distinguishes:
- computational expressibility over an explicit immutable store (D3/D4);
- local source-boundary equivalence for an unchanged zero-argument observer.

If the effect is reproducible only after adding a current-store/location carrier
or rewriting observer(store), the factor is not DERIVED-D4-LOCAL. The missing
authority is classified as a CARRIER-PREMISE rather than promoted to a new root.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
STATE_PASSING = ROOT / "crates" / "sens" / "tests" / "post_d4_setq_state_passing.rs"
BOUNDARY = ROOT / "crates" / "sens" / "tests" / "post_d4_transform_boundary.rs"
SHARED_LOCATION = ROOT / "crates" / "sens" / "tests" / "post_d4_setq_shared_location.rs"
OUT = ROOT / "benchmarks" / "post-d4-root-min" / "shared-location-result.json"


Store = tuple[tuple[str, str], ...]


def store_read(store: Store, location: str) -> str:
    for key, value in store:
        if key == location:
            return value
    raise KeyError(location)


def store_update_existing(store: Store, location: str, value: str) -> Store:
    found = False
    out: list[tuple[str, str]] = []
    for key, old in store:
        if key == location:
            out.append((key, value))
            found = True
        else:
            out.append((key, old))
    if not found:
        raise KeyError(location)
    return tuple(out)


@dataclass(frozen=True)
class ClosedObserver:
    """Original source protocol: observer() closes over one immutable snapshot."""

    location: str
    captured_store: Store

    def call(self) -> str:
        return store_read(self.captured_store, self.location)


@dataclass(frozen=True)
class ExplicitObserver:
    """Whole-program rewrite protocol: observer(store)."""

    location: str

    def call(self, store: Store) -> str:
        return store_read(store, self.location)


def nearest_existing_location(
    frames: tuple[tuple[tuple[str, str], ...], ...], name: str
) -> str:
    for frame in frames:
        for bound_name, location in frame:
            if bound_name == name:
                return location
    raise KeyError(name)


def source_controls() -> None:
    state = STATE_PASSING.read_text(encoding="utf-8")
    boundary = BOUNDARY.read_text(encoding="utf-8")
    shared = SHARED_LOCATION.read_text(encoding="utf-8")

    assert "Pre-existing observers are transformed closures that receive the current" in state
    assert "(00001000 (location)\n    (00001000 (store)" in state
    assert "(00001000 (observer store)\n    (observer store))" in state
    assert "derivation_uses_only_existing_d3_d4_semantic_primitives" in state

    assert "immutable_observer_with_original_zero_arg_protocol_keeps_old_snapshot" in boundary
    assert "rewritten_observer_protocol_can_receive_current_state_explicitly" in boundary

    assert (
        "nearest_existing_update_changes_the_same_outer_location_for_existing_observers"
        in shared
    )
    assert "lower_bound_is_location_identity_not_generic_value_change" in shared


def bounded_countermodel() -> dict:
    old_store: Store = (("l0", "old"), ("l1", "other"))
    new_store = store_update_existing(old_store, "l0", "new")

    closed = ClosedObserver("l0", old_store)
    explicit = ExplicitObserver("l0")

    # Immutable persistence: computing a new store cannot retroactively alter a
    # closure that captured the old store under its original zero-arg protocol.
    assert closed.call() == "old"
    assert store_read(new_store, "l0") == "new"
    assert closed.call() == "old"

    # Global state-passing compilation can reproduce OLD -> NEW only by changing
    # the observer protocol so the caller supplies the current store.
    assert explicit.call(old_store) == "old"
    assert explicit.call(new_store) == "new"

    frames = (
        (("z", "l1"),),
        (("x", "l0"), ("alias", "l0")),
    )
    assert nearest_existing_location(frames, "x") == "l0"
    assert nearest_existing_location(frames, "alias") == "l0"
    assert explicit.call(new_store) == "new"

    missing_failed = False
    try:
        nearest_existing_location(frames, "missing")
    except KeyError:
        missing_failed = True
    assert missing_failed

    return {
        "immutable_store_persistence": True,
        "unchanged_zero_arg_observer_after_external_update": closed.call(),
        "explicit_observer_old_store": explicit.call(old_store),
        "explicit_observer_new_store": explicit.call(new_store),
        "alias_location": "l0",
        "missing_name_fails_closed": True,
        "local_protocol_preserved_by_explicit_state_model": False,
    }


def render() -> dict:
    source_controls()
    model = bounded_countermodel()

    return {
        "schema": "post-d4-root-min/1",
        "issue": "#2628",
        "parent": "#2617",
        "phase": "SENS-DERIVATION",
        "factor": "shared-location-update",
        "structural_status": "BOUNDED-INDEPENDENT",
        "global_compilability": "COMPILABLE-TO-D4-GLOBAL",
        "local_derivation": "NOT-DERIVED-D4-LOCAL",
        "root_status": "CARRIER-PREMISE",
        "carrier_premise": {
            "name": "ambient-current-store/shared-location",
            "observable_role": (
                "an unchanged pre-existing observer must resolve the current value "
                "of the same logical location without receiving a new store argument"
            ),
            "explicit_data_encoding": "frames + location ids + immutable store",
            "why_not_derived_locally": (
                "the D3/D4 explicit-state encoding changes observer() into observer(store)"
            ),
        },
        "derived_components": [
            "nearest-existing lookup over explicit frame data",
            "existing-location update over explicit immutable store data",
            "alias preservation when names map to one explicit location id",
            "fail-on-miss policy over explicit data",
        ],
        "bounded_countermodel": model,
        "escape_hatches": [
            {
                "escape": "pass new store explicitly",
                "classification": "whole-program observer protocol rewrite",
            },
            {
                "escape": "mutate captured store/location in place",
                "classification": "imports mutable shared-location carrier",
            },
            {
                "escape": "read implicit global/current store",
                "classification": "imports ambient state carrier",
            },
            {
                "escape": "replace every old observer with a new closure",
                "classification": "whole-program value/protocol rewrite",
            },
        ],
        "root_promoted_by_this_result": False,
        "new_residents": 0,
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
        "evidence": [
            "#2402",
            "#2442",
            "#2468",
            "#2480",
            "#2589",
            "#2598",
            "#2615",
        ],
        "falsifier": (
            "A context-preserving D1-D4 replacement that leaves pre-existing "
            "zero-argument observers/callers unchanged yet makes them observe "
            "the nearest existing location's new value without importing an "
            "ambient/mutable store-location channel."
        ),
        "non_conclusions": [
            "CARRIER-PREMISE is not a bit-width theorem",
            "global D4 compilability is not local semantic derivation",
            "the carrier premise is not assigned a D5/D6 coordinate here",
        ],
    }


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    result = render()
    text = canonical(result)

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
    if args.check:
        assert OUT.exists(), "shared-location root-min artifact missing"
        assert OUT.read_text(encoding="utf-8") == text, "shared-location root-min artifact stale"

    print("SHARED-LOCATION-ROOT-MIN=PASS")
    print("GLOBAL-D4-COMPILABLE=yes")
    print("LOCAL-D4-DERIVED=no")
    print("ROOT-STATUS=CARRIER-PREMISE")
    print("ROOT-PROMOTED-BY-THIS-RESULT=no")
    print("WIDTH=UNKNOWN")
    print("COORDINATE=UNPLACED")
    print("NEW-RESIDENTS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
