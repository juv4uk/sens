#!/usr/bin/env python3
"""#2628 — minimize shared-location-update against immutable state threading.

Research-only root minimization.

Question:
Can the observable OLD -> NEW behavior of a pre-existing shared-location
observer be reconstructed from admitted pure values/functions?

Result vocabulary:
PROVEN-ROOT | DERIVED | POLICY-OVER-ROOT | CARRIER-PREMISE | UNRESOLVED

The witness deliberately separates:
1. pure update law over an explicit Store/Location carrier; and
2. transparent observation through a pre-existing observer with unchanged
   no-state-argument protocol.

If (1) is reproducible but (2) requires an ambient/shared store channel, the
factor is a CARRIER-PREMISE rather than an independent operation root.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

ROOT = Path(__file__).resolve().parents[2]
DONOR = ROOT / "crates" / "sens" / "tests" / "post_d4_set_setq_factor.rs"


class MissingBinding(Exception):
    pass


@dataclass(frozen=True)
class ImmutableStore:
    # nearest frame first: symbol -> location id
    frames: Tuple[Dict[str, str], ...]
    cells: Dict[str, str]


@dataclass(frozen=True)
class ExplicitObserver:
    location: str

    def read(self, store: ImmutableStore) -> str:
        return store.cells[self.location]


@dataclass(frozen=True)
class FrozenObserver:
    # A pure closure that captured the old value/state snapshot.
    captured_value: str

    def read(self) -> str:
        return self.captured_value


class AmbientStore:
    """Explicit model of the imported shared-state channel."""

    def __init__(self, store: ImmutableStore):
        self.frames = tuple(dict(frame) for frame in store.frames)
        self.cells = dict(store.cells)

    def nearest_location(self, name: str) -> str:
        for frame in self.frames:
            if name in frame:
                return frame[name]
        raise MissingBinding(name)

    def update(self, name: str, value: str) -> None:
        location = self.nearest_location(name)
        self.cells[location] = value


@dataclass
class AmbientObserver:
    ambient: AmbientStore
    location: str

    def read(self) -> str:
        return self.ambient.cells[self.location]


def sample_store() -> ImmutableStore:
    # nearest x shadows outer x; alias points to the same nearest location.
    return ImmutableStore(
        frames=(
            {"x": "L-inner", "alias": "L-inner"},
            {"x": "L-outer", "y": "L-y"},
        ),
        cells={
            "L-inner": "INNER-OLD",
            "L-outer": "OUTER-OLD",
            "L-y": "Y-OLD",
        },
    )


def nearest_location(store: ImmutableStore, name: str) -> str:
    for frame in store.frames:
        if name in frame:
            return frame[name]
    raise MissingBinding(name)


def pure_nearest_existing_fail_update(
    store: ImmutableStore, name: str, value: str
) -> ImmutableStore:
    """Strongest pure reconstruction: explicit Store in, fresh Store out."""

    location = nearest_location(store, name)
    cells = dict(store.cells)
    cells[location] = value
    return ImmutableStore(
        frames=tuple(dict(frame) for frame in store.frames),
        cells=cells,
    )


def source_audit() -> dict:
    text = DONOR.read_text(encoding="utf-8")
    required = [
        "nearest_existing_fail_update",
        "both_select_the_same_nearest_existing_location",
        "MissingBinding",
        "core_math_factor_cannot_be_smuggled_into_core_mutation_domain",
    ]
    missing = [term for term in required if term not in text]
    if missing:
        raise AssertionError(f"current donor drifted; missing {missing}")
    return {
        "donor": str(DONOR.relative_to(ROOT)),
        "required_terms": required,
        "status": "PASS",
    }


def run_models() -> dict:
    s0 = sample_store()
    location = nearest_location(s0, "x")

    # Shared-location alias property exists in the explicit carrier.
    assert nearest_location(s0, "alias") == location

    explicit_observer = ExplicitObserver(location)
    frozen_observer = FrozenObserver(explicit_observer.read(s0))

    # Pure reconstruction: update law itself is ordinary state transformation
    # when Store + Location identity are explicit data.
    s1 = pure_nearest_existing_fail_update(s0, "x", "INNER-NEW")
    assert s0.cells[location] == "INNER-OLD"
    assert s1.cells[location] == "INNER-NEW"
    assert s1.cells["L-outer"] == "OUTER-OLD"
    assert explicit_observer.read(s0) == "INNER-OLD"
    assert explicit_observer.read(s1) == "INNER-NEW"
    assert ExplicitObserver(nearest_location(s1, "alias")).read(s1) == "INNER-NEW"

    # But the unchanged no-state-argument observer cannot see the new immutable
    # state; it remains attached to the old snapshot/value.
    assert frozen_observer.read() == "INNER-OLD"
    _ = s1
    assert frozen_observer.read() == "INNER-OLD"

    # Importing an ambient mutable store restores the original local protocol:
    # the observer existed before update, receives no replacement state, yet
    # reads NEW afterwards. This is exactly the carrier/channel being charged.
    ambient = AmbientStore(s0)
    ambient_observer = AmbientObserver(ambient, location)
    assert ambient_observer.read() == "INNER-OLD"
    ambient.update("x", "INNER-NEW")
    assert ambient_observer.read() == "INNER-NEW"
    assert AmbientObserver(ambient, ambient.nearest_location("alias")).read() == "INNER-NEW"

    try:
        pure_nearest_existing_fail_update(s0, "missing", "NEW")
    except MissingBinding:
        pure_missing_fails = True
    else:
        pure_missing_fails = False

    try:
        ambient.update("missing", "NEW")
    except MissingBinding:
        ambient_missing_fails = True
    else:
        ambient_missing_fails = False

    assert pure_missing_fails and ambient_missing_fails

    return {
        "pure_explicit_store": {
            "update_law_reconstructed": True,
            "nearest_existing_preserved": True,
            "fail_on_missing_preserved": True,
            "alias_location_identity_preserved": True,
            "preexisting_observer_old": explicit_observer.read(s0),
            "preexisting_observer_new_if_new_store_explicitly_passed": explicit_observer.read(s1),
            "unchanged_no_state_argument_protocol": False,
        },
        "frozen_pure_observer": {
            "before": "INNER-OLD",
            "after_update_elsewhere": frozen_observer.read(),
            "sees_new_without_new_state_argument": False,
        },
        "ambient_shared_store": {
            "before": "INNER-OLD",
            "after": ambient_observer.read(),
            "sees_new_without_new_state_argument": True,
            "imported_authority": "shared Store/Location identity + ambient current-state channel",
        },
    }


def classify(models: dict) -> dict:
    pure = models["pure_explicit_store"]
    frozen = models["frozen_pure_observer"]
    ambient = models["ambient_shared_store"]

    assert pure["update_law_reconstructed"]
    assert pure["alias_location_identity_preserved"]
    assert not pure["unchanged_no_state_argument_protocol"]
    assert not frozen["sees_new_without_new_state_argument"]
    assert ambient["sees_new_without_new_state_argument"]

    return {
        "factor": "shared-location-update",
        "bounded_independent": True,
        "derivable_from_basis": False,
        "derived_component": "nearest-existing/fail state transition once Store+Location carrier is explicit",
        "hidden_capability_needed": True,
        "hidden_capability": "shared Store/Location identity + current-state observation channel",
        "basis_dependencies": [
            "ordinary immutable data",
            "lookup over explicit frame data",
            "explicit Store/Location carrier",
        ],
        "root_status": "CARRIER-PREMISE",
        "counterexample": (
            "a pre-existing no-argument observer remains OLD under pure immutable "
            "threading unless the new state/channel is supplied; ambient shared "
            "store restores OLD->NEW but imports exactly that authority"
        ),
        "width": "UNKNOWN",
        "coordinate": "UNPLACED",
        "new_residents": 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    audit = source_audit()
    models = run_models()
    verdict = classify(models)

    artifact = {
        "schema": "post-d4-root-min-r1/v1",
        "phase": "SENS-DERIVATION",
        "authority": "research-only",
        "source_audit": audit,
        "models": models,
        "verdict": verdict,
        "escape_hatches": [
            {
                "name": "mutable-cell/location",
                "effect": "preserves no-arg observer OLD->NEW",
                "charge": "shared-location carrier authority",
            },
            {
                "name": "hidden-global-store",
                "effect": "preserves no-arg observer OLD->NEW",
                "charge": "ambient state channel",
            },
            {
                "name": "alias-table/location-token",
                "effect": "preserves alias identity",
                "charge": "explicit location carrier",
            },
            {
                "name": "explicit-state-threading",
                "effect": "reconstructs update/read only when new Store is passed",
                "charge": "changes local observation protocol",
            },
        ],
        "positive_control": {
            "non_local_exit": "PROVEN-ROOT externally #2488/#2504; not rederived here"
        },
        "non_conclusions": [
            "CARRIER-PREMISE does not imply D5/D6 residency",
            "local D6 width pressure from SETQ evidence is a separate placement theorem",
            "explicit immutable state threading is not locally protocol-equivalent to ambient shared mutation",
            "no width or coordinate is inferred",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    row = verdict
    with (args.out / "verdict.tsv").open("w", newline="", encoding="utf-8") as fh:
        fields = [
            "factor",
            "bounded_independent",
            "derivable_from_basis",
            "hidden_capability_needed",
            "hidden_capability",
            "root_status",
            "width",
            "coordinate",
            "new_residents",
        ]
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerow({key: row[key] for key in fields})

    report = """# R1 shared-location-update root minimization — #2628

Bounded classification: **CARRIER-PREMISE**

The strongest pure reconstruction succeeds only after making Store + Location
identity explicit:

- nearest-existing selection is reproduced;
- fail-on-missing is reproduced;
- alias identity is reproduced;
- OLD and NEW are both readable when the corresponding immutable Store is
  explicitly passed.

But a pre-existing observer with the original no-state-argument protocol remains
OLD under pure immutable threading. Restoring transparent OLD -> NEW requires an
ambient/shared current-store channel (or equivalent mutable-cell authority).

Therefore the **update transform is derivable over an explicit carrier**, while
transparent shared-location observation depends on a **Store/Location carrier
premise**. The factor is not promoted to an independent operation root.

Width: UNKNOWN
Coordinate: UNPLACED
New residents: 0
"""
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
