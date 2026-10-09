#!/usr/bin/env python3
"""Measured physical SENS execution and identical-byte transport comparisons.

Every wall-clock sample includes a new subprocess: startup + decode/parse +
execution or rendering. Python and Rust 'view' do identical T5 -> words -> text
work, but distinct runtimes; 'sens' and 'sens-trit eval' use the same SENS engine.
Neither comparison proves current/legacy semantic equivalence or language law.
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
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words  # noqa: E402

FORM = ("10", "001", "00", "000", "01")
VIEW_PY = (
    "import sys;from pathlib import Path;"
    "sys.path.insert(0,'scripts');"
    "from sens_t5_codec import decode_bytes;"
    "print(' '.join(decode_bytes(Path(sys.argv[1]).read_bytes())))"
)
LANES = ("sens-exec", "sens-trit-eval", "rust-t5-view", "python-t5-view")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def percent(samples: list[int], position: float) -> int:
    ordered = sorted(samples)
    index = (len(ordered) - 1) * position
    low = int(index)
    high = min(low + 1, len(ordered) - 1)
    return round(ordered[low] + (ordered[high] - ordered[low]) * (index - low))


def run(cmd: list[str], *, timeout: int) -> tuple[int, bytes]:
    start = time.perf_counter_ns()
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=False, timeout=timeout)
    elapsed = time.perf_counter_ns() - start
    if proc.returncode:
        raise RuntimeError(
            f"command failed {cmd!r}, exit={proc.returncode}: "
            + proc.stderr.decode("utf-8", "replace")[-1200:]
        )
    return elapsed, proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sens", type=Path, required=True)
    parser.add_argument("--sens-trit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reps", type=int, default=19)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--sizes", default="1,16,128,1024",
                        help="count of repeated already-admitted D3 QUOTE forms")
    args = parser.parse_args()
    sizes = [int(x) for x in args.sizes.split(",")]
    if args.reps < 3 or args.warmups < 1 or not sizes or any(x <= 0 or x > 2048 for x in sizes):
        parser.error("reps>=3, warmups>=1, 1<=sizes<=2048 are required")
    for binary in (args.sens, args.sens_trit):
        if not binary.is_file():
            parser.error(f"missing built binary: {binary}")
    sens = str(args.sens.resolve())
    trit = str(args.sens_trit.resolve())
    args.out.mkdir(parents=True, exist_ok=True)

    raw: list[dict] = []
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="sens-benchmark-") as temporary:
        for count in sizes:
            words = list(FORM) * count
            physical = encode_words(words)
            if decode_bytes(physical) != words:
                raise RuntimeError("T5 transport identity was not preserved")
            visible = (" ".join(words) + "\n").encode("ascii")
            binary_file = Path(temporary) / f"quote-{count}.sens"
            binary_file.write_bytes(physical)
            commands = {
                "sens-exec": [sens, str(binary_file)],
                "sens-trit-eval": [trit, "eval", str(binary_file)],
                "rust-t5-view": [trit, "open", str(binary_file)],
                "python-t5-view": [sys.executable, "-c", VIEW_PY, str(binary_file)],
            }
            references: dict[str, bytes] = {}
            for lane in LANES:
                _, output = run(commands[lane], timeout=30)
                references[lane] = output
            if references["sens-exec"] != references["sens-trit-eval"]:
                raise RuntimeError("the two current SENS execution entrypoints disagree")
            if references["rust-t5-view"] != visible or references["python-t5-view"] != visible:
                raise RuntimeError("T5 decoder changed or truncated exact binary words")
            if not references["sens-exec"]:
                raise RuntimeError("empty execution result cannot be benchmarked")

            samples: dict[str, list[int]] = {lane: [] for lane in LANES}
            for trial in range(args.warmups + args.reps):
                # Rotate order, so one lane never always gets the hottest cache.
                order = LANES[trial % len(LANES):] + LANES[:trial % len(LANES)]
                for lane in order:
                    elapsed, output = run(commands[lane], timeout=30)
                    if output != references[lane]:
                        raise RuntimeError(f"unstable result: {lane} trial={trial}")
                    if trial >= args.warmups:
                        samples[lane].append(elapsed)
                        raw.append({"forms": count, "lane": lane,
                                    "trial": trial - args.warmups + 1, "wall_ns": elapsed})
            for lane in LANES:
                med = round(statistics.median(samples[lane]))
                results.append({
                    "forms": count,
                    "lane": lane,
                    "samples": len(samples[lane]),
                    "median_wall_ns": med,
                    "p95_wall_ns": percent(samples[lane], 0.95),
                    "min_wall_ns": min(samples[lane]),
                    "forms_per_second": round(count * 1e9 / med, 2),
                    "physical_bytes": len(physical),
                    "visible_ascii_bytes": len(visible),
                    "payload_bits": sum(map(len, words)),
                    "T5_sha256": sha(physical),
                    "output_sha256": sha(references[lane]),
                    "parity_verified": True,
                })
            print(f"measured {count} quoted forms; T5={len(physical)} B; ASCII={len(visible)} B", flush=True)

    environment = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "logical_cores": os.cpu_count(),
        "python": platform.python_version(),
        "sens_sha256": sha(Path(sens).read_bytes()),
        "sens_trit_sha256": sha(Path(trit).read_bytes()),
        "reps": args.reps, "warmups": args.warmups, "forms": sizes,
        "measurement": "wall-clock subprocess startup + workload; GitHub runners are shared",
        "caveats": [
            "SENS eval lanes use the same SENS engine, not independent language implementations",
            "Python vs Rust open lanes compare only T5 decoding/rendering; process startup included",
            "No historical Lisp or independent current-language semantic oracle inferred",
            "No speedup claims across workloads with different computational semantics",
        ],
    }
    (args.out / "environment.json").write_text(
        json.dumps(environment, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.out / "results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (args.out / "raw.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["forms", "lane", "trial", "wall_ns"], delimiter="\t")
        writer.writeheader()
        writer.writerows(raw)

    lines = [
        "# Physical SENS performance — actual T5 / canonical D2",
        "",
        f"Commit: `{environment['commit']}`. {args.reps} samples per lane, "
        f"{args.warmups} warmups; subprocess startup INCLUDED.",
        "",
        "| Forms | Lane | Median ms | p95 ms | Forms/s | T5 bytes | ASCII bytes |",
        "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for x in results:
        lines.append(
            f"| {x['forms']} | {x['lane']} | {x['median_wall_ns']/1e6:.3f} | "
            f"{x['p95_wall_ns']/1e6:.3f} | {x['forms_per_second']:.1f} | "
            f"{x['physical_bytes']} | {x['visible_ascii_bytes']} |"
        )
    lines += ["", "**Scope:** real release-built physical SENS executable; Python/Rust "
              "T5 view lanes are equivalent byte workloads, not whole-language benchmarks.",
              "Unmodified warm/cold execution or historic Function8 parity is NOT implied.",
              "Machine/environment details, exact outputs, SHA-256 and all raw trials "
              "are in the artifacts.", ""]
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
