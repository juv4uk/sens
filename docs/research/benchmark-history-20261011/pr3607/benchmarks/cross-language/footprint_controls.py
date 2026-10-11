#!/usr/bin/env python3
"""Scoped same-host footprint collector for the paired cross-language corpus.

Every emitted row is keyed by (runtime, workload). This is deliberate:
- RSS is workload-specific;
- native Rust artifact size is workload-specific;
- interpreter/SENS-runner artifact sizes may repeat across workloads, but are
  still recorded against the exact execution row they accompany.

The collector never infers semantic size from binary size.
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
CASES = tuple(external_controls.CASES)

if tuple(current_sens.CASES) != CASES:
    raise RuntimeError("paired workload corpus drift between SENS and external controls")


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


def find_launcher(command: str) -> str:
    found = shutil.which(command)
    if found is None:
        raise RuntimeError(f"executable not found: {command}")
    return found


def artifact_path(command: str) -> Path:
    found = find_launcher(command)
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


def max_rss_kib(cmd: list[str], expected: str, report: Path) -> int:
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


def generate_programs(
    workdir: Path,
    rustc_command: str,
    python_command: str,
) -> tuple[
    dict[tuple[str, str], list[str]],
    dict[tuple[str, str], Path],
    dict[tuple[str, str], Path],
]:
    commands: dict[tuple[str, str], list[str]] = {}
    artifacts: dict[tuple[str, str], Path] = {}
    sources: dict[tuple[str, str], Path] = {}

    python_cmd = find_launcher(python_command)

    for workload in CASES:
        py_src = workdir / f"{workload}.py"
        lua_src = workdir / f"{workload}.lua"
        racket_src = workdir / f"{workload}.rkt"
        sbcl_src = workdir / f"{workload}.lisp"
        rust_src = workdir / f"{workload}.rs"
        sens_src = workdir / f"{workload}-sens.lisp"
        rust_bin = workdir / f"{workload}-rust"

        py_src.write_text(external_controls.python_source(workload), encoding="utf-8")
        lua_src.write_text(external_controls.lua_source(workload), encoding="utf-8")
        racket_src.write_text(external_controls.racket_source(workload), encoding="utf-8")
        sbcl_src.write_text(external_controls.sbcl_source(workload), encoding="utf-8")
        rust_src.write_text(external_controls.rust_source(workload), encoding="utf-8")
        sens_src.write_text(current_sens.source(workload), encoding="utf-8")

        compile_proc = subprocess.run(
            [rustc_command, "-O", str(rust_src), "-o", str(rust_bin)],
            capture_output=True,
            text=True,
            check=False,
        )
        if compile_proc.returncode != 0:
            raise RuntimeError(
                f"rustc failed for {workload}:\n"
                f"{compile_proc.stdout}\n{compile_proc.stderr}"
            )

        for runtime, src in [
            ("cpython", py_src),
            ("lua54", lua_src),
            ("racket-cs", racket_src),
            ("sbcl", sbcl_src),
            ("rust-native", rust_src),
            ("sens-exact", sens_src),
        ]:
            sources[(runtime, workload)] = src

        artifacts[("rust-native", workload)] = rust_bin.resolve()
        commands[("rust-native", workload)] = [str(rust_bin.resolve())]

        commands[("cpython", workload)] = [python_cmd, str(py_src)]

    return commands, artifacts, sources


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

    rustc_command = find_launcher(args.rustc)
    # Do not resolve rustc: on rustup-managed installations argv[0] dispatch
    # matters, and resolving the symlink turns "rustc -O" into invalid "rustup -O".
    commands, artifacts, sources = generate_programs(
        workdir, rustc_command, args.python
    )

    sens_runner = Path(args.sens_runner).resolve()
    if not sens_runner.is_file():
        raise RuntimeError(f"SENS runner not found: {sens_runner}")

    python_artifact = artifact_path(args.python)
    lua_launcher = find_launcher(args.lua)
    racket_launcher = find_launcher(args.racket)
    sbcl_launcher = find_launcher(args.sbcl)
    lua_artifact = Path(lua_launcher).resolve()
    racket_artifact = Path(racket_launcher).resolve()
    sbcl_artifact = Path(sbcl_launcher).resolve()

    for workload in CASES:
        commands[("lua54", workload)] = [lua_launcher, str(sources[("lua54", workload)])]
        commands[("racket-cs", workload)] = [
            racket_launcher,
            str(sources[("racket-cs", workload)]),
        ]
        commands[("sbcl", workload)] = [
            sbcl_launcher,
            "--noinform",
            "--disable-debugger",
            "--script",
            str(sources[("sbcl", workload)]),
        ]
        commands[("sens-exact", workload)] = [
            str(sens_runner),
            str(sources[("sens-exact", workload)]),
        ]
        artifacts[("cpython", workload)] = python_artifact
        artifacts[("lua54", workload)] = lua_artifact
        artifacts[("racket-cs", workload)] = racket_artifact
        artifacts[("sbcl", workload)] = sbcl_artifact
        artifacts[("sens-exact", workload)] = sens_runner

    rows: list[dict[str, object]] = []
    runtimes = (
        "cpython",
        "lua54",
        "racket-cs",
        "sbcl",
        "rust-native",
        "sens-exact",
    )

    for workload in CASES:
        expected = external_controls.EXPECTED[workload]
        if current_sens.EXPECTED[workload] != expected:
            raise RuntimeError(f"paired oracle drift for {workload}")

        for runtime in runtimes:
            cmd = commands[(runtime, workload)]
            external_controls.run_checked(cmd, expected)
            rss_samples = [
                max_rss_kib(
                    cmd,
                    expected,
                    workdir / f"time-{runtime}-{workload}-{rep}.txt",
                )
                for rep in range(1, args.rss_reps + 1)
            ]
            exe = artifacts[(runtime, workload)]
            src = sources[(runtime, workload)]
            rows.append(
                {
                    "runtime": runtime,
                    "workload": workload,
                    "artifact_scope": "resolved command artifact for this runtime/workload row; dependency closure excluded",
                    "artifact_path": str(exe),
                    "artifact_bytes": exe.stat().st_size,
                    "text_section_bytes": text_section_bytes(exe),
                    "rss_scope": f"max RSS of shared {workload} process",
                    "rss_bytes": int(statistics.median(rss_samples)) * 1024,
                    "program_scope": f"generated shared {workload} source",
                    "program_source_bytes": src.stat().st_size,
                    "kernel_scope": "N/A",
                    "kernel_source_bytes": "",
                    "kernel_loc": "",
                    "git_sha": git_fact("rev-parse", "HEAD"),
                }
            )
            print(
                f"[footprint] {runtime}/{workload}: "
                f"artifact={exe.stat().st_size} B "
                f"rss={int(statistics.median(rss_samples)) * 1024} B"
            )

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
        "paired_carrier": "#3601",
        "workloads": list(CASES),
        "rss_reps": args.rss_reps,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "scope_rules": {
            "join_key": ["runtime", "workload"],
            "artifact": "resolved command artifact; wrappers/shared-library/dependency closure excluded",
            "rss": "median max RSS from /usr/bin/time -v for the same workload",
            "program": "generated benchmark source bytes for the same workload",
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
        "# Paired runtime/workload footprint",
        "",
        "Each row uses the same (runtime, workload) key as the execution corpus.",
        "This does not infer semantic size. Command artifacts are not full installed/runtime dependency closures.",
        "",
        "| workload | runtime | artifact bytes | .text bytes | median max RSS bytes | source bytes |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        text_bytes = (
            str(row["text_section_bytes"])
            if row["text_section_bytes"] is not None
            else "N/A"
        )
        report.append(
            f"| {row['workload']} | {row['runtime']} | {row['artifact_bytes']} | "
            f"{text_bytes} | {row['rss_bytes']} | {row['program_source_bytes']} |"
        )
    report += [
        "",
        f"SENS benchmark-visible glue slice: {visible_bytes} bytes / {visible_loc} LOC.",
        "That glue slice is diagnostic only and is **not** semantic-kernel size.",
        "",
    ]
    (out / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
