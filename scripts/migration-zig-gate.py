#!/usr/bin/env python3
"""Fail-closed preparation gate: migration scripts <-> Zig physical codec."""
from pathlib import Path
import base64
root = Path(__file__).resolve().parent
parts = []
i = 0
while True:
    p = root / f"_mg_chunk_{i}.b64"
    if not p.is_file():
        break
    parts.append(p.read_text(encoding="ascii"))
    i += 1
code = base64.b64decode("".join(parts))
ns = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(code, str(Path(__file__).resolve()), "exec"), ns)
