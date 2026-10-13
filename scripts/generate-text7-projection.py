#!/usr/bin/env python3
"""Verify the legacy UPC7 donor pin and current SENS D7 display authority.

The 107-cell donor remains a historical reference only. No donor code table
may generate executable Text7 cells; those come solely from ratified D7 #3572.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "contracts/text7-upc7.lock"
D7 = ROOT / "knowledge/d7-ratified.json"
OUTPUT = ROOT / "crates/sens/src/text7_projection_generated.rs"


def _pin(text: str, name: str) -> str:
    matches = re.findall(r"\(" + re.escape(name) + r'\s+"([^"]+)"\)', text)
    if len(matches) != 1:
        raise ValueError(f"donor lock: expected exactly one {name}")
    return matches[0]


def generate() -> str:
    lock = LOCK.read_text(encoding="utf-8")
    revision = _pin(lock, "revision")
    sha = _pin(lock, "sha256")
    layout_sha = _pin(lock, "layout-sha256")
    if not (re.fullmatch(r"[0-9a-f]{40}", revision)
            and re.fullmatch(r"[0-9a-f]{64}", sha)
            and re.fullmatch(r"[0-9a-f]{64}", layout_sha)):
        raise ValueError("donor revision/checksum has invalid width")

    authority = json.loads(D7.read_text(encoding="utf-8"))
    if (authority["authority"], authority["status"], authority["width"],
            authority["capacity"], authority["occupancy"]) != (
                "#3572", "owner-ratified", 7, 128, 126):
        raise ValueError("D7 ratification mismatch")
    if set(authority["reserved_coordinates"]) != {"0100001", "0101010"}:
        raise ValueError("owner pins changed")
    if len(authority["rows"]) != 128 or len(authority["residents"]) != 126:
        raise ValueError("owner coordinates/ledger incomplete")

    return "\n".join((
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Historical UPC7 donor provenance ONLY. No executable or display mapping.",
        "// Active exact 126/128 D7 glyphs live in d7_display_registry_generated.rs.",
        "// Generator: scripts/generate-text7-projection.py",
        f'pub(crate) const UPC7_SOURCE_REVISION: &str = "{revision}";',
        "pub(crate) const UPC7_TABLE_SHA256: &str =",
        f'    "{sha}";',
        "pub(crate) const UPC7_LAYOUT_SHA256: &str =",
        f'    "{layout_sha}";',
        "",
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = generate()
        if args.check:
            if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
                raise ValueError("generated UPC7 donor metadata drift")
            print("D7-PROJECTION=PASS: donor metadata only; active map owner #3572")
        else:
            OUTPUT.write_text(expected, encoding="utf-8")
    except (OSError, KeyError, ValueError) as exc:
        print(f"D7-PROJECTION=FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
