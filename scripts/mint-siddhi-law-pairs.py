#!/usr/bin/env python3
"""सिद्धि: materialize law pairs from knowledge/d11/restore/siddhi/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d8-notevery-invalid-root-law', 'd8-notany-invalid-root-law', 'd8-all-not-invalid-root-law', 'd6-maplist-suffix-identity-law', 'unification-constructor-law', 'd6-maplist-preflight-laws']

r = root()
src = r / "knowledge" / "d11" / "restore" / "siddhi"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sb = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    vb = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sb)
    (sem / stem).write_bytes(vb)
    print("minted", stem, len(sb))
