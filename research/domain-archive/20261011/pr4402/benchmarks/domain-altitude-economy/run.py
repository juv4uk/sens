#!/usr/bin/env python3
"""Pareto consumer for SENS domain-altitude economy research (#4397/#4398).

This benchmark is intentionally a *consumer* of admitted semantic evidence.
It never infers program equivalence, domain meaning, or residency from names.

Input is JSONL. Each row must contain:
  case_id              equivalence group identifier
  variant_id           representation/program variant
  observable_digest    oracle/evaluator observable digest
  semantic_widths      exact domain widths used by semantic residents
  exact_bits           exact dense bit cost from an admitted accounting path

Optional:
  i_refs                dynamic mechanism evidence; reported but never scored
  residency_pair_id     explicit resident/expanded comparison id
  representation_role  "resident" or "expanded"

Rows are Pareto-compared only inside one case_id and only after every row in
that case has the same observable_digest.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "sens-domain-altitude-economy/v1"
ROLES = {"resident", "expanded"}


@dataclass(frozen=True)
class Point:
    case_id: str
    variant_id: str
    observable_digest: str
    semantic_widths: tuple[int, ...]
    exact_bits: int
    i_refs: int | None = None
    residency_pair_id: str | None = None
    representation_role: str | None = None

    @property
    def altitude(self) -> int:
        return max(self.semantic_widths)


def _require_str(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def parse_row(row: dict[str, Any], line_no: int) -> Point:
    case_id = _require_str(row, "case_id")
    variant_id = _require_str(row, "variant_id")
    observable_digest = _require_str(row, "observable_digest")

    widths = row.get("semantic_widths")
    if not isinstance(widths, list) or not widths:
        raise ValueError(f"line {line_no}: semantic_widths must be a non-empty list")
    if any(not isinstance(width, int) or isinstance(width, bool) or width <= 0 for width in widths):
        raise ValueError(f"line {line_no}: semantic_widths must contain positive integers")

    exact_bits = row.get("exact_bits")
    if not isinstance(exact_bits, int) or isinstance(exact_bits, bool) or exact_bits < 0:
        raise ValueError(f"line {line_no}: exact_bits must be a non-negative integer")

    i_refs = row.get("i_refs")
    if i_refs is not None and (
        not isinstance(i_refs, int) or isinstance(i_refs, bool) or i_refs < 0
    ):
        raise ValueError(f"line {line_no}: i_refs must be a non-negative integer or null")

    pair_id = row.get("residency_pair_id")
    role = row.get("representation_role")
    if pair_id is not None:
        if not isinstance(pair_id, str) or not pair_id:
            raise ValueError(f"line {line_no}: residency_pair_id must be a non-empty string")
        if role not in ROLES:
            raise ValueError(
                f"line {line_no}: representation_role must be resident or expanded"
            )
    elif role is not None:
        raise ValueError(
            f"line {line_no}: representation_role requires residency_pair_id"
        )

    return Point(
        case_id=case_id,
        variant_id=variant_id,
        observable_digest=observable_digest,
        semantic_widths=tuple(widths),
        exact_bits=exact_bits,
        i_refs=i_refs,
        residency_pair_id=pair_id,
        representation_role=role,
    )


def load_points(path: Path) -> list[Point]:
    points: list[Point] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        raw = json.loads(line)
        if not isinstance(raw, dict):
            raise ValueError(f"line {line_no}: JSON row must be an object")
        points.append(parse_row(raw, line_no))
    if not points:
        raise ValueError("artifact is empty")
    return points


def dominates(left: Point, right: Point) -> bool:
    """True iff left Pareto-dominates right on altitude × exact bits."""
    no_worse = left.altitude <= right.altitude and left.exact_bits <= right.exact_bits
    strictly_better = left.altitude < right.altitude or left.exact_bits < right.exact_bits
    return no_worse and strictly_better


def validate_digest_groups(points: list[Point]) -> None:
    by_case: dict[str, set[str]] = defaultdict(set)
    for point in points:
        by_case[point.case_id].add(point.observable_digest)
    bad = {case: digests for case, digests in by_case.items() if len(digests) != 1}
    if bad:
        detail = "; ".join(
            f"{case}={sorted(digests)}" for case, digests in sorted(bad.items())
        )
        raise ValueError(f"observable digest mismatch inside equivalence group: {detail}")


def pareto_cases(points: list[Point]) -> list[dict[str, Any]]:
    validate_digest_groups(points)
    by_case: dict[str, list[Point]] = defaultdict(list)
    for point in points:
        by_case[point.case_id].append(point)

    cases: list[dict[str, Any]] = []
    for case_id in sorted(by_case):
        group = sorted(by_case[case_id], key=lambda p: p.variant_id)
        rows = []
        for point in group:
            dominated_by = sorted(
                other.variant_id
                for other in group
                if other.variant_id != point.variant_id and dominates(other, point)
            )
            dominates_ids = sorted(
                other.variant_id
                for other in group
                if other.variant_id != point.variant_id and dominates(point, other)
            )
            rows.append(
                {
                    "variant_id": point.variant_id,
                    "observable_digest": point.observable_digest,
                    "altitude_max_domain_width": point.altitude,
                    "exact_bits": point.exact_bits,
                    "pareto_front": not dominated_by,
                    "dominated_by": dominated_by,
                    "dominates": dominates_ids,
                    "i_refs": point.i_refs,
                    "residency_pair_id": point.residency_pair_id,
                    "representation_role": point.representation_role,
                }
            )
        cases.append(
            {
                "case_id": case_id,
                "observable_digest": group[0].observable_digest,
                "frontier": [row["variant_id"] for row in rows if row["pareto_front"]],
                "variants": rows,
            }
        )
    return cases


def residency_dividends(points: list[Point]) -> list[dict[str, Any]]:
    by_pair: dict[str, list[Point]] = defaultdict(list)
    for point in points:
        if point.residency_pair_id is not None:
            by_pair[point.residency_pair_id].append(point)

    reports: list[dict[str, Any]] = []
    for pair_id in sorted(by_pair):
        group = by_pair[pair_id]
        resident = [p for p in group if p.representation_role == "resident"]
        expanded = [p for p in group if p.representation_role == "expanded"]
        if len(resident) != 1 or len(expanded) != 1:
            raise ValueError(
                f"{pair_id}: residency pair requires exactly one resident and one expanded row"
            )
        r = resident[0]
        e = expanded[0]
        if r.case_id != e.case_id or r.observable_digest != e.observable_digest:
            raise ValueError(
                f"{pair_id}: residency pair must share case_id and observable_digest"
            )
        reports.append(
            {
                "residency_pair_id": pair_id,
                "case_id": r.case_id,
                "observable_digest": r.observable_digest,
                "resident_variant_id": r.variant_id,
                "expanded_variant_id": e.variant_id,
                "resident_exact_bits": r.exact_bits,
                "expanded_exact_bits": e.exact_bits,
                "bit_dividend": e.exact_bits - r.exact_bits,
                "resident_altitude": r.altitude,
                "expanded_altitude": e.altitude,
                "resident_i_refs": r.i_refs,
                "expanded_i_refs": e.i_refs,
            }
        )
    return reports


def build_report(points: list[Point]) -> dict[str, Any]:
    cases = pareto_cases(points)
    dividends = residency_dividends(points)
    return {
        "schema": SCHEMA,
        "measurement_kind": "pareto-domain-altitude-x-exact-bits",
        "semantic_authority": False,
        "scalar_optimum": False,
        "equivalence_rule": "identical observable_digest inside each case_id",
        "pareto_axes": ["altitude_max_domain_width", "exact_bits"],
        "dynamic_evidence_role": "i_refs are reported separately and never folded into Pareto dominance",
        "case_count": len(cases),
        "variant_count": len(points),
        "residency_pair_count": len(dividends),
        "cases": cases,
        "residency_dividends": dividends,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = build_report(load_points(args.artifact))
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    print(
        f"cases={report['case_count']} variants={report['variant_count']} "
        f"residency_pairs={report['residency_pair_count']} scalar_optimum=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
