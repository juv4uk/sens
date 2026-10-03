#!/usr/bin/env python3
"""#2526 — alternative semantic-parent falsifier for D6 binding placement.

Research-only.  Tests whether current D1-D4 residents can reach the
shared-location SETQ-core target with fewer independent semantic deltas than
DEFINE, without importing hidden adapter authority.

No coordinate allocation.
"""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MissingBinding(Exception):
    pass


class Scope(str, Enum):
    CURRENT = "current"
    NEAREST = "nearest-existing"
    FRESH = "fresh-frame"
    NONE = "none"


class Miss(str, Enum):
    CREATE = "create"
    FAIL = "fail"
    NOT_APPLICABLE = "n/a"


class Access(str, Enum):
    READ = "read"
    WRITE = "write"
    CONSTRUCT = "construct"


class ValueSource(str, Enum):
    EXISTING = "existing-value"
    CALLER = "caller-provided"
    STRUCTURAL = "structural-args"


@dataclass(frozen=True)
class Capability:
    name: str
    access: Access
    scope: Scope
    miss: Miss
    value_source: ValueSource
    base_family: str


DEFINE = Capability(
    "DEFINE",
    Access.WRITE,
    Scope.CURRENT,
    Miss.CREATE,
    ValueSource.CALLER,
    "binding-location-write",
)

SETQ_CORE = Capability(
    "SETQ_CORE",
    Access.WRITE,
    Scope.NEAREST,
    Miss.FAIL,
    ValueSource.CALLER,
    "binding-location-write",
)

LOOKUP = Capability(
    "LOOKUP",
    Access.READ,
    Scope.NEAREST,
    Miss.FAIL,
    ValueSource.EXISTING,
    "binding-location-read",
)

BIND = Capability(
    "BIND",
    Access.WRITE,
    Scope.FRESH,
    Miss.CREATE,
    ValueSource.CALLER,
    "fresh-binding-construction",
)

CONS = Capability(
    "CONS",
    Access.CONSTRUCT,
    Scope.NONE,
    Miss.NOT_APPLICABLE,
    ValueSource.STRUCTURAL,
    "pair-construction",
)


def nearest_index(frames: list[dict[str, str]], name: str):
    for idx, frame in enumerate(frames):
        if name in frame:
            return idx
    return None


def execute(
    cap: Capability,
    frames: list[dict[str, str]],
    name: str,
    caller_value: str = "NEW",
):
    """Small observable semantics for the parent tournament."""
    before = deepcopy(frames)

    if cap is CONS:
        return {
            "status": "ok",
            "result": ("PAIR", name, caller_value),
            "frames": before,
            "mutated": False,
            "target": None,
            "used_caller_value": True,
        }

    if cap is LOOKUP:
        target = nearest_index(before, name)
        if target is None:
            raise MissingBinding(name)
        return {
            "status": "ok",
            "result": before[target][name],
            "frames": before,
            "mutated": False,
            "target": target,
            "used_caller_value": False,
        }

    if cap is BIND:
        after = deepcopy(before)
        after.insert(0, {name: caller_value})
        return {
            "status": "ok",
            "result": caller_value,
            "frames": after,
            "mutated": True,
            "target": 0,
            "used_caller_value": True,
        }

    # DEFINE / SETQ_CORE share the same base binding-location write operation.
    after = deepcopy(before)
    target = None
    if cap.scope is Scope.CURRENT:
        if name in after[0]:
            target = 0
    elif cap.scope is Scope.NEAREST:
        target = nearest_index(after, name)

    if target is None:
        if cap.miss is Miss.FAIL:
            raise MissingBinding(name)
        target = 0

    after[target][name] = caller_value
    return {
        "status": "ok",
        "result": caller_value,
        "frames": after,
        "mutated": True,
        "target": target,
        "used_caller_value": True,
    }


CASES = {
    "inherited": [{}, {"x": "OLD"}],
    "missing": [{}, {}],
    "same-frame": [{"x": "OLD"}, {"x": "OUTER"}],
}


