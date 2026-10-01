#!/usr/bin/env python3
"""Direct CPython .pyc phase driver for #1546.

This is a cached-code-object lane, intentionally separate from normal import:
- load: validate magic/header and unmarshal the code object;
- ready: load + execute module definitions, no benchmark call;
- repeat N: ready + N calls;
- full: ready + one call + printed result.

The .pyc is generated before measurement by the same pinned CPython.
"""

from __future__ import annotations

import importlib.util
import marshal
import sys
from types import CodeType


PYC_HEADER_BYTES = 16


def load_program(path: str) -> CodeType:
    with open(path, "rb") as handle:
        header = handle.read(PYC_HEADER_BYTES)
        if len(header) != PYC_HEADER_BYTES:
            raise RuntimeError("truncated pyc header")
        if header[:4] != importlib.util.MAGIC_NUMBER:
            raise RuntimeError("pyc magic does not match this CPython")
        code = marshal.load(handle)
    if not isinstance(code, CodeType):
        raise RuntimeError("pyc payload is not a code object")
    return code


def ready_program(path: str):
    code = load_program(path)
    namespace = {"__name__": "sens_cross_bench_module"}
    exec(code, namespace)
    return namespace


def main() -> int:
    if len(sys.argv) not in (3, 4):
        raise SystemExit(
            "usage: cpython_pyc_driver.py PROGRAM.pyc load|ready|repeat|full [REPEATS]"
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

    bench = namespace["bench"]
    if mode == "full":
        result = bench()
        print(result)
        globals()["_black_box_result"] = result
        return 0

    if mode != "repeat" or len(sys.argv) != 4:
        raise SystemExit("repeat mode requires REPEATS")

    repeats = int(sys.argv[3])
    if repeats < 1:
        raise SystemExit("REPEATS must be >= 1")

    result = None
    for _ in range(repeats):
        result = bench()

    globals()["_black_box_result"] = result
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
