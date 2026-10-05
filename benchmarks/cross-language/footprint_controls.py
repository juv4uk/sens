#!/usr/bin/env python3
"""Scoped footprint collector for the paired cross-language benchmark.

This measures concrete artifacts and one shared benchmark process on the same
host as the paired Cachegrind run. It does not infer semantic size from binary
size and does not attempt to estimate whole installed runtime closures.
"""

from __future__ import annotations

import argparse
import csv
import json
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import current_sens
import external_controls

ROOT = Path(__file__).resolve().parents[2]
WORKLOAD = "fib"


def git_fact(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except Exception as exc:
        return f"unknown ({exc})"


def resolve_executable(command: str) -> Path:
    found = shutil.which(command)
    if found is None:
        raise RuntimeError(f"executable not found: {command}")
    return Path(found).resolve()


def text_section_bytes(path: Path) -> int | None:
    proc = subprocess.run(
        ["size", "-A", "-d", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 2 and fields[0] == ".text":
            try:
                return int(fields[1])
            except ValueError:
                return None
    return None


def max_rss_kib(cmd: list[str], expected: str, scratch: Path) -> int:
    report = scratch / "time.txt"
    proc = subprocess.run(
        ["/usr/bin/time", "-v", "-o", str(report), *cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"RSS command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    got = lines[-1] if lines else ""
    if got != expected:
        raise RuntimeError(
            f"RSS correctness failed: {' '.join(cmd)}: "
            f"expected={expected!r}, got={got!r}"
        )
    match = re.search(
        r"Maximum resident set size \(kbytes\):\s*(\d+)",
        report.read_text(encoding="utf-8", errors="replace"),
    )
    if match is None:
        raise RuntimeError(f"/usr/bin/time did not report max RSS for {' '.join(cmd)}")
    return int(match.group(1))


def source_stats(paths: list[Path]) -> tuple[int, int]:
    total_bytes = 0
    total_loc = 0
    for path in paths:
        data = path.read_bytes()
        total_bytes += len(data)
        total_loc += len(data.decode("utf-8", errors="replace").splitlines())
    return total_bytes, total_loc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens-runner", required=True)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--lua", default="lua")
    ap.add_argument("--racket", default="racket")
    ap.add_argument("--sbcl", default="sbcl")
    ap.add_argument("--rustc", default="rustc")
    ap.add_argument("--rss-reps", type=int, default=3)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    if args.rss_reps < 1:
        ap.error("--rss-reps must be >= 1")

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    workdir = Path(tempfile.mkdtemp(prefix="sens-footprint-"))

    # Generate exactly the same fib workload through the paired harness donors.
    py_src = workdir / "fib.py"
    lua_src = workdir / "fib.lua"
    racket_src = workdir / "fib.rkt"
    sbcl_src = workdir / "fib.lisp"
    rust_src = workdir / "fib.rs"
    sens_src = workdir / "fib-sens.lisp"
    rust_bin = workdir / "fib-rust"

    py_src.write_text(external_controls.python_source(WORKLOAD), encoding="utf-8")
    lua_src.write_text(external_controls.lua_source(WORKLOAD), encoding="utf-8")
    racket_src.write_text(external_controls.racket_source(WORKLOAD), encoding="utf-8")
    sbcl_src.write_text(external_controls.sbcl_source(WORKLOAD), encoding="utf-8")
    rust_src.write_text(external_controls.rust_source(WORKLOAD), encoding="utf-8")
    sens_src.write_text(current_sens.source(WORKLOAD), encoding="utf-8")

    rustc = resolve_executable(args.rustc)
    compile_proc = subprocess.run(
        [str(rustc), "-O", str(rust_src), "-o", str(rust_bin)],
        capture_output=True,
        text=True,
        check=False,
    )
    if compile_proc.returncode != 0:
        raise RuntimeError(
            f"rustc failed:\n{compile_proc.stdout}\n{compile_proc.stderr}"
        )

    sens_runner = Path(args.sens_runner).resolve()
    if not sens_runner.is_file():
        raise RuntimeError(f"SENS runner not found: {sens_runner}")

    executables = {
        "cpython": resolve_executable(args.python),
        "lua54": resolve_executable(args.lua),
        "racket-cs": resolve_executable(args.racket),
        "sbcl": resolve_executable(args.sbcl),
        "rust-native": rust_bin.resolve(),
        "sens-exact": sens_runner,
    }
    commands = {
        "cpython": [str(executables["cpython"]), str(py_src)],
        "lua54": [str(executables["lua54"]), str(lua_src)],
        "racket-cs": [str(executables["racket-cs"]), str(racket_src)],
        "sbcl": [
            str(executables["sbcl"]),
            "--noinform",
            "--disable-debugger",
            "--script",
            str(sbcl_src),
        ],
        "rust-native": [str(executables["rust-native"])],
        "sens-exact": [str(sens_runner), str(sens_src)],
    }
    source_paths = {
        "cpython": py_src,
        "lua54": lua_src,
        "racket-cs": racket_src,
        "sbcl": sbcl_src,
        "rust-native": rust_src,
        "sens-exact": sens_src,
    }

    expected = external_controls.EXPECTED[WORKLOAD]
    if current_sens.EXPECTED[WORKLOAD] != expected:
        raise RuntimeError("paired workload oracle drift between harnesses")

    rows: list[dict[str, object]] = []
    for runtime, cmd in commands.items():
        # Hard correctness gate before footprint evidence.
        external_controls.run_checked(cmd, expected)
        rss_samples = [
            max_rss_kib(cmd, expected, workdir) for _ in range(args.rss_reps)
        ]
        exe = executables[runtime]
        rows.append(
            {
                "runtime": runtime,
                "workload": WORKLOAD,
                "artifact_scope": "resolved benchmark executable only",
                "artifact_path": str(exe),
                "artifact_bytes": exe.stat().st_size,
                "text_section_bytes": text_section_bytes(exe),
                "rss_scope": f"max RSS of shared {WORKLOAD} process",
                "rss_bytes": int(statistics.median(rss_samples)) * 1024,
                "program_scope": f"generated shared {WORKLOAD} source",
                "program_source_bytes": source_paths[runtime].stat().st_size,
                "kernel_scope": "N/A",
                "kernel_source_bytes": "",
                "kernel_loc": "",
                "git_sha": git_fact("rev-parse", "HEAD"),
            }
        )
        print(
            f"[footprint] {runtime}: artifact={exe.stat().st_size} B "
            f"rss={int(statistics.median(rss_samples)) * 1024} B"
        )

    # Report a deliberately narrow SENS source slice separately from kernel size,
    # so nobody mistakes benchmark-visible glue for the full semantic core.
    sens_slice = [
        ROOT / "crates/sens/src/mixed_source.rs",
        ROOT / "crates/sens/examples/current_exact_domain_bench.rs",
    ]
    visible_bytes, visible_loc = source_stats(sens_slice)

    fields = [
        "runtime",
        "workload",
        "artifact_scope",
        "artifact_path",
        "artifact_bytes",
        "text_section_bytes",
        "rss_scope",
        "rss_bytes",
        "program_scope",
        "program_source_bytes",
        "kernel_scope",
        "kernel_source_bytes",
        "kernel_loc",
        "git_sha",
    ]
    with (out / "footprint.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)

    environment = {
        "git_sha": git_fact("rev-parse", "HEAD"),
        "benchmark_issue": "#3527",
        "paired_carrier": "#3539",
        "workload": WORKLOAD,
        "rss_reps": args.rss_reps,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "scope_rules": {
            "artifact": "resolved executable file only; shared-library closure excluded",
            "rss": "median max RSS from /usr/bin/time -v on the shared fib process",
            "program": "generated fib benchmark source bytes",
            "semantic": "not measured here",
            "kernel": "N/A unless a separately ratified source boundary exists",
        },
        "sens_benchmark_visible_source_slice": {
            "paths": [str(path.relative_to(ROOT)) for path in sens_slice],
            "bytes": visible_bytes,
            "loc": visible_loc,
            "warning": "diagnostic glue slice only; not SENS semantic-kernel size",
        },
    }
    (out / "environment.json").write_text(
        json.dumps(environment, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = [
        "# Paired runtime footprint",
        "",
        "Scope: executable file + shared-fib max RSS on the same host as #3539.",
        "This does not infer semantic size and excludes shared-library dependency closure.",
        "",
        "| runtime | artifact bytes | .text bytes | median max RSS bytes | fib source bytes |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        text_bytes = (
            str(row["text_section_bytes"])
            if row["text_section_bytes"] is not None
            else "N/A"
        )
        report.append(
            f"| {row['runtime']} | {row['artifact_bytes']} | {text_bytes} | "
            f"{row['rss_bytes']} | {row['program_source_bytes']} |"
        )
    report += [
        "",
        f"SENS benchmark-visible glue slice: {visible_bytes} bytes / {visible_loc} LOC.",
        "That glue slice is diagnostic only and is **not** reported as semantic-kernel size.",
        "",
    ]
    (out / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
