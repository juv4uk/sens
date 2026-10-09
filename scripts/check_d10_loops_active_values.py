#!/usr/bin/env python3
"""Bounded LOOPS active-value witness and fail-closed D10 intake check.

This is NOT an independently executed Xerox LOOPS runtime oracle.
All historical English names below are evidence/model labels, never executable SENS words.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
EVIDENCE = ROOT / "knowledge/d10-loops-active-values-intake-v1.json"
NAMES = ("ACTIVE-VALUE-GET", "ACTIVE-VALUE-PUT")


@dataclass
class Active:
    local: Any
    get_fn: Callable[[Any, list[str]], Any] | None = None
    put_fn: Callable[["Active", Any, list[str]], None] | None = None


def get_value(value: Any, events: list[str]) -> Any:
    if not isinstance(value, Active):
        return value
    # §5.2: resolve the inner node before invoking the outer getFn.
    inner = get_value(value.local, events)
    return value.get_fn(inner, events) if value.get_fn else inner


def put_value(value: Active, new_value: Any, events: list[str]) -> Any:
    if not isinstance(value, Active):
        raise TypeError("put needs an active-value reference")
    if value.put_fn is None:
        # §5.1: absent putFn replaces this node's localState, no inner trigger.
        value.local = new_value
    else:
        # §5.2: explicit delegation is required to traverse inward.
        value.put_fn(value, new_value, events)
    return new_value


def put_local_state(parent: Active, new_value: Any, events: list[str]) -> Any:
    # §5.5: ordinary PutLocalState triggers an embedded active value.
    if isinstance(parent.local, Active):
        return put_value(parent.local, new_value, events)
    parent.local = new_value
    return new_value


def get_local_state_only(value: Active) -> Any:
    # §5.5: returns the immediate node unchanged, no getFn callbacks.
    return value.local


def put_local_state_only(value: Active, new_value: Any) -> Any:
    # §5.5: replaces immediate node unchanged, no nested callbacks.
    value.local = new_value
    return new_value


def log_get(label: str, operation: Callable[[Any], Any]) -> Callable[[Any, list[str]], Any]:
    def handler(value: Any, events: list[str]) -> Any:
        events.append(label + ":get")
        return operation(value)
    return handler


def log_put(label: str, *, delegate: bool) -> Callable[[Active, Any, list[str]], None]:
    def handler(node: Active, new_value: Any, events: list[str]) -> None:
        events.append(label + ":put")
        if delegate:
            put_local_state(node, new_value, events)
    return handler


def check_intake() -> None:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    rows = inventory["rows"]
    acct = inventory["accounting"]

    assert inventory["domain"] == "D10" and inventory["capacity"] == 1024
    assert inventory["status"].startswith("RESEARCH")
    assert acct["selected_semantic_candidates"] == 627
    assert acct["unplaced_selected_candidates"] == 371
    assert acct["remaining_semantic_inventory"] == 397
    assert acct["law_forced_coordinates"] == 256
    assert acct["ratified_d10_residents"] == 0
    assert len(rows) == 627 and 627 + 397 == inventory["capacity"]
    assert sum(row["coordinate"] is None for row in rows) == 371
    assert len({row["stable_id"] for row in rows}) == len(rows)
    assert len({row["semantic_name"] for row in rows}) == len(rows)
    assert len(evidence["rows"]) == 2

    for proposal in evidence["rows"]:
        name = proposal["semantic_name"]
        assert name in NAMES
        candidates = [row for row in rows if row["semantic_name"] == name]
        assert len(candidates) == 1, (name, "missing/duplicate in D10")
        row = candidates[0]
        assert row["status"] == "SELECTED-RESEARCH-CANDIDATE"
        assert row["proposal_status"] == "pending-owner-review"
        assert row["source_class"] == "HISTORICAL-LOOPS-ACTIVE-VALUES"
        assert row["coordinate"] is None
        assert row["coordinate_basis"] == "UNPLACED"
        assert row["ratified_resident"] is False
        assert row["surface_uk"] and row["surface_ukr"]
        assert row["behavior"] == proposal["observable_law"]
        assert row["primary_url"] == evidence["source"]["url"]
        assert len(proposal["positive_witnesses"]) >= 2
        assert len(proposal["falsifiers"]) >= 2
        assert proposal["coordinate"] is None and proposal["ratified"] is False
        assert proposal["proposal_status"] == "pending-owner-review"
        for d in range(1, 10):
            table = (ROOT / ("lib/domains/d%d.lisp" % d)).read_text(encoding="utf-8")
            pattern = r"\(LISP\s+" + re.escape(name) + r"(?=[\s\)])"
            assert not re.search(pattern, table, flags=re.IGNORECASE), (name, d)

    assert evidence["baseline"]["selected_before"] == 625
    assert evidence["baseline"]["selected_after"] == 627
    assert evidence["boundary"]["language_structure"] == "D2 exclusively"
    assert evidence["boundary"]["physical_t5_authorized"] is False
    assert all(hold["status"].startswith("HOLD") for hold in evidence["holds"])
    print("D10 LOOPS intake: PASS 627/1024 selected, 371 unplaced, 397 remaining, 0 ratified")


class HistoricalLawWitness(unittest.TestCase):
    """Small executable model, tests based on LOOPS Manual §5.1–5.5."""

    def fixture(self) -> tuple[Active, Active]:
        inner = Active(10, get_fn=log_get("inner", lambda x: x + 2),
                       put_fn=log_put("inner", delegate=True))
        outer = Active(inner, get_fn=log_get("outer", lambda x: x * 3),
                       put_fn=log_put("outer", delegate=True))
        return outer, inner

    def test_read_inner_before_outer_and_result(self) -> None:
        outer, _ = self.fixture()
        events: list[str] = []
        self.assertEqual(get_value(outer, events), 36)
        self.assertEqual(events, ["inner:get", "outer:get"])
        # Wrong-order and double-call negative controls.
        self.assertNotEqual(events, ["outer:get", "inner:get"])
        self.assertNotEqual(events, ["inner:get", "inner:get", "outer:get"])

    def test_write_outer_before_inner_by_explicit_delegation(self) -> None:
        outer, inner = self.fixture()
        events: list[str] = []
        self.assertEqual(put_value(outer, 19, events), 19)
        self.assertEqual(events, ["outer:put", "inner:put"])
        self.assertEqual(inner.local, 19)

    def test_outer_put_without_delegation_does_not_mutate_inner(self) -> None:
        outer, inner = self.fixture()
        outer.put_fn = log_put("outer", delegate=False)
        events: list[str] = []
        put_value(outer, 99, events)
        self.assertEqual(events, ["outer:put"])
        self.assertEqual(inner.local, 10)

    def test_get_local_only_skips_inner_handler(self) -> None:
        outer, inner = self.fixture()
        self.assertIs(get_local_state_only(outer), inner)
        self.assertIsInstance(get_local_state_only(outer), Active)

    def test_put_local_only_replaces_immediate_node_without_effects(self) -> None:
        outer, inner = self.fixture()
        self.assertEqual(put_local_state_only(outer, 23), 23)
        self.assertEqual(outer.local, 23)
        self.assertEqual(inner.local, 10)

    def test_missing_handlers_use_unmodified_local_state(self) -> None:
        active = Active(4)
        events: list[str] = []
        self.assertEqual(get_value(active, events), 4)
        self.assertEqual(put_value(active, 7, events), 7)
        self.assertEqual(get_value(active, events), 7)
        self.assertEqual(events, [])

    def test_no_access_effect_on_unrelated_instance(self) -> None:
        outer, _ = self.fixture()
        unrelated = Active(111)
        events: list[str] = []
        put_value(outer, 29, events)
        self.assertEqual(unrelated.local, 111)
        self.assertEqual(events, ["outer:put", "inner:put"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true",
                        help="run historical bounded witness + canonical inventory proof")
    args = parser.parse_args()
    try:
        check_intake()
        if args.self_test:
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(HistoricalLawWitness)
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            if not result.wasSuccessful():
                sys.exit(1)
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        sys.exit("D10 LOOPS intake: FAIL %s" % (exc,))
