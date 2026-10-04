#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d4-cleanroom-full-candidate.json").read_text(encoding="utf-8"))
assert d["authority"]=="superseded-research-evidence"
assert d["superseded_by"]=="#3272"
assert len(d["rows"])==16
assert sum(r["status"]=="hole" for r in d["rows"])==2
print("D4-PRE-RATIFICATION-EVIDENCE: PASS")
