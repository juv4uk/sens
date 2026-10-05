#!/usr/bin/env python3
"""Guard the binding-only projection from existing Lisp definitions to ratified D5 identities."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "lib/surface/d5-definition-bindings.lisp"
GENERATED = ROOT / "crates/sens/src/d5_definition_bindings_generated.rs"
AUTHORITY = ROOT / "knowledge/d5-ratified.json"

ROW = re.compile(r'^\s*\(row\s+"([^"]+)"\s+"([01]{5})"\)\s*$')


def fail(message: str) -> None:
    raise SystemExit(f"D5-DEFINITION-BINDING-GUARD: FAIL: {message}")


def parse_rows() -> list[tuple[str, str]]:
    rows = []
    for line_number, line in enumerate(SOURCE.read_text(encoding="utf-8").splitlines(), 1):
        if not line.lstrip().startswith("(row "):
            continue
        match = ROW.match(line)
        if not match:
            fail(f"cannot parse row at line {line_number}")
        rows.append(match.groups())
    return rows


def render(rows: list[tuple[str, str]]) -> str:
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Authority: lib/surface/d5-definition-bindings.lisp",
        "// Checked by: scripts/check-d5-definition-bindings.py",
        "",
        "#[derive(Clone, Copy, Debug, Eq, PartialEq)]",
        "pub(super) struct D5DefinitionBinding {",
        "    pub(super) name: &'static str,",
        "    pub(super) bits: u8,",
        "}",
        "",
        "pub(super) const D5_DEFINITION_BINDINGS: &[D5DefinitionBinding] = &[",
    ]
    for name, bits in rows:
        lines.append(f'    D5DefinitionBinding {{ name: "{name}", bits: 0b{bits} }},')
    lines.append("];")
    return "\n".join(lines) + "\n"


def validate(rows: list[tuple[str, str]]) -> None:
    expected = {
        "reverse": ("10100", "REVERSE"),
        "reverse-onto": ("10101", "REVERSE-ONTO"),
        "quotient": ("10111", "QUOTIENT"),
        "assoc": ("11100", "ASSOC"),
        "member?": ("11101", "MEMBER"),
        "subst": ("11111", "SUBST"),
    }
    if dict(rows) != {name: bits for name, (bits, _) in expected.items()}:
        fail("binding projection differs from the approved first slice")
    if len(set(rows)) != len(rows):
        fail("duplicate binding row")

    residents = json.loads(AUTHORITY.read_text(encoding="utf-8"))["residents"]
    for name, (bits, resident) in expected.items():
        if residents.get(bits) != resident:
            fail(f"{name}: D5 authority drift at {bits}; expected {resident}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-generated", action="store_true")
    args = parser.parse_args()

    rows = parse_rows()
    validate(rows)
    expected = render(rows)
    if args.write_generated:
        GENERATED.write_text(expected, encoding="utf-8")
    elif GENERATED.read_text(encoding="utf-8") != expected:
        fail("generated Rust projection is stale")

    print("D5-DEFINITION-BINDING-GUARD: PASS")
    print("bindings=6 exact-d5=6 legacy-byte-authority=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
