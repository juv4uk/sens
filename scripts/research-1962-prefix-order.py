#!/usr/bin/env python3
"""#1962: falsify global 'nearest seed by dependency-set' prefix assignment.

Research-only. Показує, що unordered seed-support не зберігає порядок
композиції і тому не може сам визначати prefix-parent.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"
EDGES = ROOT / "docs/research/1962-lisp1-15-edges.tsv"


def read_tsv(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


nodes = read_tsv(NODES)
edges = read_tsv(EDGES)
node = {row["id"]: row for row in nodes}
seed_code = {
    row["id"]: row["seed3_code"]
    for row in nodes
    if row["seed3_code"]
}


def lcp(a: str, b: str) -> int:
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def tree_distance(a: str, b: str) -> int:
    return len(a) + len(b) - 2 * lcp(a, b)


def direct_seed_support(name: str) -> list[str]:
    out = []
    for e in edges:
        if e["source"] != name:
            continue
        target = e["target"]
        if target in seed_code and target not in out:
            out.append(target)
    return out


def best_seed_anchors(name: str) -> tuple[int, list[str], dict[str, int]]:
    support = direct_seed_support(name)
    if not support:
        return 0, [], {}
    scores = {}
    for candidate, code in seed_code.items():
        scores[candidate] = sum(
            tree_distance(code, seed_code[dep])
            for dep in support
        )
    best = min(scores.values())
    winners = sorted(k for k, v in scores.items() if v == best)
    return best, winners, scores


def main() -> None:
    interesting = ["caar", "cadr", "cdar", "cddr", "list", "null", "equal", "append"]

    print("node\tdirect-seed-support\tbest-seed-anchor(s)\tscore")
    for name in interesting:
        support = direct_seed_support(name)
        score, winners, _ = best_seed_anchors(name)
        print(
            f"{name}\t"
            f"{','.join(support) or '-'}\t"
            f"{','.join(winners) or '-'}\t"
            f"{score if winners else '-'}"
        )

    # Ключовий falsification: однаковий unordered support не зберігає порядок.
    assert set(direct_seed_support("cadr")) == {"car", "cdr"}
    assert set(direct_seed_support("cdar")) == {"car", "cdr"}

    _, cadr_winners, _ = best_seed_anchors("cadr")
    _, cdar_winners, _ = best_seed_anchors("cdar")
    assert cadr_winners == ["car", "cdr"]
    assert cdar_winners == ["car", "cdr"]

    # Але exact ordered composition дає різні коди й різні перші операції.
    assert node["cadr"]["prefix_code"] == "1011"
    assert node["cdar"]["prefix_code"] == "1100"
    assert node["cadr"]["prefix_code"][:3] == seed_code["car"]
    assert node["cdar"]["prefix_code"][:3] == seed_code["cdr"]

    print()
    print("PASS: unordered dependency support cannot distinguish CADR from CDAR;")
    print("ordered composition path does: 1011=CAR→CDR, 1100=CDR→CAR.")


if __name__ == "__main__":
    main()
