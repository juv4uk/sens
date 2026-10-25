#!/usr/bin/env python3
"""कर्म: materialize 5 T5M law pairs from zlib payload."""
from pathlib import Path
import base64, zlib, subprocess, sys

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

r = root()
payload = r / "knowledge" / "d11" / "restore" / "mint-karma-law-pairs.py.zlib.b64"
if not payload.is_file():
    print("missing", payload, file=sys.stderr)
    sys.exit(1)
body = zlib.decompress(base64.b64decode(payload.read_text().strip()))
exec(compile(body, str(payload), "exec"), {"__name__": "__mint__"})
