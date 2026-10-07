#!/usr/bin/env python3
"""Measure the structural transmission cost of exact-width ladder programs.

This is deliberately not a wall-clock benchmark. It answers a narrower,
reproducible question: for the same validated canonical program, how many
semantic bits are present, how many bytes would a dense bit-packed payload
need, and how much UTF-8 whitespace/token overhead does the textual witness
add? Correctness/parity is checked before any size ratio is reported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path


HERE = Path(__file__).resolve()
CONFORMANCE_DIR = HERE.parents[1] / "execution-ladder-conformance"
sys.path.insert(0, str(CONFORMANCE_DIR))
from validate import validate_file  # noqa: E402


EXPECTED_LAYERS = {"L0", "L1"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict]:
    count = validate_file(path)
    if count == 0:
        raise ValueError("validated artifact is empty")
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_case: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_case.setdefault(row["case_id"], {})[row["producer_layer"]] = row
    if set(layer for case in by_case.values() for layer in case) != EXPECTED_LAYERS:
        raise ValueError("objective benchmark requires exactly L0 and L1 rows per case")
    for case_id, case in by_case.items():
        l0, l1 = case["L0"], case["L1"]
        if l0["parity_status"] != "ORACLE":
            raise ValueError(f"{case_id}: L0 row is not ORACLE")
        if l1["parity_status"] != "PASS":
            raise ValueError(f"{case_id}: L1 row is not PASS")
        if l1["observable_digest"] != l0["oracle_digest"]:
            raise ValueError(f"{case_id}: L1 observable diverges from L0 oracle")
        if l1["program"] != l0["program"]:
            raise ValueError(f"{case_id}: L1 program differs from L0 program")
        if l0["legacy_identity_used"] or l1["legacy_identity_used"]:
            raise ValueError(f"{case_id}: legacy identity used")
    return [case["L0"] for case in by_case.values()]


def exact_width_metrics(program: str) -> dict[str, int | float]:
    tokens = program.split()
    if not tokens or any(not token or set(token) - {"0", "1"} for token in tokens):
        raise ValueError(f"non-binary canonical-source program: {program!r}")
    bit_length = sum(len(token) for token in tokens)
    source_bytes = len(program.encode("utf-8"))
    packed_bytes = math.ceil(bit_length / 8)
    return {
        "word_count": len(tokens),
        "semantic_bit_length": bit_length,
        "dense_packed_bytes_lower_bound": packed_bytes,
        "canonical_source_utf8_bytes": source_bytes,
        "text_overhead_bytes": source_bytes - packed_bytes,
        "text_to_dense_ratio": round(source_bytes / packed_bytes, 6),
    }


def percentile(values: list[int], p: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def make_report(path: Path) -> dict:
    oracle_rows = load_rows(path)
    cases = []
    for row in sorted(oracle_rows, key=lambda item: item["case_id"]):
        metrics = exact_width_metrics(row["program"])
        cases.append(
            {
                "case_id": row["case_id"],
                "program_digest": row["program_digest"],
                "observable_digest": row["observable_digest"],
                "result_kind": row["observable"]["result_kind"],
                **metrics,
            }
        )

    bits = [case["semantic_bit_length"] for case in cases]
    packed = [case["dense_packed_bytes_lower_bound"] for case in cases]
    source = [case["canonical_source_utf8_bytes"] for case in cases]
    words = [case["word_count"] for case in cases]
    result_kinds = Counter(case["result_kind"] for case in cases)
    return {
        "schema": "sens-execution-ladder-objective/v1",
        "measurement_kind": "structural-transmission-cost",
        "wall_clock_measured": False,
        "interpretation": "dense_packed_bytes_lower_bound excludes transport framing, integrity tags, and channel coding",
        "artifact": str(path),
        "artifact_sha256": sha256_file(path),
        "validated_rows": len(cases) * 2,
        "validated_cases": len(cases),
        "parity": {"l0_oracle": len(cases), "l1_pass": len(cases), "l1_fail": 0},
        "result_kinds": dict(sorted(result_kinds.items())),
        "aggregate": {
            "semantic_bits_total": sum(bits),
            "dense_packed_bytes_lower_bound_total": sum(packed),
            "canonical_source_utf8_bytes_total": sum(source),
            "text_overhead_bytes_total": sum(source) - sum(packed),
            "text_to_dense_ratio_total": round(sum(source) / sum(packed), 6),
            "semantic_bits_min": min(bits),
            "semantic_bits_median": statistics.median(bits),
            "semantic_bits_p95": percentile(bits, 0.95),
            "semantic_bits_max": max(bits),
            "word_count_min": min(words),
            "word_count_median": statistics.median(words),
            "word_count_max": max(words),
        },
        "cases": cases,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = make_report(args.artifact)
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    aggregate = report["aggregate"]
    print(
        f"validated cases={report['validated_cases']} "
        f"parity_failures={report['parity']['l1_fail']} "
        f"semantic_bits={aggregate['semantic_bits_total']} "
        f"packed_bytes_lb={aggregate['dense_packed_bytes_lower_bound_total']} "
        f"text_bytes={aggregate['canonical_source_utf8_bytes_total']} "
        f"text_to_dense={aggregate['text_to_dense_ratio_total']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
