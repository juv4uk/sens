#!/usr/bin/env python3
"""Minimal matched phase driver (ready / repeat / full)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load(path: Path):
    spec = importlib.util.spec_from_file_location("bench_mod", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    path = Path(sys.argv[1])
    mode = sys.argv[2]
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    if mode == "ready":
        mod = load(path)
        assert hasattr(mod, "bench")
        return 0
    if mode == "repeat":
        mod = load(path)
        for _ in range(n):
            mod.bench()
        return 0
    if mode == "full":
        print(load(path).bench())
        return 0
    raise SystemExit(f"unknown mode {mode}")


if __name__ == "__main__":
    raise SystemExit(main())
