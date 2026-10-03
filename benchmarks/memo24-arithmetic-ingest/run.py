#!/usr/bin/env python3
"""Validate #2715 Memo 24 vs 1962 arithmetic chronology sidecar."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "research" / "2715-memo24-arithmetic-comparison.json"
LATER = ROOT / "docs" / "research" / "2709-lisp15-arithmetic-ledger.json"

def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    later = json.loads(LATER.read_text(encoding="utf-8"))
    rows = data["rows"]
    assert data["phase"] == "HISTORICAL-INGEST"
    assert len(rows) == data["counts"]["rows"] == len(later["rows"]) == 26
    assert [r["historical_name"] for r in rows] == [r["historical_name"] for r in later["rows"]]
    assert data["counts"] == {
        "rows": 26, "attested": 21, "not_attested": 5, "unresolved_presence": 0,
        "same": 15, "changed": 4, "extended": 5, "unresolved_relation": 2,
    }
    assert all(r["current_domain_candidate"] == "unresolved" for r in rows)
    assert all(r["binary_object"] == "UNPLACED" for r in rows)

    by = {r["historical_name"]: r for r in rows}
    for name in ("QUOTIENT","REMAINDER","DIVIDE","EXPT","LEFTSHIFT"):
        assert by[name]["memo24_presence"] == "NOT-ATTESTED-IN-MEMO24"
        assert by[name]["manual1962_relation"] == "EXTENDED"
    assert by["LESSP"]["memo24_behavior"] == "true if x <= y; false otherwise"
    assert by["GREATERP"]["memo24_behavior"] == "true if x >= y"
    assert by["ONEP"]["memo24_behavior"] == "true if x=1"
    assert "exactly equal" in by["EQUAL"]["memo24_behavior"]
    assert by["ZEROP"]["manual1962_relation"] == "UNRESOLVED"
    assert by["FLOATP"]["manual1962_relation"] == "UNRESOLVED"
    assert "fixed-point number is defined as zero" in by["RECIP"]["memo24_behavior"]
    assert "-0" in by["MINUSP"]["memo24_behavior"]
    print("MEMO24-ARITHMETIC-CHRONOLOGY=PASS")
    print("ROWS=26")
    print("ATTESTED=21")
    print("NOT-ATTESTED=5")
    print("SAME=15 CHANGED=4 EXTENDED=5 UNRESOLVED=2")
    print("ALL-BINARY-OBJECTS=UNPLACED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
