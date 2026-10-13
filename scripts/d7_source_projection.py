#!/usr/bin/env python3
"""D7 v2 text/data projection: 128 ASCII-indexed W7 keyboard cells.

The historical D7 v1 phonemic/sound authority is research provenance only.
No phonemic or SID8 identity can be inferred from this text projection.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from domain_tables import D7_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "knowledge/d7-keyboard-v2-ratified.json"
NAMESPACES = ("ук", "укр", "uk", "san", "en", "sym")
EXACT_W7 = re.compile(r"[01]{7}\Z")


class D7ProjectionError(ValueError):
    """Missing width, unsupported role/surface or noncanonical authority."""


def load_current_d7() -> tuple[dict, dict[str, object]]:
    owner = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if (owner.get("schema"), owner.get("status"), owner.get("width"),
            owner.get("capacity"), owner.get("occupancy")) != (
            "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128):
        raise D7ProjectionError("D7 v2 owner authority mismatch")
    evidence = {item["bits"]: item for item in owner["table"]}
    rows = read_domain_table(D7_TABLE)
    by_coordinate = {row.bits: row for row in rows}
    expected = {f"{n:07b}" for n in range(128)}
    if len(rows) != 128 or set(by_coordinate) != expected or set(evidence) != expected:
        raise D7ProjectionError("D7 v2 coverage must be 128/128")
    for bits, row in by_coordinate.items():
        glyphs = evidence[bits]
        if row.lisp is not None or glyphs["ascii"] != chr(int(bits, 2)):
            raise D7ProjectionError(f"D7:{bits} callable/coordinate drift")
        n = int(bits, 2)
        expected_glyphs = (
            (glyphs["uk"], glyphs["uk"], glyphs["san"],
             glyphs["ascii"], glyphs["uk"])
            if 32 <= n < 127 else (None, None, None, None, None)
        )
        if (row.uk, row.ukr, row.san, row.en, row.sym) != expected_glyphs:
            raise D7ProjectionError(f"D7:{bits} glyph drift")
    for field in ("ascii", "uk", "san"):
        if len({item[field] for item in evidence.values()}) != 128:
            raise D7ProjectionError(f"D7:{field} ambiguous glyph")
    return evidence, by_coordinate


def project(bits: str, *, role: str, namespace: str = "ук") -> dict:
    """Return display-only text, or separately sourced Shiva LocalOrdinal provenance."""
    if not EXACT_W7.fullmatch(bits):
        raise D7ProjectionError("D7 requires exactly seven binary digits")
    if role not in ("text", "local-ordinal"):
        raise D7ProjectionError("role must be explicit: text or local-ordinal")
    if namespace not in NAMESPACES:
        raise D7ProjectionError(f"unsupported D7 human namespace: {namespace}")
    owner, surface = load_current_d7()
    if role == "local-ordinal":
        corpus = json.loads(
            (ROOT / "benchmarks/d7-local-ordinal-corpus/fixtures/projection.json")
            .read_text(encoding="utf-8")
        )
        ordinals = {row["bits"]: row for row in corpus["rows"]}
        if len(ordinals) != 14 or set(ordinals) != {f"{n:07b}" for n in range(1, 15)}:
            raise D7ProjectionError("D7 historical local-ordinal witness drift")
        if bits not in ordinals:
            raise D7ProjectionError(f"D7:{bits} has no donor-ratified LocalOrdinal provenance")
        item = ordinals[bits]
        return {
            "domain": "D7", "coordinate": bits, "width": 7,
            "role": "local-ordinal", "status": "D7-VALID-PROVENANCE",
            "donor_ref": item["donor_ref"], "source_order": item["source_order"],
            "surface": None, "callable": False, "arithmetic_number": False,
        }
    row = surface[bits]
    label = "uk" if namespace == "uk" else {
        "ук": "uk", "укр": "ukr", "san": "san", "en": "en", "sym": "sym",
    }[namespace]
    glyph = getattr(row, label)
    return {
        "domain": "D7", "coordinate": bits, "width": 7,
        "role": "text", "semantic_role": "text-data",
        "status": "OWNER-RATIFIED", "namespace": namespace,
        "surface": glyph, "symbol": glyph,
        "report_name": None, "callable": False, "arithmetic_number": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--coordinate")
    parser.add_argument("--role", choices=["text", "local-ordinal"])
    parser.add_argument("--namespace", choices=NAMESPACES, default="ук")
    args = parser.parse_args()
    try:
        if args.check:
            owner, cells = load_current_d7()
            for bits in (f"{n:07b}" for n in range(1, 15)):
                assert project(bits, role="local-ordinal")["callable"] is False
            print("D7-PROJECTION: PASS keyboard/v2 128/128 no-callable, local-ordinal separate")
            return 0
        if args.coordinate is None or args.role is None:
            parser.error("--coordinate and --role are required")
        print(json.dumps(project(args.coordinate, role=args.role,
                                 namespace=args.namespace), ensure_ascii=False))
        return 0
    except (D7ProjectionError, ValueError, OSError) as exc:
        print("D7-PROJECTION: BLOCKED: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
