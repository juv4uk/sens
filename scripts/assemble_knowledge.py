#!/usr/bin/env python3
"""Assemble lib/knowledge.lisp from b64 chunks (D1 COND migration)."""
import base64, gzip
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
n = 6
parts = [(HERE / ("kb64_%d.txt" % i)).read_text().strip() for i in range(n)]
text = gzip.decompress(base64.b64decode("".join(parts))).decode("utf-8")
out = ROOT / "lib" / "knowledge.lisp"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(text, encoding="utf-8")
print(len(text), "bytes ->", out)
