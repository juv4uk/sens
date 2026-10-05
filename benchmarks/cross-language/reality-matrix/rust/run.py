#!/usr/bin/env python3
"""#3687: first current-SENS vs direct-Rust reality slice.

This is intentionally a D3 smoke/control lane. It does not bypass the blocked
headline current-en-vs-d1d8 corpus.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FIXTURE = ROOT / "benchmarks" / "current-en-vs-d1d8" / "fixtures" / "d3-smoke.json"
CONTROL_RS = Path(__file__).with_name("rust_control.rs")
SENS_EXAMPLE = "current_en_vs_d1d8_cpu"
CASES = ("d3-quote-empty", "d3-car-empty")


def run_text(args: list[str], *, cwd: Path | None = None) -> str:
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for raw in text.splitlines():
        if "=" in raw:
            key, value = raw.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def decode_hex(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def contract_version() -> str:
    text = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")
    import re

    m = re.search(
        r"\(\(major\s+\.\s+#d(?P<major>[0-9]+)\)\s+\(minor\s+\.\s+(?P<minor>[0-9]+)\)",
        text,
    )
    if m is None:
        raise RuntimeError("cannot read Contract version")
    return f"{m.group('major')}.{m.group('minor')}"


def build_sens() -> Path:
    subprocess.run(
        ["cargo", "build", "--release", "-p", "sens", "--example", SENS_EXAMPLE],
        cwd=ROOT,
        check=True,
    )
    suffix = ".exe" if os.name == "nt" else ""
    path = ROOT / "target" / "release" / "examples" / f"{SENS_EXAMPLE}{suffix}"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def build_rust(out_dir: Path) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    binary = out_dir / f"rust_control{suffix}"
    subprocess.run(
        [
            "rustc",
            str(CONTROL_RS),
            "--edition=2021",
            "-C",
            "opt-level=3",
            "-C",
            "debuginfo=0",
            "-C",
            "strip=symbols",
            "-o",
            str(binary),
        ],
        check=True,
    )
    return binary


def load_cases() -> dict[str, dict[str, object]]:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    ready = {
        row["id"]: row
        for row in payload["workloads"]
        if row.get("status") == "ready" and row.get("id") in CASES
    }
    missing = sorted(set(CASES) - set(ready))
    if missing:
        raise RuntimeError(f"missing ready fixtures: {missing}")
    return ready


def write_sources(tmp: Path, row: dict[str, object]) -> tuple[Path, Path]:
    english = tmp / f"{row['id']}.english.lisp"
    canonical = tmp / f"{row['id']}.canonical.lisp"
    english.write_text(str(row["english_source"]), encoding="utf-8")
    canonical.write_text(str(row["canonical_source"]), encoding="utf-8")
    return english, canonical


def sens_preflight(helper: Path, candidate: str, source: Path) -> dict[str, str]:
    fields = parse_kv(run_text([str(helper), candidate, "preflight", str(source)]))
    for key in ("TRACE_HEX", "VALUE_HEX", "OUTPUT_HEX"):
        if key not in fields:
            raise RuntimeError(f"SENS preflight missing {key}")
    return {
        "trace": decode_hex(fields["TRACE_HEX"]),
        "value": decode_hex(fields["VALUE_HEX"]),
        "output": decode_hex(fields["OUTPUT_HEX"]),
    }


def rust_preflight(binary: Path, case: str) -> str:
    fields = parse_kv(run_text([str(binary), case, "preflight"]))
    if "VALUE" not in fields:
        raise RuntimeError("Rust control preflight missing VALUE")
    return fields["VALUE"]


def run_with_usage(args: list[str]) -> tuple[str, int | None]:
    if not hasattr(os, "wait4"):
        proc = subprocess.run(args, check=True, capture_output=True, text=True)
        return proc.stdout, None

    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    _pid, status, usage = os.wait4(proc.pid, 0)
    stdout = proc.stdout.read() if proc.stdout is not None else ""
    stderr = proc.stderr.read() if proc.stderr is not None else ""
    if proc.stdout is not None:
        proc.stdout.close()
    if proc.stderr is not None:
        proc.stderr.close()
    code = os.waitstatus_to_exitcode(status)
    if code != 0:
        raise RuntimeError(f"command failed ({code}): {args}\n{stderr}")
    return stdout, int(usage.ru_maxrss)


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, (95 * len(ordered) + 99) // 100 - 1))
    return ordered[rank]


def summary(values: list[float]) -> tuple[float, float]:
    return float(statistics.median(values)), float(percentile95(values))


def verdict_lower(sens_value: float, competitor_value: float) -> str:
    if sens_value < competitor_value:
        return "sens"
    if competitor_value < sens_value:
        return "competitor"
    return "tie"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True, type=Path)
    ap.add_argument("--outer-reps", type=int, default=10)
    ap.add_argument("--inner-repeats", type=int, default=10000)
    ap.add_argument("--evidence-mode", choices=("smoke", "performance"), default="smoke")
    ap.add_argument("--load-context", choices=("idle", "high", "unknown"), default="unknown")
    args = ap.parse_args()
    if args.outer_reps <= 0 or args.inner_repeats <= 0:
        raise SystemExit("repeat counts must be positive")
    if args.evidence_mode == "performance" and args.outer_reps < 10:
        raise SystemExit("performance mode requires at least 10 outer repetitions")
    if args.evidence_mode == "performance" and args.load_context == "unknown":
        raise SystemExit("performance mode requires an explicit idle/high load context")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    sens = build_sens()
    rust = build_rust(args.out_dir)
    fixtures = load_cases()

    raw_rows: list[dict[str, object]] = []
    workloads: list[dict[str, object]] = []
    verdicts: list[dict[str, str]] = []

    with tempfile.TemporaryDirectory(prefix="sens-rust-reality-") as tmp_name:
        tmp = Path(tmp_name)
        for case in CASES:
            row = fixtures[case]
            english, canonical = write_sources(tmp, row)

            left = sens_preflight(sens, "english-surface", english)
            right = sens_preflight(sens, "canonical-d1d8", canonical)
            if left != right:
                raise RuntimeError(f"{case}: English/canonical SENS preflight mismatch")
            if left["value"] != row["expected_value"] or left["output"] != row["expected_output"]:
                raise RuntimeError(f"{case}: SENS oracle mismatch: {left!r}")
            rust_value = rust_preflight(rust, case)
            if rust_value != row["expected_value"]:
                raise RuntimeError(f"{case}: Rust oracle mismatch: {rust_value!r}")

            sens_ns: list[float] = []
            rust_ns: list[float] = []
            sens_rss: list[float] = []
            rust_rss: list[float] = []

            for rep in range(args.outer_reps):
                sens_stdout, s_rss = run_with_usage(
                    [str(sens), "canonical-d1d8", "repeated", str(canonical), str(args.inner_repeats)]
                )
                rust_stdout, r_rss = run_with_usage(
                    [str(rust), case, "repeated", str(args.inner_repeats)]
                )
                s_fields = parse_kv(sens_stdout)
                r_fields = parse_kv(rust_stdout)
                s_per = int(s_fields["ELAPSED_NS"]) / args.inner_repeats
                r_per = int(r_fields["ELAPSED_NS"]) / args.inner_repeats
                sens_ns.append(s_per)
                rust_ns.append(r_per)
                if s_rss is not None:
                    sens_rss.append(float(s_rss))
                if r_rss is not None:
                    rust_rss.append(float(r_rss))
                raw_rows.append(
                    {
                        "workload": case,
                        "rep": rep,
                        "inner_repeats": args.inner_repeats,
                        "sens_ns_per_op": s_per,
                        "rust_ns_per_op": r_per,
                        "sens_maxrss_kb": "" if s_rss is None else s_rss,
                        "rust_maxrss_kb": "" if r_rss is None else r_rss,
                    }
                )

            s_med, s_p95 = summary(sens_ns)
            r_med, r_p95 = summary(rust_ns)
            measurements: list[dict[str, object]] = [
                {
                    "axis": "warm_ready_execution_ns_per_op",
                    "status": "measured",
                    "unit": "ns/op",
                    "sens_samples": sens_ns,
                    "competitor_samples": rust_ns,
                    "sens_median": s_med,
                    "competitor_median": r_med,
                    "sens_p95": s_p95,
                    "competitor_p95": r_p95,
                    "notes": "SENS eval of already-lowered exact-domain expression vs direct native Rust mechanism control.",
                }
            ]
            perf_verdict = (
                verdict_lower(s_med, r_med)
                if args.evidence_mode == "performance"
                else "inconclusive"
            )
            perf_note = (
                f"median SENS={s_med:.3f} ns/op; Rust={r_med:.3f} ns/op"
                if args.evidence_mode == "performance"
                else f"smoke observation only: median SENS={s_med:.3f} ns/op; Rust={r_med:.3f} ns/op"
            )
            verdicts.append(
                {
                    "axis": f"{case}:warm_ready_execution_ns_per_op",
                    "verdict": perf_verdict,
                    "evidence": perf_note,
                }
            )

            if sens_rss and rust_rss:
                sr_med, sr_p95 = summary(sens_rss)
                rr_med, rr_p95 = summary(rust_rss)
                measurements.append(
                    {
                        "axis": "process_maxrss_kb",
                        "status": "measured",
                        "unit": "KiB",
                        "sens_samples": sens_rss,
                        "competitor_samples": rust_rss,
                        "sens_median": sr_med,
                        "competitor_median": rr_med,
                        "sens_p95": sr_p95,
                        "competitor_p95": rr_p95,
                        "notes": "Whole helper-process RSS; includes runtime footprint, not only the timed operation.",
                    }
                )
                rss_verdict = (
                    verdict_lower(sr_med, rr_med)
                    if args.evidence_mode == "performance"
                    else "inconclusive"
                )
                rss_note = (
                    f"median SENS={sr_med:.0f} KiB; Rust={rr_med:.0f} KiB"
                    if args.evidence_mode == "performance"
                    else f"smoke observation only: median SENS={sr_med:.0f} KiB; Rust={rr_med:.0f} KiB"
                )
                verdicts.append(
                    {
                        "axis": f"{case}:process_maxrss_kb",
                        "verdict": rss_verdict,
                        "evidence": rss_note,
                    }
                )

            workloads.append(
                {
                    "id": case,
                    "parity": "pass",
                    "params": {
                        "outer_reps": args.outer_reps,
                        "inner_repeats": args.inner_repeats,
                        "scope": "D3 smoke only",
                        "evidence_mode": args.evidence_mode,
                    },
                    "measurements": measurements,
                }
            )

    artifact_measurement = {
        "id": "runtime-artifact-control",
        "parity": "pass",
        "params": {"scope": "binary file only; dependency closure not included"},
        "measurements": [
            {
                "axis": "binary_artifact_bytes",
                "status": "measured",
                "unit": "bytes",
                "sens_samples": [float(sens.stat().st_size)],
                "competitor_samples": [float(rust.stat().st_size)],
                "sens_median": float(sens.stat().st_size),
                "competitor_median": float(rust.stat().st_size),
                "sens_p95": float(sens.stat().st_size),
                "competitor_p95": float(rust.stat().st_size),
                "notes": "SENS benchmark helper vs standalone optimized Rust control binary.",
            }
        ],
    }
    workloads.append(artifact_measurement)
    verdicts.append(
        {
            "axis": "binary_artifact_bytes",
            "verdict": verdict_lower(float(sens.stat().st_size), float(rust.stat().st_size)),
            "evidence": f"SENS={sens.stat().st_size} bytes; Rust={rust.stat().st_size} bytes",
        }
    )

    git_sha = run_text(["git", "rev-parse", "HEAD"], cwd=ROOT)
    rustc = run_text(["rustc", "--version"])
    environment = {
        "os": platform.platform(),
        "arch": platform.machine(),
        "cpu": platform.processor() or None,
        "load_context": args.load_context,
        "evidence_mode": args.evidence_mode,
        "toolchain": {"rustc": rustc},
    }
    comparison = {
        "system": "rust",
        "sens": {
            "commit": git_sha,
            "contract": contract_version(),
            "ratified_domains": "D1-D7",
        },
        "competitor": {"name": "Rust", "version": rustc, "commit": None},
        "environment": environment,
        "workloads": workloads,
        "semantic_density": None,
        "verdicts": verdicts,
    }

    with (raw_dir / "runs.tsv").open("w", newline="", encoding="utf-8") as fh:
        fields = list(raw_rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(raw_rows)

    (args.out_dir / "environment.json").write_text(
        json.dumps(environment, indent=2) + "\n", encoding="utf-8"
    )
    (args.out_dir / "comparison.json").write_text(
        json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
    )

    report = [
        "# SENS vs Rust — D3 smoke reality slice",
        "",
        "This is a native-mechanism control, not a whole-language ranking.",
        "The blocked headline corpus is not bypassed.",
        f"Evidence mode: {args.evidence_mode}; load context: {args.load_context}.",
        "",
        "| axis | verdict | evidence |",
        "|---|---|---|",
    ]
    for item in verdicts:
        report.append(f"| {item['axis']} | {item['verdict']} | {item['evidence']} |")
    report.append("")
    (args.out_dir / "report.md").write_text("\n".join(report), encoding="utf-8")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
