#!/usr/bin/env python3
"""#2322/#3281 selector-family positive control under Contract 11.6.

Current semantic authority:
- D3 roots: 011 (CDR), 100 (CAR), authority #3202.
- D4-D6 continue the admitted one-bit selector generator.
- D7 is a separate Sound7/Text7 domain (#3572), so selector ancestry does not
  pass through D7.
- D8 is research (#3281). Its selector candidate set is generated directly
  from current D6 selector residents by appending TWO selector choices at once.

This witness proves coordinate generation only. It does not ratify D8
residency or callability and it never uses Function8/Sens8 history.
"""

from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path

ROOTS = ("011", "100")  # CDR, CAR under #3202
STALE_ROOTS_2934 = ("101", "110")  # donor-only negative control
LAW_BITS = ("0", "1")   # compose CAR / compose CDR selector choice
CURRENT_SELECTOR_MAX_WIDTH = 6
D7_WIDTH = 7
D8_WIDTH = 8

EXPECTED = {
    3: {"011", "100"},
    4: {"0110", "0111", "1000", "1001"},
    5: {
        "01100", "01101", "01110", "01111",
        "10000", "10001", "10010", "10011",
    },
}


def current_selector_words(width: int) -> list[str]:
    """Generate the current D3-D6 selector family only."""
    if not 3 <= width <= CURRENT_SELECTOR_MAX_WIDTH:
        raise ValueError("current selector ladder is defined only for D3-D6")
    suffix_width = width - 3
    return sorted(
        root + "".join(bits)
        for root in ROOTS
        for bits in product(LAW_BITS, repeat=suffix_width)
    )


def d8_selector_candidates_from_d6() -> list[str]:
    """Two-step D6 -> D8 jump; D7 is not a semantic parent."""
    return sorted(
        parent + "".join(bits)
        for parent in current_selector_words(6)
        for bits in product(LAW_BITS, repeat=2)
    )


def d8_direct_root_expansion() -> list[str]:
    """Independent coordinate equality witness, not a D7 semantic chain."""
    return sorted(
        root + "".join(bits)
        for root in ROOTS
        for bits in product(LAW_BITS, repeat=5)
    )


def stale_d8_selector_words_2934() -> list[str]:
    """Historical donor negative control from obsolete roots; never authority."""
    return sorted(
        root + "".join(bits)
        for root in STALE_ROOTS_2934
        for bits in product(LAW_BITS, repeat=5)
    )


def selector_words(width: int) -> list[str]:
    if 3 <= width <= CURRENT_SELECTOR_MAX_WIDTH:
        return current_selector_words(width)
    if width == D7_WIDTH:
        return []
    if width == D8_WIDTH:
        return d8_selector_candidates_from_d6()
    raise ValueError("this bounded witness supports D3-D8 only")


def semantic_status(width: int) -> str:
    if 3 <= width <= 6:
        return "current"
    if width == 7:
        return "foreign-domain-no-selector-admission"
    if width == 8:
        return "research-candidate"
    raise ValueError(width)


def derivation(width: int) -> str:
    if width == 3:
        return "owner-ratified-roots"
    if 4 <= width <= 6:
        return "one-bit-selector-generator"
    if width == 7:
        return "D7-owned-by-Sound7/Text7"
    if width == 8:
        return "D6-plus-two-selector-bits"
    raise ValueError(width)


def row_for(width: int) -> dict[str, object]:
    words = selector_words(width)
    capacity = 1 << width
    owned = len(words)
    return {
        "width": width,
        "capacity": capacity,
        "selector_coordinates": owned,
        "selector_fraction": owned / capacity,
        "semantic_status": semantic_status(width),
        "derivation": derivation(width),
        "unexplained_or_other_domain": capacity - owned,
    }


def build(min_width: int, max_width: int):
    if min_width < 3 or max_width > 8 or max_width < min_width:
        raise ValueError("require 3 <= min-width <= max-width <= 8")

    rows = [row_for(width) for width in range(min_width, max_width + 1)]
    words = {f"D{width}": selector_words(width) for width in range(min_width, max_width + 1)}

    for width, expected in EXPECTED.items():
        if min_width <= width <= max_width:
            assert set(words[f"D{width}"]) == expected

    if min_width <= 6 <= max_width:
        assert len(words["D6"]) == 16

    if min_width <= 7 <= max_width:
        assert words["D7"] == []

    if min_width <= 8 <= max_width:
        d8 = words["D8"]
        assert len(d8) == 64
        assert d8 == d8_direct_root_expansion()
        d6 = set(current_selector_words(6))
        assert all(word[:6] in d6 for word in d8)
        stale = set(stale_d8_selector_words_2934())
        assert len(stale) == 64
        assert set(d8).isdisjoint(stale)

    for width in range(max(4, min_width), min(6, max_width) + 1):
        assert len(words[f"D{width}"]) == 2 * len(words[f"D{width - 1}"])

    return rows, words


def report(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Selector-family authority forecast — #2322 / #3281",
        "",
        "Contract 11.6 boundary: D3-D6 current selector ladder; D7 Sound7/Text7;",
        "D8 research-only two-step candidate generation from D6.",
        "",
        "| domain | capacity | selector coordinates | share | semantic status | derivation |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| D{row['width']} | {row['capacity']:,} | "
            f"{row['selector_coordinates']:,} | "
            f"{float(row['selector_fraction']):.2%} | "
            f"{row['semantic_status']} | {row['derivation']} |"
        )

    lines += [
        "",
        "Proved bounded facts:",
        "- D3-D6 selector counts are 2, 4, 8, 16 under the current roots 011/100.",
        "- D7 contributes zero selector semantic residents; its width is owned by Sound7/Text7.",
        "- D8 has 64 generated selector coordinate candidates from D6 × W2.",
        "- The D8 set equals direct root + five selector bits as a coordinate identity check,",
        "  but no D7 semantic ancestry is used or claimed.",
        "- Historical donor #2934 used obsolete roots 101/110; overlap with the current",
        "  64-coordinate D8 selector candidate set is exactly 0/64.",
        "",
        "NON-CONCLUSIONS:",
        "- the 64 D8 coordinates are not owner-ratified D8 residents;",
        "- the remaining 192 D8 coordinates are not free invitations for allocation;",
        "- W8 capacity does not imply Function8/Sens8 ontology;",
        "- coordinate generation does not imply runtime callability.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-width", type=int, default=3)
    ap.add_argument("--max-width", type=int, default=8)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    try:
        rows, words = build(args.min_width, args.max_width)
    except ValueError as exc:
        ap.error(str(exc))

    text = report(rows)

    if args.out is not None:
        args.out.mkdir(parents=True, exist_ok=True)
        fields = list(rows[0].keys())
        with (args.out / "forecast.tsv").open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=fields,
                delimiter="\t",
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)
        (args.out / "selector-words.json").write_text(
            json.dumps(words, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (args.out / "report.md").write_text(text, encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
