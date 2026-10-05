#!/usr/bin/env python3
"""Валідація machine-readable STORE -> AIR -> LOAD evidence."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

SCHEMA = "sens-store-air-load/v1"
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")
REPRESENTATIONS = {"canonical-packed", "text-surface"}
CARRIER_MODES = {"exact-bitstream", "byte-container", "text-bytes"}
LOAD_FIELDS = (
    "decode_i_refs",
    "parse_i_refs",
    "lower_i_refs",
    "ready_i_refs",
    "cold_total_i_refs",
    "warm_incremental_i_refs",
)


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def validate_row(row: dict[str, object], line_no: int) -> None:
    if row.get("schema") != SCHEMA:
        raise ValueError(f"line {line_no}: wrong schema")
    if row.get("representation") not in REPRESENTATIONS:
        raise ValueError(f"line {line_no}: invalid representation")
    if row.get("carrier_mode") not in CARRIER_MODES:
        raise ValueError(f"line {line_no}: invalid carrier_mode")
    if not SHA40_RE.fullmatch(str(row.get("git_sha", ""))):
        raise ValueError(f"line {line_no}: invalid git_sha")
    if not SHA64_RE.fullmatch(str(row.get("semantic_identity_digest", ""))):
        raise ValueError(f"line {line_no}: invalid semantic_identity_digest")

    fixture_id = str(row["fixture_id"])
    semantic_word_count = int(row["semantic_word_count"])
    expected_semantic_bits = int(row["expected_semantic_bits"])
    semantic_bits = int(row["semantic_payload_bits"])
    framing_bits = int(row["framing_bits"])
    tail_bits = int(row["tail_unused_bits"])
    carrier_bits = int(row["carrier_payload_bits"])
    storage_bits = int(row["storage_container_bits"])
    total_wire_bits = int(row["total_wire_bits"])
    physical_bytes = int(row["physical_container_bytes"])
    bitrate = float(row["bitrate_bps"])
    airtime = float(row["ideal_airtime_seconds"])

    if semantic_word_count <= 0:
        raise ValueError(f"line {line_no}: semantic_word_count must be positive")
    if expected_semantic_bits <= 0 or semantic_bits <= 0 or carrier_bits <= 0 or total_wire_bits <= 0:
        raise ValueError(f"line {line_no}: bit counts must be positive")
    if semantic_bits != expected_semantic_bits:
        raise ValueError(
            f"line {line_no} fixture={fixture_id}: "
            f"expected_semantic_bits={expected_semantic_bits} "
            f"actual_semantic_bits={semantic_bits} "
            f"artifact_bytes={physical_bytes}"
        )
    if framing_bits < 0 or not 0 <= tail_bits <= 7:
        raise ValueError(f"line {line_no}: invalid framing/tail bits")
    if physical_bytes <= 0 or storage_bits != physical_bytes * 8:
        raise ValueError(f"line {line_no}: storage bits must equal physical bytes * 8")
    if total_wire_bits != carrier_bits + framing_bits:
        raise ValueError(f"line {line_no}: total_wire_bits must be carrier + framing")
    if bitrate <= 0 or not close(airtime, total_wire_bits / bitrate):
        raise ValueError(f"line {line_no}: invalid airtime derivation")

    representation = row["representation"]
    carrier_mode = row["carrier_mode"]
    if representation == "canonical-packed":
        if carrier_mode not in {"exact-bitstream", "byte-container"}:
            raise ValueError(f"line {line_no}: canonical row has invalid carrier mode")
        if storage_bits - semantic_bits != tail_bits:
            raise ValueError(
                f"line {line_no} fixture={fixture_id}: canonical packing mismatch "
                f"expected_semantic_bits={expected_semantic_bits} "
                f"actual_semantic_bits={semantic_bits} "
                f"artifact_bytes={physical_bytes} storage_bits={storage_bits} "
                f"tail_unused_bits={tail_bits}"
            )
        if carrier_mode == "exact-bitstream" and carrier_bits != semantic_bits:
            raise ValueError(f"line {line_no}: exact-bitstream must carry semantic bits exactly")
        if carrier_mode == "byte-container" and carrier_bits != storage_bits:
            raise ValueError(f"line {line_no}: byte-container must carry storage bits")
    else:
        text_bytes = row.get("text_surface_bytes")
        if not isinstance(text_bytes, int) or text_bytes <= 0:
            raise ValueError(f"line {line_no}: text row needs text_surface_bytes")
        if carrier_mode != "text-bytes":
            raise ValueError(f"line {line_no}: text row must use text-bytes carrier")
        if physical_bytes != text_bytes or carrier_bits != text_bytes * 8:
            raise ValueError(f"line {line_no}: text byte accounting mismatch")
        if tail_bits != 0:
            raise ValueError(f"line {line_no}: text row cannot claim canonical tail bits")

    for field in LOAD_FIELDS:
        value = row.get(field)
        if value is not None and (not isinstance(value, int) or value < 0):
            raise ValueError(f"line {line_no}: invalid {field}")

    load_values = {field: row.get(field) for field in LOAD_FIELDS}
    if any(value is not None for value in load_values.values()):
        for field in (
            "lower_i_refs",
            "ready_i_refs",
            "cold_total_i_refs",
            "warm_incremental_i_refs",
        ):
            if load_values[field] is None:
                raise ValueError(
                    f"line {line_no} fixture={fixture_id}: partial LOAD row missing {field}"
                )

        decode = load_values["decode_i_refs"]
        parse = load_values["parse_i_refs"]
        if representation == "canonical-packed":
            if decode is None or parse is not None:
                raise ValueError(
                    f"line {line_no} fixture={fixture_id}: "
                    "canonical LOAD row must have decode_i_refs and null parse_i_refs"
                )
        else:
            if parse is None or decode is not None:
                raise ValueError(
                    f"line {line_no} fixture={fixture_id}: "
                    "text LOAD row must have parse_i_refs and null decode_i_refs"
                )

        if int(load_values["cold_total_i_refs"]) < int(load_values["ready_i_refs"]):
            raise ValueError(
                f"line {line_no} fixture={fixture_id}: cold total is below ready cost"
            )


def validate_file(path: Path) -> tuple[int, int]:
    rows: list[dict[str, object]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        row = json.loads(raw)
        if not isinstance(row, dict):
            raise ValueError(f"line {line_no}: row must be an object")
        validate_row(row, line_no)
        rows.append(row)

    if not rows:
        raise ValueError("evidence file is empty")

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["fixture_id"])].append(row)

    for fixture_id, group in grouped.items():
        by_rep = {str(row["representation"]): row for row in group}
        if len(by_rep) != len(group):
            raise ValueError(f"{fixture_id}: duplicate representation")
        canonical = by_rep.get("canonical-packed")
        if canonical is None:
            raise ValueError(f"{fixture_id}: missing canonical-packed row")

        text = by_rep.get("text-surface")
        if str(canonical["fixture_kind"]) == "paired-program":
            if text is None:
                raise ValueError(f"{fixture_id}: paired fixture missing text row")
            for field in (
                "git_sha",
                "contract_version",
                "semantic_identity_digest",
                "semantic_word_count",
                "expected_semantic_bits",
                "semantic_payload_bits",
                "text_surface_bytes",
                "packed_vs_text_ratio",
            ):
                if canonical[field] != text[field]:
                    raise ValueError(f"{fixture_id}: paired rows mismatch {field}")

            text_bytes = int(text["text_surface_bytes"])
            packed_bytes = int(canonical["physical_container_bytes"])
            expected_ratio = text_bytes / packed_bytes
            if not close(float(canonical["packed_vs_text_ratio"]), expected_ratio):
                raise ValueError(f"{fixture_id}: packed/text ratio is not derived")
        elif text is not None:
            raise ValueError(f"{fixture_id}: mechanical fixture must not claim text equivalence")

    return len(rows), len(grouped)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", type=Path, nargs="+")
    args = parser.parse_args()

    for path in args.jsonl:
        rows, fixtures = validate_file(path)
        print(f"validated {rows} rows / {fixtures} fixtures: {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