def observe(cap: Capability):
    rows = []
    for case, frames in CASES.items():
        try:
            out = execute(cap, frames, "x", "NEW")
            rows.append(
                (
                    case,
                    "ok",
                    out["target"],
                    out["mutated"],
                    out["used_caller_value"],
                    out["result"],
                    tuple(tuple(sorted(f.items())) for f in out["frames"]),
                )
            )
        except MissingBinding:
            rows.append((case, "error"))
    return tuple(rows)


def lookup_accepts_value_but_reads(frames, name, caller_value):
    """Delta 1 control: add caller-value arity but do not add mutation."""
    target = nearest_index(frames, name)
    if target is None:
        raise MissingBinding(name)
    return {
        "result": frames[target][name],
        "frames": deepcopy(frames),
        "mutated": False,
        "used_caller_value": False,
    }


def lookup_mutates_old_value(frames, name):
    """Delta 2 control: add mutation but no caller replacement semantics."""
    after = deepcopy(frames)
    target = nearest_index(after, name)
    if target is None:
        raise MissingBinding(name)
    old = after[target][name]
    after[target][name] = old
    return {
        "result": old,
        "frames": after,
        "mutated": True,
        "used_caller_value": False,
    }


def lookup_independent_delta_controls():
    frames = [{}, {"x": "OLD"}]
    target = execute(SETQ_CORE, frames, "x", "NEW")

    a = lookup_accepts_value_but_reads(frames, "x", "NEW")
    b = lookup_mutates_old_value(frames, "x")

    assert a["frames"] != target["frames"]
    assert not a["mutated"]
    assert b["frames"] != target["frames"]
    assert b["result"] == "OLD"
    assert not b["used_caller_value"]

    return {
        "caller-value-without-mutation_differs": True,
        "mutation-without-caller-value_differs": True,
    }


def bind_independent_delta_controls():
    # Existing inherited binding: fresh construction differs from nearest update.
    inherited = CASES["inherited"]
    b = execute(BIND, inherited, "x", "NEW")
    s = execute(SETQ_CORE, inherited, "x", "NEW")
    assert b["frames"] != s["frames"]

    # Missing binding: BIND succeeds by construction; SETQ fails.
    missing = CASES["missing"]
    bind_missing = execute(BIND, missing, "x", "NEW")
    assert bind_missing["status"] == "ok"
    try:
        execute(SETQ_CORE, missing, "x", "NEW")
    except MissingBinding:
        setq_missing_fails = True
    else:
        setq_missing_fails = False
    assert setq_missing_fails

    return {
        "fresh-vs-existing-location_differs": True,
        "create-vs-fail_differs": True,
    }


