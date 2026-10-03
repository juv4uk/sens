#!/usr/bin/env python3
"""#2986 — audit internal law of the owner-ratified Core.D5 32/32 map.

This is a proof/classification tool, not an allocator.
OD-005 coordinates remain authoritative and immutable here.

It checks:
- the owner map is still exactly 32 unique five-bit coordinates;
- every coordinate's recorded D4 prefix matches its first four bits;
- every 4-bit prefix has exactly suffix-0 and suffix-1 children;
- semantic-generator claims are restricted to the proved selector family;
- coordinate-parent-only rows correspond to D4 prefixes that are unallocated
  under current D4 authority #2169;
- full occupancy is not silently promoted into a universal suffix theorem.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

OWNER_MAP = Path("knowledge/d5-historical-full-map.json")
AUDIT_MAP = Path("knowledge/d5-internal-law-audit.json")

EXPECTED_SELECTOR_PAIRS = {
    "1010": ("CAAAR", "CAADR"),
    "1011": ("CADAR", "CADDR"),
    "1100": ("CDAAR", "CDADR"),
    "1101": ("CDDAR", "CDDDR"),
}

ALLOWED_PRIMARY = {
    "SEMANTIC-GENERATOR",
    "LOCAL-SIBLING-LAW",
    "COORDINATE-PARENT-ONLY",
    "HISTORICAL-PAIRING",
    "UNRESOLVED",
}
ALLOWED_RELATION = {
    "SEMANTIC-LAW",
    "COORDINATE-LAW",
    "ACCIDENTAL",
    "UNKNOWN",
}


def fail(message: str) -> None:
    raise SystemExit(f"D5-INTERNAL-LAW-AUDIT=FAIL\n{message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    owner = load(OWNER_MAP)
    audit = load(AUDIT_MAP)

    require(owner.get("domain") == "Core.D5", "owner map domain drift")
    require(owner.get("width") == 5, "owner map width must remain D5")
    require(owner.get("capacity") == 32, "owner map capacity must remain 32")

    rows = owner.get("coordinates", [])
    require(len(rows) == 32, f"owner map occupancy is {len(rows)}, expected 32")

    coordinates = [row["coordinate"] for row in rows]
    require(len(set(coordinates)) == 32, "owner map has duplicate coordinates")
    require(
        set(coordinates) == {format(i, "05b") for i in range(32)},
        "owner map must occupy every exact D5 coordinate once",
    )

    owner_by_prefix: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        coordinate = row["coordinate"]
        require(len(coordinate) == 5 and set(coordinate) <= {"0", "1"}, f"bad coordinate {coordinate}")
        prefix, suffix = coordinate[:4], coordinate[4]
        require(
            row["parent_d4"] == prefix,
            f"{coordinate}: parent_d4={row['parent_d4']} does not match exact prefix {prefix}",
        )
        owner_by_prefix[prefix][suffix] = row

    require(len(owner_by_prefix) == 16, "expected all 16 four-bit prefixes")
    for prefix, children in owner_by_prefix.items():
        require(set(children) == {"0", "1"}, f"{prefix}: missing suffix sibling")

    pairs = audit.get("pairs", [])
    require(len(pairs) == 16, f"audit has {len(pairs)} pairs, expected 16")
    audit_by_prefix = {pair["prefix"]: pair for pair in pairs}
    require(len(audit_by_prefix) == 16, "duplicate audit prefix")
    require(set(audit_by_prefix) == set(owner_by_prefix), "audit prefix coverage differs from owner map")

    d4_residents = audit.get("d4_ratified_residents", {})
    d4_unallocated = set(audit.get("d4_unallocated", []))
    require(set(d4_residents) | d4_unallocated == set(owner_by_prefix), "D4 resident/unallocated partition incomplete")
    require(not (set(d4_residents) & d4_unallocated), "D4 resident/unallocated overlap")

    for prefix, pair in sorted(audit_by_prefix.items()):
        primary = pair["primary_class"]
        relation = pair["relation_class"]
        require(primary in ALLOWED_PRIMARY, f"{prefix}: invalid primary class {primary}")
        require(relation in ALLOWED_RELATION, f"{prefix}: invalid relation class {relation}")

        owner_children = (
            owner_by_prefix[prefix]["0"]["name"],
            owner_by_prefix[prefix]["1"]["name"],
        )
        require(tuple(pair["children"]) == owner_children, f"{prefix}: audit child names drift from owner map")

        if prefix in d4_residents:
            require(pair["parent"] == d4_residents[prefix], f"{prefix}: D4 semantic parent name mismatch")
        else:
            require(pair["parent"] is None, f"{prefix}: unallocated D4 prefix must not be called semantic parent")

        if primary == "SEMANTIC-GENERATOR":
            require(prefix in d4_residents, f"{prefix}: generator lacks semantic D4 parent")
            require(relation == "SEMANTIC-LAW", f"{prefix}: generator must be semantic-law")
            require(pair.get("same_base_object") is True, f"{prefix}: generator must preserve base object")
            require(pair.get("one_delta_axis") is True, f"{prefix}: generator must have one local axis")
            require(bool(pair.get("replay_law")), f"{prefix}: generator missing replay law")
            require(prefix in EXPECTED_SELECTOR_PAIRS, f"{prefix}: unproved non-selector generator claim")
            require(owner_children == EXPECTED_SELECTOR_PAIRS[prefix], f"{prefix}: selector generator mapping drift")

        if primary == "COORDINATE-PARENT-ONLY":
            require(prefix in d4_unallocated, f"{prefix}: coordinate-only class requires absent D4 semantic parent")
            require(relation == "COORDINATE-LAW", f"{prefix}: owner prefix placement is coordinate-law here")
            require(pair.get("replay_law") is None, f"{prefix}: coordinate-only row must not pretend parent replay")

        if primary == "HISTORICAL-PAIRING":
            require(prefix in d4_residents, f"{prefix}: historical pairing unexpectedly lacks D4 resident prefix")
            require(relation == "COORDINATE-LAW", f"{prefix}: historical owner pairing should be coordinate-law")
            require(pair.get("replay_law") is None, f"{prefix}: historical pairing must not claim generator replay")

    classes = Counter(pair["primary_class"] for pair in pairs)
    relations = Counter(pair["relation_class"] for pair in pairs)

    require(classes["SEMANTIC-GENERATOR"] == 4, "selector generator pair count drift")
    require(classes["COORDINATE-PARENT-ONLY"] == 2, "0101/1001 coordinate-parent control count drift")
    require(classes["HISTORICAL-PAIRING"] == 10, "historical-pairing count drift")
    require(classes["LOCAL-SIBLING-LAW"] == 0, "local sibling law promoted without dedicated executable proof")
    require(classes["UNRESOLVED"] == 0, "unexpected unresolved pair in v1 audit")

    generated_children = 2 * classes["SEMANTIC-GENERATOR"]
    semantic_parent_children = 2 * len(d4_residents)
    global_suffix_theorem = classes["SEMANTIC-GENERATOR"] == 16

    print("D5-INTERNAL-LAW-AUDIT=PASS")
    print("D5-OCCUPANCY=32/32")
    print(f"D4-SEMANTIC-PARENT-PREFIXES={len(d4_residents)}/16")
    print(f"D4-SEMANTIC-PARENT-CHILDREN={semantic_parent_children}/32")
    print(f"SEMANTIC-GENERATOR-PAIRS={classes['SEMANTIC-GENERATOR']}")
    print(f"SEMANTIC-GENERATED-CHILDREN={generated_children}/32")
    print(f"COORDINATE-PARENT-ONLY-PAIRS={classes['COORDINATE-PARENT-ONLY']}")
    print(f"HISTORICAL-PAIRING-PAIRS={classes['HISTORICAL-PAIRING']}")
    print(f"LOCAL-SIBLING-LAW-PAIRS={classes['LOCAL-SIBLING-LAW']}")
    print("GLOBAL-D5-SUFFIX-THEOREM=" + ("PROVED" if global_suffix_theorem else "NOT-PROVED"))
    print(f"RELATION-SEMANTIC-LAW={relations['SEMANTIC-LAW']}")
    print(f"RELATION-COORDINATE-LAW={relations['COORDINATE-LAW']}")
    print("OWNER-OCCUPANCY-MUTATION=NONE")
    print("RULE=full-occupancy-does-not-imply-full-generativity")
    print("RULE=prefix-ancestry-does-not-imply-semantic-ancestry")


if __name__ == "__main__":
    main()
