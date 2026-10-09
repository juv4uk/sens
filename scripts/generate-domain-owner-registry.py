#!/usr/bin/env python3
"""#2958 — generate canonical D3-D9 owner-coordinate projection.

Authority inputs:
- D3/D4: knowledge/exact-width-admitted-corpus.json (widths 3/4 only)
- D5: knowledge/d5-historical-full-map.json (OD-005)
- D6: knowledge/d6-historical-full-map.json (OD-006)
- D7: knowledge/d7-ratified.json (#3572; 126 residents, 2 pinned reservations)\n- D8/D9: dense-width occupancy certificates from #3960/#4008 exact resident maps

The generated Rust intentionally excludes human labels, surfaces and legacy
backend bytes. Those are projections/compatibility metadata, not occupancy
authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "knowledge" / "exact-width-admitted-corpus.json"
D5 = ROOT / "knowledge" / "d5-historical-full-map.json"
D6 = ROOT / "knowledge" / "d6-historical-full-map.json"
D7 = ROOT / "knowledge" / "d7-ratified.json"
D8 = ROOT / "knowledge" / "d8-ratified.json"
D9 = ROOT / "knowledge" / "d9-ratified.json"
OUT = ROOT / "crates" / "sens" / "src" / "domain_owner_generated.rs"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def owner_rows():
    corpus = load_json(CORPUS)
    d5 = load_json(D5)
    d6 = load_json(D6)
    d7 = load_json(D7)
    rows = []

    for row in corpus["rows"]:
        width = row["width"]
        word = row["word"]
        status = row["status"]
        if width == 3 and word != "000" and status == "admitted":
            rows.append((3, word, 0))
        elif width == 4 and status in {"admitted", "generated"}:
            rows.append((4, word, 0))

    if d5["width"] != 5 or d5["capacity"] != 32 or len(d5["coordinates"]) != 32:
        raise SystemExit("OD-005 shape mismatch")
    if d6["width"] != 6 or d6["capacity"] != 64 or len(d6["coordinates"]) != 64:
        raise SystemExit("OD-006 shape mismatch")

    rows.extend((5, row["coordinate"], 1) for row in d5["coordinates"])
    rows.extend((6, row["coordinate"], 2) for row in d6["coordinates"])

    # The D7 authority describes occupancy, not executable primitives.
    # Include only owner-ratified residents; never infer a role from width
    # and never fill the two pinned/reserved cells.
    reserved = {"0100001", "0101010"}
    if (
        d7.get("domain") != "D7"
        or d7.get("authority") != "#3572"
        or d7.get("status") != "owner-ratified"
        or d7.get("width") != 7
        or d7.get("capacity") != 128
        or d7.get("occupancy") != 126
        or set(d7.get("reserved_coordinates", [])) != reserved
        or d7.get("owner_reserved_pinned") != 2
    ):
        raise SystemExit("D7 owner authority or reservations drift")
    d7_words = list(d7.get("residents", {}))
    if (
        len(d7_words) != 126
        or any(len(word) != 7 or set(word) - {"0", "1"} for word in d7_words)
        or set(d7_words) & reserved
        or set(d7_words) | reserved != {f"{n:07b}" for n in range(128)}
    ):
        raise SystemExit("D7 admitted coordinate set drift")
    rows.extend((7, word, 3) for word in d7_words)
    rows.sort(key=lambda row: (row[0], int(row[1], 2)))

    if len(rows) != 243:
        raise SystemExit(f"expected 243 owner coordinates, got {len(rows)}")
    if len({(width, word) for width, word, _ in rows}) != len(rows):
        raise SystemExit("duplicate exact-domain coordinate")

    counts = {width: sum(1 for row in rows if row[0] == width) for width in (3, 4, 5, 6, 7)}
    if counts != {3: 7, 4: 14, 5: 32, 6: 64, 7: 126}:
        raise SystemExit(f"owner count mismatch: {counts}")

    for control in [(4, "1100"), (5, "01010"), (6, "001111")]:
        if not any((width, word) == control for width, word, _ in rows):
            raise SystemExit(f"missing positive control D{control[0]}:{control[1]}")

    return rows



def full_owner_widths():
    """Read dense owner occupancy from ratified sources, not Rust assumptions.

    Residency alone is NOT permission to call a mechanism; D10 is research.
    """
    results = []
    for width, path, authority in ((8, D8, "#3960"), (9, D9, "#4008")):
        data = load_json(path)
        capacity = 1 << width
        positions = data.get("residents", {})
        if not isinstance(positions, dict) or (
            data.get("status") != "owner-ratified"
            or data.get("domain") != f"D{width}"
            or data.get("width") != width
            or data.get("authority") != authority
            or data.get("capacity") != capacity
            or data.get("occupancy") != capacity
            or data.get("distinct_residents") != capacity
            or set(positions) != {f"{n:0{width}b}" for n in range(capacity)}
            or len(set(positions.values())) != capacity
        ):
            raise SystemExit(f"D{width} owner-ratified full-occupancy certificate drift")
        results.append(width)
    return tuple(results)


def render(rows):
    body = "\n".join(
        f"    DomainOwnerCoordinate {{ width: {width}, bits: 0b{word}, source: {source} }},"
        for width, word, source in rows
    )
    # A performance projection only: derive the D3-D7 occupancy bitmap from
    # the exact same owner-coordinate set, never from Rust-authored rules.
    bitmap_rows = []
    for width in (3, 4, 5, 6, 7):
        bits = {int(word, 2) for row_width, word, _ in rows if row_width == width}
        slots = [
            sum(1 << (bit % 64) for bit in bits if bit // 64 == slot)
            for slot in (0, 1)
        ]
        bitmap_rows.append((width, slots))
    bitmaps = "\n".join(
        f"    DomainOwnerBitmap {{ width: {width}, slots: [0x{slots[0]:016x}, 0x{slots[1]:016x}] }},"
        for width, slots in bitmap_rows
    )
    return f"""// @generated by scripts/generate-domain-owner-registry.py; DO NOT EDIT.
