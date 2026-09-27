#!/usr/bin/env python3
"""CPython steady-execution driver for #1546.

Loads one generated workload module once, then calls its bench() function N
times. N=0 is the matched ready/control path used to subtract process/module
setup from N repeated calls.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        raise SystemExit("usage: cpython_driver.py PROGRAM.py REPEATS")
    path = Path(sys.argv[1])
    repeats = int(sys.argv[2])
    if repeats < 0:
        raise SystemExit("REPEATS must be >= 0")

    namespace = runpy.run_path(str(path), run_name="sens_cross_bench_module")
    bench = namespace["bench"]
    result = None
    for _ in range(repeats):
        result = bench()

    # Keep the result live without adding printing/formatting to the measured path.
    if repeats:
        globals()["_black_box_result"] = result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
