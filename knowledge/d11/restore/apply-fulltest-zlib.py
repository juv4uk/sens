#!/usr/bin/env python3
"""Відновити tests/test_domain_function_reuse_rule.py з zlib+b64 (Ануграха)."""
from pathlib import Path
import base64, zlib
root = Path(__file__).resolve().parents[3]
blob = (Path(__file__).parent / "fulltest.zlib.b64").read_text().strip()
out = root / "tests" / "test_domain_function_reuse_rule.py"
out.write_bytes(zlib.decompress(base64.b64decode(blob)))
print("restored", out, out.stat().st_size)
text = out.read_text(encoding="utf-8")
assert "test_staged_reads_index_not_unstaged_worktree" in text
assert "STAGED_DUP" in text
