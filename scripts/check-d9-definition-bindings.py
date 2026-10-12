#!/usr/bin/env python3
"""Guard the binding-only D9 definition projection from the ratified D9 table."""
from __future__ import annotations
import argparse
from pathlib import Path
from domain_tables import D9_TABLE, read_domain_table

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "crates/sens/src/d9_definition_bindings_generated.rs"

def fail(message: str) -> None:
    raise SystemExit(f"D9-DEFINITION-BINDINGS: FAIL: {message}")

def rust_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def names(row) -> list[str]:
    out: list[str] = []
    for value in (row.uk, row.ukr, row.san, row.en, row.lisp):
        if value is not None and value not in out:
            out.append(value)
    return out

def render() -> str:
    rows = read_domain_table(D9_TABLE)
    if len(rows) != 512 or {r.bits for r in rows} != {f"{n:09b}" for n in range(512)}:
        fail("D9 table must contain complete 512-coordinate coverage")
    seen: dict[str, str] = {}
    for row in rows:
        for name in names(row):
            old = seen.get(name)
            if old is not None and old != row.bits:
                fail(f"ambiguous definition name {name!r}: {old}/{row.bits}")
            seen[name] = row.bits
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Authority: lib/domains/d9.lisp (owner-ratified D9 residency).",
        "// Checked by: scripts/check-d9-definition-bindings.py",
        "// Binding-only: these rows do NOT grant generic D9 callability.",
        "",
        "#[derive(Clone, Copy, Debug, Eq, PartialEq)]",
        "pub(super) struct D9DefinitionBinding {",
        "    pub(super) bits: u16,",
        "    pub(super) names: &'static [&'static str],",
        "}",
        "",
        "pub(super) const D9_DEFINITION_BINDINGS: &[D9DefinitionBinding] = &[",
    ]
    for row in rows:
        ns = ", ".join(rust_string(name) for name in names(row))
        lines.append(f"    D9DefinitionBinding {{ bits: 0b{row.bits}, names: &[{ns}] }},")
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
    print("D9-DEFINITION-BINDINGS: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
