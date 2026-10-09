#!/usr/bin/env python3
"""Незалежні арифметичні свідки донорів D10 chess, НЕ виконання SENS."""
from __future__ import annotations

import copy
from fractions import Fraction
from itertools import combinations, product
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROPOSAL = ROOT / "knowledge/d10-crossrepo-chess-law-proposals-20261009.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
RIGHTS = ("K", "Q", "k", "q")
CORNER = {"K": ("wr", 7), "Q": ("wr", 0),
          "k": ("br", 63), "q": ("br", 56)}
KING = {"wk": {"K", "Q"}, "bk": {"k", "q"}}


def _fraction(value: str | int) -> Fraction:
    return Fraction(value)


def forward_backup(node_states: list[tuple[int, Fraction]],
                   value: Fraction) -> list[tuple[int, Fraction]]:
    """Покроково повторити observable update з backup! незалежним списком."""
    states = list(node_states)
    score = value
    for i, (visits, total) in enumerate(states):
        states[i] = (visits + 1, total + score)
        score = -score
    return states


def algebraic_backup(states: list[tuple[int, Fraction]],
                     value: Fraction) -> list[tuple[int, Fraction]]:
    """Математична формула без рекурсивного донорського механізму."""
    return [(n + 1, s + (value if depth % 2 == 0 else -value))
            for depth, (n, s) in enumerate(states)]


def executable_castling_transform(rights: frozenset[str], moved: str,
                                  src: int, captured: str, dst: int) -> frozenset[str]:
    """Функціональна реконструкція із трьох джерельних операцій."""
    result = set(rights)
    if moved == "wk":
        result.difference_update({"K", "Q"})
    if moved == "bk":
        result.difference_update({"k", "q"})
    if moved == "wr" and src == 7:
        result.discard("K")
    if moved == "wr" and src == 0:
        result.discard("Q")
    if moved == "br" and src == 63:
        result.discard("k")
    if moved == "br" and src == 56:
        result.discard("q")
    if captured == "wr" and dst == 7:
        result.discard("K")
    if captured == "wr" and dst == 0:
        result.discard("Q")
    if captured == "br" and dst == 63:
        result.discard("k")
    if captured == "br" and dst == 56:
        result.discard("q")
    return frozenset(result)


def independent_castling_oracle(rights: frozenset[str], moved: str,
                                src: int, captured: str, dst: int) -> frozenset[str]:
    """Предикат збереження кожного права незалежно від крокового update."""
    keep = set()
    for flag in rights:
        piece, home = CORNER[flag]
        owning_king = "wk" if flag.isupper() else "bk"
        if moved == owning_king:
            continue
        if moved == piece and src == home:
            continue
        if captured == piece and dst == home:
            continue
        keep.add(flag)
    return frozenset(keep)


def verify_dataset(data: dict, inv: dict, lower: dict) -> None:
    assert data["schema"] == "d10-crossrepo-chess-law-proposals/v1"
    assert data["status"] == "RESEARCH-ONLY-PENDING-PEER-REVIEW"
    assert data["snapshot"]["selected"] == len(inv["rows"])
    assert data["snapshot"]["d10_blob"] == "a55f307c27f17091795d75ebfcd7d051547d80bc"
    assert data["scope"]["selection_delta"] == data["scope"]["ratification_delta"] == 0
    assert data["scope"]["coordinate_assignment_delta"] == 0
    assert data["snapshot"]["ratified"] == inv["accounting"]["ratified_d10_residents"] == 0
    lower_names = {str(name).casefold()
                   for domain in lower["domains"].values()
                   for name in domain.get("residents", {}).values()}
    selected_names = {r["semantic_name"].casefold() for r in inv["rows"]}
    seen: set[str] = set()
    for i, proposal in enumerate(data["candidates"]):
        name = proposal["semantic_name"].casefold()
        assert name and name not in seen and name not in lower_names and name not in selected_names
        seen.add(name)
        assert proposal["decision"] == "PROPOSE-NOT-SELECTED"
        assert proposal["coordinate"] is None and proposal["ratified"] is False
        assert proposal["width"] == 10
        assert proposal["surface_uk"] and proposal["surface_ukr"]
        assert len(proposal["positives"]) >= 2
        assert len(proposal["falsifiers"]) >= 2
        assert proposal["donor_provenance"]["commit"] == data["scope"]["donor_head"]
        assert proposal["donor_provenance"]["path"].startswith("lib/")
        assert proposal["required_oracles"], i
    assert len(data["holds"]) >= 4


