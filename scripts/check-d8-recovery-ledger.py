#!/usr/bin/env python3
"""Fail-closed consistency check for D8 recovery ledgers.

Research guard only: it synchronizes records; it grants no D8 authority.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "knowledge" / "d8-recovery-candidate-map.json"
APPENDIX = ROOT / "knowledge" / "d8-lisp15-appendix-a-recovery.json"

MANDATORY = {
    "RPLACA", "RPLACD", "ERRORSET", "ERROR", "ERROR1",
    "A-LIST", "APVAL", "CSET", "CSETQ",
    "ATTRIB", "PROP", "GET", "REMPROP", "FLAG", "REMFLAG", "PRINTPROP",
    "ARRAY", "VECTOR",
    "GENSYM", "INTERN", "REMOB", "OBLIST",
    "READ", "PRINT", "PRIN1",
    "TRACE", "UNTRACE", "COUNT", "UNCOUNT", "SPEAK",
    "PROG2", "SELECT",
    "SPECIAL", "UNSPECIAL", "COMMON", "UNCOMMON",
    "CONC", "NCONC", "EFFACE", "MAPCON",
}

def main() -> None:
    candidate_doc = json.loads(CANDIDATES.read_text(encoding="utf-8"))
    appendix_doc = json.loads(APPENDIX.read_text(encoding="utf-8"))

    rows = appendix_doc["rows"]
    names = {name for row in rows for name in row["names"]}

    missing = sorted(MANDATORY - names)
    assert not missing, f"Appendix-A recovery ledger lost mandatory names: {missing}"

    provisional = candidate_doc["provisional_ladder_candidates"]
    coords = [row["ladder_coordinate"] for row in provisional]
    assert len(coords) == len(set(coords)), "duplicate provisional D8 coordinate"

    numeric = [int(coord, 2) for coord in coords]
    assert numeric == sorted(numeric), "candidate map must stay in coordinate order"

    for row in provisional:
        assert row["candidate"] in names, (
            f"provisional candidate missing from historical/recovery ledger: {row['candidate']}"
        )

    ledger_coords = {
        coord
        for row in rows
        if row["classification"] == "D8-RECOVERY-CANDIDATE"
        for coord in row.get("coordinates", [])
    }
    assert set(coords) == ledger_coords, (
        f"candidate-map/Appendix-ledger coordinate drift: "
        f"map={sorted(coords)}, ledger={sorted(ledger_coords)}"
    )

    assert appendix_doc["accounting"]["families"] == len(rows)
    assert candidate_doc["accounting"]["ratified_d8_residents"] == 0
    assert appendix_doc["invariants"][-1] == "Current D8 ratified residents remain zero."

    print(
        "D8 recovery ledger: OK "
        f"({len(rows)} families, {len(provisional)} provisional candidates, 0 ratified)"
    )

if __name__ == "__main__":
    main()
