#!/usr/bin/env python3
"""Finite GF(2) minimum-recurrence law, research only, not SENS machine bytecode.

Two DIFFERENT algorithms: exhaustive enumeration and Gaussian feasibility.
No generated function code, no claimed experimental SDR noise recovery.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-gf2-minimal-recurrence-research-v1.json"
LOWER = ROOT / "knowledge/d1-d9-foundation.json"
UPPER = ROOT / "knowledge/d10-v1-semantic-inventory.json"

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def validate_bits(seq):
    if not isinstance(seq, (tuple, list)) or any(type(x) is not int or x not in (0, 1) for x in seq):
        raise ValueError("expected a finite sequence of D1 bits")
    return tuple(seq)

def exhaustive(seq):
    s = validate_bits(seq)
    n = len(s)
    for order in range(n + 1):
        for mask in range(1 << order):   # lex order: a1 is MOST significant
            taps = tuple((mask >> (order - j - 1)) & 1 for j in range(order))
            if all(s[t] == (sum(taps[j] & s[t - j - 1] for j in range(order)) & 1)
                   for t in range(order, n)):
                return order, taps
    raise AssertionError("a length-n recurrence must fit any n-bit word")

def feasible(rows, num_variables):
    """Independent GF(2) Gaussian rank/consistency oracle."""
    pivots = {}
    for mask, rhs in rows:
        m, v = mask, rhs
        while m:
            pivot = (m & -m).bit_length() - 1
            if pivot in pivots:
                prior, val = pivots[pivot]
                m ^= prior
                v ^= val
            else:
                pivots[pivot] = (m, v)
                break
        if not m and v:
            return False
    return True

def algebraic(seq):
    s = validate_bits(seq)
    n = len(s)
    for order in range(n + 1):
        base = [
            (sum(s[t - j - 1] << j for j in range(order)), s[t])
            for t in range(order, n)
        ]
        if not feasible(base, order):
            continue
        fixed = []
        for j in range(order):  # choose zero whenever a completion exists
            if feasible(base + fixed + [(1 << j, 0)], order):
                fixed.append((1 << j, 0))
            else:
                assert feasible(base + fixed + [(1 << j, 1)], order)
                fixed.append((1 << j, 1))
        taps = tuple(v for _, v in fixed)
        assert all(s[t] == (sum(taps[j] & s[t-j-1] for j in range(order)) & 1)
                   for t in range(order, n))
        return order, taps
    raise AssertionError("finite word has no recurrence")

def metadata(dossier, lower, upper):
    assert dossier["schema"] == "d10-gf2-minimal-recurrence/v1"
    assert dossier["status"] == "SOURCE-PINNED-RESEARCH-PENDING-DEDUP-AND-OWNER"
    assert dossier["candidate"]["semantic_name"] == "BINARY-LFSR-MINIMAL-RECURRENCE"
    assert dossier["candidate"]["surface_uk"] and dossier["candidate"]["surface_ukr"]
    assert dossier["candidate"]["coordinate"] is None
    assert dossier["candidate"]["ratified"] is False
    assert dossier["candidate"]["selected"] is False
    assert dossier["candidate"]["not_a_migration_block"] is True
    assert dossier["candidate"]["core_or_library"] == "PENDING-OWNER-REVIEW"
    assert dossier["candidate"]["positive_witnesses"] and dossier["candidate"]["falsifiers"]
    assert dossier["candidate"]["owner_boundary"] == "D10-VALUES-NOT-D2-FORM"
    assert "doc.sagemath.org" in dossier["primary_sources"][0]["url"]
    assert len(upper["rows"]) == upper["accounting"]["selected_semantic_candidates"]
    assert upper["accounting"]["ratified_d10_residents"] == 0
    lower_names = {str(v).upper() for d in lower["domains"].values() for v in d["residents"].values()}
    upper_names = {r["semantic_name"].upper() for r in upper["rows"]}
    assert dossier["candidate"]["semantic_name"] not in lower_names
    assert dossier["candidate"]["semantic_name"] not in upper_names
    # A recent selection by another agent MUST make this check fail.
    assert "PRIMITIVE-BINARY-WORD-ROOT" in upper_names
    assert "GRAY-ENCODE-WORD" in upper_names
    assert "GRAY-DECODE-WORD" in upper_names

def run_witnesses():
    examples = {
        "": (0, ()),
        "0": (0, ()),
        "1": (1, (0,)),
        "00000": (0, ()),
        "11111": (1, (1,)),
        "010101": (2, (0, 1)),
        "101001": (3, (1, 0, 1)),
        "11010110010001111010": (4, (1, 0, 0, 1)),
    }
    for word, expected in examples.items():
        s = tuple(int(c) for c in word)
        assert exhaustive(s) == expected, (word, exhaustive(s))
        assert algebraic(s) == expected
    assert exhaustive((1, 0, 1, 0, 0, 1)) != exhaustive((1, 0, 1, 0, 1, 0))
    assert exhaustive((0, 1, 0, 1, 0, 1)) != (1, (1,))
    exhaustive_cases = 0
    for n in range(10):
        for integer in range(1 << n):
            s = tuple((integer >> j) & 1 for j in range(n-1, -1, -1))
            brute = exhaustive(s)
            gaussian = algebraic(s)
            assert brute == gaussian, (s, brute, gaussian)
            exhaustive_cases += 1
    rng = random.Random(20261009)
    for n in (10, 11, 12, 13, 14, 15, 16):
        for _ in range(32):
            s = [rng.randrange(2) for _ in range(n)]
            assert exhaustive(s) == algebraic(s), (n, s)
    # Invalid inputs do not silently coerce floats or booleans.
    for bad in ([-1], [2], [0.0], [True], None, "101", [0, "1"]):
        try:
            exhaustive(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid input accepted")
    return exhaustive_cases, 224

def adverse(dossier, low, high):
    def reject(change):
        item = copy.deepcopy(dossier)
        change(item)
        try:
            metadata(item, low, high)
        except AssertionError:
            return
        raise AssertionError("adversarial metadata passed")
    reject(lambda x: x["candidate"].__setitem__("coordinate", "0000000000"))
    reject(lambda x: x["candidate"].__setitem__("ratified", True))
    reject(lambda x: x["candidate"].__setitem__("selected", True))
    reject(lambda x: x["candidate"].__setitem__("semantic_name", "CAR"))
    reject(lambda x: x["candidate"].__setitem__("semantic_name", "PRIMITIVE-BINARY-WORD-ROOT"))
    reject(lambda x: x["candidate"].__setitem__("surface_uk", ""))
    reject(lambda x: x["candidate"].__setitem__("falsifiers", []))
    reject(lambda x: x["candidate"].__setitem__("owner_boundary", "D2-SYNTAX"))
    reject(lambda x: x["candidate"].__setitem__("core_or_library", "CORE-RATIFIED"))
    reject(lambda x: x["candidate"].__setitem__("not_a_migration_block", False))
    return 10

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    dossier, low, high = map(read, (DOSSIER, LOWER, UPPER))
    metadata(dossier, low, high)
    counts = run_witnesses()
    n = adverse(dossier, low, high) if args.self_test else 0
    print(f"PASS: binary GF(2) recurrence, {counts[0]} exhaustive words + {counts[1]} deterministic words, "
          f"{n} negative dossier mutations, 0 selected, 0 ratified, 0 coordinates")

if __name__ == "__main__":
    main()
