#!/usr/bin/env python3
"""Measure encoding density choices for the same validated ladder programs."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent))
from run import load_rows, exact_width_metrics  # noqa: E402


def case_metrics(row: dict) -> dict:
    base = exact_width_metrics(row["program"])
    widths = [len(token) for token in row["program"].split()]
    bit_length = base["semantic_bit_length"]
    dense = math.ceil(bit_length / 8)
    byte_aligned = sum(math.ceil(width / 8) for width in widths)
    fixed_d3 = math.ceil(len(widths) * 3 / 8)
    return {
        "case_id": row["case_id"],
        "word_count": len(widths),
        "semantic_bits": bit_length,
        "canonical_text_bytes": base["canonical_source_utf8_bytes"],
        "dense_exact_width_bytes": dense,
        "dense_padding_bits": dense * 8 - bit_length,
        "byte_aligned_word_bytes": byte_aligned,
        "byte_aligned_padding_bits": byte_aligned * 8 - bit_length,
        "fixed_d3_stream_bytes": fixed_d3,
        "fixed_d3_padding_bits": fixed_d3 * 8 - len(widths) * 3,
    }


def report(artifact: Path) -> dict:
    rows = load_rows(artifact)
    cases = [case_metrics(row) for row in sorted(rows, key=lambda item: item["case_id"])]
    keys = [
        "canonical_text_bytes",
        "dense_exact_width_bytes",
        "byte_aligned_word_bytes",
        "fixed_d3_stream_bytes",
    ]
    totals = {key: sum(case[key] for case in cases) for key in keys}
    return {
        "schema": "sens-execution-ladder-encoding-cost/v1",
        "measurement_kind": "encoding-density-model",
        "wall_clock_measured": False,
        "artifact": str(artifact),
        "validated_cases": len(cases),
        "parity_failures": 0,
        "models": {
            "canonical_text_bytes": "UTF-8 canonical source including spaces",
            "dense_exact_width_bytes": "all exact-width bits concatenated, then padded only at final byte",
            "byte_aligned_word_bytes": "each exact-width word independently padded to a whole byte",
            "fixed_d3_stream_bytes": "naive three-bit slot per word, then padded at final byte",
        },
        "aggregate": {
            **totals,
            "dense_vs_byte_aligned_savings_bytes": totals["byte_aligned_word_bytes"] - totals["dense_exact_width_bytes"],
            "dense_vs_fixed_d3_savings_bytes": totals["fixed_d3_stream_bytes"] - totals["dense_exact_width_bytes"],
            "dense_vs_text_ratio": round(totals["canonical_text_bytes"] / totals["dense_exact_width_bytes"], 6),
            "dense_padding_bits": sum(case["dense_padding_bits"] for case in cases),
            "byte_aligned_padding_bits": sum(case["byte_aligned_padding_bits"] for case in cases),
            "fixed_d3_padding_bits": sum(case["fixed_d3_padding_bits"] for case in cases),
        },
        "cases": cases,
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
    a = result["aggregate"]
    print(
        f"validated cases={result['validated_cases']} "
        f"text={a['canonical_text_bytes']} dense={a['dense_exact_width_bytes']} "
        f"byte_aligned={a['byte_aligned_word_bytes']} fixed_d3={a['fixed_d3_stream_bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
