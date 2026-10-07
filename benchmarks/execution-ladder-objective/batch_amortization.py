#!/usr/bin/env python3
"""Measure whether fixed/per-case delivery overhead amortizes over batches."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
from delivery_cost import framed_package  # noqa: E402
from run import load_rows, exact_width_metrics  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def batch_row(rows: list[dict], artifact_sha: str) -> dict:
    text = sum(exact_width_metrics(row["program"])["canonical_source_utf8_bytes"] for row in rows)
    dense = sum(exact_width_metrics(row["program"])["dense_packed_bytes_lower_bound"] for row in rows)
    framed = len(framed_package(rows, artifact_sha))
    return {
        "case_count": len(rows),
        "canonical_text_bytes": text,
        "dense_semantic_payload_bytes": dense,
        "framed_semantic_package_bytes": framed,
        "framed_minus_text_bytes": framed - text,
        "framed_minus_dense_bytes": framed - dense,
        "text_to_framed_ratio": round(text / framed, 6),
        "dense_to_framed_ratio": round(dense / framed, 6),
    }


def report(artifact: Path) -> dict:
    rows = load_rows(artifact)
    artifact_sha = sha256_file(artifact)
    ordered = sorted(rows, key=lambda row: row["case_id"])
    requested = [1, 2, 4, 8, 16, len(ordered)]
    batch_sizes = sorted(set(size for size in requested if size <= len(ordered)))
    batches = [batch_row(ordered[:size], artifact_sha) for size in batch_sizes]
    return {
        "schema": "sens-execution-ladder-batch-amortization/v1",
        "measurement_kind": "delivery-overhead-amortization",
        "wall_clock_measured": False,
        "format_status": "research-model-not-production-protocol",
        "artifact": str(artifact),
        "artifact_sha256": artifact_sha,
        "validated_cases": len(ordered),
        "parity_failures": 0,
        "batch_policy": "deterministic prefix of case_id-sorted validated L0 cases",
        "batches": batches,
        "interpretation": "A positive framed_minus_text means this explicit evidence package is larger than the same cases as canonical text. It says nothing about a production protocol with different metadata or compression.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = report(args.artifact)
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    print(
        "batch cases=" + ",".join(str(row["case_count"]) for row in result["batches"])
        + " framed_minus_text="
        + ",".join(str(row["framed_minus_text_bytes"]) for row in result["batches"])
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
