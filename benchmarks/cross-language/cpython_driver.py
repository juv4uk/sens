#!/usr/bin/env python3
"""Matched CPython phase driver for #1546.

All measured CPython phases use this same process/module path:
- load: read + compile source, do not execute module;
- ready: load + execute module definitions, do not call bench();
- repeat N: ready + call bench() N times.

This mirrors SENS ci_bench load/ready/repeat and avoids phase differences
caused by unrelated imports or different Python entry paths.
"""

from __future__ import annotations

import sys


def load_program(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()
    return compile(source, path, "exec")


def ready_program(path: str):
    code = load_program(path)
    namespace = {"__name__": "sens_cross_bench_module"}
    exec(code, namespace)
    return namespace


def main() -> int:
    if len(sys.argv) not in (3, 4):
        raise SystemExit(
            "usage: cpython_driver.py PROGRAM.py load|ready|repeat [REPEATS]"
        )

    path = sys.argv[1]
    mode = sys.argv[2]

    if mode == "load":
        globals()["_black_box_code"] = load_program(path)
        return 0

    namespace = ready_program(path)
    if mode == "ready":
        globals()["_black_box_namespace"] = namespace
        return 0

    if mode != "repeat" or len(sys.argv) != 4:
        raise SystemExit("repeat mode requires REPEATS")

    repeats = int(sys.argv[3])
    if repeats < 1:
        raise SystemExit("REPEATS must be >= 1")

    bench = namespace["bench"]
    result = None
    for _ in range(repeats):
        result = bench()

    globals()["_black_box_result"] = result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
