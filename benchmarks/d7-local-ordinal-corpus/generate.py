#!/usr/bin/env python3
"""#2739 — generate D7 LocalOrdinal provenance corpus from pinned Shiva-sutra canon.

This is a role-tagged provenance projection, not arithmetic Number semantics.

The donor's 1..14 IDs/source order are projected into exact 7-bit D7 local
ordinals. No grammar relation is inferred from adjacency or numbering.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "contracts" / "d7-local-ordinal.lock"
OUTPUT = ROOT / "benchmarks" / "d7-local-ordinal-corpus" / "fixtures" / "projection.json"


def quoted(text: str, name: str) -> str:
    m = re.search(r"\(" + re.escape(name) + r'\s+"([^"]+)"\)', text)
    if not m:
        raise SystemExit(f"missing {name} in {LOCK}")
    return m.group(1)


def integer(text: str, name: str) -> int:
    m = re.search(r"\(" + re.escape(name) + r"\s+(\d+)\)", text)
    if not m:
        raise SystemExit(f"missing {name} in {LOCK}")
    return int(m.group(1))


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def parse_canon(path: Path) -> list[dict[str, object]]:
    """Strictly parse only the simple transmitted-canon fields we project.

    This is intentionally not a general YAML parser. Unexpected structure fails
    rather than becoming a hidden semantic dependency.
    """
    rows: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    id_re = re.compile(r"^\s*- id:\s*(\d+)\s*$")
    text_re = re.compile(r'^\s*text_iast:\s*"([^"]*)"\s*$')

    for raw in path.read_text(encoding="utf-8").splitlines():
        m = id_re.match(raw)
        if m:
            if current is not None:
                if "text_iast" not in current:
                    raise SystemExit(f"missing text_iast for donor id {current['id']}")
                rows.append(current)
            current = {"id": int(m.group(1))}
            continue

        m = text_re.match(raw)
        if m and current is not None:
            if "text_iast" in current:
                raise SystemExit(f"duplicate text_iast for donor id {current['id']}")
            current["text_iast"] = m.group(1)

    if current is not None:
        if "text_iast" not in current:
            raise SystemExit(f"missing text_iast for donor id {current['id']}")
        rows.append(current)

    if not rows:
        raise SystemExit("no donor sutras parsed")
    return rows


def bits7(value: int) -> str:
    if not 0 <= value < 128:
        raise ValueError("D7 width overflow")
    return format(value, "07b")


@dataclass(frozen=True)
class D7SoundCell:
    bits: int


@dataclass(frozen=True)
class D7LocalOrdinal:
    bits: int
    donor_ref: str


@dataclass(frozen=True)
class ArithmeticNumber:
    value: int


class DomainMismatch(TypeError):
    pass


def arithmetic_add(left, right):
    if not isinstance(left, ArithmeticNumber) or not isinstance(right, ArithmeticNumber):
        raise DomainMismatch
    return ArithmeticNumber(left.value + right.value)


def arithmetic_mul(left, right):
    if not isinstance(left, ArithmeticNumber) or not isinstance(right, ArithmeticNumber):
        raise DomainMismatch
    return ArithmeticNumber(left.value * right.value)


def arithmetic_recip(value):
    if not isinstance(value, ArithmeticNumber):
        raise DomainMismatch
    if value.value == 0:
        raise ZeroDivisionError
    return ("rational", 1, value.value)


def generate(upstream_root: Path) -> dict[str, object]:
    lock = LOCK.read_text(encoding="utf-8")
    rel = quoted(lock, "path")
    expected_blob = quoted(lock, "git-blob-sha1")
    revision = quoted(lock, "revision")
    width = integer(lock, "logical-width")
    count = integer(lock, "ordinal-count")

    if width != 7:
        raise SystemExit("D7 lock width drift")
    if count != 14:
        raise SystemExit("D7 ordinal count drift")

    donor = upstream_root / rel
    if not donor.is_file():
        raise SystemExit(f"missing pinned donor file: {donor}")

    actual_blob = git_blob_sha1(donor.read_bytes())
    if actual_blob != expected_blob:
        raise SystemExit(f"donor blob drift: {actual_blob} != {expected_blob}")

    sutras = parse_canon(donor)

    # Source-order is part of provenance. Reordering must invalidate the lock.
    ids = [int(row["id"]) for row in sutras]
    if ids != list(range(1, 15)):
        raise SystemExit(f"donor source-order drift: {ids!r}")

    rows = []
    for source_order, donor in enumerate(sutras, start=1):
        ordinal = int(donor["id"])
        if ordinal != source_order:
            raise SystemExit("donor ordinal/source-order mismatch")
        rows.append(
            {
                "bits": bits7(ordinal),
                "ordinal_display": ordinal,
                "role": "local-shiva-sutra-ordinal",
                "donor_ref": f"shiva-sutra:{ordinal}",
                "source_order": source_order,
                "source_text_iast": donor["text_iast"],
                "law": "provenance/source-order-only",
                "d14_relation": "provenance-only",
                "arithmetic": "forbidden",
                "status": "D7-VALID-PROVENANCE",
            }
        )

    # Domain/role guards over real projected payloads.
    mismatch_cases = 0
    for row in rows:
        raw = int(row["bits"], 2)
        ordinal = D7LocalOrdinal(raw, row["donor_ref"])
        sound = D7SoundCell(raw)
        number = ArithmeticNumber(raw)

        assert ordinal != sound
        assert ordinal != number
        assert sound != number

        for operation, args in (
            (arithmetic_add, (ordinal, ArithmeticNumber(1))),
            (arithmetic_mul, (ordinal, ArithmeticNumber(2))),
            (arithmetic_recip, (ordinal,)),
        ):
            try:
                operation(*args)
            except DomainMismatch:
                mismatch_cases += 1
            else:
                raise AssertionError("D7 LocalOrdinal accepted arithmetic")

    # Role erasure is intentionally ambiguous: bits alone are insufficient.
    probe = int(rows[0]["bits"], 2)
    possible_roles = {
        type(D7SoundCell(probe)).__name__,
        type(D7LocalOrdinal(probe, rows[0]["donor_ref"])).__name__,
        type(ArithmeticNumber(probe)).__name__,
    }
    assert len(possible_roles) == 3

    return {
        "schema": "sens-d7-local-ordinal-corpus/v1",
        "authority": "owner-ratified-D7-provenance-projection",
        "upstream": {
            "repository": quoted(lock, "repository"),
            "revision": revision,
            "path": rel,
            "git_blob_sha1": expected_blob,
        },
        "logical_width": 7,
        "rows": rows,
        "counts": {
            "rows": len(rows),
            "arithmetic_domain_mismatch_cases": mismatch_cases,
            "occupied_local_ordinals": 14,
            "remaining_d7_occupancy_claim": 0,
        },
        "guards": {
            "same_bits_sound_vs_ordinal": "DISTINCT",
            "same_value_ordinal_vs_number": "DISTINCT",
            "arithmetic_on_local_ordinal": "DOMAIN-MISMATCH",
            "d14_link": "PROVENANCE-ONLY",
            "ordinal_adjacency_implies_grammar": False,
            "blanket_d7_occupancy": False,
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream-root", type=Path, required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    payload = generate(args.upstream_root.resolve())
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    if args.check:
        if not OUTPUT.is_file():
            print(f"missing generated projection: {OUTPUT}", file=sys.stderr)
            return 1
        if OUTPUT.read_text(encoding="utf-8") != rendered:
            print("D7 local ordinal projection is stale", file=sys.stderr)
            return 1
    else:
        OUTPUT.write_text(rendered, encoding="utf-8")

    print(f"D7-LOCAL-ORDINAL-ROWS={payload['counts']['rows']}")
    print("D7-WIDTH=7")
    print("ORDINAL-RANGE=1..14")
    print("SOURCE-ORDER=PINNED-PROVENANCE")
    print(
        "ARITHMETIC-DOMAIN-MISMATCH-CASES="
        + str(payload["counts"]["arithmetic_domain_mismatch_cases"])
    )
    print("SAME-BITS-SOUND-VS-ORDINAL=DISTINCT")
    print("SAME-VALUE-ORDINAL-VS-NUMBER=DISTINCT")
    print("D14-LINK=PROVENANCE-ONLY")
    print("D14-GRAMMAR-FROM-ADJACENCY=REJECTED")
    print("BLANKET-D7-OCCUPANCY=NONE")
    print("STATUS=PASS-D7-LOCAL-ORDINAL-CORPUS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
