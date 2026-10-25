#!/usr/bin/env python3
"""विन्यास: materialize pairs from per-file b64 under knowledge/d11/restore/vinyasa/."""
from pathlib import Path
import base64, subprocess, sys

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEMS = [
    "d6-filter-independent-law",
    "d6-filter-onto-accumulator-law",
    "d6-d8-zip-swap-interoperability-law",
    "d6-compose-flip-law",
    "d5-selector-derived-law",
]

r = root()
src = r / "knowledge" / "d11" / "restore" / "vinyasa"
sem = r / "tests" / "semantic"
for stem in STEMS:
    sens_b = base64.b64decode((src / f"{stem}.sens.b64").read_text().strip())
    view_b = base64.b64decode((src / f"{stem}.view.b64").read_text().strip())
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
