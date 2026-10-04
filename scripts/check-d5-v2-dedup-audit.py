#!/usr/bin/env python3
"""#3304 — D5-V2 lower-domain duplicate audit.

Research-only. This checker never ratifies D5 and never invents replacement
residents. It requires every current D5-V2 shadow row to carry an explicit
dedup decision or UNKNOWN.

Key separation:
- "derivable from D1-D4" is evidence;
- "same semantic identity already owned below D5" is a stronger claim;
- a compact D5 role must state an observable refinement/role distinction;
- Core-Math derivability is not Core-domain duplication (#2508).
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "knowledge/d5-v2-dedup-audit.json"
SHADOW = ROOT / "knowledge/d5-v2-generator-shadow.json"

ALLOWED = {
    "KEEP-DISTINCT",
    "LOWER-DOMAIN-DUPLICATE",
    "DERIVED-BUT-D5-COMPACT-ROLE",
    "UNKNOWN",
}


def fail(message: str) -> None:
    raise SystemExit(f"D5-V2-DEDUP-AUDIT=FAIL\n{message}")


def require(cond: bool, message: str) -> None:
    if not cond:
        fail(message)


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    shadow = json.loads(SHADOW.read_text(encoding="utf-8"))

    require(audit["status"] == "research-not-authority", "audit must stay research-only")
    require(shadow["status"] == "research-shadow-not-authority", "shadow must stay non-authority")

    rows = audit["rows"]
    source = shadow["coordinates"]

    require(len(rows) == 32, f"expected 32 audit rows, got {len(rows)}")
    require(len(source) == 32, f"expected 32 shadow rows, got {len(source)}")

    by_bits = {row["coordinate"]: row for row in rows}
    require(len(by_bits) == 32, "duplicate audit coordinate")

    expected_bits = {f"{i:05b}" for i in range(32)}
    require(set(by_bits) == expected_bits, "audit must cover every 5-bit coordinate exactly once")

    source_by_bits = {row["coordinate"]: row for row in source}
    for bits in sorted(expected_bits):
        row = by_bits[bits]
        src = source_by_bits[bits]

        require(row["candidate"] == src["name"], f"{bits}: candidate drift {row['candidate']} != {src['name']}")
        require(row["decision"] in ALLOWED, f"{bits}: invalid decision {row['decision']}")
        require(bool(row["falsifier"].strip()), f"{bits}: missing falsifier")
        require("observable_same_semantics" in row, f"{bits}: missing semantic differential")
        require("refinement_delta" in row, f"{bits}: missing refinement delta")

        if row["decision"] == "LOWER-DOMAIN-DUPLICATE":
            require(
                row["observable_same_semantics"] == "YES",
                f"{bits}: duplicate requires observable_same_semantics=YES",
            )
            require(
                row["nearest_lower_domain_behavior"] != "UNKNOWN",
                f"{bits}: duplicate must name lower-domain owner/behavior",
            )
            require(row["witness"], f"{bits}: duplicate requires executable witness")

        if row["decision"] == "KEEP-DISTINCT":
            require(
                row["refinement_delta"] not in {"", "UNKNOWN", "UNRESOLVED"},
                f"{bits}: KEEP-DISTINCT requires explicit observable delta",
            )
            require(row["witness"], f"{bits}: KEEP-DISTINCT requires witness")

        if row["decision"] == "DERIVED-BUT-D5-COMPACT-ROLE":
            require(
                row["refinement_delta"] not in {"", "UNKNOWN", "UNRESOLVED"},
                f"{bits}: compact role requires explicit role/delta",
            )

    counts = Counter(row["decision"] for row in rows)

    # Positive controls from current D5-V2 research.
    for bits in ["01100", "01101", "01110", "01111", "10000", "10001", "10010", "10011"]:
        require(by_bits[bits]["decision"] == "KEEP-DISTINCT", f"{bits}: selector control must stay distinct")

    require(by_bits["10101"]["candidate"] == "REVERSE-ONTO", "REVERSE-ONTO control moved")
    require(by_bits["10101"]["decision"] == "KEEP-DISTINCT", "REVERSE-ONTO law control must stay distinct")

    # Historical-derivability attack controls must remain visible until each is
    # independently resolved. A future decision may change UNKNOWN, but may not
    # erase the prior classification/evidence.
    for name in ["EVALQUOTE", "FUNCTION", "LABEL", "PAIRLIS", "SUBST"]:
        row = next(row for row in rows if row["candidate"] == name)
        require(row["prior_classification"] != "UNCLASSIFIED", f"{name}: missing prior derivability evidence")
        require(row["prior_evidence"], f"{name}: missing prior evidence refs")

    print("D5-V2-DEDUP-AUDIT=PASS")
    print(f"rows={len(rows)}")
    for key in sorted(ALLOWED):
        print(f"{key.lower()}={counts[key]}")
    print("owner-ready=" + ("YES" if counts["UNKNOWN"] == 0 else "NO"))
    if counts["UNKNOWN"]:
        unknown = [row["candidate"] for row in rows if row["decision"] == "UNKNOWN"]
        print("unknown=" + ",".join(unknown))


if __name__ == "__main__":
    main()
