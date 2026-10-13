#!/usr/bin/env python3
"""Guard the binding-only D6 definition projection from the ratified D6 table."""
from __future__ import annotations
import argparse
from pathlib import Path
from domain_tables import DOMAIN_TABLES, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
D6_TABLE = DOMAIN_TABLES[5]
GENERATED = ROOT / "crates/sens/src/d6_definition_bindings_generated.rs"

def fail(message: str) -> None:
    raise SystemExit(f"D6-DEFINITION-BINDINGS: FAIL: {message}")

def rust_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def names(row) -> list[str]:
    out: list[str] = []
    for value in (row.uk, row.ukr, row.san, row.en, row.lisp):
        if value is not None and value not in out:
            out.append(value)
    return out

def render() -> str:
    rows = read_domain_table(D6_TABLE)
    if len(rows) != 64 or {r.bits for r in rows} != {f"{n:06b}" for n in range(64)}:
        fail("D6 table must contain complete 64-coordinate coverage")
    seen: dict[str, str] = {}
    for row in rows:
        for name in names(row):
            old = seen.get(name)
            if old is not None and old != row.bits:
                fail(f"ambiguous definition name {name!r}: {old}/{row.bits}")
            seen[name] = row.bits
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Authority: lib/domains/d6.lisp (owner-ratified D6 residency).",
        "// Checked by: scripts/check-d6-definition-bindings.py",
        "// Binding-only: these rows do NOT grant generic D6 callability.",
        "",
        "#[derive(Clone, Copy, Debug, Eq, PartialEq)]",
        "pub(super) struct D6DefinitionBinding {",
        "    pub(super) bits: u8,",
        "    pub(super) names: &'static [&'static str],",
        "}",
        "",
        "pub(super) const D6_DEFINITION_BINDINGS: &[D6DefinitionBinding] = &[",
    ]
    for row in rows:
        ns = ", ".join(rust_string(name) for name in names(row))
        lines.append(f"    D6DefinitionBinding {{ bits: 0b{row.bits}, names: &[{ns}] }},")
    lines.append("];")
    return "\n".join(lines) + "\n"

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-generated", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.write_generated:
        GENERATED.write_text(expected, encoding="utf-8")
    elif not GENERATED.exists():
        fail(f"missing {GENERATED}")
    elif GENERATED.read_text(encoding="utf-8") != expected:
        fail("generated projection is stale; rerun with --write-generated")
    print("D6-DEFINITION-BINDINGS: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
