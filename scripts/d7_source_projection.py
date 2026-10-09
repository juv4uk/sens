#!/usr/bin/env python3
"""D7 owner-ratified projection — never a host-created semantic identity.

Sound/Text residency comes exclusively from knowledge/d7-ratified.json (#3572),
with human surfaces read from lib/domains/d7.lisp. LocalOrdinal is a distinct
explicitly selected W7 role; it never borrows Sound/Text residency or Number
semantics. This script is a read-only projection, not a runtime Lisp callable.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from domain_tables import D7_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "knowledge/d7-ratified.json"
NAMESPACES = ("ук", "укр", "san", "en", "sym")
EXACT_W7 = re.compile(r"[01]{7}\Z")


class D7ProjectionError(ValueError):
    """Wrong width, absent residency or ambiguous role; no best-effort alias."""


def load_current_d7() -> tuple[dict, dict[str, object]]:
    owner = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    if (owner["status"], owner["authority"], owner["width"],
        owner["capacity"], owner["occupancy"]) != ("owner-ratified", "#3572", 7, 128, 126):
        raise D7ProjectionError("D7 authority changed; explicit review required")
    pins = set(owner["reserved_coordinates"])
    rows = read_domain_table(D7_TABLE)
    by_coordinate = {row.bits: row for row in rows}
    if (len(by_coordinate) != 126 or set(by_coordinate) != set(owner["residents"])
        or pins != {"0100001", "0101010"}
        or pins.intersection(by_coordinate)):
        raise D7ProjectionError("D7 Lisp table and owner-ratified residency diverged")
    for bits, row in by_coordinate.items():
        if row.en != owner["residents"][bits] or row.lisp is not None:
            raise D7ProjectionError(f"D7:{bits} changed or minted a Lisp callable")
    evidence = {item["coordinate"]: item for item in owner["rows"]}
    if len(evidence) != 128:
        raise D7ProjectionError("D7 owner evidence must cover all 128 coordinates")
    for bits in by_coordinate:
        if evidence[bits]["status"] != "OWNER-RATIFIED":
            raise D7ProjectionError(f"D7:{bits} lacks owner admission")
    for bits in pins:
        if evidence[bits]["status"] != "OWNER-RESERVED-PINNED":
            raise D7ProjectionError(f"D7:{bits} lost owner reservation")
    return evidence, by_coordinate


def project(bits: str, *, role: str, namespace: str = "ук") -> dict:
    """Project one explicitly role-qualified W7 word; no inferred meaning."""
    if not EXACT_W7.fullmatch(bits):
        raise D7ProjectionError("D7 requires exactly seven binary digits")
    if namespace not in NAMESPACES:
        raise D7ProjectionError(f"unsupported D7 human namespace: {namespace}")
    if role not in ("sound-text", "local-ordinal"):
        raise D7ProjectionError("D7 role must be explicit: sound-text or local-ordinal")

    evidence, table = load_current_d7()
    if role == "local-ordinal":
        # LocalOrdinal uses ONLY the 14 donor-locked Shiva-sutra ordinals.
        # Equal W7 bits do not mint Sound/Text residency or arithmetic Number.
        corpus = json.loads((ROOT / "benchmarks/d7-local-ordinal-corpus/fixtures/projection.json").read_text(encoding="utf-8"))
        ordinals = {row["bits"]: row for row in corpus["rows"]}
        if len(ordinals) != 14 or set(ordinals) != {f"{i:07b}" for i in range(1, 15)}:
            raise D7ProjectionError("D7 LocalOrdinal donor-locked corpus drift")
        if bits not in ordinals:
            raise D7ProjectionError(f"D7:{bits} has no donor-ratified LocalOrdinal provenance")
        ordinal = ordinals[bits]
        return {
            "domain": "D7", "coordinate": bits, "width": 7,
            "role": "local-ordinal", "status": "D7-VALID-PROVENANCE",
            "donor_ref": ordinal["donor_ref"], "source_order": ordinal["source_order"],
            "surface": None, "callable": False, "arithmetic_number": False,
        }

    row = table.get(bits)
    if row is None:
        raise D7ProjectionError(f"D7:{bits} is reserved; owner admission required")
    owner = evidence[bits]
    surface = getattr(row, namespace)
    if surface is None:
        raise D7ProjectionError(f"D7:{bits} has no {namespace} projection")
    return {
        "domain": "D7", "coordinate": bits, "width": 7,
        "role": "sound-text", "semantic_role": owner["semantic_role"],
        "status": "OWNER-RATIFIED", "namespace": namespace,
        "surface": surface, "callable": False, "arithmetic_number": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="validate owner map and D7 surface projection")
    ap.add_argument("--coordinate", help="exact seven-bit D7 word")
    ap.add_argument("--role", choices=["sound-text", "local-ordinal"])
    ap.add_argument("--namespace", choices=NAMESPACES, default="ук")
    opts = ap.parse_args()
    try:
        if opts.check:
            load_current_d7()
            for bits in ("0000001", "0001110"):
                project(bits, role="local-ordinal")
            print("D7-PROJECTION=PASS; owner-residents=126/128; reserved=2; no-Rust-law")
            return 0
        if opts.coordinate is None or opts.role is None:
            ap.error("--coordinate and --role are both required without --check")
        result = project(opts.coordinate, role=opts.role, namespace=opts.namespace)
    except D7ProjectionError as exc:
        ap.exit(2, f"BLOCKED: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
