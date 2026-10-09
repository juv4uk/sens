#!/usr/bin/env python3
"""#3238 clean-room QUOTE-fibre orthogonality attack.

Allowed premise: a represented semantic object can exist without either of the
two post-D3 capabilities under test.

Capability A:
  construct a parameterized executable behavior now, provide its value later.

Capability E:
  enter/execute represented semantic content.

The experiment asks whether current evidence justifies treating A and E as the
two values of one appended D1 factor under one D3 parent.

It does NOT prove that no future shared generator can ever be found.  It tests
the current pair hypothesis and returns UNKNOWN when the two capabilities are
observably independent and no common one-factor law is supplied.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Machine:
    late_bound_construction: bool
    stage_entry: bool

    def preserve_representation(self, form):
        return ("represented", form)

    def construct_parameterized(self, body):
        if not self.late_bound_construction:
            return ("NO-WITNESS",)
        return ("behavior", body)

    def enter_closed(self, represented):
        if not self.stage_entry:
            return ("NO-WITNESS",)
        tag, form = represented
        assert tag == "represented"
        if form[0] == "const":
            return form[1]
        return ("MALFORMED",)

    def enter_parameterized(self, behavior, value):
        if not (self.late_bound_construction and self.stage_entry):
            return ("NO-WITNESS",)
        tag, body = behavior
        assert tag == "behavior"
        if body == ("param",):
            return value
        return ("MALFORMED",)


def observations(machine: Machine) -> dict[str, object]:
    represented = machine.preserve_representation(("const", 7))
    behavior = machine.construct_parameterized(("param",))
    return {
        "preserve": represented,
        "construct_parameterized": behavior,
        "enter_closed": machine.enter_closed(represented),
        "construct_then_enter": machine.enter_parameterized(behavior, 11)
        if behavior != ("NO-WITNESS",)
        else ("NO-WITNESS",),
    }


def pass_vector(obs: dict[str, object]) -> dict[str, bool]:
    return {
        "preserve": obs["preserve"] == ("represented", ("const", 7)),
        "construct_parameterized": obs["construct_parameterized"]
        == ("behavior", ("param",)),
        "enter_closed": obs["enter_closed"] == 7,
        "construct_then_enter": obs["construct_then_enter"] == 11,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    states = {
        "00": Machine(False, False),
        "10": Machine(True, False),
        "01": Machine(False, True),
        "11": Machine(True, True),
    }

    obs = {key: observations(machine) for key, machine in states.items()}
    vectors = {key: pass_vector(value) for key, value in obs.items()}

    # The represented-object parent invariant is available in every state.
    assert all(v["preserve"] for v in vectors.values())

    # Independent intervention controls.
    assert not vectors["00"]["construct_parameterized"]
    assert vectors["10"]["construct_parameterized"]
    assert not vectors["01"]["construct_parameterized"]
    assert vectors["11"]["construct_parameterized"]

    assert not vectors["00"]["enter_closed"]
    assert not vectors["10"]["enter_closed"]
    assert vectors["01"]["enter_closed"]
    assert vectors["11"]["enter_closed"]

    # Composition requires both independent capabilities.
    assert not vectors["10"]["construct_then_enter"]
    assert not vectors["01"]["construct_then_enter"]
    assert vectors["11"]["construct_then_enter"]

    # Independence is visible under interventions:
    # toggling A with E fixed leaves the closed-entry observation unchanged;
    # toggling E with A fixed leaves the construction observation unchanged.
    assert vectors["00"]["enter_closed"] == vectors["10"]["enter_closed"]
    assert vectors["01"]["enter_closed"] == vectors["11"]["enter_closed"]
    assert (
        vectors["00"]["construct_parameterized"]
        == vectors["01"]["construct_parameterized"]
    )
    assert (
        vectors["10"]["construct_parameterized"]
        == vectors["11"]["construct_parameterized"]
    )

    rows = []
    for key, machine in states.items():
        rows.append(
            {
                "state": key,
                "late_bound_construction": int(machine.late_bound_construction),
                "stage_entry": int(machine.stage_entry),
                **{f"task_{k}": int(v) for k, v in vectors[key].items()},
            }
        )

    with (args.out / "capability-square.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(rows[0].keys()), delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    # A one-factor sibling claim needs an independently stated common factor
    # whose two values explain both children.  Current evidence instead yields
    # two independently toggleable capability axes.  Therefore the candidate
    # pair does not earn placement from the available evidence.
    result = {
        "schema": "d4-cleanroom-quote-fibre-orthogonality/v1",
        "authority": "research-only",
        "parent_invariant": "represented semantic content is preserved",
        "capability_axes": [
            "late-bound executable construction",
            "stage entry / execution of represented content",
        ],
        "observable_states": ["00", "10", "01", "11"],
        "all_four_states_distinct": len(
            {
                json.dumps(obs[key], sort_keys=True, default=str)
                for key in states
            }
        )
        == 4,
        "intervention_independence": True,
        "candidate_two-child_status": "UNKNOWN",
        "coordinate_earned": False,
        "reason": (
            "current evidence supplies two independently toggleable capabilities, "
            "not one proved two-valued local factor with a uniform generator equation"
        ),
        "positive_control_shape": {
            "selector_factor": "one local projection-choice factor with two values",
            "candidate_here": "two independent enable/disable axes",
        },
        "falsifier_boundary": (
            "a future uniform generator G(QUOTE,b) with one semantic suffix factor, "
            "parent recovery and controls may overturn UNKNOWN"
        ),
        "non_conclusions": [
            "late-bound construction is not refuted as a post-D3 capability",
            "stage entry is not refuted as a post-D3 capability",
            "the two capabilities may coexist or compose",
            "this does not assign either capability to another D3 parent",
            "UNKNOWN is not REFUTED globally",
        ],
    }
    assert result["all_four_states_distinct"]

    (args.out / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = """# D4 clean-room QUOTE fibre — orthogonality attack

The represented-content base survives in all four models.

| state | late-bound construction | stage entry | construction task | closed-entry task | combined task |
|---|---:|---:|---:|---:|---:|
"""
    for row in rows:
        report += (
            f"| {row['state']} | {row['late_bound_construction']} | "
            f"{row['stage_entry']} | {row['task_construct_parameterized']} | "
            f"{row['task_enter_closed']} | {row['task_construct_then_enter']} |\n"
        )

    report += """
Both capability axes can be toggled independently while the represented-content
parent invariant is held fixed.  The current evidence therefore does not supply
one common two-valued suffix factor or uniform generator equation.

**Status: UNKNOWN. Coordinate earned: NO.**

This is a placement falsifier for the current sibling hypothesis, not a
refutation of either post-D3 capability itself.
"""
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
