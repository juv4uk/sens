#!/usr/bin/env python3
"""Cross-language recursive-tree baseline plus delivery-cost measurements."""
from __future__ import annotations
import argparse, gzip, hashlib, json, shutil, subprocess, tempfile, time
from pathlib import Path

PROGRAMS = Path(__file__).resolve().parent / "programs"

def tree(depth: int, seed: int) -> int:
    if depth == 0: return seed
    left = tree(depth - 1, seed * 3 + 1)
    right = tree(depth - 1, seed * 3 + 2)
    return left ^ (right + depth)

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=18)
    ap.add_argument("--reps", type=int, default=7)
    ap.add_argument("--warmups", type=int, default=2)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.depth < 1 or args.reps < 3 or args.warmups < 0: raise SystemExit("invalid depth/reps/warmups")
    expected = str(tree(args.depth, 1))
    args.out.mkdir(parents=True, exist_ok=True)
    source = {name: PROGRAMS / f"tree.{ext}" for name, ext in [("c-gcc-o2", "c"), ("rustc-o", "rs"), ("python3", "py"), ("node22", "js")]}
    with tempfile.TemporaryDirectory(prefix="sens-tree-baseline-") as tmp:
        build = Path(tmp)
        compile_specs = {
            "c-gcc-o2": ["gcc", "-O2", "-std=c11", str(source["c-gcc-o2"]), "-o", str(build / "tree-c")],
            "rustc-o": [shutil.which("rustc") or next(iter(sorted(Path("/usr/local/rustup/toolchains").glob("*/bin/rustc"))), "rustc"), "-O", str(source["rustc-o"]), "-o", str(build / "tree-rust")],
        }
        compiled = {}
        for name, command in compile_specs.items():
            t = time.perf_counter_ns(); proc = subprocess.run(command, capture_output=True, text=True, timeout=120); compile_ns = time.perf_counter_ns() - t
            if proc.returncode: raise SystemExit(f"compile failed {name}: {proc.stderr}")
            artifact = Path(command[-1]); compiled[name] = {"compile_wall_ns": compile_ns, "artifact_bytes": artifact.stat().st_size, "artifact_sha256": sha(artifact)}
        commands = {"c-gcc-o2": [str(build / "tree-c")], "rustc-o": [str(build / "tree-rust")], "python3": ["python3", str(source["python3"])], "node22": ["node", str(source["node22"])]}
        rows = []
        for name, base in commands.items():
            command = base + [str(args.depth)]
            for _ in range(args.warmups): subprocess.run(command, capture_output=True, text=True, check=True, timeout=120)
            samples = []
            for _ in range(args.reps):
                t = time.perf_counter_ns(); proc = subprocess.run(command, capture_output=True, text=True, check=True, timeout=120); samples.append(time.perf_counter_ns() - t)
                if proc.stdout.strip() != expected: raise SystemExit(f"parity failed {name}: {proc.stdout!r} != {expected}")
            samples.sort(); row = {"implementation": name, "depth": args.depth, "expected": expected, "parity": True, "samples_ns": samples, "median_ns": samples[len(samples)//2], "p95_ns": samples[min(len(samples)-1, int(len(samples)*.95))], "source_bytes": source[name].stat().st_size, "gzip_source_bytes": len(gzip.compress(source[name].read_bytes(), compresslevel=9))}
            row.update(compiled.get(name, {})); rows.append(row)
    result = {"schema": "sens-cross-language-recursive-tree/v1", "workload": "recursive-tree-checksum", "depth": args.depth, "expected": expected, "implementations": rows, "fairness": ["same recursive algorithm and seed", "parity before timing", "cold process timing", "source/gzip/artifact delivery cost separated"], "scope": "concrete host implementations; not a universal language ranking and not SENS runtime evidence"}
    (args.out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Cross-language recursive-tree baseline", "", f"Workload: recursive checksum, depth `{args.depth}`, expected `{expected}`.", "", "| Implementation | Median cold ns | p95 ns | Source B | gzip B | Compiled artifact B | Compile ns |", "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows: lines.append(f"| {r['implementation']} | {r['median_ns']} | {r['p95_ns']} | {r['source_bytes']} | {r['gzip_source_bytes']} | {r.get('artifact_bytes', 'n/a')} | {r.get('compile_wall_ns', 'n/a')} |")
    lines += ["", "> Delivery size and cold process time are separate axes. These are measurements of concrete toolchains on one host, not a universal language ranking.", ""]
    (args.out / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__": main()
