#!/usr/bin/env python3
"""Physical-only byte-copy experiment; NOT a SENS semantic oracle."""
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: copy.py CORPUS COPIES", file=sys.stderr)
        return 2
    try:
        copies = int(sys.argv[2])
    except ValueError:
        return 2
    if not 1 <= copies <= 5_000_000:
        return 2
    source = Path(sys.argv[1]).read_bytes()
    if not source or len(source) > 64 * 1024 * 1024:
        return 2
    dest = bytearray(len(source))
    observed = 0
    for i in range(copies):
        # Each round damages the destination: a real new copy must repair it.
        dest[i % len(source)] ^= 1
        dest[:] = source
        observed += dest[i % len(source)]
    if dest != source:
        print("PHYSICAL_COPY_FAIL byte-parity", file=sys.stderr)
        return 1
    print(f"PHYSICAL_COPY\tbytes={len(source)}\tcopies={copies}\tobserved={observed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
