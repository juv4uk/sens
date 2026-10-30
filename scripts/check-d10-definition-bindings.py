#!/usr/bin/env python3
"""Перевірка binding-only проєкції конкретних D10-функцій і макросів SENS."""
from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parents[1]
GENERATED = ROOT / "crates/sens/src/d10_definition_bindings_generated.rs"
MIGRATOR = ROOT / "scripts/migrate-three-pass.py"


def fail(message: str) -> None:
    raise SystemExit(f"D10-DEFINITION-BINDINGS: FAIL: {message}")


def rust_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def concrete_d10_rows():
    """Reuse the migrator's parsed concrete library definition analysis."""
    spec = importlib.util.spec_from_file_location("sens_migrate_three_pass", MIGRATOR)
    if spec is None or spec.loader is None:
        fail(f"не вдалося завантажити аналіз конкретних D10-визначень: {MIGRATOR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.core4_d10_defined_rows()


def names(row) -> list[str]:
    result: list[str] = []
    for value in (row.uk, row.ukr, row.san, row.en, row.lisp, row.sym):
        if value is not None and value not in result:
            result.append(value)
    return result


def render() -> str:
    rows = concrete_d10_rows()
    if not rows:
        fail("бібліотеки SENS не мають конкретних D10-визначень для binding")
    seen: dict[str, str] = {}
    for bits, row in rows.items():
        if len(bits) != 10 or set(bits) - {"0", "1"}:
            fail(f"некоректна D10 identity у Core4 binding: {bits!r}")
        for name in names(row):
            old = seen.get(name)
            if old is not None and old != bits:
                fail(f"неоднозначне ім'я визначення {name!r}: {old}/{bits}")
            seen[name] = bits
    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Identity: lib/domains/d10.lisp; definitions: concrete SENS library closures and macros.",
        "// Binding-only: concrete definitions, never generic D10 callability.",
        "// Checked by: scripts/check-d10-definition-bindings.py",
        "",
        "#[derive(Clone, Copy, Debug, Eq, PartialEq)]",
        "pub(super) struct D10DefinitionBinding {",
        "    pub(super) bits: u16,",
        "    pub(super) names: &'static [&'static str],",
        "}",
        "",
        "pub(super) const D10_DEFINITION_BINDINGS: &[D10DefinitionBinding] = &[",
    ]
    for bits, row in sorted(rows.items()):
        ns = ", ".join(rust_string(name) for name in names(row))
        lines.append(f"    D10DefinitionBinding {{ bits: 0b{bits}, names: &[{ns}] }},")
    lines.append("];")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-generated", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.write_generated:
        GENERATED.write_text(expected, encoding="utf-8")
    elif not GENERATED.exists() or GENERATED.read_text(encoding="utf-8") != expected:
        fail("згенерований binding застарів; запусти --write-generated")
    print("D10-DEFINITION-BINDINGS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
