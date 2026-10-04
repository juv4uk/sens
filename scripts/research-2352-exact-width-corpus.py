#!/usr/bin/env python3
"""Current admitted exact-width D1-D4 projection.

Authority:
- #3202 owns current D3/bīja3 A;
- #3272 owns current dense D4 16/16;
- #3278 explicitly revokes current semantic admission for D5/D6/D8.

This projection therefore stops at D4. Exact W5/W6/W8 carriers remain
mechanically representable elsewhere, but carrier existence is not semantic
admission. D5+ selector continuation is fail-closed pending #3209.

The compatibility surface registry is intentionally not an authority input.
"""

from __future__ import annotations

import argparse
import csv
import json
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
    "011": ("selector-root", "admitted", "CDR"),
    "100": ("selector-root", "admitted", "CAR"),
    "101": ("foundation", "admitted", "EQ"),
    "110": ("foundation", "admitted", "COND"),
    "111": ("foundation", "admitted", "CONS"),
}

D4 = {
    "0000": ("bootstrap", "admitted", "APPLY"),
    "0001": ("bootstrap", "admitted", "EVAL"),
    "0010": ("bootstrap", "admitted", "LAMBDA"),
    "0011": ("bootstrap", "admitted", "DEFINE"),
    "0100": ("bootstrap", "admitted", "NOT"),
    "0101": ("bootstrap", "admitted", "NULL"),
    "0110": ("selector", "generated", "CDAR"),
    "0111": ("selector", "generated", "CDDR"),
    "1000": ("selector", "generated", "CAAR"),
    "1001": ("selector", "generated", "CADR"),
    "1010": ("bootstrap", "admitted", "LOOKUP"),
    "1011": ("bootstrap", "admitted", "BIND"),
    "1100": ("bootstrap", "admitted", "EVCON"),
    "1101": ("bootstrap", "admitted", "EVLIS"),
    "1110": ("bootstrap", "admitted", "LIST"),
    "1111": ("bootstrap", "admitted", "APPEND"),
}

def rows() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for width, mapping, authority, generator in (
        (1, D1, "#2151", None),
        (2, D2, "#2151", None),
        (3, D3, "#3202", None),
        (4, D4, "#3272", "#2055/#3272"),
    ):
        assert len(mapping) == 1 << width
        for word in sorted(mapping):
            role, status, label = mapping[word]
            result.append({
                "word": word,
                "width": width,
                "role": role,
                "status": status,
                "family": "selector" if role in {"selector", "selector-root"} else role,
                "authority_ref": authority,
                "generator_ref": generator if status == "generated" else None,
                "human_label_optional": label,
            })
    return result

def validate(corpus: list[dict[str, Any]]) -> dict[str, Any]:
    assert len(corpus) == 30
    seen = set()
    for row in corpus:
        key = (row["width"], row["word"])
        assert key not in seen
        seen.add(key)
        assert len(row["word"]) == row["width"]
        assert set(row["word"]) <= {"0", "1"}
        assert row["status"] in {"admitted", "generated"}

    by = {(row["width"], row["word"]): row for row in corpus}
    expected_d3 = {
        "000": "()", "001": "QUOTE", "010": "ATOM", "011": "CDR",
        "100": "CAR", "101": "EQ", "110": "COND", "111": "CONS",
    }
    expected_d4 = {
        "0000": "APPLY", "0001": "EVAL", "0010": "LAMBDA", "0011": "DEFINE",
        "0100": "NOT", "0101": "NULL", "0110": "CDAR", "0111": "CDDR",
        "1000": "CAAR", "1001": "CADR", "1010": "LOOKUP", "1011": "BIND",
        "1100": "EVCON", "1101": "EVLIS", "1110": "LIST", "1111": "APPEND",
    }
    for word, name in expected_d3.items():
        assert by[(3, word)]["human_label_optional"] == name
    for word, name in expected_d4.items():
        assert by[(4, word)]["human_label_optional"] == name

    d4_generated = {
        word for (width, word), row in by.items()
        if width == 4 and row["status"] == "generated"
    }
    assert d4_generated == {"0110", "0111", "1000", "1001"}

    counts = {
        status: sum(row["status"] == status for row in corpus)
        for status in ("admitted", "generated")
    }
    assert counts == {"admitted": 26, "generated": 4}

    return {
        "schema": "exact-width-admitted-corpus/v2",
        "authority": "projection-only",
        "authority_refs": ["#2151", "#3202", "#3272", "#3278"],
        "forbidden_input": "lib/surface/semantic-registry.lisp",
        "row_count": len(corpus),
        "status_counts": counts,
        "function_like_active_rows": sum(row["width"] >= 3 for row in corpus),
        "current_semantic_widths": [1, 2, 3, 4, 7],
        "d4_generated_selector_count": len(d4_generated),
        "d5_plus_semantic_admission": "revoked/research by #3278",
        "selector_generation_above_d4": "fail-closed pending #3209",
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
            writer.writerow({key: ("-" if value is None else value) for key, value in row.items()})
    (out_dir / "summary.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

def check_projection(target_dir: Path) -> None:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        write_outputs(tmp_dir)
        for name in ("exact-width-admitted-corpus.json", "exact-width-admitted-corpus.tsv"):
            expected = (tmp_dir / name).read_bytes()
            actual_path = target_dir / name
            if not actual_path.exists():
                raise SystemExit(f"missing generated projection: {actual_path}")
            if actual_path.read_bytes() != expected:
                raise SystemExit(f"stale exact-width corpus projection: {actual_path}; run script with --write")

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--target-dir", type=Path, default=Path("knowledge"))
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.write:
        write_outputs(args.target_dir)
    else:
        check_projection(args.target_dir)
    if args.out is not None:
        write_outputs(args.out)
    print(json.dumps(validate(rows()), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
