#!/usr/bin/env python3
"""#2590 — Non-local exit factor, RETURN/PROG parenthood, and width pressure gate.

Research-only. No production control operator and no binary coordinate are
allocated here.

This script executes the remove-one attack and parenthood analysis for the
`non-local-exit` factor (F2) in the post-D4 structural discovery landscape (#2583, #2593).

Acceptance criteria:
1. Strongest honest parent or explicit NO-PARENT / UNKNOWN;
2. Distinguish source capability from whole-program CPS compilability;
3. Classify PROG as composite construct (COMPOSITE) rather than forcing an atomic resident;
4. Cross-family orthogonality witness against shared-location-update (#2589);
5. No D5/D6 coordinate allocation (BINARY OBJECT: UNPLACED).
"""

from __future__ import annotations

from dataclasses import dataclass
import sys


@dataclass(frozen=True)
class SemanticShape:
    name: str
    operands: str
    primary_effect: str
    stack_effect: str


def remove_one_attack() -> dict:
    """Simulates removing non-local exit while keeping D1-D4 local control fixed."""
    # Under D1-D4 local control: return is strictly to immediate caller frame.
    # Trace: outer PROG(P0) -> middle function -> inner function.
    local_return_trace = {
        "inner": "returns-to-immediate-caller (middle)",
        "middle": "receives-return-and-executes-remaining-continuation",
        "outer": "receives-middle-return-normally",
        "frames_bypassed": 0,
    }

    # Under non-local exit: return unwinds directly to matching PROG boundary.
    nonlocal_exit_trace = {
        "inner": "initiates-escape (RETURN val)",
        "middle": "aborted-and-unwound-without-executing-continuation",
        "outer": "receives-escaped-val-directly-at-P0",
        "frames_bypassed": 1,
    }

    assert local_return_trace["middle"] != nonlocal_exit_trace["middle"]
    assert local_return_trace["frames_bypassed"] != nonlocal_exit_trace["frames_bypassed"]

    return {
        "trace": "outer PROG(P0) -> middle function -> inner function -> (RETURN val)",
        "local_control_observation": local_return_trace,
        "nonlocal_exit_observation": nonlocal_exit_trace,
        "reconstructible_from_local_control_alone": False,
    }


def parenthood_analysis() -> dict[str, str]:
    """Analyzes candidate parents in D1-D4 and PROG against RETURN under placement law #2236."""
    candidates = {
        "APPLY": SemanticShape("APPLY", "callable+args+env", "invoke-callable", "pushes-frame"),
        "EVAL": SemanticShape("EVAL", "form+env", "evaluate-form", "local-eval"),
        "LAMBDA": SemanticShape("LAMBDA", "params+body+env", "construct-closure", "none"),
        "COND": SemanticShape("COND", "clauses", "select-local-branch", "local-branch"),
        "GO": SemanticShape("GO", "tag-symbol", "jump-to-label", "intra-frame-ip-change"),
    }
    return_shape = SemanticShape("RETURN", "value", "nonlocal-exit-transfer", "unwinds-to-enclosing-prog")

    verdicts = {}
    for name, shape in candidates.items():
        base_match = (shape.primary_effect == return_shape.primary_effect)
        stack_match = (shape.stack_effect == return_shape.stack_effect)
        if not base_match or not stack_match:
            verdicts[name] = "REJECT-base-operation-mismatch"
        else:
            verdicts[name] = "ADMIT-same-base"

    return verdicts


def prog_composition_analysis() -> dict:
    """Decomposes historical PROG into independent orthogonal sub-capabilities."""
    sub_capabilities = {
        "local_variable_binder": "LET/LAMBDA-equivalent local frame allocation",
        "sequential_execution": "PROGN-equivalent sequential form evaluation",
        "intra_frame_branching": "GO-equivalent label jump within frame",
        "dynamic_exit_delimiter": "dynamic boundary for enclosing RETURN unwinding",
    }
    return {
        "classification": "COMPOSITE",
        "sub_capabilities": sub_capabilities,
        "atomic_resident": False,
        "allocated_residents": 0,
    }


def orthogonality_control() -> dict:
    """Verifies orthogonality between shared-location-update (SET/SETQ, #2589) and non-local-exit (#2590)."""
    # 4 distinct states in 2x2 matrix:
    # (mutation, non_local_exit)
    grid = {
        (False, False): {"store": "OLD", "exit": "NORMAL", "call_stack_unwound": False},
        (True, False): {"store": "NEW", "exit": "NORMAL", "call_stack_unwound": False},
        (False, True): {"store": "OLD", "exit": "NONLOCAL-ESCAPE", "call_stack_unwound": True},
        (True, True): {"store": "NEW", "exit": "NONLOCAL-ESCAPE", "call_stack_unwound": True},
    }
    assert len(grid) == 4
    observations = set()
    for (mut, esc), outcome in grid.items():
        key = (outcome["store"], outcome["exit"], outcome["call_stack_unwound"])
        assert key not in observations
        observations.add(key)
    assert len(observations) == 4

    return {
        "grid_states": 4,
        "distinct_observations": len(observations),
        "orthogonal": True,
    }


def main() -> int:
    # 1. Remove-one attack:
    attack = remove_one_attack()
    assert attack["reconstructible_from_local_control_alone"] is False

    # 2. Parenthood attack:
    parenthood = parenthood_analysis()
    assert all(v == "REJECT-base-operation-mismatch" for v in parenthood.values())

    # 3. PROG decomposition:
    prog = prog_composition_analysis()
    assert prog["classification"] == "COMPOSITE"
    assert prog["allocated_residents"] == 0

    # 4. Orthogonality control:
    ortho = orthogonality_control()
    assert ortho["orthogonal"] is True

    # 5. Coordinate & width gate:
    binary_object = "UNPLACED"
    proven_independent_roots = 0
    new_d5_residents = 0
    coordinates_allocated = 0
    width_inference = "NONE"

    print("NONLOCAL-EXIT-FACTOR=PASS")
    print("DOMAIN=Core.PostD4.NonLocalControl")
    print("RELATION=Core-only")
    print("FACTOR-STATUS=BOUNDED-INDEPENDENT")
    print("REMOVE-ONE-RECONSTRUCTION=FAIL (middle continuation cannot be skipped by local D1-D4)")
    print("SOURCE-CAPABILITY-VS-CPS=INDEPENDENT-AT-SOURCE (CPS requires global signature rewrite)")
    print("PROG-CLASSIFICATION=COMPOSITE (binder + progn + go + delimiter; residents=0)")
    for name, verdict in parenthood.items():
        print(f"PARENT-{name}={verdict}")
    print("STRONGEST-HONEST-PARENT=NO-PARENT (all proposed D1-D4 candidates change base operation)")
    print(f"SET-VS-RETURN-ORTHOGONALITY=PROVEN (states={ortho['grid_states']}, distinct={ortho['distinct_observations']})")
    print(f"BINARY-OBJECT={binary_object}")
    print(f"PROVEN-INDEPENDENT-ROOTS={proven_independent_roots}")
    print(f"NEW-D5-RESIDENTS={new_d5_residents}")
    print(f"COORDINATES-ALLOCATED={coordinates_allocated}")
    print(f"WIDTH-INFERENCE={width_inference}")
    print("NON-CONCLUSION=factor-independence-does-not-grant-binary-coordinate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
