#!/usr/bin/env python3
"""#3583 phase-1 real-evaluator D6 selector replay.

Measures prepared exact-domain AST evaluation through the real SENS evaluator.
The control is an equivalent nested exact D3 CAR/CDR chain; a quote-only lane
captures the shared exact-D3 QUOTE/data cost. No production flat table exists.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import re
import statistics
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = "d6_selector_eval_replay"
MODES = ("d6", "d3-chain", "quote-only")
PATTERNS = ("repeated", "random", "alternating")
COUNTERS = {
    "i_refs": re.compile(r"I\s+refs:\s+([0-9,]+)"),
    "i1_misses": re.compile(r"I1\s+misses:\s+([0-9,]+)"),
    "d1_misses": re.compile(r"D1\s+misses:\s+([0-9,]+)"),
    "branches": re.compile(r"Branches:\s+([0-9,]+)"),
    "mispredicts": re.compile(r"Mispredicts:\s+([0-9,]+)"),
}


def sh(args, *, env=None):
    return subprocess.run(args, cwd=ROOT, check=True, text=True, capture_output=True, env=env)


def binary() -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return ROOT / "target" / "release" / "examples" / f"{EXAMPLE}{suffix}"


def build() -> Path:
    sh(["cargo", "build", "--release", "-p", "sens", "--example", EXAMPLE])
    result = binary()
    if not result.exists():
        raise RuntimeError(f"example binary not found: {result}")
    return result


def verify(bin_path: Path) -> None:
    proc = sh([str(bin_path), "verify", "prepare", "repeated", "1"])
    if "VERIFY\tPASS" not in proc.stdout:
        raise RuntimeError(proc.stdout + proc.stderr)


def cachegrind(bin_path: Path, mode: str, phase: str, pattern: str, calls: int, cpu: int | None):
    with tempfile.NamedTemporaryFile(prefix="cg-3583-", delete=False) as tmp:
        out = tmp.name
    os.unlink(out)

    cmd = [
        "valgrind", "--tool=cachegrind", "--cache-sim=yes", "--branch-sim=yes",
        f"--cachegrind-out-file={out}",
        str(bin_path), mode, phase, pattern, str(calls),
    ]
    if cpu is not None:
        cmd = ["taskset", "-c", str(cpu)] + cmd

    env = os.environ.copy()
    env["LC_ALL"] = "C"
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, env=env)
    try:
        os.unlink(out)
    except FileNotFoundError:
        pass
    if proc.returncode != 0:
        raise RuntimeError(f"cachegrind failed: {proc.stderr}")

    result = {}
    for key, regex in COUNTERS.items():
        match = regex.search(proc.stderr)
        if not match:
            raise RuntimeError(f"missing {key}: {proc.stderr}")
        result[key] = int(match.group(1).replace(",", ""))
    return result


def median(samples, key):
    return int(statistics.median(s[key] for s in samples))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--calls", type=int, default=20_000)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--cpu", type=int, default=None)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    if args.calls <= 0 or args.samples <= 0:
        raise SystemExit("calls/samples must be positive")

    bin_path = build()
    verify(bin_path)

    rows = []
    for pattern in PATTERNS:
        for mode in MODES:
            prepare_samples = []
            full_samples = []
            for _ in range(args.samples):
                prepare_samples.append(cachegrind(bin_path, mode, "prepare", pattern, args.calls, args.cpu))
                full_samples.append(cachegrind(bin_path, mode, "full", pattern, args.calls, args.cpu))

            exec_samples = []
            for prepare, full in zip(prepare_samples, full_samples, strict=True):
                delta = {
                    "i_refs": full["i_refs"] - prepare["i_refs"],
                    "branches": full["branches"] - prepare["branches"],
                }
                if any(v < 0 for v in delta.values()):
                    raise RuntimeError(f"negative additive delta: {mode=} {pattern=} {delta=}")
                exec_samples.append(delta)

            rows.append({
                "pattern": pattern,
                "mode": mode,
                "calls": args.calls,
                "samples": args.samples,
                "execute_i_refs": median(exec_samples, "i_refs"),
                "i_refs_per_call": f"{median(exec_samples, 'i_refs') / args.calls:.3f}",
                "execute_branches": median(exec_samples, "branches"),
                "branches_per_call": f"{median(exec_samples, 'branches') / args.calls:.3f}",
                "prepare_i1_misses": median(prepare_samples, "i1_misses"),
                "full_i1_misses": median(full_samples, "i1_misses"),
                "prepare_d1_misses": median(prepare_samples, "d1_misses"),
                "full_d1_misses": median(full_samples, "d1_misses"),
                "prepare_mispredicts": median(prepare_samples, "mispredicts"),
                "full_mispredicts": median(full_samples, "mispredicts"),
            })

    by_key = {(r["pattern"], r["mode"]): r for r in rows}
    for row in rows:
        quote = by_key[(row["pattern"], "quote-only")]
        row["net_over_quote_i_refs"] = row["execute_i_refs"] - quote["execute_i_refs"]
        row["net_over_quote_i_refs_per_call"] = (
            f"{row['net_over_quote_i_refs'] / args.calls:.3f}"
        )

    out_dir = Path(args.out) if args.out else ROOT / "benchmarks/d6-evaluator/results"
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with (out_dir / "evaluator.tsv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    env = {
        "schema": "sens-d6-selector-evaluator-replay/v1",
        "issue": "#3583",
        "parent": "#3597 / #1988",
        "runtime": "#3588 / #3394",
        "authority": "#3572 / Contract 11.6; D6 map #3393",
        "git_sha": sh(["git", "rev-parse", "HEAD"]).stdout.strip(),
        "cargo": sh(["cargo", "--version"]).stdout.strip(),
        "rustc": sh(["rustc", "--version"]).stdout.strip(),
        "valgrind": sh(["valgrind", "--version"]).stdout.strip(),
        "python": platform.python_version(),
        "cpu": next(
            (line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines()
             if line.startswith("model name")),
            "unknown",
        ),
        "phase_1_control": "equivalent nested exact D3 CAR/CDR DomainCall chain",
        "flat16_status": "not injected into production evaluator",
    }
    (out_dir / "environment.json").write_text(json.dumps(env, indent=2) + "\n", encoding="utf-8")

    print("real-evaluator parity: PASS")
    for pattern in PATTERNS:
        d6 = by_key[(pattern, "d6")]
        chain = by_key[(pattern, "d3-chain")]
        quote = by_key[(pattern, "quote-only")]
        print(
            f"{pattern:11s} d6={d6['i_refs_per_call']} "
            f"d3-chain={chain['i_refs_per_call']} quote={quote['i_refs_per_call']} "
            f"d6-net={d6['net_over_quote_i_refs_per_call']} "
            f"chain-net={chain['net_over_quote_i_refs_per_call']}"
        )
    print(f"wrote {out_dir / 'evaluator.tsv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
