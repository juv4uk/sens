#!/usr/bin/env python3
"""#4158 — guard D2-only canonical source/structural control.

This checks the language/reader boundary only. Evaluation forms such as COND,
GO, RETURN, DO or WHILE are deliberately out of scope unless they attempt to
own source framing or reinterpret W2/D2 structure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "knowledge" / "d2-structure-audit.json"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def require(
    condition: bool,
    message: str,
    failures: list[str],
) -> None:
    if not condition:
        failures.append(message)


def check_d2_table(failures: list[str]) -> None:
    text = read("lib/domains/d2.lisp")
    expected = {
        "00": "separator",
        "01": "close",
        "10": "open",
        "11": "dot",
    }
    for bits, english in expected.items():
        pattern = rf"^\s*\({bits}\s+.*?\(en\s+{re.escape(english)}\)"
        require(
            re.search(pattern, text, flags=re.MULTILINE) is not None,
            f"D2 law missing or changed: {bits}={english}",
            failures,
        )


def check_language_contract(failures: list[str]) -> None:
    text = read("language-contract.lisp")
    require(
        "D2 is the sole owner of canonical language source/structural control"
        in text,
        "language contract does not state exclusive D2 structural ownership",
        failures,
    )
    require(
        "Transport framing metadata is mechanism only "
        "and never D2 semantic authority" in text,
        "language contract does not separate transport framing from D2 semantics",
        failures,
    )


def check_canonical_reader(failures: list[str]) -> None:
    text = read("crates/sens/src/canonical_reader.rs")
    markers = [
        "const D2_SEPARATOR: u8 = 0b00;",
        "const D2_CLOSE: u8 = 0b01;",
        "const D2_OPEN: u8 = 0b10;",
        "const D2_DOT: u8 = 0b11;",
        "BinarySourceWord::W2(word) => match word.packed_bits()",
        "D2 has already been consumed structurally above",
    ]
    for marker in markers:
        require(
            marker in text,
            f"canonical reader lost D2 structural marker: {marker}",
            failures,
        )


def check_exact_width_carriers(failures: list[str]) -> None:
    source_words = read("crates/sens/src/source_words.rs")
    require(
        "Structural roles remain language-owned; width is the only fact here."
        in source_words,
        "source-word carrier no longer separates width from D2 structural roles",
        failures,
    )

    packing = read("crates/sens/src/source_packing.rs")
    for marker in [
        "assigns no semantic roles and defines no wire framing",
        "caller-owned boundary information",
        "structural_bit_patterns_are_packed_as_payload_not_transport_delimiters",
    ]:
        require(
            marker in packing,
            f"source packing lost semantic/framing separation marker: {marker}",
            failures,
        )

    forbidden_backend_markers = [
        "D2_SEPARATOR",
        "D2_CLOSE",
        "D2_OPEN",
        "D2_DOT",
        "CONTROL_ESCAPE",
    ]
    for path in [
        "crates/sens/src/compiler_bootstrap.rs",
        "crates/sens/src/gpu_execution_packet.rs",
    ]:
        text = read(path)
        for marker in forbidden_backend_markers:
            require(
                marker not in text,
                f"backend/compiler carrier claims D2 structural control: "
                f"{path}: {marker}",
                failures,
            )


def check_migration(failures: list[str]) -> None:
    text = read("scripts/migrate-three-pass.py")
    markers = [
        "D2 words are reserved exclusively for structural control",
        "D2 word {t} is structural control only; "
        "it cannot be an executable head",
        "D2 word {t} is structural control only; "
        "it cannot be ordinary data",
        '"control_domain":"D2-only"',
    ]
    for marker in markers:
        require(
            marker in text,
            f"migration path lost D2-only rule: {marker}",
            failures,
        )


def check_surface_translation(failures: list[str]) -> None:
    text = read("scripts/translate-domain-program.py")
    require(
        "Structural labels are documentation only, never token rewrites." in text,
        "surface translator may be treating D2 labels as ordinary tokens",
        failures,
    )


def check_transport(spec: dict, failures: list[str]) -> None:
    framing = read("crates/sens/src/binary_framing.rs")
    wire_test = read("crates/sens/tests/text7_canonical_wire.rs")
    active = {
        "crates/sens/src/binary_framing.rs": framing,
        "crates/sens/tests/text7_canonical_wire.rs": wire_test,
    }

    for forbidden in spec["forbidden_active_claims"]:
        for path, text in active.items():
            require(
                forbidden not in text,
                f"active transport path still claims legacy language control: "
                f"{path}: {forbidden}",
                failures,
            )

    require(
        "not Core.D2 semantic objects" in framing,
        "transport framing lacks explicit D2 semantic separation",
        failures,
    )
    require(
        "current_d2_dot_round_trips_as_domain_identity_not_wire_escape"
        in framing,
        "transport framing lacks D2:11 non-alias witness",
        failures,
    )


def check_structure_inventory(failures: list[str]) -> None:
    text = read("knowledge/structure-not-ontology-inventory.lisp")
    require(
        "(dot . human-reader-only)" not in text,
        "active structure inventory still denies D2:11 dot",
        failures,
    )
    require(
        "(dot . d2-11)" in text,
        "active structure inventory does not record D2:11 dot",
        failures,
    )


def main() -> int:
    spec = json.loads(AUDIT.read_text(encoding="utf-8"))
    failures: list[str] = []

    check_d2_table(failures)
    check_language_contract(failures)
    check_canonical_reader(failures)
    check_exact_width_carriers(failures)
    check_migration(failures)
    check_surface_translation(failures)
    check_transport(spec, failures)
    check_structure_inventory(failures)

    if failures:
        for message in failures:
            print(f"FAIL {message}", file=sys.stderr)
        return 1

    print("OK D2 alone owns canonical language source/structural control")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
