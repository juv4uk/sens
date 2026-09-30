#!/usr/bin/env python3
"""Generate SENS Text7 layout projection from pinned shiva-sutras authority."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "contracts/text7-upc7.lock"
OUTPUT = ROOT / "crates/sens/src/text7_projection_generated.rs"


def quoted_field(text: str, name: str) -> str:
    match = re.search(r"\(" + re.escape(name) + r'\s+"([^"]+)"\)', text)
    if not match:
        raise SystemExit(f"missing {name!r} in {LOCK}")
    return match.group(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_spelling(raw: str) -> str:
    return {
        r"\x20": " ",
        r"\x0a": "\n",
        r"\x09": "\t",
        r"\\": "\\",
    }.get(raw, raw)


def rust_string(text: str) -> str:
    out = ['"']
    for ch in text:
        code = ord(ch)
        if ch == '"':
            out.append(r'\"')
        elif ch == "\\":
            out.append(r"\\")
        elif ch == "\n":
            out.append(r"\n")
        elif ch == "\r":
            out.append(r"\r")
        elif ch == "\t":
            out.append(r"\t")
        elif code < 0x20 or code == 0x7F:
            out.append(f"\\u{{{code:x}}}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def direct_from_table(path: Path, column: str) -> dict[int, str]:
    out: dict[int, str] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            spelling = row[column]
            if spelling:
                out[int(row["bits"], 2)] = table_spelling(spelling)
    return out


def expanded_candidates(layout) -> list[tuple[str, tuple[int, ...] | None]]:
    direct = layout.spelling_to_code
    candidates: dict[str, tuple[int, ...] | None] = {
        spelling: (code,) for spelling, code in direct.items()
    }

    def add(spelling: str, parts) -> None:
        cells = tuple(direct[part] for part in parts)
        previous = candidates.get(spelling)
        if previous is not None and previous != cells:
            raise SystemExit(f"conflicting projection for {layout.name}:{spelling!r}")
        candidates[spelling] = cells

    for spelling, parts in layout.sequences.items():
        add(spelling, parts)
    for spelling, parts in layout.input_aliases.items():
        add(spelling, parts)
    for spelling in layout.known_unassigned:
        if spelling in candidates:
            raise SystemExit(f"assigned/unassigned collision for {layout.name}:{spelling!r}")
        candidates[spelling] = None

    return sorted(candidates.items(), key=lambda item: (-len(item[0]), item[0]))


def render_projection(layout) -> list[str | None]:
    return [layout.code_to_spelling.get(code) for code in range(128)]


def render_candidate(spelling: str, cells: tuple[int, ...] | None) -> str:
    if cells is None:
        value = "None"
    else:
        encoded = ", ".join(f"0x{cell:02x}" for cell in cells)
        value = f"Some(&[{encoded}])"
    return f"    ({rust_string(spelling)}, {value}),"


def render_table(name: str, layout) -> list[str]:
    upper = name.upper().replace("-", "_")
    lines = [
        f"pub(crate) const {upper}_ENCODE: &[(&str, Option<&[u8]>)] = &["
    ]
    lines.extend(render_candidate(spelling, cells) for spelling, cells in expanded_candidates(layout))
    lines.append("];")
    lines.append("")
    lines.append(f"pub(crate) const {upper}_RENDER: &[Option<&str>; 128] = &[")
    for spelling in render_projection(layout):
        value = "None" if spelling is None else f"Some({rust_string(spelling)})"
        lines.append(f"    {value},")
    lines.append("];")
    return lines


def generate(upstream_root: Path) -> str:
    lock = LOCK.read_text(encoding="utf-8")
    revision = quoted_field(lock, "revision")
    table_rel = quoted_field(lock, "path")
    table_hash = quoted_field(lock, "sha256")
    layout_rel = quoted_field(lock, "layout-path")
    layout_hash = quoted_field(lock, "layout-sha256")

    table = upstream_root / table_rel
    layout_source = upstream_root / layout_rel
    for path, expected in ((table, table_hash), (layout_source, layout_hash)):
        if not path.is_file():
            raise SystemExit(f"missing pinned upstream file: {path}")
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"sha256 mismatch for {path}: {actual} != {expected}")

    prototype = upstream_root / "prototype"
    sys.path.insert(0, str(prototype))
    try:
        upstream = importlib.import_module("upc7_layouts")
    finally:
        sys.path.pop(0)

    layouts = upstream.build_layouts()
    for name, column in (("uk", "uk"), ("sa-slp1", "sa-slp1")):
        actual = dict(layouts[name].code_to_spelling)
        tabular = direct_from_table(table, column)
        if actual != tabular:
            raise SystemExit(f"{name} direct layout disagrees with pinned machine table")

    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Authority: pinned juv4uk/shiva-sutras UPC-7 projection.",
        "// Generator: scripts/generate-text7-projection.py",
        f'pub(crate) const UPC7_SOURCE_REVISION: &str = "{revision}";',
        f'pub(crate) const UPC7_TABLE_SHA256: &str = "{table_hash}";',
        f'pub(crate) const UPC7_LAYOUT_SHA256: &str = "{layout_hash}";',
        "",
    ]
    lines.extend(render_table("uk", layouts["uk"]))
    lines.append("")
    lines.extend(render_table("sa-slp1", layouts["sa-slp1"]))
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    generated = generate(args.upstream_root.resolve())
    if args.check:
        if not OUTPUT.is_file():
            print(f"missing generated projection: {OUTPUT}", file=sys.stderr)
            return 1
        current = OUTPUT.read_text(encoding="utf-8")
        if current != generated:
            print("Text7 projection is stale; regenerate it.", file=sys.stderr)
            return 1
        return 0

    OUTPUT.write_text(generated, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
