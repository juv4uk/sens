#!/usr/bin/env python3
"""#2001 [BENCH][GENERATOR-ECONOMY-1] — when does a local T0/T1 law earn a
prefix child?

Benchmark-only research harness (no runtime/contract/function-table edits).

A semantic law may be *valid* and still be *worse* than one explicit residue
row. This lane measures the economic side only.

Cost model (honest, deterministic, logical steps — NOT instruction counts)
--------------------------------------------------------------------------
Per call, an explicit index lookup and a generator dispatch are modelled as the
SAME cost (1 step). Therefore the whole difference is **one-time** cost:

    explicit  : materialise the whole family      = descendants rows
    generator : rule description + derive only the
                descendants the workload touches  = rule_size + used * depth

    used = ceil(descendants * utilisation)

Consequence, stated plainly: in this model the decision does NOT depend on the
number of calls N — N cancels on both sides. The deciding variables are family
size, utilisation and path depth. A crossover *in N* only exists when per-call
costs are asymmetric (e.g. a runtime hash cache that costs more per call than a
table index); that asymmetry is exactly what the pinned Cachegrind run must
supply, so `i_refs` stays blank here and no per-call claim is made.

The bounded result this lane produces is therefore a **utilisation threshold**:

    generator pays  <=>  used * depth  <  descendants - rule_size
                    <=>  utilisation    <  (descendants - rule_size)
                                           / (descendants * depth)

No `i_refs`/`cpu`/`valgrind_version` are claimed (no gcc/valgrind in this
sandbox); join them on `case_id` from the pinned environment.

Usage:
    python3 generator_economy.py --tsv PATH
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
from dataclasses import dataclass

ROW_BYTES = 8
RULE_BYTES = 16
UTILISATIONS = [1.0, 0.5, 0.25, 0.1]
CALL_SWEEP = [1, 16, 256, 4096, 65536]


@dataclass
class Law:
    name: str
    roots: int
    descendants: int
    max_depth: int
    mean_depth: float
    rule_size: int
    residue_required: int
    special_cases: int
    semantics_valid: bool


def selector_family(depth: int) -> tuple[int, float, int]:
    """All non-empty car/cdr paths up to `depth`."""
    descendants = 2 ** (depth + 1) - 2
    mean = sum(d for d in range(1, depth + 1) for _ in range(2 ** d)) / descendants
    return descendants, mean, depth


D10 = selector_family(10)
D4 = selector_family(4)

LAWS = [
    Law("selector-carcdr-k10", 2, D10[0], D10[2], D10[1], 3, 0, 0, True),
    Law("selector-carcdr-k4", 2, D4[0], D4[2], D4[1], 3, 0, 0, True),
    Law("atom-null-oneoff", 1, 1, 1, 1.0, 4, 0, 1, True),
    Law("eq-equal-typed-family", 1, 2, 1, 1.0, 6, 0, 2, True),
    Law("cons-negative-evidence", 1, 0, 0, 0.0, 3, 0, 0, False),
    Law("cond-andor-falsifier", 1, 1, 1, 1.0, 8, 0, 3, False),
]


def used(law: Law, utilisation: float) -> int:
    return max(1, math.ceil(law.descendants * utilisation))


def explicit_once(law: Law) -> int:
    return law.descendants


def generator_once(law: Law, utilisation: float) -> int:
    return law.rule_size + used(law, utilisation) * max(1, law.mean_depth)


def threshold(law: Law):
    """Utilisation below which the generator's one-time cost is smaller."""
    if law.descendants == 0:
        return None
    return (law.descendants - law.rule_size) / (law.descendants * max(1, law.mean_depth))


def path_sharing_nodes(law: Law):
    """Distinct proper prefixes — deliberately NOT the semantic-node count."""
    if law.descendants == 0:
        return 0
    return max(0, 2 ** law.max_depth - 2)