def field_distance(a: Capability, b: Capability):
    fields = ["access", "scope", "miss", "value_source"]
    return [field for field in fields if getattr(a, field) != getattr(b, field)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    target_sig = observe(SETQ_CORE)

    # Baseline: DEFINE is same base family, exactly two observable policy deltas.
    define_deltas = field_distance(DEFINE, SETQ_CORE)
    assert define_deltas == ["scope", "miss"]
    assert observe(DEFINE) != target_sig

    # LOOKUP shares nearest/fail but is a read family and lacks caller replacement semantics.
    lookup_deltas = field_distance(LOOKUP, SETQ_CORE)
    assert lookup_deltas == ["access", "value_source"]
    lookup_controls = lookup_independent_delta_controls()
    assert all(lookup_controls.values())

    # BIND is generous: it shares write + caller value, yet fresh-location and
    # create-on-miss are independently observable differences.
    bind_deltas = field_distance(BIND, SETQ_CORE)
    assert bind_deltas == ["scope", "miss"]
    bind_controls = bind_independent_delta_controls()
    assert all(bind_controls.values())

    # CONS is incomparable structural construction.
    cons_deltas = field_distance(CONS, SETQ_CORE)
    assert len(cons_deltas) == 4

    rows = [
        {
            "parent": "DEFINE",
            "same_base_operation": True,
            "shared_observable_law": "caller-value binding-location write",
            "independent_delta_count": len(define_deltas),
            "delta_axes": "|".join(define_deltas),
            "one_bit_sufficient": False,
            "counterexample": "inherited binding distinguishes current vs nearest; missing binding distinguishes create vs fail",
            "decision": "BASELINE-PARENT-D6-LOWER-BOUND",
        },
        {
            "parent": "LOOKUP",
            "same_base_operation": False,
            "shared_observable_law": "nearest-existing + fail resolution only",
            "independent_delta_count": len(lookup_deltas),
            "delta_axes": "|".join(lookup_deltas),
            "one_bit_sufficient": False,
            "counterexample": "accepting NEW without mutation still reads OLD; mutating without caller-value semantics still cannot replace OLD with NEW",
            "decision": "REJECT-NOT-FEWER-AND-CROSS-FAMILY",
        },
        {
            "parent": "BIND",
            "same_base_operation": False,
            "shared_observable_law": "caller-provided binding write",
            "independent_delta_count": len(bind_deltas),
            "delta_axes": "location-selection|missing-policy",
            "one_bit_sufficient": False,
            "counterexample": "inherited x: fresh frame != nearest-location update; missing x: BIND succeeds while SETQ fails",
            "decision": "REJECT-NOT-FEWER-AND-FRESH-CONSTRUCTION",
        },
        {
            "parent": "CONS",
            "same_base_operation": False,
            "shared_observable_law": "none",
            "independent_delta_count": len(cons_deltas),
            "delta_axes": "|".join(cons_deltas),
            "one_bit_sufficient": False,
            "counterexample": "constructs pair and leaves environment unchanged",
            "decision": "REJECT-INCOMPARABLE-BASE-OPERATION",
        },
    ]

    # A successful falsifier would need fewer than DEFINE's two independent
    # deltas while preserving the target base-operation family.
    successful = [
        row
        for row in rows
        if row["parent"] != "DEFINE"
        and row["same_base_operation"]
        and row["independent_delta_count"] < len(define_deltas)
    ]
    assert not successful

    with (args.out / "parent-tournament.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    artifact = {
        "schema": "d6-binding-alt-parent-falsifier/v1",
        "authority": "research-only",
        "target": "shared-location SETQ-core = binding-location WRITE + nearest-existing + fail + caller-provided value",
        "baseline": {
            "parent": "DEFINE",
            "independent_deltas": define_deltas,
            "count": len(define_deltas),
        },
        "candidates": rows[1:],
        "lookup_independence_controls": lookup_controls,
        "bind_independence_controls": bind_controls,
        "successful_falsifier_found": False,
        "decision": "DEFINE-REMAINS-STRONGEST-LOCAL-PARENT",
        "non_conclusions": [
            "no D6 coordinate is ratified",
            "no axis polarity is ratified",
            "failure of current D1-D4 parents does not prove global parent uniqueness",
            "cross-family adapters are not free semantic deltas",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# D6 alternative-parent falsifier — #2526",
        "",
        "| parent | same base op? | independent deltas | one bit sufficient? | decision |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        report.append(
            f"| {row['parent']} | {row['same_base_operation']} | "
            f"{row['independent_delta_count']} | {row['one_bit_sufficient']} | "
            f"{row['decision']} |"
        )

    report += [
        "",
        "No current tested D1-D4 alternative parent reaches SETQ-core with fewer",
        "independent deltas while preserving the same base operation.",
        "",
        "LOOKUP's nearest/fail similarity is insufficient: read->write requires",
        "independent mutation and caller-value semantics.",
        "",
        "BIND already writes caller values, but fresh-location construction and",
        "missing/create behavior are independently different from existing-location SETQ.",
        "",
        "Bounded decision: DEFINE remains the strongest local semantic parent.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
