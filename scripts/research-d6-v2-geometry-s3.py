#!/usr/bin/env python3
import json
import math
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ledger = json.loads((ROOT / "knowledge/d6-v2-law-first-ledger.json").read_text(encoding="utf-8"))
families = json.loads((ROOT / "knowledge/d6-v2-binary-law-families.json").read_text(encoding="utf-8"))

free = sorted(row["coordinate"] for row in ledger["rows"] if row["status"] == "UNKNOWN")
assert len(free) == 32
assert len(families["families"]) == 16
assert all(len(f["members"]) == 2 for f in families["families"])

def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(a, b))

n = len(free)
adj = [0] * n
edges = []
for i, a in enumerate(free):
    for j in range(i + 1, n):
        b = free[j]
        if hamming(a, b) == 1:
            adj[i] |= 1 << j
            adj[j] |= 1 << i
            edges.append((i, j))

@lru_cache(maxsize=None)
def perfect_matchings(mask: int) -> int:
    if mask == 0:
        return 1
    vertices = [i for i in range(n) if (mask >> i) & 1]
    i = min(vertices, key=lambda v: (adj[v] & mask).bit_count())
    neighbors = adj[i] & mask
    total = 0
    while neighbors:
        bit = neighbors & -neighbors
        j = bit.bit_length() - 1
        total += perfect_matchings(mask & ~(1 << i) & ~(1 << j))
        neighbors -= bit
    return total

full = (1 << n) - 1
matching_count = perfect_matchings(full)

free_set = set(free)
global_axes = []
axis_pairs = {}
for bit in range(6):
    mask = 1 << bit
    seen = set()
    pairs = []
    ok = True
    for cell in free:
        if cell in seen:
            continue
        peer = f"{int(cell, 2) ^ mask:06b}"
        if peer not in free_set:
            ok = False
            break
        pair = tuple(sorted((cell, peer)))
        pairs.append(pair)
        seen.add(cell)
        seen.add(peer)
    if ok and len(pairs) == 16:
        global_axes.append(bit)
        axis_pairs[str(bit)] = sorted(set(pairs))

assert len(edges) == 56
assert matching_count == 7128
assert global_axes == [0]

family_permutations = math.factorial(16)
local_orientations = 2 ** 16
oriented_gauge = family_permutations * local_orientations

result = {
    "schema": "d6-v2-geometry-s3/v1",
    "status": "research-theorem-with-residual-gauge",
    "issue": "#3384",
    "free_cells": len(free),
    "hamming1_edges": len(edges),
    "perfect_matchings": matching_count,
    "binary_semantic_families": len(families["families"]),
    "global_axes_covering_all_free_cells": global_axes,
    "unique_common_axis": "least-significant-bit / xxxxx0<->xxxxx1",
    "axis0_pairs": axis_pairs["0"],
    "family_to_fibre_permutations_without_more_laws": family_permutations,
    "independent_pair_polarities_without_more_laws": local_orientations,
    "oriented_embeddings_after_common_axis_only": oriented_gauge,
    "coordinate_theorem": (
        "Conditional on one common one-bit refinement axis for all sixteen "
        "two-member law families, the free D6 residue forces the LSB axis uniquely."
    ),
    "not_proved": (
        "No current semantic law uniquely assigns a particular family to a particular "
        "5-bit fibre, nor fixes a universal 0/1 polarity inside all families."
    ),
}
print(json.dumps(result, indent=2, sort_keys=True))
print("D6-V2-GEOMETRY-S3: PASS")
