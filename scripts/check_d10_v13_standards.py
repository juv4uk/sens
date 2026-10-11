#!/usr/bin/env python3
"""Validate 70 archived D10 v13 research proposals; never ratify."""
import csv
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
draft=json.loads((root/"knowledge/d10-standards-draft-laws-v13-20261011.json").read_text())
ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text())
existing=json.loads((root/ptr["canonical_current"]["path"]).read_text())
names={r["semantic_name"].upper() for r in existing["rows"]}
source=root/"knowledge/d10-source-snapshots/d10-v9-unified-catalog-1809.tsv"
with source.open(newline="",encoding="utf-8") as f:
    catalog=list(csv.DictReader(f,delimiter="\t"))
source_names={r["semantic_name"] for r in catalog if r["current_d10_selected"]=="NOT_SELECTED"}
laws=draft["laws"]
if len(laws)!=70 or len(catalog)!=1809:
    raise SystemExit("D10_V13_BLOCKED:catalog count")
for name,data in laws.items():
    if name not in source_names or len(data["law"])<20 or len(data["positive"])<20 or len(data["negative"])<20:
        raise SystemExit("D10_V13_BLOCKED:missing verifiable draft "+name)
if ptr["canonical_current"]["selected"]==827 and any(name in names for name in laws):
    raise SystemExit("D10_V13_BLOCKED:duplicated research name")
print("D10 V13 DRAFT VERIFIED: 70 descriptions, F2/F3 not executed")
