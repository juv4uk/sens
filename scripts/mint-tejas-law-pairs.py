#!/usr/bin/env python3
"""तेजस्: materialize law pairs from knowledge/d11/restore/tejas/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d3-proper-tail-hot-law', 'compiler-append-proper-law', 'd6-zip-proper-law', 'd3-structural-bench-law', 'd6-union-right-validated-law']

r = root()
src = r / "knowledge" / "d11" / "restore" / "tejas"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sb = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    vb = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sb)
    (sem / stem).write_bytes(vb)
    print("minted", stem, len(sb))
