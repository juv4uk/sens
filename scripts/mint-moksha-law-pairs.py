#!/usr/bin/env python3
"""मोक्ष: materialize law pairs from knowledge/d11/restore/moksha/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = ['d6-all-invalid-root-law', 'd6-any-invalid-root-law', 'd6-d12-ratio-normalizes-integer-law', 'd4-append-general-proper-law', 'd6-d12-integer-rational-law', 'd6-let-letstar-preflight-law', 'compiler-reverse-onto-proper-law', 'd6-intersection-order-law']

r = root()
src = r / "knowledge" / "d11" / "restore" / "moksha"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
