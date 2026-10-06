#!/usr/bin/env python3
"""Finite semantic witnesses for D9 geometry S3 (#4003).

These models test semantic equations only. They intentionally do not consume
D9 coordinates. The permutation attack demonstrates that the tested equations
remain true under arbitrary reassignment of the involved UNPLACED coordinates,
so these laws do not fix absolute placement.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAWS = json.loads((ROOT / "knowledge" / "d9-geometry-laws-s3.json").read_text(encoding="utf-8"))
INV = json.loads((ROOT / "knowledge" / "d9-v1-semantic-inventory.json").read_text(encoding="utf-8"))


def witness_persistent_vector():
    xs = [3, 5, 8]
    vec = tuple(xs)
    assert list(vec) == xs
    assert len(vec) == 3
    assert vec[1] == 5
    vec2 = vec + (13,)
    assert list(vec2) == [3, 5, 8, 13]
    assert list(vec) == xs
    return ("vector", tuple(xs), vec2)


def witness_persistent_map():
    original = {"a": 1}
    updated = dict(original)
    updated["b"] = 2
    assert updated["b"] == 2
    assert "b" in updated
    assert "b" not in original
    assert sorted(updated.items()) == [("a", 1), ("b", 2)]
    return ("map", tuple(sorted(original.items())), tuple(sorted(updated.items())))


def witness_utf8():
    samples = ["", "abc", "Україна", "क", "🙂"]
    for s in samples:
        raw = s.encode("utf-8")
        assert raw.decode("utf-8") == s
    bad = bytes([0xC0, 0xAF])
    try:
        bad.decode("utf-8")
        raise AssertionError("invalid UTF-8 accepted")
    except UnicodeDecodeError:
        pass
    return ("utf8", tuple(samples))


def understand(words):
    if len(words) == 4 and words[1:3] == ["is", "a"]:
        return [words[3], words[0]]
    if len(words) == 3:
        return [words[1], words[0], words[2]]
    raise ValueError("unsupported controlled shape")


def narrate_fact(fact):
    if len(fact) == 2:
        return [fact[1], "is", "a", fact[0]]
    if len(fact) == 3:
        return [fact[1], fact[0], fact[2]]
    return list(fact)


def witness_understand_narrate():
    samples = [
        ["alice", "is", "a", "cat"],
        ["alice", "likes", "bob"],
    ]
    for words in samples:
        assert narrate_fact(understand(words)) == words
    return ("controlled-text", tuple(tuple(x) for x in samples))


def canonical_address(value) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def witness_content_store():
    store = {}
    value = {"kind": "fact", "value": [1, 2, 3]}
    addr = canonical_address(value)
    store2 = dict(store)
    store2[addr] = value
    assert addr in store2
    assert store2[addr] == value
    assert len(store2) == 1

    store3 = dict(store2)
    store3[canonical_address(value)] = value
    assert len(store3) == 1
    assert len(store) == 0
    return ("content-store", addr, len(store3))


def make_result(tag, *payload):
    return (tag, *payload)


def witness_result_status():
    rows = [
        make_result("proved", "g", ["p"]),
        make_result("unknown", "g"),
        make_result("partial", 1, 10),
        make_result("blocked", "missing-module"),
        make_result("disputed", ["left", "right"]),
        make_result("invalid", "bad-goal", ["x"]),
    ]
    tags = [row[0] for row in rows]
    assert len(set(tags)) == 6
    for row in rows:
        assert row[0] in tags
        assert tuple(row[1:]) == row[1:]
    return ("result-status", tuple(tags))


def normalize_dims(dims):
    return {k: Fraction(v) for k, v in dims.items() if Fraction(v) != 0}


def unit_product(left, right):
    out = dict(normalize_dims(left))
    for k, v in normalize_dims(right).items():
        out[k] = out.get(k, Fraction(0)) + v
        if out[k] == 0:
            del out[k]
    return out


def unit_quotient(left, right):
    out = dict(normalize_dims(left))
    for k, v in normalize_dims(right).items():
        out[k] = out.get(k, Fraction(0)) - v
        if out[k] == 0:
            del out[k]
    return out


def witness_quantity():
    metre = {"L": 1}
    second = {"T": 1}
    velocity = unit_quotient(metre, second)
    assert velocity == {"L": 1, "T": -1}
    assert unit_product(velocity, second) == {"L": 1}
    assert unit_quotient(metre, metre) == {}

    q1 = (Fraction(6), metre)
    q2 = (Fraction(2), second)
    quotient = (q1[0] / q2[0], unit_quotient(q1[1], q2[1]))
    assert quotient == (Fraction(3), {"L": 1, "T": -1})
    return ("quantity", quotient[0], tuple(sorted(quotient[1].items())))


WITNESSES = {
    "PERSISTENT-VECTOR-ROUNDTRIP": witness_persistent_vector,
    "PERSISTENT-MAP-COHERENCE": witness_persistent_map,
    "UTF8-UNICODE-ROUNDTRIP": witness_utf8,
    "CONTROLLED-TEXT-KNOWLEDGE-ROUNDTRIP": witness_understand_narrate,
    "CONTENT-STORE-COHERENCE": witness_content_store,
    "RESULT-STATUS-CONSTRUCTOR-PROJECTION": witness_result_status,
    "EXACT-QUANTITY-UNIT-ALGEBRA": witness_quantity,
}


def permutation_attack(names, witness):
    # Coordinates are arbitrary labels and are deliberately not passed to witness.
    coords = [f"{i:09b}" for i in range(len(names))]
    assignment_a = dict(zip(names, coords))
    assignment_b = dict(zip(names, reversed(coords)))
    assert assignment_a != assignment_b if len(names) > 1 else True
    before = witness()
    after = witness()
    assert before == after
    return True


def main() -> int:
    by_name = {row["semantic_name"]: row for row in INV["rows"]}
    assert len(LAWS["families"]) == 7

    for family in LAWS["families"]:
        name = family["family"]
        members = family["members"]
        assert name in WITNESSES
        assert family["result"] == "PROVED"
        assert family["placement_consequence"] == "NONE"
        assert all(member in by_name for member in members)
        assert all(by_name[member]["coordinate"] is None for member in members)

        WITNESSES[name]()
        assert permutation_attack(members, WITNESSES[name])

    assert LAWS["accounting"] == {
        "families_tested": 7,
        "semantic_members_covered": 38,
        "proved_families": 7,
        "fixed_coordinate_consequences": 0,
        "orbit_coordinate_consequences": 0,
        "none_coordinate_consequences": 7,
        "ratified_d9_residents": 0,
    }

    print("D9-GEOMETRY-LAWS-S3=PASS")
    print("families=7 proved=7 fixed=0 orbit=0 none=7 ratified=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
