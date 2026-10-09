#!/usr/bin/env python3
"""One-shot physical T5 performance: current .sens, real CLIs, reproducible samples.

Correctness is an admission gate, not the metric. Same packed bytes must yield
exactly the same output from sens and sens-trit eval; sens-trit open must agree
with the independent Python T5 decoder. Timings include process startup,
file I/O, decoding and (for eval modes) evaluation, NOT warm interpreter time.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = (
    "tests/fixtures/migration-quote-cohort-main/quote-legacy.sens",
    "tests/fixtures/migration-multiform-cohort-main/two-forms.sens",
)
MODES = ("sens-execute", "sens-trit-eval", "sens-trit-open")


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def measure(argv: list[str]) -> tuple[int, bytes]:
    started = time.perf_counter_ns()
    proc = subprocess.run(argv, capture_output=True, timeout=30, check=False)
    elapsed = time.perf_counter_ns() - started
    if proc.returncode:
        raise RuntimeError(f"{argv!r} exited {proc.returncode}: {proc.stderr[:1000]!r}")
    return elapsed, proc.stdout


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.lower().startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def p95(ns: list[int]) -> int:
    sorted_ns = sorted(ns)
    return sorted_ns[(95 * len(sorted_ns) + 99) // 100 - 1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sens", type=Path, required=True)
    ap.add_argument("--trit", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--warmup", type=int, default=4)
    ap.add_argument("--reps", type=int, default=25)
    args = ap.parse_args()
    if args.warmup < 0 or args.reps < 5:
        ap.error("warmup must be >=0, timed reps >=5")
    sens, trit = str(args.sens.resolve()), str(args.trit.resolve())
    if not Path(sens).is_file() or not Path(trit).is_file():
        raise FileNotFoundError("build release sens and sens-trit first")

    sys.path.insert(0, str(ROOT / "scripts"))
    from sens_t5_codec import decode_bytes

    args.out.mkdir(parents=True, exist_ok=True)
    git = os.environ.get("GITHUB_SHA")
    if not git:
        p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                           capture_output=True, text=True, check=False)
        git = p.stdout.strip() if p.returncode == 0 else "unknown"
    report = {
        "schema": "sens-physical-t5-performance/v1",
        "git_sha": git,
        "cpu": cpu_model(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "binary_sha256": {
            "sens": digest(Path(sens).read_bytes()),
            "sens-trit": digest(Path(trit).read_bytes()),
        },
        "reps": args.reps,
        "warmup": args.warmup,
        "metric": "one-shot-process-wall-ns; OS page cache may be warm",
        "claim_boundary": (
            "Two tiny admitted D3 physical programs only; no general language speed "
            "claim, no warmed in-process interpreter measurement, no uncached disk claim"
        ),
        "cases": [],
    }
    raw = []
    markdown = [
        "# Measured physical SENS T5 performance", "",
        f"Commit: `{git}`; CPU: {report['cpu']}.", "",
        f"{args.reps} measured process invocations per mode after {args.warmup} warmups. "
        "Wall time includes startup, I/O, decode and (where applicable) execution.", "",
        "| Program | Mode | Median ms | p95 ms | First observed ms |",
        "|---|---|---:|---:|---:|",
    ]

    for fixture in FIXTURES:
        file = ROOT / fixture
        physical = file.read_bytes()
        words = decode_bytes(physical)
        visible = (" ".join(words) + "\n").encode("ascii")
        if set(visible) - {48, 49, 32, 10}:
            raise RuntimeError(f"non-binary visible stream {fixture}")
        commands = {
            "sens-execute": [sens, str(file)],
            "sens-trit-eval": [trit, "eval", str(file)],
            "sens-trit-open": [trit, "open", str(file)],
        }
        first, expected = {}, {}
        for mode in MODES:
            first[mode], expected[mode] = measure(commands[mode])
        if expected["sens-execute"] != expected["sens-trit-eval"]:
            raise RuntimeError(f"{fixture}: current SENS CLI execution parity failed")
        if expected["sens-trit-open"] != visible:
            raise RuntimeError(f"{fixture}: T5 bytes disagree with exact binary words")

        samples = {mode: [] for mode in MODES}
        for round_no in range(args.warmup + args.reps):
            # Rotate to avoid giving one CLI the same repeated cache position.
            modes = MODES[round_no % 3:] + MODES[:round_no % 3]
            for mode in modes:
                ns, observed = measure(commands[mode])
                if observed != expected[mode]:
                    raise RuntimeError(f"{fixture}/{mode}: nondeterministic output")
                if round_no >= args.warmup:
                    samples[mode].append(ns)
                    raw.append({
                        "fixture": fixture, "mode": mode,
                        "rep": round_no - args.warmup, "wall_ns": ns,
                        "output_sha256": digest(observed),
                    })
        human = file.with_suffix(".lisp")
        case = {
            "fixture": fixture, "t5_sha256": digest(physical),
            "result_sha256": digest(expected["sens-execute"]),
            "sizes": {
                "physical_t5_bytes": len(physical),
                "visible_binary_bytes": len(visible),
                "human_lisp_bytes": human.stat().st_size if human.is_file() else None,
                "source_words": len(words),
            }, "modes": {},
        }
        for mode in MODES:
            vals = samples[mode]
            vals_summary = {
                "median_ns": int(statistics.median(vals)),
                "p95_ns": p95(vals),
                "first_ns": first[mode],
                "samples": len(vals),
            }
            case["modes"][mode] = vals_summary
            markdown.append(
                f"| `{file.name}` | {mode} | "
                f"{vals_summary['median_ns']/1e6:.3f} | "
                f"{vals_summary['p95_ns']/1e6:.3f} | "
                f"{vals_summary['first_ns']/1e6:.3f} |"
            )
        report["cases"].append(case)
        print(
            f"{file.name}: T5={len(physical)}B, visible={len(visible)}B, "
            f"words={len(words)}, SENS={case['modes']['sens-execute']['median_ns']/1e6:.3f}ms, "
            f"trit-eval={case['modes']['sens-trit-eval']['median_ns']/1e6:.3f}ms",
            flush=True,
        )

    markdown.extend([
        "", "| Program | Physical T5 bytes | Visible binary bytes | Human Lisp bytes |",
        "|---|---:|---:|---:|",
    ])
    for case in report["cases"]:
        sz = case["sizes"]
        markdown.append(
            f"| `{Path(case['fixture']).name}` | {sz['physical_t5_bytes']} | "
            f"{sz['visible_binary_bytes']} | {sz['human_lisp_bytes']} |"
        )
    markdown.extend([
        "", "These are paired physical D3 workloads, **not** a whole-language ranking.",
        "Process start and page-cache behavior are included, not separated.", "",
    ])
    with (args.out / "raw.tsv").open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(
            output, fieldnames=("fixture", "mode", "rep", "wall_ns", "output_sha256"),
            delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(raw)
    (args.out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.out / "report.md").write_text("\n".join(markdown), encoding="utf-8")


if __name__ == "__main__":
    main()
