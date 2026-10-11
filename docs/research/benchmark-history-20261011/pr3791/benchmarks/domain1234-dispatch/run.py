#!/usr/bin/env python3
"""#2209 - compare favorable u8 flat-slot dispatch with ratified D3/D4 prefix dispatch."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import platform
import re
import statistics
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRATEGIES = ("flat", "prefix", "direct")
CANDIDATE = {
    "flat": "u8-flat-ready",
    "prefix": "d3d4-prefix-ready",
}


def candidate_name(strategy: str, workload: str) -> str:
    if strategy != "direct":
        return CANDIDATE[strategy]
    return "direct-static" if workload.startswith("repeat-") else "direct-dynamic"
WORKLOADS = ("repeat-d3", "random-d3", "repeat-d4", "random-d4", "mixed")
IREF_RE = re.compile(r"I\s+refs:\s*([0-9,]+)")
BRANCH_RE = re.compile(r"Branches:\s*([0-9,]+)")


def sh(cmd, **kwargs):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs)


def build(tmp: Path):
    plain = tmp / "d34_dispatch"
    counted = tmp / "d34_dispatch_count"
    sh(["gcc", "-O2", "-Wall", "-Wextra", "-o", str(plain), str(HERE / "d34_dispatch.c")])
    sh(["gcc", "-O2", "-Wall", "-Wextra", "-DCOUNT", "-o", str(counted), str(HERE / "d34_dispatch.c")])
    return plain, counted


def parity(binary: Path):
    rows = []
    for strategy in STRATEGIES:
        line = sh([str(binary), strategy, "mixed", "6", "check"]).stdout.strip()
        rows.append(line)
        if not line.endswith("mismatches=0"):
            raise SystemExit(f"PARITY FAILURE: {line}")
    return rows


def cachegrind(binary: Path, strategy: str, workload: str, calls: int, mode: str):
    with tempfile.NamedTemporaryFile("r", suffix=".vg") as log:
        subprocess.run(
            [
                "valgrind", "--tool=cachegrind", "--cache-sim=no", "--branch-sim=yes",
                "--cachegrind-out-file=/dev/null", f"--log-file={log.name}",
                str(binary), strategy, workload, str(calls), mode,
            ],
            check=True, capture_output=True, text=True,
        )
        text = Path(log.name).read_text(encoding="utf-8")
    im = IREF_RE.search(text)
    bm = BRANCH_RE.search(text)
    if not im or not bm:
        raise SystemExit(f"missing Cachegrind counters for {strategy}/{workload}/{mode}")
    return int(im.group(1).replace(",", "")), int(bm.group(1).replace(",", ""))


def logical_counters(binary: Path, strategy: str, workload: str, calls: int):
    out = sh([str(binary), strategy, workload, str(calls), "count"]).stdout.splitlines()
    line = next(line for line in out if line.startswith("counters\t"))
    fields = {}
    for item in line.split("\t")[3:]:
        key, value = item.split("=", 1)
        fields[key] = int(value)
    return fields


def first_line(cmd):
    try:
        proc = sh(cmd)
        return (proc.stdout or proc.stderr).splitlines()[0]
    except Exception:
        return "unknown"


def cpu_name():
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--calls", type=int, default=200_000)
    ap.add_argument("--reps", type=int, default=3)
    args = ap.parse_args()
    if args.calls <= 0 or args.reps <= 0:
        raise SystemExit("calls/reps must be positive")

    with tempfile.TemporaryDirectory() as td:
        plain, counted = build(Path(td))
        parity_rows = parity(plain)
        binary_sha = hashlib.sha256(plain.read_bytes()).hexdigest()
        git_sha = first_line(["git", "-C", str(HERE), "rev-parse", "HEAD"])
        cpu = cpu_name()
        valgrind_version = first_line(["valgrind", "--version"])
        gcc_version = first_line(["gcc", "--version"])

        raw = []
        logical = {}
        for workload in WORKLOADS:
            for strategy in STRATEGIES:
                logical[(strategy, workload)] = logical_counters(
                    counted, strategy, workload, args.calls
                )
                for rep in range(1, args.reps + 1):
                    setup_i, setup_b = cachegrind(plain, strategy, workload, args.calls, "setup")
                    full_i, full_b = cachegrind(plain, strategy, workload, args.calls, "full")
                    counters = logical[(strategy, workload)]
                    depth = "0" if workload.endswith("d3") else ("1" if workload.endswith("d4") else "mixed")
                    raw.append({
                        "case_id": f"{workload}/{candidate_name(strategy, workload)}",
                        "candidate": candidate_name(strategy, workload),
                        "family": "selector-d34",
                        "semantic_depth": depth,
                        "mode": "execute-delta",
                        "rep": rep,
                        "i_refs": full_i - setup_i,
                        "tree_steps": counters["steps"],
                        "root_selections": counters["root_selections"],
                        "bits_consumed": counters["bits"],
                        "generator_apps": counters["gens"],
                        "registry_lookups": counters["lookups"],
                        "residue_lookups": 0,
                        "cache_hits": 0,
                        "cache_misses": 0,
                        "allocations": 0,
                        "allocated_bytes": 0,
                        "object_bytes": counters["prepared_bytes"],
                        "wire_bits": "",
                        "compiler_phase": "",
                        "machine_insts": "",
                        "code_bytes": "",
                        "loads": "",
                        "stores": "",
                        "branches": full_b - setup_b,
                        "calls": args.calls,
                        "spills": "",
                        "corpus_sha": "builtin-selector-d34-v1",
                        "binary_sha": binary_sha,
                        "git_sha": git_sha,
                        "guix_channels_sha": "",
                        "cpu": cpu,
                        "valgrind_version": valgrind_version,
                        "workload": workload,
                        "setup_i_refs": setup_i,
                        "setup_branches": setup_b,
                    })

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        fields = list(raw[0])
        with out.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
            writer.writeheader()
            writer.writerows(raw)

        lines = [
            "# #2209 D3/D4 dispatch benchmark",
            "",
            f"- calls/workload: {args.calls:,}",
            f"- repetitions: {args.reps}",
            f"- compiler: {gcc_version}",
            f"- valgrind: {valgrind_version}",
            f"- cpu: {cpu}",
            f"- git: {git_sha}",
            "",
            "Parity first:",
            "~~~text",
            *parity_rows,
            "~~~",
            "",
            "| workload | candidate | I refs/call | branches/call | lookups/call | bits/call | gens/call | prepared bytes |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]

        for workload in WORKLOADS:
            for strategy in STRATEGIES:
                rows = [
                    row for row in raw
                    if row["workload"] == workload and row["candidate"] == candidate_name(strategy, workload)
                ]
                med_i = statistics.median(row["i_refs"] for row in rows) / args.calls
                med_b = statistics.median(row["branches"] for row in rows) / args.calls
                counters = logical[(strategy, workload)]
                lines.append(
                    f"| {workload} | {candidate_name(strategy, workload)} | {med_i:.3f} | {med_b:.3f} | "
                    f"{counters['lookups']/args.calls:.3f} | {counters['bits']/args.calls:.3f} | "
                    f"{counters['gens']/args.calls:.3f} | {counters['prepared_bytes']} |"
                )

        lines += [
            "",
            "Interpretation boundary:",
            "- u8-flat-ready is a favorable 256-slot mechanical baseline, not a claim that the historical Function8 table contained a symmetric row for every D4 selector.",
            "- d3d4-prefix-ready uses current ratified D3 roots 100 CAR / 011 CDR and one D4 suffix bit; no descendant row lookup.",
            "- direct-static is used only for repeated fixed call sites and is the compile-away lower-bound lane.",
            "- direct-dynamic remains a switch-based control for random/mixed streams; it is not a compiled lower bound.",
            "- identity parsing/framing is intentionally excluded; #1993 owns framing cost.",
            "",
        ]
        report = "\n".join(lines)
        Path(args.report).write_text(report + "\n", encoding="utf-8")
        print(report)
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write(report + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
