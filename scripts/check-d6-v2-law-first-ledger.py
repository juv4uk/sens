#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d6-v2-law-first-ledger.json").read_text(encoding="utf-8"))
rows=d["rows"]
assert d["status"]=="research-not-authority"
assert d["foundation"].startswith("#3331")
assert len(rows)==64
assert {r["coordinate"] for r in rows}=={f"{i:06b}" for i in range(64)}
assert sum(r["status"]=="PROVED" for r in rows)==16
assert sum(r["status"]=="CANDIDATE-WITH-LAW" for r in rows)==16
assert sum(r["status"]=="UNKNOWN" for r in rows)==32
assert len({r["coordinate"] for r in rows if r["status"]!="UNKNOWN"})==32
for name in ["RPLACA","RPLACD","NCONC","NREVERSE","SETF"]:
    assert name in d["review_first"]
print("D6-V2-LAW-FIRST-LEDGER: PASS")
print("proved=16 law-anchored=16 unknown=32")
