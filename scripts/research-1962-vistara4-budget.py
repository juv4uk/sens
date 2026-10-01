#!/usr/bin/env python3
"""#1962: compare two non-authoritative allocation objectives for vistāra4.

Research-only. Нічого не призначає. Мета — показати, які вузли стабільно
цінні за різних objective functions і де потрібне owner/semantic decision.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODES_PATH = ROOT / "docs/research/1962-lisp1-15-nodes.tsv"
EDGES_PATH = ROOT / "docs/research/1962-lisp1-15-edges.tsv"

FIXED_VISTARA4 = {"caar", "cadr", "cdar", "cddr"}
SEED = {"nil", "quote", "atom", "eq", "cons", "car", "cdr", "cond"}
FORCED_PRIMARY = {"lambda", "label"}


def read_tsv(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


nodes = read_tsv(NODES_PATH)
edges = read_tsv(EDGES_PATH)
node = {row["id"]: row for row in nodes}


def concept(name: str) -> str:
    """Collapse same evaluator/helper concept across historical eras."""
    for suffix in ("_lisp1", "_lisp15"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def metrics():
    callers = defaultdict(set)
    dependencies = defaultdict(set)
    eras = defaultdict(set)
    variants = defaultdict(set)
    kinds = defaultdict(set)

    for row in nodes:
        c = concept(row["id"])
        variants[c].add(row["id"])
        kinds[c].add(row["kind"])
        if row["era"] == "both":
            eras[c].update(("lisp1", "lisp15"))
        else:
            eras[c].add(row["era"])

    for e in edges:
        s = concept(e["source"])
        t = concept(e["target"])
        if s == t and e["relation"] == "recursion":
            continue
        callers[t].add(s)
        dependencies[s].add(t)

    out = {}
    for c, vs in variants.items():
        if c in SEED or c in FIXED_VISTARA4:
            continue
        reuse = len(callers[c])
        deps = len({d for d in dependencies[c] if d != c})
        span = len(eras[c])
        # Proxy only: a reused complex definition saves more repeated structure.
        gain = reuse * max(1, deps)
        out[c] = {
            "reuse": reuse,
            "deps": deps,
            "eras": span,
            "gain": gain,
            "variants": ",".join(sorted(vs)),
            "kinds": ",".join(sorted(kinds[c])),
        }
    return out


def reuse_key(item):
    name, m = item
    return (-m["reuse"], -m["eras"], -m["gain"], name)


def gain_key(item):
    name, m = item
    return (-m["gain"], -m["eras"], -m["reuse"], name)


def select(pool, count, key, forced=()):
    selected = []
    for n in forced:
        if n in pool and n not in selected:
            selected.append(n)
    for n, _ in sorted(pool.items(), key=key):
        if n not in selected:
            selected.append(n)
        if len(selected) == count:
            break
    return selected


def main():
    m = metrics()
    open_budget = 16 - len(FIXED_VISTARA4)
    print(f"vistāra4 capacity=16 fixed-generator={len(FIXED_VISTARA4)} open={open_budget}")
    print("fixed:", ", ".join(sorted(FIXED_VISTARA4)))

    print("\nconcept\teras\treuse\tdeps\tgain-proxy\tkind\tvariants")
    for name, x in sorted(m.items(), key=lambda kv: (-kv[1]["gain"], kv[0])):
        print(
            f"{name}\t{x['eras']}\t{x['reuse']}\t{x['deps']}\t{x['gain']}\t"
            f"{x['kinds']}\t{x['variants']}"
        )

    model_a = select(m, open_budget, reuse_key)
    model_b = select(m, open_budget, gain_key, forced=sorted(FORCED_PRIMARY))

    print("\nMODEL A — reuse-first (diagnostic)")
    print("  " + ", ".join(model_a))
    print("\nMODEL B — force LAMBDA/LABEL, then description-gain proxy")
    print("  " + ", ".join(model_b))

    common = [x for x in model_a if x in model_b]
    only_a = [x for x in model_a if x not in model_b]
    only_b = [x for x in model_b if x not in model_a]

    print("\nstability")
    print("  common:", ", ".join(common) or "-")
    print("  only-A:", ", ".join(only_a) or "-")
    print("  only-B:", ", ".join(only_b) or "-")

    # No automatic allocation if objectives disagree.
    if set(model_a) != set(model_b):
        print("\nRESULT: objectives disagree -> remaining vistāra4 allocation is NOT ratifiable yet.")
    else:
        print("\nRESULT: candidate set stable across these two weak objectives; still requires semantic evidence.")


if __name__ == "__main__":
    main()
