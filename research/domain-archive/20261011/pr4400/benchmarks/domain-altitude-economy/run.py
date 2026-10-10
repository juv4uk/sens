#!/usr/bin/env python3
"""Compute #4394 Pareto frontier and residency dividend from measured rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SCHEMA = "sens-domain-altitude-economy/v1"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != SCHEMA:
        raise ValueError(f"wrong schema: {data.get('schema')!r}")
    if len(data.get("corpora", [])) < 3:
        raise ValueError("first experiment requires at least three corpora")
    if not data.get("rows"):
        raise ValueError("manifest contains no measured rows")
    known_corpora = {row["corpus_id"] for row in data["corpora"]}
    for row in data["rows"]:
        if row["corpus_id"] not in known_corpora:
            raise ValueError(f"unknown corpus {row['corpus_id']!r}")
        if row["resident_result_digest"] != row["expansion_result_digest"]:
            raise ValueError(f"{row['resident_id']}/{row['corpus_id']}: result digest mismatch; Pareto comparison is forbidden")
        if row["resident_bits"] < 1 or row["expansion_bits"] < 1:
            raise ValueError(f"{row['resident_id']}: invalid semantic bit measure")
        if row["resident_max_width"] < 1 or row["expansion_max_width"] < 1:
            raise ValueError(f"{row['resident_id']}: invalid altitude measure")
    return data

def dominates(a: dict, b: dict) -> bool:
    return (a["altitude"] <= b["altitude"] and a["bits"] <= b["bits"] and
            (a["altitude"] < b["altitude"] or a["bits"] < b["bits"]))

def frontier(rows: list[dict]) -> list[dict]:
    out = []
    for candidate in rows:
        if not any(dominates(other, candidate) for other in rows if other is not candidate):
            out.append(candidate)
    return out

def summarize(data: dict) -> dict:
    measured = []
    by_resident = defaultdict(lambda: {"rows": 0, "dividend_bits": 0})
    for row in data["rows"]:
        item = {
            "resident_id": row["resident_id"],
            "corpus_id": row["corpus_id"],
            "altitude": row["resident_max_width"],
            "bits": row["resident_bits"],
            "expansion_altitude": row["expansion_max_width"],
            "expansion_bits": row["expansion_bits"],
            "dividend_bits": row["expansion_bits"] - row["resident_bits"],
            "result_digest": row["resident_result_digest"],
        }
        measured.append(item)
        bucket = by_resident[row["resident_id"]]
        bucket["rows"] += 1
        bucket["dividend_bits"] += item["dividend_bits"]
    return {
        "schema": SCHEMA,
        "rows": len(measured),
        "frontier_rows": len(frontier(measured)),
        "frontier": sorted(frontier(measured), key=lambda r: (r["corpus_id"], r["bits"], r["altitude"], r["resident_id"])),
        "residency_dividend": [
            {"resident_id": rid, **values} for rid, values in sorted(by_resident.items())
        ],
        "dynamic_measurements": [
            {"resident_id": row["resident_id"], "corpus_id": row["corpus_id"], **row["cachegrind"]}
            for row in data["rows"] if row.get("cachegrind") is not None
        ],
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    data = load_manifest(args.manifest)
    report = summarize(data)
    report["manifest_sha256"] = sha256_file(args.manifest)
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
