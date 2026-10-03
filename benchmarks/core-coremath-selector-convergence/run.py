#!/usr/bin/env python3
"""#2495 — bounded Core <-> Core-Math selector convergence cross-proof.

Core side:
- generated selector rows from the Core census;
- independent symbolic pair-selection semantics.

Core-Math side:
- standalone Rust bits+law executor from #2491.

The two sides share no semantic lookup table. The cross-proof compares only
exact-width bits, domain width, and the selector-extension equation.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT / "knowledge" / "function-status-census.json"

FAIL = ("FAIL",)


def atom(name: str):
    return ("ATOM", name)


def pair(left, right):
    return ("PAIR", left, right)


def project(value, bit: str):
    if not isinstance(value, tuple) or len(value) != 3 or value[0] != "PAIR":
        return FAIL
    return value[1] if bit == "0" else value[2]


def eval_selector(root_bits: str, law_path: str, value):
    root_choice = {"101": "0", "110": "1"}[root_bits]
    descriptor = root_choice + law_path
    out = value
    for bit in reversed(descriptor):
        out = project(out, bit)
        if out == FAIL:
            return FAIL
    return out


def corpus():
    leaves = [atom(chr(ord("a") + i)) for i in range(16)]
    level = leaves
    while len(level) > 1:
        level = [pair(level[i], level[i + 1]) for i in range(0, len(level), 2)]
    full = level[0]
    return [
        full,
        pair(full, atom("tail")),
        pair(atom("head"), full),
        pair(pair(atom("x"), atom("y")), pair(atom("z"), full)),
        atom("outside"),
    ]


def semantic_extension_holds(root: str, parent_path: str, delta: str) -> bool:
    child_path = parent_path + delta
    for value in corpus():
        child = eval_selector(root, child_path, value)
        staged = eval_selector(root, parent_path, project(value, delta))
        if child != staged:
            return False
    return True


def rust_apply(binary: Path, parent: str, delta: str) -> str:
    proc = subprocess.run(
        [str(binary), parent, delta],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.stdout.strip()


def selector_rows():
    data = json.loads(CENSUS.read_text(encoding="utf-8"))
    rows = [
        row
        for row in data["rows"]
        if row["status"] == "generated"
        and row.get("search_grammar") == "selector-suffix-v1"
    ]
    assert len(rows) == 12
    return sorted(rows, key=lambda row: (int(row["width"]), row["function_identity"]))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = selector_rows()
    results = []

    for row in rows:
        child = row["function_identity"]
        root = row["root_basis"]
        path = row["law_path"]
        delta = path[-1]
        parent_path = path[:-1]
        parent = root + parent_path

        assert semantic_extension_holds(root, parent_path, delta)
        generated = rust_apply(args.binary, parent, delta)

        results.append({
            "width": int(row["width"]),
            "core_child_bits": child,
            "core_root_bits": root,
            "core_law_path": path,
            "parent_bits": parent,
            "delta_bit": delta,
            "core_semantic_extension": True,
            "coremath_generated_bits": generated,
            "exact_binary_equal": generated == child,
            "exact_domain_width_equal": len(generated) == int(row["width"]),
            "human_projection": row.get("human_surface_optional") or "",
        })

    assert all(r["exact_binary_equal"] for r in results)
    assert all(r["exact_domain_width_equal"] for r in results)

    # Re-encoding/permutation attack: leave Core semantics unchanged but swap two
    # width-4 child coordinates. Exact binary equality with Core-Math must fail.
    permuted = {r["core_child_bits"]: r["core_child_bits"] for r in results}
    permuted["1010"], permuted["1011"] = "1011", "1010"
    attack_failures = 0
    for r in results:
        if r["width"] == 4 and r["core_child_bits"] in {"1010", "1011"}:
            if r["coremath_generated_bits"] != permuted[r["core_child_bits"]]:
                attack_failures += 1
    assert attack_failures == 2

    with (args.out / "selector-cross-proof.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=list(results[0].keys()),
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(results)

    artifact = {
        "schema": "core-coremath-selector-convergence/v1",
        "authority": "research-only",
        "candidate": "selector-composition",
        "classification": "CONVERGENT-BOUNDED",
        "core_witness": {
            "source": "knowledge/function-status-census.json",
            "generated_rows": len(results),
            "widths": sorted({r["width"] for r in results}),
            "semantic_equation": "extend(selector,b)(x) = selector(project_b(x))",
        },
        "core_math_witness": {
            "source": "#2491 standalone Rust bits+law executor",
            "binary_equation": "E(extend(s,b)) = 2*E(s)+b",
            "law_factor_bits": "10",
            "reads_core_census": False,
        },
        "cross_proof": {
            "exact_binary_matches": sum(r["exact_binary_equal"] for r in results),
            "exact_domain_width_matches": sum(r["exact_domain_width_equal"] for r in results),
            "semantic_extension_matches": sum(r["core_semantic_extension"] for r in results),
            "total_rows": len(results),
        },
        "permutation_attack": {
            "kind": "swap Core width-4 children 1010/1011 while preserving symbolic selector semantics",
            "exact_convergence_failures": attack_failures,
            "passes_falsifier": attack_failures > 0,
        },
        "divergent_control": {
            "candidate": "Core D7 Sound7 vs Core-Math exact-Q",
            "status": "DIVERGENT",
            "reason": "different domain and semantics; binary representation alone is insufficient",
            "refs": ["#2449", "#2490"],
        },
        "non_conclusions": [
            "bounded convergence of selector law does not merge Core and Core-Math",
            "D3 selector-root independence is not proved by this witness",
            "human selector names are diagnostic projections only",
            "other Core domains need separate cross-proofs",
        ],
    }
    (args.out / "result.json").write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Core <-> Core-Math selector convergence — #2495",
        "",
        f"Core generated selector rows checked: **{len(results)}**",
        f"Exact binary matches: **{artifact['cross_proof']['exact_binary_matches']}**",
        f"Exact domain-width matches: **{artifact['cross_proof']['exact_domain_width_matches']}**",
        f"Independent semantic-extension checks: **{artifact['cross_proof']['semantic_extension_matches']}**",
        "",
        "Bounded classification: **CONVERGENT** for the tested D4/D5 selector descendants.",
        "",
        "The Core side derives meaning from symbolic pair selection.",
        "The Core-Math side derives bits from the independent factor-10 binary law.",
        "They meet on the same exact-width binary child for every tested generated row.",
        "",
        f"Permutation attack failures: **{attack_failures}** / 2 swapped rows.",
        "So arbitrary re-numbering preserves neither the cross-proof nor the binary law.",
        "",
        "Divergent control: Core D7 Sound7 vs Core-Math exact-Q remains DIVERGENT;",
        "being binary is not enough to create a shared domain.",
        "",
    ]
    text = "\n".join(report)
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
