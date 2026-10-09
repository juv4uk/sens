#!/usr/bin/env python3
"""Physical T5 reference-codec benchmark (not SENS evaluator throughput).

Measures the existing Python transport implementation. Physical T5 is
compared against the canonical extensionless ASCII 0/1 spaced view, NOT
against Ukrainian executable source or CPython's language runtime.
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
sys.path.insert(0, str(ROOT / "scripts"))
from domain_tables import D7_TABLE, read_domain_table  # noqa: E402
from sens_t5_codec import decode_bytes, encode_words, typed_sha256  # noqa: E402

D7 = tuple(row.bits for row in read_domain_table(D7_TABLE))
assert len(D7) == len(set(D7)) == 126
assert not {"0100001", "0101010"}.intersection(D7)

def corpus(kind: str, n: int) -> list[str]:
    if kind == "d3":
        return [f"{(i * 5 + 3) % 8:03b}" for i in range(n)]
    if kind == "d7":
        return [D7[(i * 17 + i // 7) % len(D7)] for i in range(n)]
    if kind == "mixed":
        # Transport-only coordinates. This does not claim executable grammar.
        return [f"{(i * 29 + 7) % (1 << (i % 9 + 1)):0{i % 9 + 1}b}" for i in range(n)]
    raise ValueError(f"unknown case: {kind}")

def median_us(call, *, samples: int, loops: int) -> tuple[float, float]:
    for _ in range(3):
        call()
    times = []
    for _ in range(samples):
        started = time.perf_counter_ns()
        for _ in range(loops):
            call()
        times.append((time.perf_counter_ns() - started) / (1000.0 * loops))
    return statistics.median(times), max(times) - min(times)

def cpu() -> str:
    info = Path("/proc/cpuinfo")
    if info.is_file():
        for line in info.read_text(errors="replace").splitlines():
            if line.startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"

def git_sha() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--sizes", default="128,2048")
    ap.add_argument("--samples", type=int, default=9)
    ap.add_argument("--loops", type=int, default=3)
    args = ap.parse_args()
    sizes = [int(x) for x in args.sizes.split(",")]
    if not sizes or min(sizes) < 1 or args.samples < 3 or args.loops < 1:
        ap.error("nonempty positive sizes, samples >= 3 and loops >= 1 required")
    rows = []
    for kind in ("d3", "d7", "mixed"):
        for size in sizes:
            words = corpus(kind, size)
            physical = encode_words(words)
            text = (" ".join(words) + "\n").encode("ascii")
            if decode_bytes(physical) != words or encode_words(decode_bytes(physical)) != physical:
                raise RuntimeError(f"lossy T5 transport: {kind}/{size}")
            # Independent exact word-view comparison; text is not a runnable program.
            if text[:-1].decode("ascii").split(" ") != words:
                raise RuntimeError("view mismatch")
            enc_us, enc_span = median_us(lambda: encode_words(words), samples=args.samples, loops=args.loops)
            dec_us, dec_span = median_us(lambda: decode_bytes(physical), samples=args.samples, loops=args.loops)
            bits = sum(map(len, words))
            row = {
                "workload": kind, "words": size, "semantic_bits": bits,
                "physical_t5_bytes": len(physical), "ascii_bit_view_bytes": len(text),
                "t5_to_ascii_ratio": round(len(physical) / len(text), 6),
                "payload_utilization": round(bits / (8 * len(physical)), 6),
                "python_encode_median_us": round(enc_us, 3),
                "python_decode_median_us": round(dec_us, 3),
                "python_encode_spread_us": round(enc_span, 3),
                "python_decode_spread_us": round(dec_span, 3),
                "typed_word_sha256": typed_sha256(words),
                "physical_sha256": hashlib.sha256(physical).hexdigest(),
            }
            rows.append(row)
            print(f"{kind}/{size}: T5={len(physical)} B view={len(text)} B "
                  f"ratio={row['t5_to_ascii_ratio']} encode={enc_us:.2f} us decode={dec_us:.2f} us")
    args.out.mkdir(parents=True, exist_ok=True)
    environment = {
        "schema": "sens-t5-reference-benchmark/v1",
        "git_sha": git_sha(), "cpu": cpu(), "platform": platform.platform(),
        "python": platform.python_version(), "samples": args.samples, "loops": args.loops,
        "scope": "Python reference T5 transport only; no language execution",
        "comparison": "physical T5 bytes versus canonical ASCII exact-word view",
        "limits": "GitHub shared runner timings are noisy; do not compare across distinct hardware",
        "d7": "126 owner-ratified coordinates; 2 reserved and excluded",
    }
    with (args.out / "environment.json").open("w", encoding="utf-8") as f:
        json.dump(environment, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with (args.out / "results.tsv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    with (args.out / "results.json").open("w", encoding="utf-8") as f:
        json.dump({"environment": environment, "rows": rows}, f, ensure_ascii=False, indent=2)
        f.write("\n")
    lines = [
        "# SENS physical T5 reference benchmark",
        "",
        f"SHA: `{environment['git_sha']}` · CPU: {environment['cpu']}",
        "",
        "| Corpus | Words | T5 bytes | ASCII-view bytes | T5/view | Encode µs | Decode µs |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(f"| {r['workload']} | {r['words']} | {r['physical_t5_bytes']} | "
                     f"{r['ascii_bit_view_bytes']} | {r['t5_to_ascii_ratio']:.3f} | "
                     f"{r['python_encode_median_us']:.1f} | {r['python_decode_median_us']:.1f} |")
    lines.extend(["", "**Scope:** Python reference T5 codec, not SENS interpreter, native CPU, or "
                  "Ukrainian-source parsing. Pack/read roundtrip is verified before timing.",
                  "",
                  "**Reproducibility:** GitHub shared-runner wall time fluctuates; do not claim speedups "
                  "between different CPUs. See environment.json and results.tsv for samples and SHA.",
                  ""])
    report = "\n".join(lines)
    (args.out / "report.md").write_text(report, encoding="utf-8")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(report)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
