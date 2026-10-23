#!/usr/bin/env python3
"""CI_GLUE_NO_SEMANTICS: real paired Zig/Rust Frame3 Carrier benchmark.
Only exact physical F3C bytes from both executables are compared.
"""
import argparse
import hashlib
import json
import platform
import random
import statistics
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ZIG_EXE = "research/zig-codecs/f3c_bench.zig"
RUST_EXE = "zig_f3c_matched_bench"
CASES = ("quote", "car_cons")


def command(argv):
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"command={argv!r} exit={p.returncode}\n"
                           f"stdout_tail={p.stdout[-3000:]}\nstderr_tail={p.stderr[-3000:]}")
    return p.stdout + "\n" + p.stderr


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(stdout, name):
    out = []
    for line in stdout.splitlines():
        if not line.startswith(name + " "):
            continue
        row = dict(part.split("=", 1) for part in line.split()[1:])
        out.append(row)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pairs", type=int, default=3)
    p.add_argument("--zig-pin", default="0.16.0", choices=("0.16.0",))
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()
    pinned = (ROOT / ".zig-version").read_text(encoding="utf-8").strip()
    if pinned != "0.16.0" or args.zig_pin != pinned:
        raise RuntimeError("Zig pin drift: both repository and benchmark must use 0.16.0")
    if args.pairs < 3:
        raise RuntimeError("need >=3 paired independent process series")
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    meta = {"role": "CI_GLUE_NO_SEMANTICS", "codec": "F3C", "pairs": args.pairs,
            "git_sha": command(["git", "rev-parse", "HEAD"]).strip(),
            "zig_version": command(["zig", "version"]).strip(),
            "rustc": command(["rustc", "-Vv"]).strip(),
            "cpu": platform.processor() or platform.uname().machine,
            "platform": platform.platform(), "seed": 20261014}
    if meta["zig_version"] != args.zig_pin:
        raise RuntimeError(f"zig pin mismatch expected {args.zig_pin}, got {meta['zig_version']}")
    command(["zig", "test", "research/zig-codecs/tests.zig", "-lc"])
    command(["cargo", "build", "--locked", "--release", "-p", "sens",
             "--features", "rust-f3-reference", "--example", RUST_EXE])
    zb = out / "zig_f3c_bench"
    command(["zig", "build-exe", ZIG_EXE, "-O", "ReleaseFast", "-lc",
             f"-femit-bin={zb}"])
    executables = {"zig": zb, "rust": ROOT / "target" / "release" / "examples" / RUST_EXE}
    meta["binary_sha256"] = {k: sha(v) for k, v in executables.items()}
    (out / "environment.json").write_text(json.dumps(meta, indent=2) + "\n")

    rng = random.Random(meta["seed"])
    samples = []
    # Дані з різним числом повторів не можна називати порівнюваними.
    matched_repetitions = defaultdict(dict)
    fixture_count = defaultdict(set)
    with (out / "samples.jsonl").open("w") as handle:
        for pair in range(args.pairs):
            order = ["zig", "rust"]
            rng.shuffle(order)
            phys = defaultdict(dict)
            fixtures = defaultdict(dict)
            for impl in order:
                exe = executables[impl]
                output = command([str(exe)])
                (out / f"pair-{pair}-{impl}.txt").write_text(output)
                for row in rows(output, "physical"):
                    phys[row["case"]][impl] = row["hex"]
                for row in rows(output, "fixture"):
                    fixtures[row["case"]][impl] = (int(row["t5_bytes"]), int(row["f3c_bytes"]))
                    fixture_count[row["case"]].add(impl)
                times = rows(output, "sample")
                if len(times) != len(CASES) * 2 * 11:
                    raise RuntimeError(f"UNINFORMATIVE-OUTPUT pair={pair} impl={impl} "
                                       f"samples={len(times)}")
                for row in times:
                    if row["impl"] != impl or row["case"] not in CASES or row["op"] not in ("encode", "decode"):
                        raise RuntimeError(f"UNINFORMATIVE-OUTPUT {row}")
                    item = {"pair": pair, "impl": impl, "case": row["case"], "op": row["op"],
                            "reps": int(row["reps"]), "elapsed_ns": int(row["elapsed_ns"])}
                    if item["reps"] <= 0 or item["elapsed_ns"] <= 0:
                        raise RuntimeError(f"invalid sample {item}")
                    old_reps = matched_repetitions[(pair, item["case"], item["op"])].get(impl)
                    if old_reps is not None and old_reps != item["reps"]:
                        raise RuntimeError(f"BLOCKED_NO_TIMING inconsistent repetitions {item}")
                    matched_repetitions[(pair, item["case"], item["op"])][impl] = item["reps"]
                    item["ns_per_op"] = item["elapsed_ns"] / item["reps"]
                    samples.append(item)
                    handle.write(json.dumps(item) + "\n")
            for case in CASES:
                for op in ("encode", "decode"):
                    rep_count = matched_repetitions.get((pair, case, op), {})
                    if set(rep_count) != {"zig", "rust"} or rep_count["zig"] != rep_count["rust"]:
                        raise RuntimeError(f"BLOCKED_NO_TIMING unequal repetitions pair={pair} case={case} op={op} reps={rep_count}")
                if phys[case].get("zig") is None or phys[case].get("zig") != phys[case].get("rust"):
                    (out / "STATUS").write_text(f"BLOCKED_NO_TIMING physical mismatch case={case}\n")
                    raise RuntimeError(f"BLOCKED_NO_TIMING physical F3C mismatch {case}")
                if fixtures[case].get("zig") != fixtures[case].get("rust"):
                    raise RuntimeError(f"BLOCKED_NO_TIMING length mismatch {case}")
                if 2 * fixtures[case]["zig"][1] != len(phys[case]["zig"]):
                    raise RuntimeError(f"BLOCKED_NO_TIMING physical hex length {case}")

    grouped = defaultdict(list)
    for s in samples:
        grouped[(s["case"], s["op"], s["impl"])].append(s["ns_per_op"])
    report = ["# Zig ↔ Rust F3C real benchmark", "",
              f"Zig {args.zig_pin} ReleaseFast vs existing Rust --release; F3C byte parity verified.",
              "3+ process-pairs, same runner, 11 samples/op, warmup=5, matched repetitions.",
              "Each sample: quote=24000 operations; car_cons=12000; no independently repeated host runs.",
              "NOT a SENS semantic oracle; research only, 95% K-J CI NOT_MEASURED.", "",
              "| Case | Operation | Zig p50 ns/op | Rust p50 ns/op | Rust/Zig |",
              "|---|---|---:|---:|---:|"]
    for case in CASES:
        for op in ("encode", "decode"):
            zig = grouped[(case, op, "zig")]
            rust = grouped[(case, op, "rust")]
            if len(zig) != 11 * args.pairs or len(rust) != len(zig):
                raise RuntimeError(f"BLOCKED_NO_TIMING missing samples {case}/{op}")
            z, r = statistics.median(zig), statistics.median(rust)
            report.append(f"| {case} | {op} | {z:.1f} | {r:.1f} | {r/z:.3f}× |")
    report.extend(["", "Inputs: fixed Rust golden 4B→3B, 7B→6B. "
                   "Raw samples.jsonl and environment.json contain process/binary evidence.",
                   "No claims about performance for other SENS programs."])
    (out / "summary.md").write_text("\n".join(report) + "\n")
    (out / "STATUS").write_text("F3C_TRANSPORT_PARITY_VERIFIED; TIMING_EXPLORATORY; SEMANTICS_NOT_TESTED\n")
    print("\n".join(report))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"BLOCKED_NO_TIMING: {e}", file=sys.stderr)
        sys.exit(1)
