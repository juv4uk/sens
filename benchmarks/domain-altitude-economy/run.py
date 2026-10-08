#!/usr/bin/env python3
"""Pareto benchmark for SENS domain altitude × exact semantic bits.

The harness compares only observationally equivalent program variants. It
does not choose semantics, re-ratify residents, or collapse unlike costs into
one scalar score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


REQUIRED = {
    "case_id",
    "variant_id",
    "program",
    "observable_digest",
    "result_kind",
    "role",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_width_metrics(program: str) -> dict[str, int]:
    tokens = program.split()
    if not tokens:
        raise ValueError("empty canonical program")
    for token in tokens:
        if not token or set(token) - {"0", "1"}:
            raise ValueError(f"non-binary canonical token: {token!r}")
    widths = [len(token) for token in tokens]
    bits = sum(widths)
    return {
        "word_count": len(tokens),
        "semantic_bits": bits,
        "semantic_altitude": max(widths),
        "dense_packed_bytes_lower_bound": math.ceil(bits / 8),
    }


def load_rows(path: Path) -> list[dict]:
    rows = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        missing = REQUIRED - row.keys()
        if missing:
            raise ValueError(f"{path}:{lineno}: missing fields {sorted(missing)}")
        if row["role"] not in {"resident", "expanded", "alternate"}:
            raise ValueError(f"{path}:{lineno}: unsupported role {row['role']!r}")
        if row["role"] in {"resident", "expanded"} and not row.get("resident_id"):
            raise ValueError(f"{path}:{lineno}: role {row['role']} requires resident_id")
        rows.append(row)
    if not rows:
        raise ValueError("input artifact is empty")
    return rows


def dominates(a: dict, b: dict) -> bool:
    return (
        a["semantic_altitude"] <= b["semantic_altitude"]
        and a["semantic_bits"] <= b["semantic_bits"]
        and (
            a["semantic_altitude"] < b["semantic_altitude"]
            or a["semantic_bits"] < b["semantic_bits"]
        )
    )


def analyze(path: Path) -> dict:
    raw_rows = load_rows(path)
    by_case: dict[str, list[dict]] = defaultdict(list)
    for raw in raw_rows:
        enriched = {**raw, **exact_width_metrics(raw["program"])}
        by_case[raw["case_id"]].append(enriched)

    cases = []
    dividend_rows = []
    for case_id, variants in sorted(by_case.items()):
        digests = {row["observable_digest"] for row in variants}
        result_kinds = {row["result_kind"] for row in variants}
        if len(digests) != 1 or len(result_kinds) != 1:
            raise ValueError(
                f"{case_id}: equivalence gate failed "
                f"(digests={sorted(digests)}, result_kinds={sorted(result_kinds)})"
            )

        ids = [row["variant_id"] for row in variants]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{case_id}: duplicate variant_id")

        edges = []
        dominated = set()
        for a in variants:
            for b in variants:
                if a is b:
                    continue
                if dominates(a, b):
                    edges.append([a["variant_id"], b["variant_id"]])
                    dominated.add(b["variant_id"])
        frontier = sorted(row["variant_id"] for row in variants if row["variant_id"] not in dominated)

        by_resident: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
        for row in variants:
            rid = row.get("resident_id")
            if rid and row["role"] in {"resident", "expanded"}:
                by_resident[rid][row["role"]].append(row)

        case_dividends = []
        for resident_id, roles in sorted(by_resident.items()):
            resident_rows = roles.get("resident", [])
            expanded_rows = roles.get("expanded", [])
            if len(resident_rows) != 1 or len(expanded_rows) != 1:
                raise ValueError(
                    f"{case_id}/{resident_id}: dividend requires exactly one "
                    "resident and one expanded variant"
                )
            resident = resident_rows[0]
            expanded = expanded_rows[0]
            record = {
                "case_id": case_id,
                "resident_id": resident_id,
                "resident_variant_id": resident["variant_id"],
                "expanded_variant_id": expanded["variant_id"],
                "resident_semantic_bits": resident["semantic_bits"],
                "expanded_semantic_bits": expanded["semantic_bits"],
                "gross_dividend_bits": expanded["semantic_bits"] - resident["semantic_bits"],
                "resident_altitude": resident["semantic_altitude"],
                "expanded_altitude": expanded["semantic_altitude"],
                "altitude_delta_expanded_minus_resident": (
                    expanded["semantic_altitude"] - resident["semantic_altitude"]
                ),
            }
            case_dividends.append(record)
            dividend_rows.append(record)

        cases.append(
            {
                "case_id": case_id,
                "observable_digest": next(iter(digests)),
                "result_kind": next(iter(result_kinds)),
                "variants": sorted(variants, key=lambda row: row["variant_id"]),
                "pareto_frontier": frontier,
                "dominance_edges": sorted(edges),
                "residency_dividends": case_dividends,
            }
        )

    aggregate: dict[str, dict] = {}
    for row in dividend_rows:
        rid = row["resident_id"]
        entry = aggregate.setdefault(
            rid,
            {
                "verified_occurrences": 0,
                "gross_dividend_bits": 0,
                "positive_cases": 0,
                "zero_cases": 0,
                "negative_cases": 0,
            },
        )
        entry["verified_occurrences"] += 1
        entry["gross_dividend_bits"] += row["gross_dividend_bits"]
        if row["gross_dividend_bits"] > 0:
            entry["positive_cases"] += 1
        elif row["gross_dividend_bits"] == 0:
            entry["zero_cases"] += 1
        else:
            entry["negative_cases"] += 1

    return {
        "schema": "sens-domain-altitude-economy/v1",
        "measurement_kind": "pareto-domain-altitude-vs-exact-bits",
        "semantic_authority_changed": False,
        "wall_clock_measured": False,
        "artifact": str(path),
        "artifact_sha256": sha256_file(path),
        "validated_cases": len(cases),
        "axes": {
            "semantic_altitude": "maximum exact domain width used by the canonical program",
            "semantic_bits": "sum of exact widths of all canonical program words",
        },
        "equivalence_gate": "same case + observable_digest + result_kind",
        "cases": cases,
        "resident_economics": aggregate,
        "interpretation": {
            "gross_dividend_bits": (
                "expanded semantic bits minus resident semantic bits; positive means "
                "the resident saved canonical payload bits on verified equivalent uses"
            ),
            "non_scalar_rule": (
                "proof/certificate/mechanism/runtime costs remain separate Pareto coordinates "
                "and are not subtracted into this bit dividend"
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    result = analyze(args.artifact)
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    total_dividend = sum(row["gross_dividend_bits"] for row in result["resident_economics"].values())
    print(
        f"validated_cases={result['validated_cases']} "
        f"resident_ids={len(result['resident_economics'])} "
        f"gross_dividend_bits_total={total_dividend}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
