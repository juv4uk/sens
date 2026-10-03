#!/usr/bin/env python3
"""Validate #2709 LISP 1.5 arithmetic historical-ingest sidecar."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "research" / "2709-lisp15-arithmetic-ledger.json"

def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = data["rows"]
    assert data["phase"] == "HISTORICAL-INGEST"
    assert data["counts"]["rows"] == 26 == len(rows)
    assert "printed pp.25-27" in data["source"]["citation"]
    assert "Appendix A printed pp.63-64" in data["source"]["citation"]
    names = [r["historical_name"] for r in rows]
    assert len(set(names)) == 26
    assert all(r["historical_presence"] == "yes" for r in rows)
    assert all(r["current_domain_candidate"] == "unresolved" for r in rows)
    assert all(r["binary_object"] == "UNPLACED" for r in rows)
    assert all(r["later_SENS_status"] == "not-yet-analyzed" for r in rows)
    assert all("D5" not in r["binary_object"] and "D6" not in r["binary_object"] for r in rows)

    categories = {}
    for row in rows:
        categories[row["category"]] = categories.get(row["category"], 0) + 1
    assert categories == {"arithmetic": 13, "numeric-predicate": 9, "logical-word": 4}

    by_name = {r["historical_name"]: r for r in rows}
    assert "fixed-point reciprocal is defined as zero" in by_name["RECIP"]["historical_behavior"]
    assert by_name["RECIP"]["relation_to_core_math"] == "comparison-only-no-shared-identity"
    assert by_name["DIVIDE"]["historical_result"] == "proper two-element list [quotient,remainder]"
    assert by_name["QUOTIENT"]["historical_behavior"] == "quotient of x and y"
    assert by_name["MINUSP"]["negative_zero"] is True
    assert by_name["ZEROP"]["tolerance_relation"] == "<="
    assert by_name["ZEROP"]["tolerance_value"] == "3e-6"
    assert by_name["ONEP"]["tolerance_relation"] == "<="
    assert by_name["ONEP"]["tolerance_value"] == "3e-6"
    assert by_name["EQUAL"]["tolerance_relation"] == "<"
    assert by_name["EQUAL"]["tolerance_value"] == "3e-6"
    assert "non-number input errors" in by_name["FLOATP"]["partiality"]
    assert all("36-bit" in by_name[n]["historical_numeric_domain"] for n in ("LOGOR","LOGAND","LOGXOR","LEFTSHIFT"))
    assert by_name["ZEROP"]["tolerance_relation"] == "<="
    assert by_name["ZEROP"]["tolerance_value"] == "3e-6"
    assert by_name["ONEP"]["tolerance_relation"] == "<="
    assert by_name["ONEP"]["tolerance_value"] == "3e-6"
    assert by_name["EQUAL"]["tolerance_relation"] == "<"
    assert by_name["EQUAL"]["tolerance_value"] == "3e-6"
    assert by_name["MINUSP"]["negative_zero"] is True

    print("LISP15-ARITHMETIC-INGEST=PASS")
    print("ROWS=26")
    print("ARITHMETIC=13")
    print("NUMERIC-PREDICATES=9")
    print("LOGICAL-WORD=4")
    print("ALL-BINARY-OBJECTS=UNPLACED")
    print("RECIP-HISTORICAL-FIXED=0")
    print("SHARED-NAME-DOES-NOT-IMPLY-SHARED-LAW=PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
