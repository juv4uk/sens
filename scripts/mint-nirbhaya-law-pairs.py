#!/usr/bin/env python3
"""निर्भय: materialize law pairs from knowledge/d11/restore/nirbhaya/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d9-f6-object-addresses-law', 'd9-fs-binding-map-strict-law', 'result-status-d7-label-law', 'd5-member-total-list-law', 'd5-assoc-total-list-law']

r = root()
src = r / "knowledge" / "d11" / "restore" / "nirbhaya"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
