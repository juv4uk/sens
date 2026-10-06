#!/usr/bin/env python3
"""Generate/check D1-D6 tables in the same Lisp-first shape as SENS8."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / "knowledge/d1-d7-foundation.json"
SURFACE_SOURCES = (
    ROOT / "lib/surface/domain-surfaces-d1-d4.lisp",
    ROOT / "lib/surface/domain-surfaces-d5.lisp",
    ROOT / "lib/surface/domain-surfaces-d6.lisp",
)
LEGACY_LEXICAL_DONOR = ROOT / "lib/surface/semantic-registry.lisp"
LISP_OUTPUT = ROOT / "lib/generated/domain-table-d1-d6.lisp"
MD_OUTPUT = ROOT / "docs/generated/domain-tables-d1-d6.md"

COLUMNS = ["ук", "укр", "san", "eng", "LISP", "SUM"]
EMPTY = "()"
HEADER = "| bits | ук | укр | san | eng | LISP | SUM |"
DIVIDER = "|---|---|---|---|---|---|---|"

SURFACE_TOKEN = r'(\(\)|"[^"]*")'
EXACT_ROW = re.compile(
    r'^\s*\(row\s+(D[1-6])\s+"([01]+)"\s+(\S+)\s+'
    + SURFACE_TOKEN + r'\s+'
    + SURFACE_TOKEN + r'\s+'
    + SURFACE_TOKEN + r'\s+'
    + r'(\S+)\s+(\S+)\)\s*$'
)
LEGACY_ROW = re.compile(
    r'^\s*\([01]{8}\s+'
    + r'\(en\s+' + SURFACE_TOKEN + r'\)\s+'
    + r'\(ук\s+' + SURFACE_TOKEN + r'\)\s+'
    + r'\(укр\s+' + SURFACE_TOKEN + r'\)\s+'
    + r'\(sa\s+' + SURFACE_TOKEN + r'\)'
)


def fail(message: str) -> None:
    raise SystemExit(f"DOMAIN-TABLES-D1-D6: FAIL: {message}")


def decode(token: str) -> str | None:
    if token == EMPTY:
        return None
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    fail(f"bad token {token!r}")


def atom(value: str | None) -> str:
    if value is None or value == "":
        return EMPTY
    if any(ch.isspace() for ch in value) or any(ch in '()"' for ch in value):
        return json.dumps(value, ensure_ascii=False)
    return value


def load_exact() -> dict[tuple[str, str], dict[str, str | None]]:
    rows: dict[tuple[str, str], dict[str, str | None]] = {}
    for path in SURFACE_SOURCES:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.lstrip().startswith("(row "):
                continue
            m = EXACT_ROW.match(line)
            if not m:
                fail(f"cannot parse {path}:{line_no}")
            domain, bits, role, eng_t, uk_t, san_t, uk_status, san_status = m.groups()
            key = (domain, bits)
            if key in rows:
                fail(f"duplicate exact row {domain}:{bits}")
            rows[key] = {
                "role": role,
                "eng": decode(eng_t),
                "uk": decode(uk_t),
                "san": decode(san_t),
                "uk_status": uk_status,
                "san_status": san_status,
            }
    return rows


def load_ukr_donor() -> dict[str, str | None]:
    donor: dict[str, str | None] = {}
    for line in LEGACY_LEXICAL_DONOR.read_text(encoding="utf-8").splitlines():
        m = LEGACY_ROW.match(line)
        if not m:
            continue
        eng_t, _uk_t, ukr_t, _san_t = m.groups()
        eng = decode(eng_t)
        if eng:
            donor[eng.lower()] = decode(ukr_t)
    return donor


def lisp_label(domain: str, resident: str) -> str | None:
    if domain == "D1":
        return "NIL" if resident == "NO" else "T"
    if domain == "D2":
        return None
    if domain == "D3" and resident == "EMPTY":
        return "NIL"
    return resident


def validate(
    foundation: dict,
    exact: dict[tuple[str, str], dict[str, str | None]],
) -> None:
    total = 0
    for width in range(1, 7):
        domain = f"D{width}"
        current = foundation["domains"][domain]
        if not current.get("sanskrit_name"):
            fail(f"{domain}: missing sanskrit_name")
        expected_bits = sorted(current["residents"], key=lambda bits: int(bits, 2))
        if len(expected_bits) != (1 << width):
            fail(f"{domain}: authority is not dense {1 << width}/{1 << width}")
        for bits in expected_bits:
            row = exact.get((domain, bits))
            if row is None:
                fail(f"{domain}:{bits}: missing exact surface row")
            resident = current["residents"][bits]
            if row["eng"] is None:
                fail(f"{domain}:{bits}: English reference must be present")
            if row["eng"].upper() != resident:
                fail(
                    f"{domain}:{bits}: exact surface {row['eng']!r} "
                    f"!= resident {resident!r}"
                )
            total += 1
    if total != 126 or len(exact) != 126:
        fail(f"expected exactly 126 D1-D6 rows, got authority={total} exact={len(exact)}")


def iter_rows(
    foundation: dict,
    exact: dict[tuple[str, str], dict[str, str | None]],
    ukr_donor: dict[str, str | None],
):
    for width in range(1, 7):
        domain = f"D{width}"
        info = foundation["domains"][domain]
        name = info["sanskrit_name"]
        for bits, resident in sorted(
            info["residents"].items(), key=lambda item: int(item[0], 2)
        ):
            surface = exact[(domain, bits)]
            eng = surface["eng"]
            uk = surface["uk"]
            san = surface["san"]
            ukr = ukr_donor.get((eng or "").lower())
            if ukr is None:
                ukr = uk
            yield {
                "domain": domain,
                "name": name,
                "bits": bits,
                "formal": f"identity:{name}:{bits}",
                "uk": uk,
                "ukr": ukr,
                "san": san,
                "eng": eng,
                "lisp": lisp_label(domain, resident),
                "sum": f"{name}:{bits}={resident}",
            }


def render_lisp(all_rows: list[dict[str, str | None]]) -> str:
    out = [
        "; GENERATED — DO NOT EDIT BY HAND",
        "; Authority: knowledge/d1-d7-foundation.json (#3572)",
        "; Surface sources: lib/surface/domain-surfaces-d1-d4.lisp, domain-surfaces-d5.lisp, domain-surfaces-d6.lisp",
        "; Generator: scripts/generate-domain-tables-d1-d6.py",
        "; Schema domain-ft/1: (domain-name bits formal (ук ...) (укр ...) (san ...) (eng ...) (LISP ...) (SUM ...))",
        "; Display order: ук → укр → san → eng → LISP → SUM",
        "; Empty/missing surface: ()",
        "; Projection only: exact bits + exact domain + ratified law remain semantic authority",
        "",
        "(domain-ft/1",
    ]
    current_name = None
    for row in all_rows:
        if row["name"] != current_name:
            current_name = row["name"]
            out.append(f"  ; {row['name']} / {row['domain']}")
        out.append(
            "  ("
            + f"{row['name']} {row['bits']} {row['formal']}"
            + f" (ук {atom(row['uk'])})"
            + f" (укр {atom(row['ukr'])})"
            + f" (san {atom(row['san'])})"
            + f" (eng {atom(row['eng'])})"
            + f" (LISP {atom(row['lisp'])})"
            + f" (SUM {atom(row['sum'])})"
            + ")"
        )
    out += [")", ""]
    return "\n".join(out)


def render_md(all_rows: list[dict[str, str | None]]) -> str:
    out = [
        "# Domain tables D1–D6",
        "",
        "**Authority:** `knowledge/d1-d7-foundation.json` (#3572).",
        "",
        "**Machine-readable projection:** `lib/generated/domain-table-d1-d6.lisp`.",
        "",
        "Canonical surface order: **ук → укр → san → eng → LISP → SUM**.",
        "Empty/missing surface marker: `()`.",
        "",
    ]
    current_name = None
    for row in all_rows:
        if row["name"] != current_name:
            if current_name is not None:
                out.append("")
            current_name = row["name"]
            out += [
                f"## {row['name']} ({row['domain']})",
                "",
                HEADER,
                DIVIDER,
            ]
        cells = [
            row["uk"],
            row["ukr"],
            row["san"],
            row["eng"],
            row["lisp"],
            row["sum"],
        ]
        rendered = " | ".join(f"`{atom(value)}`" for value in cells)
        out.append(f"| `{row['bits']}` | {rendered} |")
    return "\n".join(out).rstrip() + "\n"


def write_or_check(path: Path, content: str, write: bool) -> None:
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
        return
    if not path.exists():
        fail(f"missing generated file {path.relative_to(ROOT)}")
    if path.read_text(encoding="utf-8") != content:
        fail(f"stale generated file {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    exact = load_exact()
    validate(foundation, exact)
    ukr_donor = load_ukr_donor()
    all_rows = list(iter_rows(foundation, exact, ukr_donor))

    if len(all_rows) != 126:
        fail(f"expected 126 generated rows, got {len(all_rows)}")

    write_or_check(LISP_OUTPUT, render_lisp(all_rows), args.write)
    write_or_check(MD_OUTPUT, render_md(all_rows), args.write)

    print("DOMAIN-TABLES-D1-D6: PASS")
    print("rows=126 form=SENS8-like-lisp-first order=ук->укр->san->eng->LISP->SUM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
