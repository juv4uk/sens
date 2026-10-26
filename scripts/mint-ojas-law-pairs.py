#!/usr/bin/env python3
"""ओजस्: materialize law pairs from knowledge/d11/restore/ojas/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['time-internet-timestamp-law', 'compiler-authority-proper-law', 'd9-fs-binding-map-strict-law', 'result-status-proper-list-d3-law', 'd6-nth-exact-index-d3-laws']

r = root()
src = r / "knowledge" / "d11" / "restore" / "ojas"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sb = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    vb = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sb)
    (sem / stem).write_bytes(vb)
    print("minted", stem, len(sb))