//
// Canonical owner occupancy only. Human labels, surfaces and historical
// backend bytes are deliberately excluded from this artifact.

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct DomainOwnerCoordinate {{
    pub(crate) width: u8,
    pub(crate) bits: u8,
    pub(crate) source: u8,
}}

pub(crate) const DOMAIN_OWNER_COORDINATES: &[DomainOwnerCoordinate] = &[
{body}
];

/// Bitset derived mechanically from exactly the above D3-D7 owner rows.
/// No language names, callable laws, or backend/SID8 lookup are encoded.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct DomainOwnerBitmap {{
    pub(crate) width: u8,
    pub(crate) slots: [u64; 2],
}}

pub(crate) const DOMAIN_OWNER_BITMAPS: &[DomainOwnerBitmap] = &[
{bitmaps}
];

/// Widths whose *entire* coordinate set is covered by separately owner-ratified
/// complete maps. Generated from D8 #3960 / D9 #4008 after exhaustive checks.
/// A full-width residency certificate is never a callable mechanism.
pub(crate) const DOMAIN_OWNER_FULL_WIDTHS: &[u8] = &{list(full_owner_widths())};

#[cfg(test)]
mod tests {{
    use super::*;

    #[test]
    fn generated_projection_has_owner_counts_and_controls() {{
        assert_eq!(DOMAIN_OWNER_COORDINATES.len(), 243);
        assert_eq!(DOMAIN_OWNER_COORDINATES.iter().filter(|row| row.width == 3).count(), 7);
        assert_eq!(DOMAIN_OWNER_COORDINATES.iter().filter(|row| row.width == 4).count(), 14);
        assert_eq!(DOMAIN_OWNER_COORDINATES.iter().filter(|row| row.width == 5).count(), 32);
        assert_eq!(DOMAIN_OWNER_COORDINATES.iter().filter(|row| row.width == 6).count(), 64);
        assert_eq!(DOMAIN_OWNER_COORDINATES.iter().filter(|row| row.width == 7).count(), 126);

        for (width, bits) in [(4, 0b1100), (5, 0b01010), (6, 0b001111)] {{
            assert!(DOMAIN_OWNER_COORDINATES
                .iter()
                .any(|row| row.width == width && row.bits == bits));
        }}
    }}

    #[test]
    fn generated_d7_occupancy_excludes_two_pinned_reservations() {{
        for word in 0..128u8 {{
            let admitted = DOMAIN_OWNER_COORDINATES
                .iter()
                .any(|row| row.width == 7 && row.bits == word);
            assert_eq!(admitted, word != 0b0100001 && word != 0b0101010);
        }}
    }}

    #[test]
    fn generated_occupancy_masks_equal_every_explicit_owner_coordinate() {{
        for mask in DOMAIN_OWNER_BITMAPS {{
            for bits in 0u16..(1u16 << mask.width) {{
                let explicit = DOMAIN_OWNER_COORDINATES
                    .iter().any(|row| row.width == mask.width && u16::from(row.bits) == bits);
                let occupied = ((mask.slots[usize::from(bits / 64)] >> (bits % 64)) & 1) != 0;
                assert_eq!(occupied, explicit, "D{{}}:{{}} owner bitmap drift", mask.width, bits);
            }}
        }}
    }}

    #[test]
    fn generated_dense_owner_widths_are_source_certified_not_function_tables() {{
        assert_eq!(DOMAIN_OWNER_FULL_WIDTHS, &[8, 9]);
        assert!(!DOMAIN_OWNER_FULL_WIDTHS.contains(&10));
    }}

    #[test]
    fn generated_projection_has_unique_domain_coordinates() {{
        let mut seen = std::collections::HashSet::new();
        for row in DOMAIN_OWNER_COORDINATES {{
            assert!(seen.insert((row.width, row.bits)));
        }}
    }}
}}
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    expected = render(owner_rows())
    if args.check:
        actual = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if actual != expected:
            raise SystemExit("domain owner generated projection is stale")
        print("domain owner generated projection: PASS")
        return 0

    OUT.write_text(expected, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
