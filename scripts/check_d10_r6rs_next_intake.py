#!/usr/bin/env python3
"""R6RS intake: source-pin and evidence integrity, without forging canonical D10 authority."""
import hashlib
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def data(path):
    return (ROOT / path).read_bytes()
def obj(path):
    return json.loads(data(path))
def sha(payload):
    return hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
def require(ok, reason):
    if not ok:
        raise AssertionError("D10_R6RS_BLOCK: "+reason)
def check():
    m = obj("knowledge/d10-r6rs-next-intake-20261011.json")
    donor = obj(m["source"]["path"])
    require(m["source"]["git_blob"] == sha(data(m["source"]["path"])), "donor pin")
    require(m["source"]["standard"] == donor["source"]["url"], "primary reference")
    require(m["source"]["oracle_script"] == donor["admission"]["independent_donor_oracle"], "oracle source")
    require(m["status"].startswith("RESEARCH-INTAKE") and m["counts"] == {
       "candidates":2,"selected_added":0,"coordinates_added":0,"ratified_added":0}, "authority boundary")
    rows = m["candidates"]
    require(len(rows) == len(donor["rows"]) == 2, "cardinality")
    for row, origin in zip(rows,donor["rows"]):
        require(row["semantic_name"] == origin["historical_name"], "identity drift")
        require(row["observable_law"] == origin["law"], "law drift")
        require(row["positive_witnesses"] == origin["positive_witnesses"] and
                row["falsifiers"] == origin["falsifiers"], "witness drift")
        require(row["F2"].startswith("HOLD") and row["F3"].startswith("HOLD"), "unproven witness/dedup promoted")
        require(row["coordinate"] is None and row["ratified"] is False, "fabricated opcode")
    ptr = obj("knowledge/d10-current-inventory.json")["canonical_current"]
    require(ptr["git_blob"] == sha(data(ptr["path"])), "current inventory mismatch")
    current = obj(ptr["path"])
    existing = {r["semantic_name"].upper():r for r in current["rows"]}
    for row in rows:
        if row["semantic_name"] in existing:
            require(existing[row["semantic_name"]]["behavior"] == row["observable_law"], "name collision with changed semantics")
    print("D10_R6RS_INTAKE PASS sources=2 F2=HOLD F3=HOLD ratified=0")
if __name__ == "__main__":
    check()
