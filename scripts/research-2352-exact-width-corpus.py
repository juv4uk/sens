#!/usr/bin/env python3
"""#2352 historical pre-bīja3 exact-width corpus donor.

IMPORTANT: the hard-coded D3/D4/D5 model in this file predates the ratified
bīja3 A map (#3202), the later D4 clean-room reset (#3225), and the D5+ selector
collision boundary (#3209). It is retained only to reproduce historical
62-row evidence while #2352 is rewritten from the full owner inputs.

Normal current-authority generation MUST NOT use this script.

This script intentionally does not read lib/surface/semantic-registry.lisp.
That registry remains a compatibility/surface mechanism during the exact-width
migration and must not become authority for the replacement projection.
"""

from __future__ import annotations

import argparse
import csv
import json
from itertools import product
from pathlib import Path
from typing import Any

D1 = {
    "0": ("answer", "admitted", "NO"),
    "1": ("answer", "admitted", "YES"),
}

D2 = {
    "00": ("structure", "admitted", "separator"),
    "01": ("structure", "admitted", "close"),
    "10": ("structure", "admitted", "open"),
    "11": ("structure", "admitted", "dot"),
}

D3 = {
    "000": ("foundation", "admitted", "()"),
    "001": ("foundation", "admitted", "QUOTE"),
    "010": ("foundation", "admitted", "ATOM"),
    "011": ("foundation", "admitted", "COND"),
    "100": ("foundation", "admitted", "CONS"),
    "101": ("selector-root", "admitted", "CAR"),
    "110": ("selector-root", "admitted", "CDR"),
    "111": ("foundation", "admitted", "EQ"),
}

D4 = {
    "0000": ("bootstrap", "admitted", "APPLY"),
    "0001": ("bootstrap", "admitted", "EVAL"),
    "0010": ("bootstrap", "admitted", "LAMBDA"),
    "0011": ("bootstrap", "admitted", "DEFINE"),
    "0100": ("bootstrap", "admitted", "NOT"),
    "0101": ("unallocated", "unallocated", None),
    "0110": ("bootstrap", "admitted", "EVCON"),
    "0111": ("bootstrap", "admitted", "EVLIS"),
    "1000": ("bootstrap", "admitted", "LIST"),
    "1001": ("unallocated", "unallocated", None),
    "1010": ("selector", "generated", "CAAR"),
    "1011": ("selector", "generated", "CADR"),
    "1100": ("selector", "generated", "CDAR"),
    "1101": ("selector", "generated", "CDDR"),
    "1110": ("bootstrap", "admitted", "LOOKUP"),
    "1111": ("bootstrap", "admitted", "BIND"),
}

ROOTS = {
    "101": "A",
    "110": "D",
}


def selector_name(root_letter: str, suffix: str) -> str:
    letters = root_letter + "".join("A" if bit == "0" else "D" for bit in suffix)
    return "C" + letters + "R"


def d5() -> dict[str, tuple[str, str, str | None]]:
    out: dict[str, tuple[str, str, str | None]] = {
        f"{value:05b}": ("unallocated", "unallocated", None)
        for value in range(32)
    }
    for root, root_letter in ROOTS.items():
        for bits in product("01", repeat=2):
            suffix = "".join(bits)
            word = root + suffix
            out[word] = ("selector", "generated", selector_name(root_letter, suffix))
    return dict(sorted(out.items()))


def authority_for(width: int, status: str) -> tuple[str, str | None]:
    if width <= 4:
        if status == "generated":
            return ("#2151/#2170", "#1968/#2329")
        return ("#2151/#2170", None)
    if width == 5 and status == "generated":
        return ("#2175/#2329", "#1968/#2329")
    if width == 5:
        return ("#2175/#2329", None)
    raise AssertionError(width)


def rows() -> list[dict[str, Any]]:
    domains = {1: D1, 2: D2, 3: D3, 4: D4, 5: d5()}
    result: list[dict[str, Any]] = []
    for width, mapping in domains.items():
        assert len(mapping) == 1 << width
        for word in sorted(mapping):
            role, status, label = mapping[word]
            authority_ref, generator_ref = authority_for(width, status)
            result.append({
                "word": word,
                "width": width,
                "role": role,
                "status": status,
                "family": "selector" if role in {"selector", "selector-root"} else role,
                "authority_ref": authority_ref,
                "generator_ref": generator_ref,
                "human_label_optional": label,
            })
    return result


