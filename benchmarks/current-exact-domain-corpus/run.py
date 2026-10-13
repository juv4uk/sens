#!/usr/bin/env python3
"""Current D1–D7 exact-width coordinate report, including D7 keyboard/v2 data.

D7 v1 phonetic occupancy (126/128) is historical, NOT a runtime or test source.
D7 W7 values are text data, never function names or arithmetic numbers.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D1_D6 = ROOT / "knowledge/d1-d6-foundation.json"
MAPS = {
    "D4": ROOT / "knowledge/d4-cleanroom.json",
    "D5": ROOT / "knowledge/d5-ratified.json",
    "D6": ROOT / "knowledge/d6-ratified.json",
}
D7 = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
CURRENT_DOMAINS = [f"D{i}" for i in range(1, 8)]
SOURCE_BY_DOMAIN = {
    "D1": "knowledge/d1-d6-foundation.json",
    "D2": "knowledge/d1-d6-foundation.json",
    "D3": "knowledge/d1-d6-foundation.json",
    "D4": "knowledge/d4-cleanroom.json",
    "D5": "knowledge/d5-ratified.json",
    "D6": "knowledge/d6-ratified.json",
    "D7": "knowledge/d7-keyboard-v2-ratified.json",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_report() -> dict:
    foundation = load(D1_D6)
    maps = {domain: load(path) for domain, path in MAPS.items()}
    d7 = load(D7)
    require(
        (d7.get("schema"), d7.get("status"), d7.get("width"),
         d7.get("capacity"), d7.get("occupancy")) ==
        ("sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128),
        "current owner D7 v2 authority mismatch",
    )
    require(
        [r["bits"] for r in d7["table"]] == [f"{i:07b}" for i in range(128)],
        "current W7 coordinate mismatch",
    )
    for key in ("ascii", "uk", "san"):
        glyphs = [r[key] for r in d7["table"]]
        require(len(set(glyphs)) == 128 and all(len(g) == 1 for g in glyphs),
                f"D7 {key} projection is not bijective")
    rows = []
    for width in range(1, 8):
        domain = f"D{width}"
        if width <= 3:
            residents = foundation["domains"][domain]["residents"]
            authority = foundation["domains"][domain]["authority"]
        elif width <= 6:
            residents = maps[domain]["residents"]
            authority = maps[domain]["authority"]
        else:
            residents = None
            authority = "2026-10-13 D7 keyboard/v2"
        for index in range(1 << width):
            bits = f"{index:0{width}b}"
            if width != 7:
                require(bits in residents, f"missing {domain}:{bits}")
            rows.append({
                "domain": domain,
                "width": width,
                "word": bits,
                "status": "admitted",
                "role": None if width == 7 else residents[bits],
                "authority_ref": authority,
                "normative_source": SOURCE_BY_DOMAIN[domain],
                "mechanism_status": "text-data-only" if width == 7 else "separate-not-projected",
            })
    require(len(rows) == 254, "D1–D7 coordinate count drift")
    return {
        "schema": "current-exact-domain-corpus/v2",
        "status": "CURRENT-AUTHORITY-PROJECTION",
        "contract": "11.9",
        "identity_rule": "exact bits + exact domain + admitted/proved law",
        "generated_from": [*map(str, SOURCE_BY_DOMAIN.values())],
        "accounting": {
            "current_domains": CURRENT_DOMAINS,
            "research_domains": [],
            "coordinate_rows": 254,
            "admitted_residents": 254,
            "owner_reserved_pinned": 0,
            "d8_rows": 0,
        },
        "rows": rows,
        "non_conclusions": [
            "This report is an exact-width projection, not new semantic authority.",
            "D7 keyboard data is not a function or an arithmetic number.",
            "All 128 current D7 W7 data coordinates are admitted; no historical v1 reservations.",
            "D8–D10 are beyond the scope of this D1–D7 report.",
        ],
    }


FIELDS = (
    "domain", "width", "word", "status", "role",
    "authority_ref", "normative_source", "mechanism_status",
)


def render_tsv(report: dict) -> str:
    def cell(value) -> str:
        if value is None:
            return ""
        return str(value).replace("\t", "\\t").replace("\n", "\\n")
    return "\n".join(
        ["\t".join(FIELDS)] +
        ["\t".join(cell(row[key]) for key in FIELDS) for row in report["rows"]]
    ) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    parser.add_argument("--target-dir", type=Path, default=ROOT / "knowledge")
    args = parser.parse_args()
    report = build_report()
    outputs = {
        "current-exact-domain-corpus.json": json.dumps(
            report, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n",
        "current-exact-domain-corpus.tsv": render_tsv(report),
    }
    if args.write:
        args.target_dir.mkdir(parents=True, exist_ok=True)
    for name, content in outputs.items():
        file = args.target_dir / name
        if args.write:
            file.write_text(content, encoding="utf-8")
        elif file.read_text(encoding="utf-8") != content:
            raise SystemExit(f"CURRENT-EXACT-DOMAIN-CORPUS: BLOCKED {name} drift")
    print("CURRENT-EXACT-DOMAIN-CORPUS: PASS — 254 admitted; D7 v2 128/128; no reservations")


if __name__ == "__main__":
    main()
