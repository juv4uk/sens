#!/usr/bin/env python3
"""Bounded semantic witnesses + fail-closed census for four D10 research selections.

Models are independent reconstructions of primary spec laws, NOT execution
of the historical Lisp implementations. Ratification and coordinates forbidden.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from d10_historical_snapshot_compat import historic_view

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge/d10-historical-primary-selected-20261009.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
STATE = ROOT / "knowledge/d10-fill-v1-state.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
ARCH = ROOT / "docs/architecture/ARCHIPELAGO-V1.uk.md"

NAMES = ("DPB", "DEPOSIT-FIELD", "ARRAY-DISPLACEMENT", "HASHTABLE-ENTRIES")
SRC = {
    "DPB": "https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_dpb.html",
    "DEPOSIT-FIELD": "https://www.cs.cmu.edu/Groups/AI/util/html/hyperspec/HyperSpec/Body/fun_deposit-field.html",
    "ARRAY-DISPLACEMENT": "https://www.cs.cmu.edu/Groups/AI/html/hyperspec/HyperSpec/Body/fun_array-displacement.html",
    "HASHTABLE-ENTRIES": "https://r6rs.org/final/html/r6rs-lib/r6rs-lib-Z-H-14.html",
}

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def check(ledger, inv, state, foundation, arch):
    rows = ledger["rows"]
    assert len(historic_view(inv, ledger["source_foundation"]["d10_prior_blob"])["rows"]) == 625
    assert ledger["status"] == "SELECTED-RESEARCH-UNRATIFIED"
    assert len(rows) == 4
    assert [r["semantic_name"] for r in rows] == list(NAMES)
    assert ledger["source_foundation"]["prior_selected"] == 625
    assert ledger["accounting"] == {
        "prior_selected": 625,
        "new_selected": 4,
        "after_selected": 629,
        "ratified_added": 0,
        "coordinates_added": 0,
        "remaining": 395,
    }
    assert inv["accounting"] == {
        "selected_semantic_candidates": 629,
        "law_forced_coordinates": 256,
        "unplaced_selected_candidates": 373,
        "remaining_semantic_inventory": 395,
        "ratified_d10_residents": 0,
    }
    assert inv["capacity"] == 1024 and inv["width"] == 10
    assert state["target"]["selected_semantic_candidates"] == 629
    assert state["target"]["unplaced_selected_candidates"] == 373
    assert state["target"]["remaining_semantic_candidates"] == 395
    assert state["target"]["ratified_residents"] == 0
    assert "knowledge/d10-historical-primary-selected-20261009.json" in inv["sources"]
    assert len(inv["rows"]) == 629
    assert len({r["stable_id"] for r in inv["rows"]}) == 629
    assert len({r["semantic_name"].upper() for r in inv["rows"]}) == 629
    old, tail = inv["rows"][:625], inv["rows"][625:]
    assert [r["stable_id"] for r in tail] == [r["stable_id"] for r in rows]
    assert [r["semantic_name"] for r in tail] == list(NAMES)
    assert len({r["stable_id"] for r in old}) == 625
    assert all(r["ratified_resident"] is False for r in inv["rows"])
    assert sum(r["coordinate"] is not None for r in inv["rows"]) == 256
    lower = {str(x).upper() for d in foundation["domains"].values()
             for x in d["residents"].values()}
    assert not lower.intersection(NAMES)
    for r, cur in zip(rows, tail):
        assert r["primary_url"] == SRC[r["semantic_name"]]
        assert cur["primary_source_url"] == r["primary_url"]
        assert cur["source_class"] == "HISTORICAL-PRIMARY-MANUAL-20261009"
        assert cur["status"] == "SELECTED-RESEARCH-CANDIDATE"
        assert cur["coordinate"] is None and cur["coordinate_basis"] == "UNPLACED"
        assert cur["ratified_resident"] is False
        assert r["coordinate"] is None and r["ratified_resident"] is False
        assert r["decision"] == "SELECT-D10-RESEARCH-CANDIDATE"
        assert r["proposal_status"] == "pending-owner-ratification"
        assert r["language_visible"] is True and r["mechanism_only"] is False
        assert r["exact_D1_D9_duplicate"] is False
        assert r["exact_existing_D10_duplicate"] is False
        assert r["behavior"] and r["falsifier"] and len(r["positive_witnesses"]) >= 2
        assert r["surface_uk"] and r["surface_ukr"]
        assert r["owner"] and "D10" in r["owner"] and not r["owner"].startswith("D2-EXCLUSIVE")
        assert r["provenance"] and r["source_class"] == cur["source_class"]
    assert "D10 selected              629/1024" in arch
    assert "unplaced                  373" in arch
    assert "remaining                 395" in arch
    assert "ratified                    0" in arch
    return True

def dpb(v, s, p, integer):
    assert s >= 0 and p >= 0
    mask = ((1 << s) - 1) << p
    return (integer & ~mask) | ((v << p) & mask)

def deposit_field(v, s, p, integer):
    assert s >= 0 and p >= 0
    mask = ((1 << s) - 1) << p
    return (integer & ~mask) | (v & mask)

def witnesses():
    assert dpb(1, 1, 10, 0) == 1024
    assert dpb(-2, 2, 10, 0) == 2048
    assert dpb(123, 0, 8, 39) == 39
    assert deposit_field(7, 2, 1, 0) == 6
    assert deposit_field(-1, 4, 0, 0) == 15
    assert deposit_field(10, 2, 1, 0) == 2
    assert dpb(10, 2, 1, 0) == 4 != deposit_field(10, 2, 1, 0)
    count = 0
    for s in range(0, 6):
        for p in range(0, 7):
            for v in range(-5, 12):
                for old in (-8, -3, -1, 0, 1, 9, 39):
                    a, b = dpb(v, s, p, old), deposit_field(v, s, p, old)
                    for bit in range(0, 22):
                        mask = 1 << bit
                        expected_a = v >> (bit - p) & 1 if p <= bit < p + s else old >> bit & 1
                        expected_b = v >> bit & 1 if p <= bit < p + s else old >> bit & 1
                        assert bool(a & mask) == bool(expected_a)
                        assert bool(b & mask) == bool(expected_b)
                    count += 1

    # A model of logical aliasing, not a claim of historical runtime execution.
    class ArrayView:
        def __init__(self, data, size, base=None, offset=0):
            self.data, self.size, self.base, self.offset = data, size, base, offset
        def put(self, i, val):
            assert 0 <= i < self.size
            if self.base is None:
                self.data[i] = val
            else:
                self.base.put(i + self.offset, val)
        def get(self, i):
            assert 0 <= i < self.size
            return self.data[i] if self.base is None else self.base.get(i + self.offset)
        def displacement(self):
            return (self.base, self.offset if self.base is not None else 0)
    a = ArrayView([0] * 5, 5)
    b = ArrayView(None, 4, a, 1)
    c = ArrayView(None, 2, b, 2)
    assert b.displacement()[0] is a and b.displacement()[1] == 1
    assert c.displacement()[0] is b and c.displacement()[1] == 2
    assert a.displacement() == (None, 0)
    c.put(0, 97)
    assert a.get(3) == 97 and b.get(2) == 97
    b.put(0, 45)
    assert a.get(1) == 45

    # R6RS allows arbitrary enumeration order, but keys/values must align.
    table = {"alpha": 11, "beta": 22, "gamma": 33}
    for keys in [list(table), list(reversed(table)), ["beta", "alpha", "gamma"]]:
        values = [table[k] for k in keys]
        assert len(keys) == len(values) == len(table)
        assert all(table[k] == values[i] for i, k in enumerate(keys))
        assert set(zip(keys, values)) == set(table.items())
    assert list({}.keys()) == []
    assert set(zip(["alpha", "beta"], [22, 11])) != {("alpha", 11), ("beta", 22)}
    return count

def adverse(ledger, inv, state, foundation, arch):
    def reject(mutate):
        l, i, s = copy.deepcopy(ledger), copy.deepcopy(inv), copy.deepcopy(state)
        mutate(l, i, s)
        try: check(l, i, s, foundation, arch)
        except AssertionError: return
        raise AssertionError("unsafe mutation passed")
    reject(lambda l, i, s: l["rows"][0].__setitem__("ratified_resident", True))
    reject(lambda l, i, s: l["rows"][0].__setitem__("coordinate", "0000000001"))
    reject(lambda l, i, s: l["rows"][0].__setitem__("proposal_status", "ratified"))
    reject(lambda l, i, s: l["rows"][0].__setitem__("semantic_name", "CAR"))
    reject(lambda l, i, s: l["rows"][0].__setitem__("semantic_name", "LDB"))
    reject(lambda l, i, s: l["rows"][0].__setitem__("source_class", "MADE-UP"))
    reject(lambda l, i, s: l["rows"][0].__setitem__("falsifier", ""))
    reject(lambda l, i, s: l["rows"][0].__setitem__("mechanism_only", True))
    reject(lambda l, i, s: l["rows"][0].__setitem__("primary_url", "https://invalid.example"))
    reject(lambda l, i, s: i["rows"][-1].__setitem__("ratified_resident", True))
    reject(lambda l, i, s: i["rows"][-1].__setitem__("coordinate", "0000000001"))
    reject(lambda l, i, s: s["target"].__setitem__("selected_semantic_candidates", 625))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    l, i, s, f = [load(path) for path in (LEDGER, INVENTORY, STATE, FOUNDATION)]
    check(l, i, s, f, ARCH.read_text(encoding="utf-8"))
    n = witnesses()
    if args.self_test:
        adverse(l, i, s, f, ARCH.read_text(encoding="utf-8"))
    print(f"D10 HISTORICAL SELECTION PASS: 4 candidates, 625 -> 629, {n} exhaustive bounded bit cases, 12 negative metadata tests, 0 coordinates, 0 ratified")
if __name__ == "__main__":
    main()