def validate(corpus: list[dict[str, Any]]) -> dict[str, Any]:
    assert len(corpus) == 62
    seen = set()
    for row in corpus:
        key = (row["width"], row["word"])
        assert key not in seen
        seen.add(key)
        assert len(row["word"]) == row["width"]
        assert set(row["word"]) <= {"0", "1"}
        assert row["status"] in {"admitted", "generated", "unallocated"}

    by = {(row["width"], row["word"]): row for row in corpus}
    assert by[(4, "0101")]["status"] == "unallocated"
    assert by[(4, "1001")]["status"] == "unallocated"

    d4_generated = {
        word for (width, word), row in by.items()
        if width == 4 and row["status"] == "generated"
    }
    assert d4_generated == {"1010", "1011", "1100", "1101"}

    d5_generated = {
        word for (width, word), row in by.items()
        if width == 5 and row["status"] == "generated"
    }
    expected_d5 = {
        root + "".join(bits)
        for root in ROOTS
        for bits in product("01", repeat=2)
    }
    assert d5_generated == expected_d5
    assert len(d5_generated) == 8

    counts = {
        status: sum(row["status"] == status for row in corpus)
        for status in ("admitted", "generated", "unallocated")
    }
    assert counts == {"admitted": 24, "generated": 12, "unallocated": 26}

    function_rows = [
        row for row in corpus
        if row["width"] >= 3 and row["status"] != "unallocated"
    ]
    return {
        "schema": "exact-width-admitted-corpus/v1",
        "authority": "projection-only",
        "authority_refs": ["#2151", "#2170", "#2175", "#2329"],
        "forbidden_input": "lib/surface/semantic-registry.lisp",
        "row_count": len(corpus),
        "status_counts": counts,
        "function_like_active_rows": len(function_rows),
        "d4_reserved_holes": ["0101", "1001"],
        "d5_generated_selector_count": len(d5_generated),
        "d5_nonselector_admitted_count": 0,
    }


def write_outputs(out_dir: Path) -> None:
    corpus = rows()
    meta = validate(corpus)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "exact-width-admitted-corpus.json").write_text(
        json.dumps({"meta": meta, "rows": corpus}, indent=2) + "\n",
        encoding="utf-8",
    )

    fields = [
        "word", "width", "role", "status", "family",
        "authority_ref", "generator_ref", "human_label_optional",
    ]
    with (out_dir / "exact-width-admitted-corpus.tsv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in corpus:
            writer.writerow({
                key: ("-" if value is None else value)
                for key, value in row.items()
            })

    (out_dir / "summary.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def check_projection(target_dir: Path) -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        write_outputs(tmp_dir)
        for name in (
            "exact-width-admitted-corpus.json",
            "exact-width-admitted-corpus.tsv",
        ):
            expected = (tmp_dir / name).read_bytes()
            actual_path = target_dir / name
            if not actual_path.exists():
                raise SystemExit(f"missing generated projection: {actual_path}")
            actual = actual_path.read_bytes()
            if actual != expected:
                raise SystemExit(
                    f"stale exact-width corpus projection: {actual_path}; "
                    "run script with --write"
                )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--target-dir", type=Path, default=Path("knowledge"))
    ap.add_argument("--out", type=Path)
    ap.add_argument(
        "--historical-pre-bija3",
        action="store_true",
        help="explicitly reproduce the stale pre-#3202 62-row donor projection",
    )
    args = ap.parse_args()

    if not args.historical_pre_bija3:
        raise SystemExit(
            "refusing stale #2352 projection as current authority: "
            "this generator hard-codes superseded pre-bīja3 / legacy-derived D3/D4/D5 coordinates; "
            "use --historical-pre-bija3 only for provenance reproduction"
        )

    if args.write:
        write_outputs(args.target_dir)
    else:
        check_projection(args.target_dir)

    if args.out is not None:
        write_outputs(args.out)

    meta = validate(rows())
    print(json.dumps(meta, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
