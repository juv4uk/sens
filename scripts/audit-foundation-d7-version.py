#!/usr/bin/env python3
"""Read-only D7 source-era diagnostic for SENS foundation JSON.

This observer has no semantic authority and is NOT an automatic CI gate.
It does not rewrite a source, domain table, or physical T5 program.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(foundation, keyboard):
    findings = []
    domains = foundation.get("domains")
    declared = foundation.get("current_domains")
    if not isinstance(domains, dict) or not isinstance(declared, list):
        return ["INVALID_FOUNDATION_STRUCTURE"]
    duplicates = sorted({item for item in declared if declared.count(item) > 1})
    if duplicates:
        findings.append("DUPLICATE_CURRENT_DOMAIN:" + ",".join(duplicates))
    unknown = sorted(set(declared) - set(domains))
    missing = sorted(set(domains) - set(declared))
    if unknown:
        findings.append("DECLARED_DOMAIN_MISSING_BODY:" + ",".join(unknown))
    if missing:
        findings.append("DOMAIN_BODY_NOT_DECLARED:" + ",".join(missing))

    if (keyboard.get("schema"), keyboard.get("status"), keyboard.get("width"),
        keyboard.get("capacity"), keyboard.get("occupancy")) != (
        "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128
    ):
        findings.append("BAD_D7_V2_AUTHORITY")
        return findings
    table = keyboard.get("table")
    if not isinstance(table, list) or len(table) != 128:
        findings.append("BAD_D7_V2_TABLE_LENGTH")
        return findings
    expected = {format(i, "07b") for i in range(128)}
    actual = {row.get("bits") for row in table if isinstance(row, dict)}
    if actual != expected:
        findings.append("BAD_D7_V2_COORDINATES")
        return findings
    for index, row in enumerate(table):
        if not isinstance(row, dict) or row.get("bits") != format(index, "07b"):
            findings.append("BAD_D7_V2_ROW_ORDER")
            return findings
        if row.get("ascii") != chr(index):
            findings.append("BAD_D7_V2_ASCII")
            return findings
    for view in ("ascii", "uk", "san"):
        glyphs = [row.get(view) for row in table]
        if not all(isinstance(glyph, str) and len(glyph) == 1
                   for glyph in glyphs):
            findings.append("BAD_D7_V2_GLYPH:" + view)
            return findings
        if len(set(glyphs)) != 128:
            findings.append("BAD_D7_V2_BIJECTION:" + view)
            return findings

    d7 = domains.get("D7")
    if not isinstance(d7, dict):
        findings.append("FOUNDATION_MISSING_D7")
        return findings
    keys = set(d7.get("residents", {}))
    if d7.get("width") != 7 or any(
        not isinstance(bit, str) or len(bit) != 7 or set(bit) - {"0", "1"}
        for bit in keys
    ):
        findings.append("FOUNDATION_BAD_D7_BITS")
    if d7.get("occupancy") != 128 or keys != expected:
        lost = sorted(expected - keys)
        findings.append("HISTORICAL_D7_PROFILE_IN_FOUNDATION:"
                        f" occupancy={d7.get('occupancy')}"
                        f" missing_v2_coordinates={','.join(lost) or 'none'}")
    if d7.get("owner_reserved_pinned"):
        findings.append("HISTORICAL_D7_RESERVED_CELLS")
    if (d7.get("authority") != "owner-ratified-2026-10-13-keyboard-v2"
        or d7.get("normative_map")
            != "knowledge/d7-keyboard-v2-ratified.json"
        or d7.get("callability") != "none-inferred-from-text-data"
        or d7.get("capacity") != 128
        or d7.get("role_counts", {}).get("text_data") != 128):
        findings.append("FOUNDATION_D7_V2_METADATA_DRIFT")
    if any(label != "text-data" for label in d7.get("residents", {}).values()):
        findings.append("FOUNDATION_D7_V2_ROLE_DRIFT")
    # Current foundation stores 128 text/data roles, not glyph identities.
    # The keyboard JSON owns the glyph projections. Never assign phoneme-v1
    # meanings by matching bits; no v1 payload migration cohort exists.
    return findings


def self_test():
    keys = [format(i, "07b") for i in range(128)]
    keyboard = {
        "schema": "sens.d7.keyboard/v2", "status": "owner-ratified",
        "width": 7, "capacity": 128, "occupancy": 128,
        "table": [{"bits": k, "ascii": chr(i), "uk": chr(i),
                   "san": chr(i)} for i, k in enumerate(keys)],
    }
    good = {
        "current_domains": ["D7"],
        "domains": {"D7": {
            "width": 7, "capacity": 128, "occupancy": 128,
            "authority": "owner-ratified-2026-10-13-keyboard-v2",
            "normative_map": "knowledge/d7-keyboard-v2-ratified.json",
            "callability": "none-inferred-from-text-data",
            "role_counts": {"text_data": 128},
            "residents": {k: "text-data" for k in keys}}},
    }
    assert inspect(good, keyboard) == []
    old = json.loads(json.dumps(good))
    old["domains"]["D7"]["occupancy"] = 126
    old["domains"]["D7"]["residents"].pop("0100001")
    old["domains"]["D7"]["residents"].pop("0101010")
    old["domains"]["D7"]["owner_reserved_pinned"] = ["0100001", "0101010"]
    assert any(x.startswith("HISTORICAL_D7_PROFILE_IN_FOUNDATION")
               for x in inspect(old, keyboard))
    assert "HISTORICAL_D7_RESERVED_CELLS" in inspect(old, keyboard)
    duplicated = json.loads(json.dumps(good))
    duplicated["current_domains"].append("D7")
    assert "DUPLICATE_CURRENT_DOMAIN:D7" in inspect(duplicated, keyboard)
    bad = json.loads(json.dumps(keyboard))
    bad["table"] = bad["table"][:-1]
    assert "BAD_D7_V2_TABLE_LENGTH" in inspect(good, bad)
    bad_ascii = json.loads(json.dumps(keyboard))
    bad_ascii["table"][0]["ascii"] = "x"
    assert "BAD_D7_V2_ASCII" in inspect(good, bad_ascii)
    bad_uk = json.loads(json.dumps(keyboard))
    bad_uk["table"][1]["uk"] = bad_uk["table"][0]["uk"]
    assert "BAD_D7_V2_BIJECTION:uk" in inspect(good, bad_uk)
    old_role = json.loads(json.dumps(good))
    old_role["domains"]["D7"]["residents"]["0000000"] = "vowel.a.oral.short"
    assert "FOUNDATION_D7_V2_ROLE_DRIFT" in inspect(old_role, keyboard)
    old_authority = json.loads(json.dumps(good))
    old_authority["domains"]["D7"]["authority"] = "#3572"
    assert "FOUNDATION_D7_V2_METADATA_DRIFT" in inspect(old_authority, keyboard)
    print("D7_FOUNDATION_AUDIT_SELF_TEST_PASS cases=8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--foundation", type=Path,
                        default=ROOT / "knowledge/d1-d11-foundation.json")
    parser.add_argument("--keyboard-v2", type=Path,
                        default=ROOT / "knowledge/d7-keyboard-v2-ratified.json")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="exit 2 for findings (manual diagnostics only)")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    foundation = json.loads(args.foundation.read_text(encoding="utf-8"))
    keyboard = json.loads(args.keyboard_v2.read_text(encoding="utf-8"))
    findings = inspect(foundation, keyboard)
    report = {
        "test_id": "foundation-d7-version-observer",
        "layer": "source-era-provenance",
        "foundation": str(args.foundation),
        "foundation_sha256": sha256(args.foundation),
        "keyboard_v2_sha256": sha256(args.keyboard_v2),
        "findings": findings,
        "semantic_authority": "SENS-only",
        "automatic_ci_gate": False,
        "reproduce": "python3 scripts/audit-foundation-d7-version.py --strict",
    }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 2 if findings and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
