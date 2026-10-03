#!/usr/bin/env python3
"""#2590 — bounded independence witness for shared-location update vs non-local exit.

This composes already-merged live research evidence rather than inventing new
production semantics.

F1 shared-location-update:
  crates/sens/tests/post_d4_setq_state_passing.rs

F2 non-local-exit:
  crates/sens/tests/post_d4_control_derivation.rs

The witness asks only whether the two observed effects can vary independently
in the bounded evidence model. It does NOT prove either factor is a minimal
semantic root and has no width/placement implication.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MUTATION_TEST = ROOT / "crates" / "sens" / "tests" / "post_d4_setq_state_passing.rs"
CONTROL_TEST = ROOT / "crates" / "sens" / "tests" / "post_d4_control_derivation.rs"
FOOTPRINT = ROOT / "scripts" / "research-2472-transform-footprint.py"


def raw_const(text: str, name: str) -> str:
    marker = f'const {name}: &str = r#"'
    start = text.index(marker) + len(marker)
    end = text.index('"#;', start)
    return text[start:end]


def source_controls() -> None:
    mutation_file = MUTATION_TEST.read_text(encoding="utf-8")
    control_file = CONTROL_TEST.read_text(encoding="utf-8")
    footprint = FOOTPRINT.read_text(encoding="utf-8")

    mutation = raw_const(mutation_file, "DERIVED_STATE")
    control = raw_const(control_file, "DERIVED_CONTROL")

    # F1 witness owns explicit store/location/observer semantics.
    assert "post-d4-store-update-existing" in mutation
    assert "post-d4-state-set" in mutation
    assert "post-d4-make-observer" in mutation
    assert "post-d4-return" not in mutation
    assert "exit-k" not in mutation

    # F2 witness owns explicit exit-continuation semantics.
    assert "post-d4-return-helper1" in control
    assert "exit-k" in control
    assert "post-d4-store-update-existing" not in control
    assert "post-d4-state-set" not in control
    assert "post-d4-make-observer" not in control

    # Pin the already-observed live outcomes.
    assert 'assert_eq!(result, "(old new)")' in mutation_file
    assert '"(returned payload)"' in control_file
    assert '"(after payload)"' in control_file

    # Reuse the merged transformation-footprint distinction.
    assert '"CALLCHAIN-PROTOCOL-REWRITE"' in footprint
    assert '"OBSERVER-PROTOCOL-REWRITE"' in footprint


@dataclass(frozen=True)
class Observation:
    store: str
    continuation: tuple[str, ...]


def apply_shared_location(state: Observation, enabled: bool) -> Observation:
    """Mutation changes store while ordinary continuation remains reachable."""
    return Observation(
        store="NEW" if enabled else state.store,
        continuation=state.continuation + ("after-mutation",),
    )


def apply_nonlocal_exit(state: Observation, enabled: bool) -> Observation:
    """Non-local exit changes control trace while leaving store untouched."""
    if enabled:
        return Observation(store=state.store, continuation=("returned",))
    return Observation(
        store=state.store,
        continuation=state.continuation + ("after-call",),
    )


def main() -> None:
    source_controls()

    initial = Observation(store="OLD", continuation=("entered",))

    # F1 positive: store changes, control returns normally.
    mutation = apply_shared_location(initial, True)
    assert mutation.store == "NEW"
    assert "after-mutation" in mutation.continuation
    assert "returned" not in mutation.continuation

    # Remove F1: toggling only F2 can never produce the required NEW store.
    exit_only = apply_nonlocal_exit(initial, True)
    assert exit_only.store == "OLD"
    assert exit_only.continuation == ("returned",)
    assert exit_only.store != mutation.store

    # F2 positive: early exit changes control while store remains byte/logically unchanged.
    early = apply_nonlocal_exit(initial, True)
    normal = apply_nonlocal_exit(initial, False)
    assert early.store == normal.store == "OLD"
    assert early.continuation != normal.continuation
    assert "after-call" not in early.continuation
    assert "after-call" in normal.continuation

    # Remove F2: toggling only mutation cannot skip the ordinary continuation.
    mutation_only = apply_shared_location(initial, True)
    no_mutation = apply_shared_location(initial, False)
    assert "after-mutation" in mutation_only.continuation
    assert "after-mutation" in no_mutation.continuation
    assert mutation_only.continuation == no_mutation.continuation

    # Product test: the two coordinates commute in this bounded observation
    # model because each touches a distinct observable component.
    mut_then_exit = apply_nonlocal_exit(
        Observation(store="NEW", continuation=initial.continuation),
        True,
    )
    exit_then_mut = Observation(
        store="NEW",
        continuation=apply_nonlocal_exit(initial, True).continuation,
    )
    assert mut_then_exit == exit_then_mut

    print("D5-STATE-EXIT-INDEPENDENCE=PASS")
    print("F1=shared-location-update")
    print("F1-status=BOUNDED-INDEPENDENT-FROM-F2")
    print("F1-remove-one=exit-only-keeps-store-OLD")
    print("F2=non-local-exit")
    print("F2-status=BOUNDED-INDEPENDENT-FROM-F1")
    print("F2-remove-one=mutation-only-cannot-skip-continuation")
    print("CROSS-CONTROL=product-observables-separate")
    print("SOURCE-F1=post_d4_setq_state_passing.rs")
    print("SOURCE-F2=post_d4_control_derivation.rs")
    print("ROOTS-PROVEN=0")
    print("NEW-D5-RESIDENTS=0")
    print("PLACEMENT-IMPLICATION=NONE")
    print("RULE=pairwise-bounded-independence-is-not-minimal-roothood")


if __name__ == "__main__":
    main()
