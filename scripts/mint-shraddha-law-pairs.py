#!/usr/bin/env python3
"""श्रद्धा: materialize law pairs from knowledge/d11/restore/shraddha/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d5-d12-zerop-negative-limit-law', 'd5-d12-zerop-promoted-nonzero-law', 'd6-let-letstar-preflight-law', 'd6-intersection-order-law', 'd6-maplist-preflight-laws']

r = root()
src = r / "knowledge" / "d11" / "restore" / "shraddha"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
