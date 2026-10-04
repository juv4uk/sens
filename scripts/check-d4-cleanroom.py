#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
d = json.loads((root / "knowledge/d4-cleanroom.json").read_text(encoding="utf-8"))

assert d["authority"] == "#3225"
assert d["admitted"] == {
    "0110": "CDAR",
    "0111": "CDDR",
    "1000": "CAAR",
    "1001": "CADR",
}
assert len(d["unknown"]) == 12
assert set(d["admitted"]).isdisjoint(d["unknown"])
assert set(d["admitted"]) | set(d["unknown"]) == {f"{i:04b}" for i in range(16)}

# Clean-room semantic source must contain none of the legacy D4 resident labels.
text = (root / "knowledge/d4-cleanroom.json").read_text(encoding="utf-8")
for banned in [
    "APPLY","EVAL","LAMBDA","DEFINE","LOOKUP","BIND","EVLIS","EVCON","LIST","NOT",
    "arithmetic-family-A","arithmetic-family-M"
]:
    assert banned not in text, banned

print("D4-CLEANROOM-GUARD: PASS")
