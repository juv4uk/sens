#!/usr/bin/env python3
"""Reject hand-maintained domain/source width routing in canonical Rust identity files."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ROOT / "crates/sens/src/source_words.rs",
    ROOT / "crates/sens/src/domain_identity.rs",
)

NUMERIC_WIDTH_ARM = re.compile(
    r"(?:Self|DomainIdentity|CoreDomainIdentity|BinarySourceWord)::"
    r"(?:D|W)\d+\([^\n]*?\)\s*=>\s*\d+\b"
)


def violations(text: str) -> list[str]:
    return [match.group(0) for match in NUMERIC_WIDTH_ARM.finditer(text)]


def self_test() -> None:
    assert violations("Self::D3(_) => 3,")
    assert violations("BinarySourceWord::W9(word) => 9,")
    assert violations("CoreDomainIdentity::D4(_) => 4,")
    assert not violations("Self::D3(_) => value.word().width(),")
    assert not violations("Self::W3(_) => Bit3::width(),")
    assert not violations("let width = certificate.width;")


def main() -> int:
    self_test()
    found: list[str] = []
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        for match in violations(text):
            found.append(f"{path.relative_to(ROOT)}: {match}")

    if found:
        print("WIDTH-AUTHORITY-BOUNDARY: FAIL")
        print("\n".join(found))
        print("Canonical Rust may preserve/consume width but may not mint Dn/Wn -> integer width tables.")
        return 1

    print("WIDTH-AUTHORITY-BOUNDARY: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
