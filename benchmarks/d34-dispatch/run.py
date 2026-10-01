#!/usr/bin/env python3
"""#2209 runner: parity first, then Cachegrind I refs and branches per call (setup vs full, net of the empty loop), counters.

    python3 benchmarks/d34-dispatch/run.py --out docs/research/2209-d34-dispatch-bench.tsv [--calls 100000] [--repeats 3]

Cachegrind with `--cache-sim=no --branch-sim=yes` (the #1987 convention plus branches). Absolute I refs of different hosts or
Valgrind images are not compared. Per-call numbers are net of lane N (the call loop that only draws a selector).
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
LANES = {"F": "u8-flat-ready", "P": "d3d4-prefix-ready", "D": "direct-specialized"}
SELECTORS = ["CAR", "CDR", "CAAR", "CADR", "CDAR", "CDDR"]
PREPARED_BYTES = {"F": 256 * 3, "P": 0, "D": 0}          # the flat lane's 256-slot row table; the others have no table


def sh(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def measure(binary, lane, wl, calls, mode):
    with tempfile.NamedTemporaryFile("r", suffix=".vg") as log:
        subprocess.run(["valgrind", "--tool=cachegrind", "--cache-sim=no", "--branch-sim=yes", "--cachegrind-out-file=/dev/null",
                        f"--log-file={log.name}", str(binary), lane, wl, str(calls), mode], check=True, capture_output=True)
        text = Path(log.name).read_text()
    ir = int(re.search(r"I\s+refs:\s+([\d,]+)", text).group(1).replace(",", ""))
    br = int(re.search(r"Branches:\s+([\d,]+)", text).group(1).replace(",", ""))
    mp = int(re.search(r"Mispredicts:\s+([\d,]+)", text).group(1).replace(",", ""))
    return ir, br, mp


def med(f, repeats):
    vals = [f() for _ in range(repeats)]
    return tuple(int(statistics.median(v[i] for v in vals)) for i in range(3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--calls", type=int, default=100000)
    ap.add_argument("--repeats", type=int, default=3)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as t:
        plain, counted = Path(t) / "d34", Path(t) / "d34c"
        sh(["gcc", "-O2", "-Wall", "-Wextra", "-o", str(plain), str(HERE / "d34_dispatch.c")])
        sh(["gcc", "-O2", "-DCOUNT", "-o", str(counted), str(HERE / "d34_dispatch.c")])
        parity = sh([str(plain), "F", "mixed", "0", "check"]).strip()
        if not parity.endswith("mismatches=0"):
            raise SystemExit(f"PARITY FAILURE: {parity}")
        out = [f"# gcc: {sh(['gcc', '--version']).splitlines()[0]}", f"# valgrind: {sh(['valgrind', '--version']).strip()}",
               f"# {parity}", "\t".join(["lane", "workload", "calls", "I_per_call_net", "branches_per_call_net", "mispredicts_per_call_net", "lookups_per_call",
                                         "bits_per_call", "generator_applications_per_call", "prepared_bytes"])]
        for wl in [str(i) for i in range(6)] + ["mixed"]:
            base = {}
            for lane in "N" + "".join(LANES):
                setup = med(lambda: measure(plain, lane, wl, a.calls, "setup"), a.repeats)
                full = med(lambda: measure(plain, lane, wl, a.calls, "full"), a.repeats)
                base[lane] = tuple((full[i] - setup[i]) / a.calls for i in range(3))
            for lane in LANES:
                line = [l for l in sh([str(counted), lane, wl, str(a.calls), "count"]).splitlines() if l.startswith("counters")][0]
                kv = dict(x.split("=") for x in line.split("\t")[3:])
                name = SELECTORS[int(wl)] if wl != "mixed" else "mixed"
                out.append("\t".join(map(str, [LANES[lane], name, a.calls, round(base[lane][0] - base["N"][0], 2),
                                               round(base[lane][1] - base["N"][1], 2), round(base[lane][2] - base["N"][2], 3), int(kv["lookups"]) / a.calls,
                                               int(kv["bits"]) / a.calls, int(kv["gens"]) / a.calls, PREPARED_BYTES[lane]])))
        Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
