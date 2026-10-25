#!/usr/bin/env python3
"""निष्ठा: materialize law pairs from knowledge/d11/restore/nistha/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d8-all-not-invalid-root-law', 'd8-notany-invalid-root-law', 'd8-notevery-invalid-root-law', 'd6-zip-structural-order-law', 'd6-scan-tail-state-law']

r = root()
src = r / "knowledge" / "d11" / "restore" / "nistha"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
