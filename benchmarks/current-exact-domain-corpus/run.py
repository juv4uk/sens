#!/usr/bin/env python3
"""Generate the current Contract 11.6 D1-D7 exact-domain projection (#2352).

This does not modify or reinterpret the historical pre-bīja3
knowledge/exact-width-admitted-corpus.* artifact.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOUNDATION = ROOT / "knowledge" / "d1-d7-foundation.json"
DOMAIN_MAPS = {
    "D4": ROOT / "knowledge" / "d4-cleanroom.json",
    "D5": ROOT / "knowledge" / "d5-ratified.json",
    "D6": ROOT / "knowledge" / "d6-ratified.json",
    "D7": ROOT / "knowledge" / "d7-ratified.json",
}
CURRENT_DOMAINS = [f"D{i}" for i in range(1, 8)]
EXPECTED_AUTHORITY = {
    "D4": "#3272",
    "D5": "#3305",
    "D6": "#3393",
    "D7": "#3572",
}
SOURCE_BY_DOMAIN = {
    "D1": "knowledge/d1-d7-foundation.json",
    "D2": "knowledge/d1-d7-foundation.json",
    "D3": "knowledge/d1-d7-foundation.json",
    "D4": "knowledge/d4-cleanroom.json",
    "D5": "knowledge/d5-ratified.json",
    "D6": "knowledge/d6-ratified.json",
    "D7": "knowledge/d7-ratified.json",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    foundation = load(FOUNDATION)
    assert foundation["schema"] == "d1-d7-foundation-ratification/v1"
    assert foundation["status"] == "owner-ratified"
    assert foundation["authority"] == "#3572"
    assert foundation["current_domains"] == CURRENT_DOMAINS
    assert foundation["research_domains"] == ["D8"]

    maps = {domain: load(path) for domain, path in DOMAIN_MAPS.items()}
    for domain, doc in maps.items():
        assert doc["status"] == "owner-ratified"
        assert doc["authority"] == EXPECTED_AUTHORITY[domain]
        assert foundation["domains"][domain]["residents"] == doc["residents"]

    reserved = set(maps["D7"]["reserved_coordinates"])
    assert maps["D7"]["capacity"] == 128
    assert maps["D7"]["occupancy"] == 126
    assert maps["D7"]["owner_reserved_pinned"] == 2
    assert reserved == {"0100001", "0101010"}

    authority_by_domain = {
        "D1": foundation["domains"]["D1"]["authority"],
        "D2": foundation["domains"]["D2"]["authority"],
        "D3": foundation["domains"]["D3"]["authority"],
        "D4": maps["D4"]["authority"],
        "D5": maps["D5"]["authority"],
        "D6": maps["D6"]["authority"],
        "D7": maps["D7"]["authority"],
    }

    rows = []
    admitted = 0
    pinned = 0
    for width, domain in enumerate(CURRENT_DOMAINS, start=1):
        domain_doc = foundation["domains"][domain]
        assert domain_doc["width"] == width
        residents = domain_doc["residents"]
        capacity = 1 << width

        for value in range(capacity):
            word = f"{value:0{width}b}"
            role = residents.get(word)
            if role is not None:
                status = "admitted"
                admitted += 1
            elif domain == "D7" and word in reserved:
                status = "owner-reserved-pinned"
                pinned += 1
            else:
                raise AssertionError(f"unexpected nonresident coordinate {domain}:{word}")

            rows.append(
                {
                    "domain": domain,
                    "width": width,
                    "word": word,
                    "status": status,
                    "role": role,
                    "authority_ref": authority_by_domain[domain],
                    "normative_source": SOURCE_BY_DOMAIN[domain],
                    "mechanism_status": "separate-not-projected",
                }
            )

    assert len(rows) == 254
    assert admitted == 252
    assert pinned == 2
    assert not any(row["domain"] == "D8" for row in rows)

    return {
        "schema": "current-exact-domain-corpus/v1",
        "status": "CURRENT-AUTHORITY-PROJECTION",
        "contract": "11.6",
        "identity_rule": "exact bits + exact domain + admitted/proved law",
        "generated_from": [
            "knowledge/d1-d7-foundation.json",
            "knowledge/d4-cleanroom.json",
            "knowledge/d5-ratified.json",
            "knowledge/d6-ratified.json",
            "knowledge/d7-ratified.json",
        ],
        "accounting": {
            "current_domains": CURRENT_DOMAINS,
            "research_domains": ["D8"],
            "coordinate_rows": len(rows),
            "admitted_residents": admitted,
            "owner_reserved_pinned": pinned,
            "d8_rows": 0,
        },
        "rows": rows,
        "non_conclusions": [
            "This corpus is an authority projection, not a new semantic authority.",
            "Residency does not imply derivability, callability, or runtime mechanism.",
            "D7 owner-reserved/pinned coordinates are not free and are not admitted residents.",
            "D8 is excluded because Contract 11.6 keeps Core.D8 unratified/research.",
            "Historical Sens8/Sid8/Function8 coordinates have zero placement authority here.",
        ],
    }


def render_tsv(report: dict) -> str:
    fields = [
        "domain",
        "width",
        "word",
        "status",
        "role",
        "authority_ref",
        "normative_source",
        "mechanism_status",
    ]

    def cell(value) -> str:
        if value is None:
            return ""
        return str(value).replace("\t", "\\t").replace("\n", "\\n")

    lines = ["\t".join(fields)]
    for row in report["rows"]:
        lines.append("\t".join(cell(row[field]) for field in fields))
    return "\n".join(lines) + "\n"


def artifacts() -> tuple[str, str]:
    report = build_report()
    json_text = json.dumps(
        report,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"
    return json_text, render_tsv(report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--target-dir", type=Path, default=ROOT / "knowledge")
    args = parser.parse_args()

    json_text, tsv_text = artifacts()
    targets = {
        args.target_dir / "current-exact-domain-corpus.json": json_text,
        args.target_dir / "current-exact-domain-corpus.tsv": tsv_text,
    }

    if args.write:
        args.target_dir.mkdir(parents=True, exist_ok=True)
        for path, text in targets.items():
            path.write_text(text, encoding="utf-8")
    else:
        for path, expected in targets.items():
            actual = path.read_text(encoding="utf-8")
            assert actual == expected, f"{path}: generated current-domain corpus drift"

    print(
        "CURRENT-EXACT-DOMAIN-CORPUS: PASS "
        "(254 coordinates; 252 admitted; 2 D7 owner-reserved/pinned; D8 rows 0)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
