#!/usr/bin/env python3
"""Pure-graph support-pressure for bīja3 seeds (#2019 companion).

Independent of corpus-declared dependency graphs (#2031).
Edges are only:
  - prefix_gen inside CAR/CDR families (typed generator)
  - no edges among non-selector seeds (conservative: absence ≠ independence)

Metrics per seed:
  support_size       nodes whose only path to a root includes this seed
  exclusive_dependents  descendants reachable only via this seed
  co_seed_count      other seeds that share any dependent (0 for selectors here)
  derived_from_seed  whether another seed is a graph-parent (always false here)

This is a **pressure map**, not a minimality proof.
"""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

SEEDS = {
    "000": "NIL",
    "001": "QUOTE",
    "010": "ATOM",
    "011": "EQ",
    "100": "CONS",
    "101": "CAR",
    "110": "CDR",
    "111": "COND",
}


def expand_selector(root: str, depth: int) -> Set[str]:
    out = {root}
    frontier = [root]
    for _ in range(depth):
        nxt = []
        for w in frontier:
            for b in "01":
                c = w + b
                out.add(c)
                nxt.append(c)
        frontier = nxt
    return out


def build(depth: int):
    car = expand_selector("101", depth)
    cdr = expand_selector("110", depth)
    # dependents of seed s: nodes that require s in every path from a root
    # For pure prefix trees: dependents of CAR = car family excluding other seeds
    dependents: Dict[str, Set[str]] = {s: set() for s in SEEDS}
    dependents["101"] = car - set(SEEDS.keys()) | {"101"}
    dependents["110"] = cdr - set(SEEDS.keys()) | {"110"}
    for s in SEEDS:
        if s not in ("101", "110"):
            dependents[s] = {s}  # only self under this graph

    rows = []
    for s, name in SEEDS.items():
        dep = dependents[s]
        exclusive = set(dep)
        for o, od in dependents.items():
            if o == s:
                continue
            exclusive -= od
        co = 0
        for o, od in dependents.items():
            if o != s and (dep & od) - {s, o}:
                co += 1
        rows.append(
            {
                "seed": s,
                "name": name,
                "max_suffix_depth": depth,
                "support_size": len(dep),
                "exclusive_dependents": len(exclusive - {s}),
                "co_seed_count": co,
                "derived_from_other_seed": 0,
                "note": "graph-absence-not-logical-independence",
            }
        )
    return rows


def main() -> None:
    all_rows: List[dict] = []
    for d in (1, 2, 4, 6):
        all_rows.extend(build(d))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(all_rows[0].keys()), delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(all_rows)
    text = buf.getvalue()
    print(text)
    out = Path("docs/research/2019-graph-pressure.tsv")
    if Path("docs/research").is_dir():
        out.write_text(text, encoding="utf-8")
        print("wrote", out)


if __name__ == "__main__":
    main()
