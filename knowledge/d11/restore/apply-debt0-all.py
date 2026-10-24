#!/usr/bin/env python3
"""सूत्रधार: host_debt=0 via live patch (zlib payloads optional, not required)."""
from pathlib import Path
import subprocess, sys

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[3]

r = root()
live = Path(__file__).parent / "patch-host-debt-live.py"
subprocess.check_call([sys.executable, str(live)], cwd=str(r))
