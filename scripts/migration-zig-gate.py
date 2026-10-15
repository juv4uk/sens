#!/usr/bin/env python3
"""Fail-closed preparation gate: migration scripts ↔ Zig physical codec."""
from pathlib import Path
import base64
root = Path(__file__).resolve().parent
a = (root / "_migration_zig_gate_body_a.b64").read_text(encoding="ascii")
b = (root / "_migration_zig_gate_body_b.b64").read_text(encoding="ascii")
code = base64.b64decode(a + b)
ns = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(code, str(Path(__file__).resolve()), "exec"), ns)
