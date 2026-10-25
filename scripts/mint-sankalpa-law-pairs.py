#!/usr/bin/env python3
"""संकल्प: materialize law pairs from knowledge/d11/restore/sankalpa/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d6-maplist-suffix-identity-law', 'd6-length-onto-d3-boundary-law', 'd6-nth-exact-index-d3-laws', 'd6-map-onto-accumulator-law', 'd4-recursion-atom-result-law']

r = root()
src = r / "knowledge" / "d11" / "restore" / "sankalpa"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
