#!/usr/bin/env python3
"""Wall-clock throughput for agent-message CPython forms (no Cachegrind).

Long-lived session: decode or decode+execute N messages (same generator as run.py).

  python3 benchmarks/agent-messages/wall_throughput.py [--n 1000] [--reps 7] [--seed 1]

Reports median seconds, µs/msg, msg/s. Does not measure SENS (needs agent_bench).
Compare only within CPython forms; do not mix with Cachegrind I-refs.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import marshal
import random
import statistics
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--reps", type=int, default=7)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument(
        "--out",
        type=Path,
        default=HERE / "results" / "wall-throughput",
    )
    args = ap.parse_args()
    am = load("am_run", HERE / "run.py")
    pa = load("am_py", HERE / "py_agent.py")

    rng = random.Random(args.seed)
    messages = [am.gen_message(rng, i) for i in range(args.n)]
    payloads = {
        "py-src": [am.python(m).encode() for m in messages],
        "py-json": [
            json.dumps(am.json_ast(m), separators=(",", ":")).encode() for m in messages
        ],
        "py-marshal": [
            marshal.dumps(compile(am.python(m), "<m>", "exec")) for m in messages
        ],
    }

    def run_decode(form: str, blobs: list[bytes]) -> float:
        t0 = time.perf_counter()
        for message in blobs:
            if form == "py-src":
                compile(message.decode(), "<m>", "exec")
            elif form == "py-marshal":
                marshal.loads(message)
            else:
                json.loads(message)
        return time.perf_counter() - t0

    def run_full(form: str, blobs: list[bytes]) -> float:
        ns: dict = {}
        defs: dict = {}
        t0 = time.perf_counter()
        for message in blobs:
            if form == "py-src":
                exec(compile(message, "<m>", "exec"), ns)
            elif form == "py-marshal":
                exec(marshal.loads(message), ns)
            else:
                pa.json_eval(json.loads(message), {}, defs)
        return time.perf_counter() - t0

    rows = []
    for form, blobs in payloads.items():
        for mode, fn in (("decode", run_decode), ("full", run_full)):
            samples = [fn(form, blobs) for _ in range(args.reps)]
            med = statistics.median(samples)
            rows.append(
                {
                    "form": form,
                    "mode": mode,
                    "n": args.n,
                    "seed": args.seed,
                    "reps": args.reps,
                    "median_s": f"{med:.6f}",
                    "us_per_msg": f"{(med / args.n) * 1e6:.3f}",
                    "msg_per_s": f"{args.n / med:.1f}",
                    "metric": "wall_clock",
                    "host_note": "connector-sandbox-python",
                }
            )
            print(
                f"{form:12} {mode:6} median_s={med:.4f} "
                f"us/msg={(med/args.n)*1e6:.1f} msg/s={args.n/med:.0f}"
            )

    args.out.mkdir(parents=True, exist_ok=True)
    tsv = args.out / "wall_throughput.tsv"
    with tsv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
