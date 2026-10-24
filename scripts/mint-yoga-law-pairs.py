#!/usr/bin/env python3
"""योग: materialize 6 T5M law pairs; bootstrap from zlib if needed."""
from pathlib import Path
import base64, zlib, subprocess, sys

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

r = root()
payload = r / "knowledge" / "d11" / "restore" / "mint-yoga-law-pairs.py.zlib.b64"
# If this file is the thin wrapper, expand full PAIRS body from payload once.
full = r / "scripts" / ".mint-yoga-law-pairs.full.py"
if payload.is_file():
    body = zlib.decompress(base64.b64decode(payload.read_text().strip()))
    # Execute full mint body in-process
    ns = {"__name__": "__mint__"}
    exec(compile(body, str(payload), "exec"), ns)
else:
    print("missing payload", payload, file=sys.stderr)
    sys.exit(1)
