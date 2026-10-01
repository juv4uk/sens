#!/usr/bin/env python3
"""#1988 harness runner: parity first, then Cachegrind I refs per phase, then the mechanical counters.

    python3 benchmarks/semantic-tree-exec/run.py --out docs/research/1988-selector-exec-bench.tsv [--calls 20000] [--quick]

Cachegrind: `--cache-sim=no`, the same convention as benchmarks/sens-surface/icount.sh. I refs are
deterministic for one binary on one image; absolute numbers from different CPUs / Valgrind images are not
compared (#1987). Preparation (setup) and execution (full - setup) are reported separately; the cost of
building the tree is common to all candidates and is removed by taking the setup of candidate B as the base.
"""
from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRATEGIES = ("A", "B", "C", "D")
DEPTHS = (0, 1, 2, 4, 8, 16)
WORKLOADS = ("repeat", "random")


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def build(tmp: Path):
    plain, counted = tmp / "selector_exec", tmp / "selector_exec_count"
    sh(["gcc", "-O2", "-Wall", "-Wextra", "-o", str(plain), str(HERE / "selector_exec.c")])
    sh(["gcc", "-O2", "-DCOUNT", "-o", str(counted), str(HERE / "selector_exec.c")])
    return plain, counted


def parity(binary: Path, max_k: int) -> list:
    rows = []
    for s in STRATEGIES:
        out = sh([str(binary), s, str(max_k), "0", "repeat", "check"]).stdout.strip()
        rows.append(out)
        if not out.endswith("mismatches=0"):
            raise SystemExit(f"PARITY FAILURE, no timing is meaningful: {out}")
    return rows


def i_refs(binary: Path, s: str, k: int, calls: int, wl: str, mode: str) -> int:
    with tempfile.NamedTemporaryFile("r", suffix=".vg") as log:
        subprocess.run(["valgrind", "--tool=cachegrind", "--cache-sim=no", "--cachegrind-out-file=/dev/null",
                        f"--log-file={log.name}", str(binary), s, str(k), str(calls), wl, mode],
                       check=True, capture_output=True, text=True)
        m = re.search(r"I\s+refs:\s+([\d,]+)", Path(log.name).read_text())
    if not m:
        raise SystemExit("no I refs in the valgrind log")
    return int(m.group(1).replace(",", ""))


def counters(binary: Path, s: str, k: int, calls: int, wl: str) -> dict:
    line = [l for l in sh([str(binary), s, str(k), str(calls), wl, "count"]).stdout.splitlines() if l.startswith("counters")][0]
    return {kv.split("=")[0]: int(kv.split("=")[1]) for kv in line.split("\t")[4:]}


def median_refs(*args, repeats: int) -> int:
    return int(statistics.median(i_refs(*args) for _ in range(repeats)))


def provenance() -> list:
    def first(cmd):
        try:
            return sh(cmd).stdout.splitlines()[0]
        except Exception:
            return "unknown"
    cpu = "unknown"
    try:
        cpu = next(l.split(":", 1)[1].strip() for l in open("/proc/cpuinfo") if l.startswith("model name"))
    except Exception:
        pass
    return [f"# gcc: {first(['gcc', '--version'])}", f"# valgrind: {first(['valgrind', '--version'])}", f"# cpu: {cpu}",
            f"# git: {first(['git', '-C', str(HERE), 'rev-parse', 'HEAD'])} (harness as committed or as in the working tree)"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--calls", type=int, default=20000)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    depths = (0, 2, 8) if a.quick else DEPTHS
    calls = 2000 if a.quick else a.calls
    with tempfile.TemporaryDirectory() as t:
        plain, counted = build(Path(t))
        par = parity(plain, 12)
        out = [*provenance(), *[f"# {p}" for p in par]]
        out.append("\t".join(["strategy", "k", "workload", "calls", "I_setup", "I_setup_minus_B", "I_calls", "I_per_call",
                              "bits_per_call", "gens_per_call", "edges_per_call", "lookups_per_call", "cache_hit_rate",
                              "allocs", "alloc_bytes"]))
        for k in depths:
            for wl in WORKLOADS:
                base = {}
                setup = {s: median_refs(plain, s, k, calls, wl, "setup", repeats=a.repeats) for s in STRATEGIES}
                for s in STRATEGIES:
                    full = median_refs(plain, s, k, calls, wl, "full", repeats=a.repeats)
                    c = counters(counted, s, k, calls, wl)
                    n = calls
                    hits = c["hits"] + c["misses"]
                    out.append("\t".join(map(str, [
                        s, k, wl, calls, setup[s], setup[s] - setup["B"], full - setup[s], round((full - setup[s]) / n, 2),
                        round(c["bits"] / n, 2), round(c["gens"] / n, 2), round(c["edges"] / n, 2), round(c["lookups"] / n, 2),
                        round(c["hits"] / hits, 4) if hits else "", c["allocs"], c["alloc_bytes"]])))
        Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
