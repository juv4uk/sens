#!/usr/bin/env python3
from pathlib import Path
import base64
root = Path(__file__).resolve().parents[3]
parts = sorted((Path(__file__).parent).glob("debt0.part*.b64"))
data = "".join(p.read_text().strip() for p in parts)
out = root / "tests" / "test_domain_function_reuse_rule.py"
out.write_bytes(base64.b64decode(data))
print("restored", out, out.stat().st_size)
assert "DomainFunctionReuseRule" in out.read_text(encoding="utf-8")
assert "STAGED_DUP" in out.read_text(encoding="utf-8")
