#!/usr/bin/env python3
"""#2241 anti-numerology gate for function-code arithmetic.

Research-only. This script distinguishes:
- semantic selector extension, expressed without code arithmetic;
- canonical coordinate formulas (append 0/1) that realize that law today;
- accidental arithmetic patterns that fail the current witness corpus or lack
  an independent semantic equation.

No function is allocated, promoted, or reclassified by this script.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
CENSUS = ROOT / "knowledge" / "function-status-census.json"


@dataclass(frozen=True)
class Edge:
    parent_key: tuple[str, str]
    child_key: tuple[str, str]
    law_bit: str


@dataclass(frozen=True)
class Formula:
    name: str
    semantic_operation: str | None
    law_bit: str | None
    fn: Callable[[int, int], int]


def load_selector_model():
    data = json.loads(CENSUS.read_text(encoding="utf-8"))
    rows = data["rows"]

    coord: dict[tuple[str, str], str] = {}
    all_by_width: dict[int, set[str]] = {}

    roots = sorted(
        {
            row["root_basis"]
            for row in rows
            if row["status"] == "generated" and row["root_basis"] is not None
        }
    )
    for root in roots:
        coord[(root, "")] = root

    for row in rows:
        ident = row["function_identity"]
        all_by_width.setdefault(int(row["width"]), set()).add(ident)
        if row["status"] != "generated":
            continue
        root = row["root_basis"]
        path = row["law_path"]
        if root is None or path is None:
            raise AssertionError("generated selector row lacks root/path")
        coord[(root, path)] = ident

    edges: list[Edge] = []
    for (root, path), ident in sorted(coord.items()):
        if not path:
            continue
        parent = (root, path[:-1])
        if parent not in coord:
            raise AssertionError(f"missing selector parent for {root}/{path}")
        edges.append(Edge(parent, (root, path), path[-1]))

    assert roots == ["101", "110"]
    assert len(edges) == 12
    return rows, coord, edges, all_by_width


def width_of(code: str) -> int:
    return len(code)


def p0(coord):
    return dict(coord)


def p3_reverse_within_width(coord):
    """Family-preserving semantic relabeling; exact width stays unchanged."""
    out = {}
    by_width: dict[int, list[tuple[tuple[str, str], str]]] = {}
    for key, code in coord.items():
        by_width.setdefault(len(code), []).append((key, code))
    for width, items in by_width.items():
        items = sorted(items, key=lambda item: item[1])
        codes = [code for _, code in items][::-1]
        for (key, _), code in zip(items, codes):
            assert len(code) == width
            out[key] = code
    return out


def p4_width_bijection(coord):
    """Deterministic width-preserving bijection over the full exact-width cube."""
    out = {}
    for key, code in coord.items():
        width = len(code)
        mask = (1 << width) - 1
        value = int(code, 2)
        # XOR with an all-ones mask is a bijection at fixed width.
        mapped = value ^ mask
        out[key] = f"{mapped:0{width}b}"
    return out


def eval_formula(formula: Formula, mapping, edges):
    relevant = [edge for edge in edges if edge.law_bit == formula.law_bit]
    failures = []
    passes = 0
    for edge in relevant:
        parent = mapping[edge.parent_key]
        child = mapping[edge.child_key]
        target_width = len(child)
        got = formula.fn(int(parent, 2), len(parent))
        got &= (1 << target_width) - 1
        if got == int(child, 2):
            passes += 1
        else:
            failures.append(
                {
                    "parent_semantic": f"{edge.parent_key[0]}/{edge.parent_key[1] or '-'}",
                    "parent_code": parent,
                    "expected_child_code": child,
                    "got_code": f"{got:0{target_width}b}",
                }
            )
    return passes, len(relevant), failures


def generic_coincidences(name, fn, rows, all_by_width):
    """Count numeric neighbors only; this is NOT semantic evidence."""
    coincidences = 0
    tested = 0
    first_nonmatch = None
    for row in rows:
        code = row["function_identity"]
        width = int(row["width"])
        target_width = width + 1
        if target_width not in all_by_width:
            continue
        tested += 1
        got = fn(int(code, 2), width) & ((1 << target_width) - 1)
        got_code = f"{got:0{target_width}b}"
        if got_code in all_by_width[target_width]:
            coincidences += 1
        elif first_nonmatch is None:
            first_nonmatch = {
                "source": code,
                "computed": got_code,
                "target_width": target_width,
            }
    return {
        "claim": name,
        "tested": tested,
        "numeric_coincidences": coincidences,
        "semantic_operation": None,
        "status": "accidental",
        "minimal_counterexample": first_nonmatch,
        "reason": "no independently stated semantic operation; numeric adjacency is not authority",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows, coord, edges, all_by_width = load_selector_model()
    encodings = {
        "P0-canonical": p0(coord),
        "P3-family-relabel": p3_reverse_within_width(coord),
        "P4-width-bijection": p4_width_bijection(coord),
    }

    formulas = [
        Formula("append-0", "selector-extend-A", "0", lambda x, w: x << 1),
        Formula("append-1", "selector-extend-D", "1", lambda x, w: (x << 1) | 1),
        Formula("xor-1-as-A", "selector-extend-A", "0", lambda x, w: x ^ 1),
        Formula("add-1-as-D", "selector-extend-D", "1", lambda x, w: x + 1),
        Formula("sub-1-as-A", "selector-extend-A", "0", lambda x, w: x - 1),
        Formula("masked-not-as-D", "selector-extend-D", "1", lambda x, w: (~x) & ((1 << (w + 1)) - 1)),
        Formula(
            "rotate-right-as-A",
            "selector-extend-A",
            "0",
            lambda x, w: (x >> 1) | ((x & 1) << w),
        ),
        Formula("zero-extend-as-D", "selector-extend-D", "1", lambda x, w: x),
    ]

    results = []

    # Representation-independent positive control: the semantic graph edge
    # exists under every relabeling. No numeric formula is claimed here.
    for law_bit, operation in (("0", "selector-extend-A"), ("1", "selector-extend-D")):
        edge_count = sum(edge.law_bit == law_bit for edge in edges)
        results.append(
            {
                "claim": operation,
                "semantic_operation": operation,
                "current_bit_formula": None,
                "P0_pass": True,
                "P3_pass": True,
                "P4_pass": True,
                "status": "semantic-law",
                "positive_witnesses": edge_count,
                "minimal_counterexample": None,
                "reason": "semantic parent/child relation is defined independently of coordinate labels",
            }
        )

    for formula in formulas:
        per_encoding = {}
        first_failure = None
        for enc_name, mapping in encodings.items():
            passed, total, failures = eval_formula(formula, mapping, edges)
            per_encoding[enc_name] = {"passed": passed, "total": total, "ok": passed == total}
            if failures and first_failure is None:
                first_failure = {"encoding": enc_name, **failures[0]}

        p0_ok = per_encoding["P0-canonical"]["ok"]
        p3_ok = per_encoding["P3-family-relabel"]["ok"]
        p4_ok = per_encoding["P4-width-bijection"]["ok"]

        if p0_ok and not (p3_ok and p4_ok):
            status = "canonical-coordinate-law"
            reason = "matches canonical selector coordinates but not semantics-preserving relabelings"
        elif p0_ok and p3_ok and p4_ok:
            status = "semantic-law"
            reason = "formula survived tested relabelings; requires independent semantic review"
        else:
            status = "accidental"
            reason = "fails the canonical executable selector witness corpus"

        results.append(
            {
                "claim": formula.name,
                "semantic_operation": formula.semantic_operation,
                "current_bit_formula": formula.name,
                "P0_pass": p0_ok,
                "P3_pass": p3_ok,
                "P4_pass": p4_ok,
                "status": status,
                "positive_witnesses": per_encoding["P0-canonical"]["passed"],
                "minimal_counterexample": first_failure,
                "reason": reason,
            }
        )

    # Explicit global arithmetic/shift claims: even numeric coincidence against
    # admitted exact-width rows is not a semantic law without an independent Φ.
    generic = [
        ("global-shift-left", lambda x, w: x << 1),
        ("global-shift-left-or-1", lambda x, w: (x << 1) | 1),
        ("global-xor-1", lambda x, w: x ^ 1),
        ("global-add-1", lambda x, w: x + 1),
        ("global-masked-not", lambda x, w: (~x) & ((1 << (w + 1)) - 1)),
    ]
    generic_results = [
        generic_coincidences(name, fn, rows, all_by_width)
        for name, fn in generic
    ]

    # Acceptance guards.
    by_claim = {row["claim"]: row for row in results}
    assert by_claim["selector-extend-A"]["status"] == "semantic-law"
    assert by_claim["selector-extend-D"]["status"] == "semantic-law"
    assert by_claim["append-0"]["status"] == "canonical-coordinate-law"
    assert by_claim["append-1"]["status"] == "canonical-coordinate-law"

    fake_claims = [
        "xor-1-as-A",
        "add-1-as-D",
        "sub-1-as-A",
        "masked-not-as-D",
        "rotate-right-as-A",
        "zero-extend-as-D",
    ]
    assert all(by_claim[name]["status"] == "accidental" for name in fake_claims)

    payload = {
        "schema": "anti-numerology/v1",
        "authority": "research-only",
        "input": "knowledge/function-status-census.json",
        "selector_edges": len(edges),
        "classification": results,
        "generic_numeric_claims": generic_results,
        "non_conclusions": [
            "canonical-coordinate-law is not representation-independent semantics",
            "numeric coincidence with an admitted coordinate is not a derivation",
            "this script allocates or promotes no function",
            "a surviving formula still requires typed semantic proof and certificate evidence",
        ],
    }
    (args.out / "classification.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    fields = [
        "claim", "semantic_operation", "current_bit_formula",
        "P0_pass", "P3_pass", "P4_pass", "status",
        "positive_witnesses", "minimal_counterexample", "reason",
    ]
    with (args.out / "classification.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in results:
            copy = dict(row)
            copy["minimal_counterexample"] = json.dumps(copy["minimal_counterexample"], sort_keys=True)
            writer.writerow(copy)

    lines = [
        "# Anti-numerology gate — #2241",
        "",
        f"Selector executable edges: {len(edges)}",
        "",
        "| claim | P0 | P3 relabel | P4 width bijection | classification |",
        "|---|---|---|---|---|",
    ]
    for row in results:
        lines.append(
            f"| {row['claim']} | {row['P0_pass']} | {row['P3_pass']} | "
            f"{row['P4_pass']} | {row['status']} |"
        )
    lines += [
        "",
        "Interpretation:",
        "- selector-extend-A/D survive because they are semantic graph laws;",
        "- append-0/1 realize those laws in the canonical coordinates but fail admissible relabeling;",
        "- arithmetic lookalikes fail the canonical witness corpus;",
        "- global shift/add/xor coincidence has no semantic authority without an independently stated operation.",
        "",
    ]
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
