#!/usr/bin/env python3
"""Validate actual Native Zero T5 timings without manufacturing green ratios.

No performance threshold: slower T5 is a valid measured result, not a CI failure.
This gate rejects missing or fabricated-shaped evidence, incorrect program sizes,
and malformed samples; correctness is checked in Rust before timing.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import statistics

SCHEMA = "sens-native-zero-t5/v1"
CASES = {"d3-quote-empty", "d1-yes", "d3-atom-empty"}
PHASES = {"warm-bare-session", "fresh-bare-session"}


def checked_positive(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{field}: not numeric")
    out = float(value)
    if not math.isfinite(out) or out <= 0:
        raise ValueError(f"{field}: non-finite or non-positive")
    return out


def validate(rows: list[dict]) -> tuple[int, list[dict]]:
    if len(rows) != len(CASES) * len(PHASES):
        raise ValueError(f"expected six measured rows, got {len(rows)}")
    pairs = {(row.get("case"), row.get("phase")) for row in rows}
    if pairs != {(case, phase) for case in CASES for phase in PHASES}:
        raise ValueError("missing/duplicate case-phase evidence")
    sample_counts = {row.get("samples") for row in rows}
    if len(sample_counts) != 1:
        raise ValueError("unequal sample counts across cases")
    samples = sample_counts.pop()
    if not isinstance(samples, int) or not (3 <= samples <= 31) or samples % 2 != 1:
        raise ValueError("invalid paired sample count")

    for row in rows:
        case, phase = row["case"], row["phase"]
        if row.get("schema") != SCHEMA or row.get("oracle") != "same-bare-exact-domain-result":
            raise ValueError(f"{case}/{phase}: missing independent result preflight")
        iterations = row.get("iterations")
        if not isinstance(iterations, int) or not (16 <= iterations <= 4096):
            raise ValueError(f"{case}/{phase}: invalid iteration count")
        if not all(isinstance(row.get(field), int) and row[field] > 0 for field in (
            "physical_bytes", "visible_bytes", "word_count", "semantic_bits",
        )):
            raise ValueError(f"{case}/{phase}: source size accounting missing")
        if case == "d3-quote-empty":
            if (row["physical_bytes"], row["visible_bytes"], row["word_count"], row["semantic_bits"]) != (4, 18, 5, 12):
                raise ValueError("canonical committed D3 QUOTE size/width changed")
        if case == "d1-yes" and (
            row["physical_bytes"], row["word_count"], row["semantic_bits"]
        ) != (1, 1, 1):
            raise ValueError("D1 YES is not the exact one-bit carrier")
        if case == "d3-atom-empty" and (
            row["word_count"], row["semantic_bits"]
        ) != (5, 12):
            raise ValueError("D3 ATOM program has lost exact widths")
        for field in ("physical_median_ns", "visible_median_ns",
                      "ratio_visible_over_physical", "decode_d2_median_ns",
                      "prepared_eval_median_ns"):
            checked_positive(row.get(field), f"{case}/{phase}/{field}")
        for field, median_field in [
            ("physical_samples_ns", "physical_median_ns"),
            ("visible_samples_ns", "visible_median_ns"),
        ]:
            values = row.get(field)
            if not isinstance(values, list) or len(values) != samples:
                raise ValueError(f"{case}/{phase}: missing raw {field}")
            checked = [checked_positive(value, field) for value in values]
            if not math.isclose(statistics.median(checked), row[median_field], abs_tol=0.02):
                raise ValueError(f"{case}/{phase}: published median disagrees with raw samples")
        ratio = row["visible_median_ns"] / row["physical_median_ns"]
        if not math.isclose(ratio, row["ratio_visible_over_physical"], rel_tol=0.001):
            raise ValueError(f"{case}/{phase}: published ratio disagrees with medians")
    return samples, rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines() if line.strip()]
    samples, validated = validate(rows)

    lines = [
        "# SENS Native Zero v1 — measured physical T5",
        "",
        f"GitHub-hosted CPU; {samples} paired alternating-order samples per phase.",
        "Raw independent D1/D3 oracle parity is checked **before** any timing.",
        "All sessions are bare: no Core4, no human Lisp names, no external width schedule.",
        "",
        "| Program | Session | Physical T5 ns/program | Visible exact D2 ns/program | Visible/T5 | Physical bytes | Visible bytes |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in validated:
        lines.append(
            f"| {row['case']} | {row['phase']} | {row['physical_median_ns']:.1f} "
            f"| {row['visible_median_ns']:.1f} | {row['ratio_visible_over_physical']:.2f}× "
            f"| {row['physical_bytes']} | {row['visible_bytes']} |"
        )
    lines.extend([
        "",
        "Ratios above 1 mean T5 was faster for this observed batch; below 1 mean slower.",
        "**No speedup, memory or native-code claim is inferred from the representation alone.**",
        "Physical path includes T5 decoding, strict D2 grammar, lowering, and execution.",
        "Visible path includes exact-width source parsing, lowering, and the same executor.",
        "Decode-only and prepared-execution medians are included in JSONL for diagnostic context,",
        "not subtracted from end-to-end medians or used as independent speedups.",
        "All samples are warm-page-cache, same-process measurements on a hosted CPU,",
        "not x86 machine-code compilation, process startup, disk I/O, GPU, or FPGA results.",
        "",
    ])
    summary = "\n".join(lines)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(summary, encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
