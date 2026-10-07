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


def fail(message: str, failures: list[str]) -> None:
    failures.append(message)


def main() -> int:
    spec = json.loads(AUDIT.read_text(encoding="utf-8"))
    failures: list[str] = []

    d2 = (ROOT / "lib/domains/d2.lisp").read_text(encoding="utf-8")
    expected = {
        "00": "separator",
        "01": "close",
        "10": "open",
        "11": "dot",
    }
    for bits, en in expected.items():
        pattern = rf"^\s*\({bits}\s+.*?\(en\s+{re.escape(en)}\)"
        if re.search(pattern, d2, flags=re.MULTILINE) is None:
            fail(f"D2 law missing or changed: {bits}={en}", failures)

    contract = (ROOT / "language-contract.lisp").read_text(encoding="utf-8")
    exclusive_owner = (
        "D2 is the sole owner of canonical language source/structural control"
    )
    transport_boundary = (
        "Transport framing metadata is mechanism only "
        "and never D2 semantic authority"
    )
    if exclusive_owner not in contract:
        fail(
            "language contract does not state exclusive D2 structural ownership",
            failures,
        )
    if transport_boundary not in contract:
        fail(
            "language contract does not separate transport framing from D2 semantics",
            failures,
        )

    reader = (ROOT / "crates/sens/src/canonical_reader.rs").read_text(
        encoding="utf-8"
    )
    required_reader = [
        "const D2_SEPARATOR: u8 = 0b00;",
        "const D2_CLOSE: u8 = 0b01;",
        "const D2_OPEN: u8 = 0b10;",
        "const D2_DOT: u8 = 0b11;",
        "BinarySourceWord::W2(word) => match word.packed_bits()",
        "D2 has already been consumed structurally above",
    ]
    for marker in required_reader:
        if marker not in reader:
            fail(f"canonical reader lost D2 structural marker: {marker}", failures)

    migrate = (ROOT / "scripts/migrate-three-pass.py").read_text(
        encoding="utf-8"
    )
    required_migrate = [
        "D2 words are reserved exclusively for structural control",
        "D2 word {t} is structural control only; it cannot be an executable head",
        "D2 word {t} is structural control only; it cannot be ordinary data",
        '"control_domain":"D2-only"',
    ]
    for marker in required_migrate:
        if marker not in migrate:
            fail(f"migration path lost D2-only rule: {marker}", failures)

    translator = (ROOT / "scripts/translate-domain-program.py").read_text(
        encoding="utf-8"
    )
    if "Structural labels are documentation only, never token rewrites." not in translator:
        fail("surface translator may be treating D2 labels as ordinary tokens", failures)

    framing_path = ROOT / "crates/sens/src/binary_framing.rs"
    framing = framing_path.read_text(encoding="utf-8")
    wire_test = (
        ROOT / "crates/sens/tests/text7_canonical_wire.rs"
    ).read_text(encoding="utf-8")
    for forbidden in spec["forbidden_active_claims"]:
        for rel, text in [
            ("crates/sens/src/binary_framing.rs", framing),
            ("crates/sens/tests/text7_canonical_wire.rs", wire_test),
        ]:
            if forbidden in text:
                fail(
                    f"active transport path still claims legacy language control: "
                    f"{rel}: {forbidden}",
                    failures,
                )
    if "not Core.D2 semantic objects" not in framing:
        fail("transport framing lacks explicit D2 semantic separation", failures)

    inventory = (ROOT / "knowledge/structure-not-ontology-inventory.lisp").read_text(
        encoding="utf-8"
    )
    if "(dot . human-reader-only)" in inventory:
        fail("active structure inventory still denies D2:11 dot", failures)
    if "(dot . d2-11)" not in inventory:
        fail("active structure inventory does not record D2:11 dot", failures)

    if failures:
        for message in failures:
            print(f"FAIL {message}", file=sys.stderr)
        return 1

    print("OK D2 alone owns canonical language source/structural control")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
