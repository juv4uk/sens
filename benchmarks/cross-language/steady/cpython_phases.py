#!/usr/bin/env python3
"""Matched CPython phase driver: load / ready / repeat / full.

ready  = compile + bind bench, zero calls
repeat = ready path + N calls of bench()
full   = fresh process: import + one call (approx one-shot)

Used so (repeat − ready) / N isolates steady execution cost.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("bench_mod", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("program", type=Path, help="Python file defining bench()")
    ap.add_argument(
        "mode",
        choices=("load", "ready", "repeat", "full"),
    )
    ap.add_argument("n", nargs="?", type=int, default=1, help="calls for repeat")
    ap.add_argument("--print-result", action="store_true")
    args = ap.parse_args()

    if args.mode == "load":
        source = args.program.read_text(encoding="utf-8")
        compile(source, str(args.program), "exec")
        return 0

    if args.mode == "ready":
        mod = load_module(args.program)
        if not hasattr(mod, "bench"):
            raise SystemExit("module must define bench()")
        return 0

    if args.mode == "repeat":
        if args.n < 1:
            raise SystemExit("n must be >= 1")
        mod = load_module(args.program)
        result = None
        for _ in range(args.n):
            result = mod.bench()
        if args.print_result:
            print(result)
        return 0

    mod = load_module(args.program)
    result = mod.bench()
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