def rows():
    out = []
    for law in LAWS:
        for util in UTILISATIONS:
            for calls in CALL_SWEEP:
                per_call = calls * 1
                variants = {
                    "explicit-row": explicit_once(law) + per_call,
                    "generator-lazy": generator_once(law, util) + per_call,
                    "compiled-route": used(law, util) + per_call,
                }
                for cand, total in variants.items():
                    out.append({
                        "case_id": f"{law.name}/u{util}/{cand}/n{calls}",
                        "candidate": cand,
                        "family": law.name,
                        "semantic_depth": str(law.max_depth),
                        "mode": "step-model-once-vs-percall",
                        "rep": str(calls),
                        "tree_steps": str(total),
                        "bits_consumed": str(law.max_depth if cand != "explicit-row" else ""),
                        "generator_apps": str(used(law, util) if cand == "generator-lazy" else ""),
                        "registry_lookups": str(calls if cand == "explicit-row" else ""),
                        "residue_lookups": str(law.residue_required),
                        "object_bytes": str(law.descendants * ROW_BYTES if cand == "explicit-row"
                                            else law.rule_size * RULE_BYTES),
                        "corpus_sha": hashlib.sha256(law.name.encode()).hexdigest()[:16],
                        # lane-specific
                        "utilisation": str(util),
                        "rows_avoided": str(law.descendants),
                        "semantic_nodes": str(law.descendants),
                        "path_sharing_nodes": str(path_sharing_nodes(law)),
                        "rule_size": str(law.rule_size),
                        "special_cases": str(law.special_cases),
                        "residue_required": str(law.residue_required),
                        "semantics_valid": "1" if law.semantics_valid else "0",
                    })
    return out


SCHEMA_1987 = [
    "case_id", "candidate", "family", "semantic_depth", "mode", "rep", "i_refs",
    "tree_steps", "root_selections", "bits_consumed", "generator_apps",
    "registry_lookups", "residue_lookups", "cache_hits", "cache_misses",
    "allocations", "allocated_bytes", "object_bytes", "wire_bits",
    "compiler_phase", "machine_insts", "code_bytes", "loads", "stores",
    "branches", "calls", "spills", "corpus_sha", "binary_sha", "git_sha",
    "guix_channels_sha", "cpu", "valgrind_version",
    "utilisation", "rows_avoided", "semantic_nodes", "path_sharing_nodes",
    "rule_size", "special_cases", "residue_required", "semantics_valid",
]


def write_tsv(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(SCHEMA_1987) + "\n")
        for r in data:
            fh.write("\t".join(str(r.get(c, "")) for c in SCHEMA_1987) + "\n")


def verdicts():
    v = {}
    for law in LAWS:
        t = threshold(law)
        if not law.semantics_valid:
            verdict = "REJECTED (no semantic claim: negative evidence / falsifier)"
        elif t is None or t <= 0.0:
            verdict = "REJECTED (one-off law never pays for its machinery)"
        else:
            verdict = f"ACCEPT if workload touches <{t:.3f} of the family"
        v[law.name] = {"utilisation_threshold": None if t is None else round(t, 4),
                       "verdict": verdict,
                       "rows_avoided": law.descendants,
                       "semantic_nodes": law.descendants,
                       "path_sharing_nodes": path_sharing_nodes(law)}
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", default="")
    args = ap.parse_args()

    v = verdicts()
    print("== #2001 generator economy (step model) ==")
    for name, info in v.items():
        print(f"  {name:26} rows={info['rows_avoided']:5} threshold={info['utilisation_threshold']}  {info['verdict']}")

    # falsifiers
    assert (v["atom-null-oneoff"]["utilisation_threshold"] is None
            or v["atom-null-oneoff"]["utilisation_threshold"] <= 0), \
        "a one-off law must never amortise"
    assert v["selector-carcdr-k10"]["utilisation_threshold"] > 0, \
        "the selector economy control must amortise below some utilisation"
    assert v["cons-negative-evidence"]["utilisation_threshold"] is None
    # path sharing must be a DIFFERENT count from semantic nodes
    assert v["selector-carcdr-k10"]["path_sharing_nodes"] != v["selector-carcdr-k10"]["semantic_nodes"], \
        "path sharing must not be reported as the semantic-node count"
    print("falsifiers: one-off rejected ✓ ; selector control amortises ✓ ; "
          "negative/falsifier laws rejected ✓ ; path-sharing != semantic-nodes ✓")

    # N-cancellation witness
    a = explicit_once(LAWS[0]); b = generator_once(LAWS[0], 0.1)
    print(f"N-cancellation: explicit_once={a}, generator_once(u=0.1)={b} "
          f"-> decision is one-time cost, independent of call count")

    prov = {"python": platform.python_version(), "machine": platform.machine()}
    print("provenance:", json.dumps(prov))
    if args.tsv:
        data = rows()
        write_tsv(args.tsv, data)
        print(f"wrote {len(data)} raw rows -> {args.tsv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
