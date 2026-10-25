#!/usr/bin/env python3
"""विन्यास/अग्नि: materialize pairs from per-file b64 under knowledge/d11/restore/vinyasa/."""
from pathlib import Path
import base64, subprocess, sys

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

def load_b64(src: Path, stem: str, kind: str) -> bytes:
    whole = src / f"{stem}.{kind}.b64"
    if whole.is_file():
        return base64.b64decode(whole.read_text().strip())
    p1 = src / f"{stem}.{kind}.b64.part1"
    p2 = src / f"{stem}.{kind}.b64.part2"
    if p1.is_file() and p2.is_file():
        return base64.b64decode(p1.read_text().strip() + p2.read_text().strip())
    raise FileNotFoundError(f"missing {kind} b64 for {stem}")

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
    sens_b = load_b64(src, stem, "sens")
    view_b = load_b64(src, stem, "view")
    (sem / f"{stem}.sens").write_bytes(sens_b)
    (sem / stem).write_bytes(view_b)
    print("minted", stem, len(sens_b))
