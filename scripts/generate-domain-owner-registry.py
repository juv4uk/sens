#!/usr/bin/env python3
"""Generate the D3-D6 runtime owner projection from canonical domain authority.

Semantic occupancy comes ONLY from:
- D3/D4 exact-width admitted corpus
- OD-005 D5 owner map
- OD-006 D6 owner map

The sparse compatibility projection may attach existing human surfaces and an
optional historical backend byte to an already-existing domain identity. It
must never create occupancy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge/exact-width-admitted-corpus.json"
D5 = ROOT / "knowledge/d5-historical-full-map.json"
D6 = ROOT / "knowledge/d6-historical-full-map.json"
COMPAT = ROOT / "knowledge/domain-legacy-compat-projection.json"
OUTPUT = ROOT / "crates/sens/src/domain_registry_generated.rs"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rust_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def owners():
    corpus = load(CORPUS)
    d5 = load(D5)
    d6 = load(D6)
    rows = []

    for row in corpus["rows"]:
        width = row["width"]
        if width not in (3, 4):
            continue
        if row["status"] not in ("admitted", "generated"):
            continue
        if width == 3 and row["word"] == "000":
            continue
        name = row["human_label_optional"]
        if not name:
            raise SystemExit(f"D{width}:{row['word']} has no owner label")
        rows.append({
            "width": width,
            "coordinate": row["word"],
            "name": name,
            "authority": "exact-width-admitted-corpus",
        })

    for row in d5["coordinates"]:
        rows.append({
            "width": 5,
            "coordinate": row["coordinate"],
            "name": row["name"],
            "authority": "OD-005",
        })

    for row in d6["coordinates"]:
        rows.append({
            "width": 6,
            "coordinate": row["coordinate"],
            "name": row["name"],
            "authority": "OD-006",
        })

    rows.sort(key=lambda row: (row["width"], int(row["coordinate"], 2)))
    counts = {width: sum(row["width"] == width for row in rows) for width in (3, 4, 5, 6)}
    expected = {3: 7, 4: 14, 5: 32, 6: 64}
    if counts != expected or len(rows) != 117:
        raise SystemExit(f"owner occupancy mismatch: counts={counts}, total={len(rows)}")
    if len({(row["width"], row["coordinate"]) for row in rows}) != len(rows):
        raise SystemExit("duplicate exact-domain owner coordinate")
    return rows


def compatibility(owner_rows):
    data = load(COMPAT)
    if data.get("semantic_authority") is not False:
        raise SystemExit("compatibility projection must declare semantic_authority=false")
    owner_by_key = {
        (row["width"], row["coordinate"]): row
        for row in owner_rows
    }
    result = {}
    for row in data["rows"]:
        domain = row["domain"]
        if not domain.startswith("Core.D"):
            raise SystemExit(f"invalid compatibility domain {domain}")
        width = int(domain.removeprefix("Core.D"))
        key = (width, row["coordinate"])
        owner = owner_by_key.get(key)
        if owner is None:
            raise SystemExit(f"compatibility row cannot create residency: {domain}:{row['coordinate']}")
        if row["name"] != owner["name"]:
            raise SystemExit(
                f"compatibility role mismatch at {domain}:{row['coordinate']}: "
                f"{row['name']} != {owner['name']}"
            )
        legacy = row.get("legacy_mechanism")
        if legacy is not None and (len(legacy) != 8 or set(legacy) - {"0", "1"}):
            raise SystemExit(f"invalid legacy backend byte at {domain}:{row['coordinate']}")
        result[key] = row
    return result


def render():
    owner_rows = owners()
    compat = compatibility(owner_rows)
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Occupancy authority:",
        "//   D3/D4: knowledge/exact-width-admitted-corpus.json",
        "//   D5:    knowledge/d5-historical-full-map.json (OD-005)",
        "//   D6:    knowledge/d6-historical-full-map.json (OD-006)",
        "// Compatibility projection:",
        "//   knowledge/domain-legacy-compat-projection.json",
        "// Generator: scripts/generate-domain-owner-registry.py",
        "//",
        "// Legacy surfaces/backend bytes never create residency.",
        "",
        "pub(crate) const DOMAIN_OWNER_ROWS: &[DomainOwnerRow] = &[",
    ]

    for owner in owner_rows:
        key = (owner["width"], owner["coordinate"])
        projection = compat.get(key, {})
        legacy_bits = projection.get("legacy_mechanism")
        legacy = f"Some(0b{legacy_bits})" if legacy_bits else "None"
        surfaces = projection.get("surfaces", [])
        surface_rust = (
            "&[" + ", ".join(rust_string(surface) for surface in surfaces) + "]"
            if surfaces
            else "&[]"
        )
        lines.append(
            "    DomainOwnerRow { "
            f"width: {owner['width']}, "
            f"bits: 0b{owner['coordinate']}, "
            f"name: {rust_string(owner['name'])}, "
            f"authority: {rust_string(owner['authority'])}, "
            f"legacy_mechanism: {legacy}, "
            f"surfaces: {surface_rust} "
            "},"
        )

    lines.extend(["];", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            raise SystemExit(
                "domain owner registry projection is stale; "
                "run scripts/generate-domain-owner-registry.py"
            )
        print("domain owner registry projection is current")
        return

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
