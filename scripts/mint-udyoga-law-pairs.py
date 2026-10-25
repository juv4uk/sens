#!/usr/bin/env python3
"""उद्योग: materialize law pairs from knowledge/d11/restore/udyoga/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d6-union-proper-law', 'd6-zip-proper-law', 'd6-union-right-validated-law', 'd6-reduce-left-law', 'd4-recursion-benchmark-law']

r = root()
src = r / "knowledge" / "d11" / "restore" / "udyoga"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
