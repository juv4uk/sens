#!/usr/bin/env python3
"""धैर्य: materialize law pairs from knowledge/d11/restore/dhairya/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d10-clips-printout-head-direct-law', 'd10-clips-assert-head-direct-law', 'compiler-append-proper-law', 'compiler-authority-proper-law', 'd10-clips-equal-head-law']

r = root()
src = r / "knowledge" / "d11" / "restore" / "dhairya"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
