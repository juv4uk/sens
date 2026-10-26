#!/usr/bin/env python3
"""M1 твердження: materialize selftest pair from knowledge/d11/restore/m1-твердження/."""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEM = "твердження-самотест-law"
r = root()
src = r / "knowledge" / "d11" / "restore" / "m1-твердження"
sem = r / "tests" / "semantic"
sb = base64.b64decode((src / f"{STEM}.sens.b64").read_text().strip())
vb = base64.b64decode(
    (src / f"{STEM}.view.part1.b64").read_text().strip()
    + (src / f"{STEM}.view.part2.b64").read_text().strip()
)
(sem / f"{STEM}.sens").write_bytes(sb)
(sem / STEM).write_bytes(vb)
print("minted", STEM, len(sb), len(vb))
