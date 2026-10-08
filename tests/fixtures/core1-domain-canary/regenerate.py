#!/usr/bin/env python3
"""Bounded domain-native specialization of the EXISTING Core1 C1-SECOND helper.

No evaluator is created here. Canonical semantic identities come from the pinned
SENS foundation. Physical bytes are produced only by sens_t5_codec.
The positive T5 fixture is *not* independent oracle/native execution evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from sens_t5_codec import decode_bytes, encode_words, typed_sha256

SOURCE = ROOT / "lib" / "core1.lisp"
FOUNDATION = ROOT / "knowledge" / "d1-d9-foundation.json"
PROJECTION = HERE / "second.lisp"
PHYSICAL = HERE / "second.sens"

# An already implemented Core1 helper; preserve its source and semantics.
# Its historic SID8 words are evidence, NOT modern D8 identity.
C1_SECOND = re.compile(
    r"\(00001001\s+C1-SECOND\s+"
    r"\(00001000\s+\(X\)\s+"
    r"\(00000101\s+\(00000110\s+X\)\s*\)\s*\)\s*\)"
)

# This closed call specializes X to a two-element proper list of empty values.
# Therefore it requires no unratified symbol/binder/Text7 representation.
NIL = ("QUOTE", ("EMPTY",))
TAIL = ("CONS", (NIL, NIL))
LIST_OF_TWO = ("CONS", (NIL, TAIL))
SECOND_OF_TWO = ("CAR", (("CDR", (LIST_OF_TWO,)),))

CANONICAL_D3 = {
    "EMPTY": "000", "QUOTE": "001", "CDR": "011",
    "CAR": "100", "CONS": "111",
}
CANONICAL_D2 = {
    "SEPARATOR": "00", "CLOSE": "01", "OPEN": "10", "DOT": "11",
}


def words_from_existing_core1(root: Path = ROOT) -> list[str]:
    historical = (root / "lib" / "core1.lisp").read_text(encoding="utf-8")
    if len(C1_SECOND.findall(historical)) != 1:
        raise ValueError("BLOCK: existing Core1 C1-SECOND has drifted or is ambiguous")

    foundation = json.loads(
        (root / "knowledge" / "d1-d9-foundation.json").read_text(encoding="utf-8")
    )
    if foundation.get("status") != "owner-ratified":
        raise ValueError("BLOCK: SENS domain foundation is not ratified")
    domains = foundation["domains"]
    for domain, required in (("D2", CANONICAL_D2), ("D3", CANONICAL_D3)):
        actual = domains[domain]["residents"]
        for role, bits in required.items():
            if actual.get(bits) != role or len(bits) != domains[domain]["width"]:
                raise ValueError(f"BLOCK: {domain} {role} not ratified at {bits}")

    # Reverse map exact words from the ratified table, never from historical SID.
    d2 = {role: bits for bits, role in domains["D2"]["residents"].items()}
    d3 = {role: bits for bits, role in domains["D3"]["residents"].items()}

    def emit(term: object) -> list[str]:
        if term == "EMPTY":
            return [d3["EMPTY"]]
        if not (isinstance(term, tuple) and len(term) == 2):
            raise ValueError("BLOCK: unknown term shape or symbol")
        role, args = term
        if role not in {"QUOTE", "CAR", "CDR", "CONS"}:
            raise ValueError("BLOCK: no admitted callable semantics")
        if not isinstance(args, tuple) or len(args) != (2 if role == "CONS" else 1):
            raise ValueError("BLOCK: arity mismatch")
        result = [d2["OPEN"], d3[role]]
        for arg in args:
            result.append(d2["SEPARATOR"])
            result.extend(emit(arg))
        return result + [d2["CLOSE"]]

    return emit(SECOND_OF_TWO)


def expected_artifacts(root: Path = ROOT) -> tuple[str, bytes, str]:
    words = words_from_existing_core1(root)
    physical = encode_words(words)  # existing authoritative T5 transport
    if decode_bytes(physical) != words:
        raise ValueError("BLOCK: T5 exact-width roundtrip mismatch")
    return " ".join(words) + "\n", physical, typed_sha256(words)


def verify_checked_in() -> tuple[int, str]:
    projection, physical, digest = expected_artifacts()
    if PROJECTION.read_text(encoding="utf-8") != projection:
        raise ValueError("BLOCK: Core1 same-stem .lisp projection drift")
    if PHYSICAL.read_bytes() != physical:
        raise ValueError("BLOCK: Core1 physical .sens mismatch or noncanonical bytes")
    if PROJECTION.stem != PHYSICAL.stem:
        raise ValueError("BLOCK: Core1 source/binary filename mismatch")
    return len(physical), digest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--create", action="store_true",
                    help="create ONLY absent same-stem fixture files; never overwrite")
    args = ap.parse_args()
    if args.create:
        if PROJECTION.exists() or PHYSICAL.exists():
            ap.error("BLOCK: refusing to overwrite existing projection or physical .sens")
        projection, physical, _digest = expected_artifacts()
        # Exclusive creates, even if another agent races the prior exists-check.
        with PROJECTION.open("x", encoding="utf-8") as out:
            out.write(projection)
        with PHYSICAL.open("xb") as out:
            out.write(physical)
    size, typed_digest = verify_checked_in()
    physical_sha = hashlib.sha256(PHYSICAL.read_bytes()).hexdigest()
    print(f"PASS: C1-SECOND existing-source -> exact D2/D3 -> T5 {size} bytes "
          f"typed_sha256={typed_digest} physical_sha256={physical_sha}")
    print("NOTE: current SENS oracle checked independently in Rust CI; native WSM parity PENDING")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