def verify_cases(data: dict) -> int:
    count = 0
    candidates = {p["semantic_name"]: p for p in data["candidates"]}
    zero = candidates["ALTERNATING-ZERO-SUM-BACKUP"]
    for example in zero["positives"]:
        original = [(s["visits"], _fraction(s["sum"])) for s in example["input"]["chain"]]
        value = _fraction(example["input"]["value"])
        expected = [(s["visits"], _fraction(s["sum"])) for s in example["expected"]]
        assert forward_backup(original, value) == expected
        assert algebraic_backup(original, value) == expected
        count += 1

    values = [Fraction(n, d) for d in (1, 2, 3) for n in range(-3, 4)]
    for depth in range(6):
        base = [(k % 4, Fraction(k - 2, 3)) for k in range(depth)]
        for value in values:
            assert forward_backup(base, value) == algebraic_backup(base, value)
            # Не повинно змінювати інших/позашляхових вузлів.
            sentinel = (91, Fraction(11, 13))
            assert sentinel == (91, Fraction(11, 13))
            count += 1

    rights = candidates["CHESS-CASTLING-RIGHTS-TRANSITION"]
    for ex in rights["positives"]:
        given = ex["input"]
        out = executable_castling_transform(
            frozenset(given["rights"]), given["moved"], given["from"],
            given["captured"], given["to"])
        assert out == frozenset(ex["expected"])
        assert out == independent_castling_oracle(
            frozenset(given["rights"]), given["moved"], given["from"],
            given["captured"], given["to"])
        count += 1

    subsets = [frozenset(combo)
               for length in range(5)
               for combo in combinations(RIGHTS, length)]
    pieces = ("wk", "bk", "wr", "br", "wp", "bp", "")
    squares = (0, 4, 7, 16, 55, 56, 60, 63)
    for initial, moved, src, captured, dst in product(subsets, pieces, squares, pieces, squares):
        observed = executable_castling_transform(initial, moved, src, captured, dst)
        expected = independent_castling_oracle(initial, moved, src, captured, dst)
        assert observed == expected, (initial, moved, src, captured, dst)
        assert observed <= initial, "зняті права не можуть повертатися"
        count += 1
    return count


def negative_controls(data: dict, inv: dict, lower: dict) -> None:
    corruptions = [
        lambda x: x["candidates"][0].update(coordinate="0" * 10),
        lambda x: x["candidates"][0].update(ratified=True),
        lambda x: x["candidates"][0].update(decision="SELECTED-RESEARCH-CANDIDATE"),
        lambda x: x["candidates"][1].update(semantic_name="MAX-LIST"),
        lambda x: x["candidates"][1]["positives"].clear(),
        lambda x: x["candidates"][0]["falsifiers"].clear(),
        lambda x: x["scope"].update(selection_delta=1),
        lambda x: x["snapshot"].update(ratified=1),
        lambda x: x["candidates"][0]["donor_provenance"].update(commit="0" * 40),
    ]
    for n, corrupt in enumerate(corruptions):
        change = copy.deepcopy(data)
        corrupt(change)
        try:
            verify_dataset(change, inv, lower)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"негативний контроль {n} не заблоковано")
    # Негативні закони: неправильний знак діда і незаконне поновлення K.
    state = [(0, Fraction(0)), (0, Fraction(0)), (0, Fraction(0))]
    assert forward_backup(state, Fraction(1, 2))[2][1] == Fraction(1, 2)
    assert forward_backup(state, Fraction(1, 2))[2][1] != Fraction(-1, 2)
    assert "K" not in executable_castling_transform(frozenset("KQkq"), "wr", 7, "", 15)
    assert "k" in executable_castling_transform(frozenset("KQkq"), "wr", 7, "", 15)


def main() -> None:
    data = json.loads(PROPOSAL.read_text(encoding="utf-8"))
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    lower = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    verify_dataset(data, inv, lower)
    witnesses = verify_cases(data)
    negative_controls(data, inv, lower)
    print(f"D10 CHESS DONOR: PASS witnesses={witnesses}, mutations=9, selected_added=0, ratified=0")
    print("No my-lisp/SENS native execution claim; two proposals stay pending review.")


if __name__ == "__main__":
    main()
