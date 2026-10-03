#!/usr/bin/env python3
"""Generate the canonical domain-first surface projection.

Identity authority:
- Contract 11 D3/D4 maps;
- knowledge/d5-historical-full-map.json;
- knowledge/d6-historical-full-map.json.

lib/surface/semantic-registry.lisp is read only as a donor of human spellings.
Its historical eight-bit coordinates are ignored for identity. When a ratified
domain role already has an implementation on the old backend, the generator
may carry that byte only as an explicitly named compatibility mechanism.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ROOT / "lib" / "surface" / "semantic-registry.lisp"
D5 = ROOT / "knowledge" / "d5-historical-full-map.json"
D6 = ROOT / "knowledge" / "d6-historical-full-map.json"
OUT = ROOT / "crates" / "sens" / "src" / "domain_surface_registry_generated.rs"

D3 = {
    "QUOTE": "001",
    "ATOM": "010",
    "COND": "011",
    "CONS": "100",
    "CAR": "101",
    "CDR": "110",
    "EQ": "111",
}

D4 = {
    "APPLY": "0000",
    "EVAL": "0001",
    "LAMBDA": "0010",
    "DEFINE": "0011",
    "NOT": "0100",
    "EVCON": "0110",
    "EVLIS": "0111",
    "LIST": "1000",
    "CAAR": "1010",
    "CADR": "1011",
    "CDAR": "1100",
    "CDDR": "1101",
    "LOOKUP": "1110",
    "BIND": "1111",
}

ALIASES = {
    "ATOM": ["atom?"],
    "EQ": ["eq?"],
    "NOT": ["not?"],
    "ZEROP": ["zero?", "zerop?"],
    "NUMBERP": ["number?", "numberp?"],
    "EVENP": ["even?", "evenp?"],
    "ODDP": ["odd?", "oddp?"],
    "INTEGERP": ["integer?", "integerp?"],
    "RATIONALP": ["rational?", "rationalp?"],
    "LESSP": ["lessp?", "less?"],
    "GREATERP": ["greaterp?", "greater?"],
    "LEQ": ["not-greaterp?", "leq?"],
    "GEQ": ["not-lessp?", "geq?"],
    "QUOTIENT": ["quotient", "divide"],
    "SETQ": ["setq"],
    "SET": ["set"],
    "DEFVAR": ["defvar"],
    "NULL": ["null?"],
    "MEMBER": ["member?"],
}

ROW_RE = re.compile(r"^\s*\(([01]{8})\s+(.*)\)\s*$")
SURFACE_RE = re.compile(
    r'\((en|ук|укр|sa|sym)\s+((?:"(?:\\.|[^"])*"|[^\s()]+|\(\)))\)'
)


def decode_atom(value: str) -> str | None:
    value = value.strip()
    if value == "()":
        return None
    if value.startswith('"') and value.endswith('"'):
        return json.loads(value)
    return value


def old_surface_rows() -> list[dict]:
    rows = []
    for line in SURFACES.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line)
        if not match:
            continue
        surfaces = []
        for namespace, raw in SURFACE_RE.findall(match.group(2)):
            value = decode_atom(raw)
            if value is not None:
                surfaces.append((namespace, value))
        en = next((name for namespace, name in surfaces if namespace == "en"), None)
        rows.append({
            "legacy_backend_byte": int(match.group(1), 2),
            "en": en,
            "surfaces": surfaces,
        })
    if len(rows) != 256:
        raise SystemExit(f"expected 256 historical surface rows, got {len(rows)}")
    return rows


def domain_roles() -> list[dict]:
    rows = [
        {"width": 3, "bits": bits, "name": name}
        for name, bits in D3.items()
    ]
    rows.extend(
        {"width": 4, "bits": bits, "name": name}
        for name, bits in D4.items()
    )
    for width, path in [(5, D5), (6, D6)]:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data["width"] != width:
            raise SystemExit(f"{path}: width mismatch")
        for row in data["coordinates"]:
            rows.append(
                {"width": width, "bits": row["coordinate"], "name": row["name"]}
            )
    return rows


def candidates(name: str) -> list[str]:
    out = [name.lower(), *ALIASES.get(name, [])]
    if name.endswith("P") and len(name) > 1:
        base = name[:-1].lower()
        out.extend([f"{base}?", f"{name.lower()}?"])
    return list(dict.fromkeys(out))


def rust_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def generate() -> str:
    old = {row["en"]: row for row in old_surface_rows() if row["en"]}
    seen_surface: dict[str, str] = {}
    generated = []

    for role in domain_roles():
        surfaces = [("core", role["name"].lower())]
        backend_bytes: set[int] = set()
        for candidate in candidates(role["name"]):
            donor = old.get(candidate)
            if donor:
                surfaces.extend(donor["surfaces"])
                backend_bytes.add(donor["legacy_backend_byte"])

        if len(backend_bytes) > 1:
            raise SystemExit(
                f'{role["name"]}: multiple historical backend bytes: {sorted(backend_bytes)}'
            )
        legacy_backend_byte = next(iter(backend_bytes), None)

        unique = []
        local = set()
        for namespace, name in surfaces:
            pair = (namespace, name)
            if pair in local:
                continue
            local.add(pair)
            unique.append(pair)

            identity = f'D{role["width"]}:{role["bits"]}'
            previous = seen_surface.get(name)
            if previous is not None and previous != identity:
                raise SystemExit(
                    f"ambiguous surface {name!r}: {previous} versus {identity}"
                )
            seen_surface[name] = identity

        generated.append({
            **role,
            "legacy_backend_byte": legacy_backend_byte,
            "surfaces": unique,
        })

    lines = [
        "// GENERATED — DO NOT EDIT BY HAND.",
        "// Authority: Contract 11 D3/D4 + D5/D6 owner maps.",
        "// Surface aliases may be donated by lib/surface/semantic-registry.lisp,",
        "// but legacy byte positions never determine domain identity.",
        "// Generator: scripts/generate-domain-surface-registry.py",
        "",
        "#[derive(Clone, Copy, Debug, Eq, PartialEq)]",
        "pub(super) struct DomainSurfaceRow {",
        "    pub(super) width: u8,",
        "    pub(super) bits: u8,",
        "    pub(super) role: &'static str,",
        "    // Compatibility implementation coordinate only; never identity.",
        "    pub(super) legacy_backend_byte: Option<u8>,",
        "    pub(super) surfaces: &'static [&'static str],",
        "}",
        "",
        "pub(super) const DOMAIN_SURFACE_ROWS: &[DomainSurfaceRow] = &[",
    ]
    for row in generated:
        surfaces = ", ".join(rust_string(name) for _, name in row["surfaces"])
        backend = (
            "None"
            if row["legacy_backend_byte"] is None
            else f'Some(0b{row["legacy_backend_byte"]:08b})'
        )
        lines.append(
            f'    DomainSurfaceRow {{ width: {row["width"]}, bits: 0b{row["bits"]}, '
            f'role: {rust_string(row["name"])}, legacy_backend_byte: {backend}, '
            f'surfaces: &[{surfaces}] }},'
        )
    lines.extend(["];", ""])
    return "\n".join(lines)


def main() -> None:
    generated = generate()
    if "--check" in __import__("sys").argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != generated:
            raise SystemExit("domain surface registry is stale; regenerate it")
        print("DOMAIN-SURFACE-REGISTRY: PASS")
        return
    OUT.write_text(generated, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
