#!/usr/bin/env python3
"""Generate/check the current SENS domain-width certificate.

The certificate is a mechanical projection of the owner-ratified
knowledge/d1-d9-foundation.json authority. It does not assign widths and must
fail closed when the source authority is malformed or inconsistent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "knowledge/d1-d9-foundation.json"
OUTPUT = ROOT / "knowledge/domain-width-authority.generated.json"


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def load_foundation() -> tuple[dict, bytes]:
    payload = SOURCE.read_bytes()
    foundation = json.loads(payload.decode("utf-8"))

    if foundation.get("status") != "owner-ratified":
        raise SystemExit("width authority source must be owner-ratified")

    current = foundation.get("current_domains")
    if not isinstance(current, list) or not current:
        raise SystemExit("current_domains must be a non-empty ordered list")
    if len(current) != len(set(current)):
        raise SystemExit("current_domains contains duplicates")

    domains = foundation.get("domains")
    if not isinstance(domains, dict):
        raise SystemExit("domains must be an object")
    if set(domains) != set(current):
        raise SystemExit("domains keys must exactly match current_domains")

    for domain in current:
        row = domains[domain]
        width = row.get("width")
        residents = row.get("residents")

        if not isinstance(width, int) or isinstance(width, bool) or width <= 0:
            raise SystemExit(f"{domain}: width must be a positive integer")
        if not isinstance(row.get("authority"), str) or not row["authority"]:
            raise SystemExit(f"{domain}: authority must be present")
        if not isinstance(residents, dict) or not residents:
            raise SystemExit(f"{domain}: residents must be a non-empty object")

        for coordinate in residents:
            if len(coordinate) != width:
                raise SystemExit(
                    f"{domain}: coordinate {coordinate!r} has width "
                    f"{len(coordinate)}, expected {width}"
                )
            if set(coordinate) - {"0", "1"}:
                raise SystemExit(f"{domain}: coordinate {coordinate!r} is not binary")

        capacity = row.get("capacity")
        if capacity is not None and capacity != 1 << width:
            raise SystemExit(
                f"{domain}: capacity {capacity} disagrees with exact width {width}"
            )

        occupancy = row.get("occupancy")
        if occupancy is not None and occupancy != len(residents):
            raise SystemExit(
                f"{domain}: occupancy {occupancy} disagrees with resident count "
                f"{len(residents)}"
            )

        distinct = row.get("distinct_residents")
        if distinct is not None and distinct != len(set(residents.values())):
            raise SystemExit(
                f"{domain}: distinct_residents {distinct} disagrees with values"
            )

    return foundation, payload


def generate() -> str:
    foundation, payload = load_foundation()
    current = foundation["current_domains"]
    domains = foundation["domains"]

    certificate = {
        "schema": "sens-domain-width-certificate/v1",
        "status": "generated-projection-non-authoritative",
        "source": {
            "path": "knowledge/d1-d9-foundation.json",
            "schema": foundation.get("schema"),
            "status": foundation.get("status"),
            "authority": foundation.get("authority"),
            "git_blob_sha1": git_blob_sha1(payload),
        },
        "current_domains": current,
        "domains": {
            domain: {
                "width": domains[domain]["width"],
                "authority": domains[domain]["authority"],
            }
            for domain in current
        },
        "verified": {
            "binary_coordinate_lengths_match_declared_width": True,
            "declared_capacities_match_power_of_two_width": True,
            "declared_occupancies_match_resident_count": True,
        },
        "law": (
            "Widths are copied from current SENS authority. "
            "This generated projection cannot mint, infer, widen, narrow, "
            "or otherwise redefine a domain width."
        ),
    }
    return json.dumps(certificate, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed generated certificate is stale",
    )
    args = parser.parse_args()

    generated = generate()
    if args.check:
        try:
            committed = OUTPUT.read_text(encoding="utf-8")
        except FileNotFoundError:
            raise SystemExit(f"missing generated certificate: {OUTPUT}")
        if committed != generated:
            raise SystemExit(
                "domain width certificate is stale; run "
                "python3 scripts/generate-domain-width-certificate.py"
            )
        print("DOMAIN-WIDTH-CERTIFICATE: PASS")
        return 0

    OUTPUT.write_text(generated, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
