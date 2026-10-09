#!/usr/bin/env python3
"""D10 RESEARCH ONLY: finite, propositional STRIPS backward goal regression.

No D10 coordinate; never emitted as .lisp/.sens and no compiler/ISA changes.
Fikes–Nilsson 1971 supplies the pre/add/delete action model; the bounded
weakest-predecessor theorem below follows mathematically from this model.
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
from typing import Iterable

SCHEMA = "d10-strips-goal-regression-research/v1"
ATOM = re.compile(r"[a-z][a-z0-9_-]*\Z")
MAX_ATOMS = 16


class ResearchBlocked(ValueError):
    pass


def atoms(items: Iterable[str], label: str) -> frozenset[str]:
    """Canonical finite positive propositional literal IDs; no code/variables."""
    if isinstance(items, (str, bytes)):
        raise ResearchBlocked(f"{label}: list of atom IDs required, not a string")
    try:
        given = list(items)
    except TypeError as exc:
        raise ResearchBlocked(f"{label}: finite iterable required") from exc
    if len(given) > MAX_ATOMS or any(not isinstance(x, str) or ATOM.fullmatch(x) is None for x in given):
        raise ResearchBlocked(f"{label}: at most {MAX_ATOMS} plain lowercase atom IDs")
    if len(set(given)) != len(given):
        raise ResearchBlocked(f"{label}: duplicate atom identity")
    return frozenset(given)


def validate(pre: Iterable[str], add: Iterable[str], delete: Iterable[str],
             goal: Iterable[str]) -> tuple[frozenset[str], ...]:
    p, a, d, g = (atoms(v, n) for v, n in
                  ((pre, "pre"), (add, "add"), (delete, "delete"), (goal, "goal")))
    if a & d:
        raise ResearchBlocked("ACTION: same atom cannot be both added and deleted")
    if len(p | a | d | g) > MAX_ATOMS:
        raise ResearchBlocked("ACTION: finite combined atom universe too large")
    return p, a, d, g


def regress(pre: Iterable[str], add: Iterable[str], delete: Iterable[str],
            goal: Iterable[str]) -> dict:
    """Weakest *positive* predecessor conjunction for one deterministic action.

    For P=pre, A=add, D=delete, G=goal, A∩D=∅:
      If G∩D≠∅: IMPOSSIBLE for this action, not "empty goal".
      Else: R=P∪(G\A) and ∀S [R⊆S ↔ (P⊆S ∧ G⊆((S\D)∪A))].
    """
    p, a, d, g = validate(pre, add, delete, goal)
    destroys = g & d
    if destroys:
        return {
            "status": "IMPOSSIBLE_BY_DELETE",
            "required_before": None,
            "destroyed_goals": sorted(destroys),
        }
    return {
        "status": "POSSIBLE",
        "required_before": sorted(p | (g - a)),
        "destroyed_goals": [],
    }


def satisfies_after(state: Iterable[str], pre: Iterable[str], add: Iterable[str],
                    delete: Iterable[str], goal: Iterable[str]) -> bool:
    """Independent *forward* transition predicate; no regression shortcut."""
    p, a, d, g = validate(pre, add, delete, goal)
    s = atoms(state, "state")
    return p <= s and g <= ((s - d) | a)


def all_states(universe: Iterable[str]):
    universe = tuple(sorted(atoms(universe, "universe")))
    for mask in range(1 << len(universe)):
        yield frozenset(k for bit, k in enumerate(universe) if mask & (1 << bit))


def brute_predecessor(pre: Iterable[str], add: Iterable[str],
                      delete: Iterable[str], goal: Iterable[str]) -> dict:
    """Independent finite-state truth-table oracle.

    Enumerate every possible initial world; if any reaches a goal, the unique
    weakest positive conjunction is the intersection of ALL successful worlds.
    This uses forward execution, NOT the symbolic regression equation.
    """
    p, a, d, g = validate(pre, add, delete, goal)
    universe = sorted(p | a | d | g)
    successes: list[frozenset[str]] = []
    for state in all_states(universe):
        if p <= state and g <= ((state - d) | a):
            successes.append(state)
    if not successes:
        return {
            "status": "IMPOSSIBLE_BY_DELETE",
            "required_before": None,
            "destroyed_goals": sorted(g & d),
        }
    candidate = frozenset.intersection(*successes)
    # Must be iff, not merely necessary for all positive witnesses.
    for state in all_states(universe):
        reachable = p <= state and g <= ((state - d) | a)
        if (candidate <= state) != reachable:
            raise AssertionError("finite worlds do not admit a pure-positive regression")
    return {
        "status": "POSSIBLE",
        "required_before": sorted(candidate),
        "destroyed_goals": [],
    }


def exhaustive_3() -> dict:
    """All 12^3 local PRE x effect x GOAL configurations, not a hand-picked demo."""
    total = 0
    impossible = 0
    for choices in itertools.product(range(12), repeat=3):
        pre, add, delete, goal = [], [], [], []
        for symbol, value in zip(("a", "b", "c"), choices):
            if value & 1:
                pre.append(symbol)
            effect = (value // 2) % 3  # 0=none, 1=add, 2=delete
            if effect == 1:
                add.append(symbol)
            elif effect == 2:
                delete.append(symbol)
            if (value // 6) & 1:
                goal.append(symbol)
        predicted = regress(pre, add, delete, goal)
        checked = brute_predecessor(pre, add, delete, goal)
        if predicted != checked:
            raise AssertionError(f"symbolic vs exhaustive mismatch: {pre, add, delete, goal}")
        total += 1
        impossible += predicted["status"] == "IMPOSSIBLE_BY_DELETE"
    return {
        "schema": SCHEMA,
        "status": "RESEARCH_ONLY_NOT_SELECTED",
        "configurations": total,
        "impossible_action_goal_cases": impossible,
        "independent_oracle": "exhaustive-forward-state-enumeration",
        "d10_coordinate": None,
        "d10_ratified": False,
        "original_executable_migrations": 0,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--self-check", action="store_true")
    p.add_argument("--pre", nargs="*", default=[])
    p.add_argument("--add", nargs="*", default=[])
    p.add_argument("--delete", nargs="*", default=[])
    p.add_argument("--goal", nargs="*", default=[])
    a = p.parse_args()
    try:
        state = exhaustive_3() if a.self_check else regress(a.pre, a.add, a.delete, a.goal)
        print(json.dumps(state, ensure_ascii=False, sort_keys=True))
        return 0
    except (ResearchBlocked, AssertionError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
