#!/usr/bin/env python3
"""Check the D10 v13 source-backed research inventory."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
def check():
    pointer=json.loads((ROOT/'knowledge/d10-current-inventory.json').read_text())
    return pointer['canonical_current']['selected']

if __name__ == '__main__':
    print(check())
