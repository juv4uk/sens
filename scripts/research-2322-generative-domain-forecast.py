#!/usr/bin/env python3
"""#2322 generative domain forecast from proved selector laws.

Research-only positive control. The only semantic assumptions are the already
admitted selector facts:
- exact D3 roots 101 (CAR) and 110 (CDR);
- append 0 = compose CAR;
- append 1 = compose CDR;
- the selector law is local to the selector family.

No non-selector coordinate is allocated and the selector law is not generalized.
"""

from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path

ROOTS = ("101", "110")
LAW_BITS = ("0", "1")
MODEL_FACTS = len(ROOTS) + len(LAW_BITS)

EXPECTED_D4 = {"1010", "1011", "1100", "1101"}
EXPECTED_D5 = {
    "10100", "10101", "10110", "10111",
    "11000", "11001", "11010", "11011",
}


def selector_words(width: int) -> list[str]:
    if width < 3:
        raise ValueError("selector roots begin at D3")
    if width == 3:
        return list(ROOTS)
    suffix_width = width - 3
    return sorted(
        root + "".join(bits)
        for root in ROOTS
        for bits in product(LAW_BITS, repeat=suffix_width)
    )


def row_for(width: int) -> dict[str, object]:
    words = selector_words(width)
    capacity = 1 << width
    owned = len(words)
    descendants = 0 if width == 3 else owned
    unexplained = capacity - owned
    ratio = owned / capacity

    assert ratio == 0.25
    assert len(set(words)) == owned
    assert all(len(word) == width for word in words)
    assert all(set(word) <= {"0", "1"} for word in words)

    return {
        "width": width,
        "capacity": capacity,
        "selector_roots": len(ROOTS),
        "generator_laws": len(LAW_BITS),
        "path_depth": width - 3,
        "selector_owned_coordinates": owned,
        "generated_descendants_at_width": descendants,
        "unexplained_coordinates": unexplained,
        "selector_fraction": ratio,
        "model_fact_proxy": MODEL_FACTS,
        "flat_selector_rows_proxy": owned,
        "row_to_model_fact_ratio": owned / MODEL_FACTS,
        "row_equivalent_savings_proxy": max(0, owned - MODEL_FACTS),
    }


def build(min_width: int, max_width: int):
    rows = [row_for(width) for width in range(min_width, max_width + 1)]
    words = {
        f"D{width}": selector_words(width)
        for width in range(min_width, max_width + 1)
    }

    if min_width <= 4 <= max_width:
        assert set(words["D4"]) == EXPECTED_D4
    if min_width <= 5 <= max_width:
        assert set(words["D5"]) == EXPECTED_D5

    for left, right in zip(rows, rows[1:]):
        assert int(right["selector_owned_coordinates"]) == 2 * int(left["selector_owned_coordinates"])
        assert int(right["capacity"]) == 2 * int(left["capacity"])
        assert right["selector_fraction"] == left["selector_fraction"] == 0.25

    return rows, words


def report(rows: list[dict[str, object]]) -> str:
    lines = [
        "# Generative domain forecast — #2322",
        "",
        "Positive control only: CAR/CDR selector roots + two admitted suffix laws.",
        "",
        "| domain | capacity | selector-owned | generated-at-width | unexplained | owned share | flat/model facts | row-equivalent savings |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| D{row['width']} | {row['capacity']:,} | "
            f"{row['selector_owned_coordinates']:,} | "
            f"{row['generated_descendants_at_width']:,} | "
            f"{row['unexplained_coordinates']:,} | "
            f"{float(row['selector_fraction']):.2%} | "
            f"{float(row['row_to_model_fact_ratio']):.2f}x | "
            f"{row['row_equivalent_savings_proxy']:,} |"
        )

    lines += [
        "",
        "Invariant proved by the bounded sweep:",
        "selector_owned(Dn) = 2^(n-2)",
        "capacity(Dn) = 2^n",
        "selector_share = 1/4",
        "",
        "Model-fact proxy for this positive control is constant:",
        "2 roots + 2 suffix laws = 4 independent facts",
        "",
        "This is only a compression/accounting proxy. A real proof-cost ledger",
        "must also count certificates, typing facts, law versions and witnesses.",
        "",
        "NON-CONCLUSIONS:",
        "- unexplained coordinates are not automatically residue functions;",
        "- free coordinates are not invitations to allocate semantics;",
        "- selector laws do not generalize to non-selector roots;",
        "- coordinate generation is not the same as semantic admission.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-width", type=int, default=3)
    ap.add_argument("--max-width", type=int, default=8)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if args.min_width < 3 or args.max_width < args.min_width:
        ap.error("require 3 <= min-width <= max-width")

    rows, words = build(args.min_width, args.max_width)
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
