#!/usr/bin/env python3
"""#2323 selector generation-certificate evidence runner."""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
from pathlib import Path

IREF_RE = re.compile(r"I\s+refs:\s*([0-9,]+)")
MODES = ("flat", "replay", "verify")


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def cachegrind(binary: Path, mode: str, reps: int) -> int:
    proc = run([
        "valgrind",
        "--tool=cachegrind",
        "--cache-sim=no",
        "--branch-sim=no",
        str(binary),
        mode,
        str(reps),
    ])
    match = IREF_RE.search(proc.stderr)
    if not match:
        raise RuntimeError(proc.stderr[-3000:])
    return int(match.group(1).replace(",", ""))


def parse_kv_line(line: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in line.split("\t")[1:]:
        key, value = field.split("=", 1)
        result[key] = value
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--binary", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--reps", type=int, default=10_000)
    args = ap.parse_args()
    if args.reps < 1:
        ap.error("--reps must be positive")

    args.out.mkdir(parents=True, exist_ok=True)

    selftest = run([str(args.binary), "selftest", "1"])
    selftest_fields = parse_kv_line(selftest.stdout.strip().splitlines()[-1])
    if int(selftest_fields["rejected"]) < 6:
        raise RuntimeError("malformed certificate suite did not execute")

    stats_proc = run([str(args.binary), "stats", "1"])
    stats_lines = [line for line in stats_proc.stdout.splitlines() if line.strip()]
    stats = list(csv.DictReader(stats_lines, delimiter="\t"))

    dump_proc = run([str(args.binary), "dump", "1"])
    certificates = []
    for line in dump_proc.stdout.splitlines():
        if not line.startswith("CERT\t"):
            continue
        row = parse_kv_line(line)
        certificates.append({
            "family": "selector.v1",
            "root_choice": int(row["root_choice"]),
            "depth": int(row["depth"]),
            "path": int(row["path"]),
            "packed_payload": int(row["payload"]),
            "packed_bit_len": int(row["bit_len"]),
            "derived_result_bits": int(row["result_bits"]),
            "derived_result_width": int(row["result_width"]),
        })

    if len(certificates) != 126:
        raise RuntimeError(f"expected 126 certificates, got {len(certificates)}")
    if sum(c["derived_result_width"] == 8 for c in certificates) != 64:
        raise RuntimeError("expected 64 D8 selector certificates")

    base = cachegrind(args.binary, "base", args.reps)
    rows = []
    ops = len(certificates) * args.reps
    for mode in MODES:
        raw = cachegrind(args.binary, mode, args.reps)
        net = raw - base
        if net < 0:
            raise RuntimeError(f"negative base-adjusted I refs for {mode}")
        rows.append({
            "mode": mode,
            "count": len(certificates),
            "reps": args.reps,
            "operations": ops,
            "base_i_refs": base,
            "raw_i_refs": raw,
            "net_i_refs": net,
            "net_i_refs_per_operation": net / ops,
        })

    with (args.out / "instruction-results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    with (args.out / "storage-results.tsv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=stats[0].keys(), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(stats)

    (args.out / "certificates.json").write_text(
        json.dumps(certificates, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    schema = {
        "schema": "selector-generation-certificate/v1",
        "authority": "research-only",
        "shared_family": "selector.v1",
        "roots": {"0": "101", "1": "110"},
        "law_bits": {"0": "compose-first-projection", "1": "compose-rest-projection"},
        "packed_layout": [
            {"field": "root_choice", "bits": 1},
            {"field": "depth", "bits": 3},
            {"field": "path", "bits": "depth"},
        ],
        "derived": {
            "result_width": "3 + depth",
            "result_bits": "root_bits || path",
        },
        "guards": [
            "bit_len in 4..9",
            "no payload bits above exact bit_len",
            "encoded depth equals bit_len-4",
            "expected exact width and bits must match when verifying",
        ],
        "non_conclusions": [
            "not a production wire format",
            "not authority for non-selector functions",
            "not proof that a materialized certificate set is smaller than raw coordinates",
        ],
    }
    (args.out / "schema.json").write_text(
        json.dumps(schema, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    mode_by_name = {row["mode"]: row for row in rows}
    report = [
        "# Selector generation certificate — #2323",
        "",
        f"Valid certificates replayed: **{len(certificates)}** (D3..D8).",
        f"Malformed/adversarial cases rejected: **{selftest_fields['rejected']}**.",
        "",
        "## Storage accounting",
        "",
        "| width | functions | flat identity bits each | self-framed cert bits each | outer-framed cert payload bits each |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in stats:
        report.append(
            f"| D{row['width']} | {int(row['count']):,} | "
            f"{row['flat_identity_bits_each']} | "
            f"{row['self_framed_cert_bits_each']} | "
            f"{row['externally_framed_cert_payload_bits_each']} |"
        )

    report += [
        "",
        "Self-framed certificates spend one extra bit per generated function versus storing only its exact coordinate.",
        "If an outer exact-width/framing layer already supplies depth, root-choice + suffix payload is two bits shorter than the coordinate.",
        "Neither comparison is a semantic-row compression claim: the real model win comes from sharing roots/laws instead of storing independent behavior per function.",
        "",
        "## Verification mechanism cost",
        "",
        "| mode | base-adjusted I refs/op |",
        "|---|---:|",
    ]
    for mode in MODES:
        report.append(
            f"| {mode} | {mode_by_name[mode]['net_i_refs_per_operation']:.3f} |"
        )

    replay = float(mode_by_name["replay"]["net_i_refs_per_operation"])
    verify = float(mode_by_name["verify"]["net_i_refs_per_operation"])
    flat = float(mode_by_name["flat"]["net_i_refs_per_operation"])
    report += [
        "",
        f"Replay/flat coordinate-read instruction ratio: **{replay/flat:.3f}x**." if flat else "",
        f"Verify/flat coordinate-read instruction ratio: **{verify/flat:.3f}x**." if flat else "",
        "",
        "The flat lane is only a coordinate-read mechanism control, not a flat semantic-registry row.",
        "No wall-clock threshold or production allocation follows from this benchmark.",
        "",
    ]
    text = "\n".join(line for line in report if line is not None) + "\n"
    (args.out / "report.md").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
