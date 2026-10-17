#!/usr/bin/env python3
"""RESEARCH_NON_GATE: execute one physical T5 input with the bounded µCPU."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from slot_cpu import compile_t5, run, visible


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("physical_sens", type=Path)
    args = parser.parse_args(argv)
    try:
        result = visible(run(compile_t5(args.physical_sens.read_bytes())))
    except (OSError, ValueError) as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
