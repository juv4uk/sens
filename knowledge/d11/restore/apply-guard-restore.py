#!/usr/bin/env python3
"""Відновити scripts/guard-domain-function-reuse.py з base64-частин (після помилкового placeholder)."""
from pathlib import Path
import base64
root = Path(__file__).resolve().parents[3]
parts = sorted((Path(__file__).parent).glob("guard.part*.b64"))
data = "".join(p.read_text().strip() for p in parts)
out = root / "scripts" / "guard-domain-function-reuse.py"
out.write_bytes(base64.b64decode(data))
print("restored", out, "bytes", out.stat().st_size)
assert "GITHUB_ACTIONS" in out.read_text(encoding="utf-8")
