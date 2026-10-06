#!/usr/bin/env python3
"""Generate/check the self-describing exact-width D1-D6 table."""

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
LEXICAL_DONOR = ROOT / "lib/surface/semantic-registry.lisp"
LISP_OUTPUT = ROOT / "lib/generated/domain-table-d1-d6.lisp"
MD_OUTPUT = ROOT / "docs/generated/domain-tables-d1-d6.md"

EMPTY = "()"
COLUMNS = ["ук", "укр", "san", "en", "LISP", "sym"]
TOKEN = r'(?:\(\)|"[^"]*"|[^()\s]+)'
ROW = re.compile(
    r'^\s*\(row\s+(D[1-6])\s+"([01]+)"\s+(\S+)\s+'
    + TOKEN + r'\s+' + TOKEN + r'\s+' + TOKEN
    + r'\s+(\S+)\s+(\S+)\)\s*$'
)
DONOR = re.compile(
    r'^\s*\([01]{8}\s+'
    + r'\(en\s+' + TOKEN + r'\)\s+'
    + r'\(ук\s+' + TOKEN + r'\)\s+'
    + r'\(укр\s+' + TOKEN + r'\)\s+'
    + r'\(sa\s+' + TOKEN + r'\)\s+'
    + r'\(sym\s+' + TOKEN + r'\)'
)


def fail(message: str) -> None:
    raise SystemExit(f"DOMAIN-TABLES-D1-D6: FAIL: {message}")


def decode(token: str) -> str | None:
    if token == EMPTY:
        return None
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    return token


def atom(value: str | None) -> str:
    if value is None or value == "":
        return EMPTY
    if value == "'" or any(ch.isspace() for ch in value) or any(ch in '()"' for ch in value):
        return json.dumps(value, ensure_ascii=False)
    return value


def load_exact() -> dict[tuple[str, str], dict[str, str | None]]:
    out: dict[tuple[str, str], dict[str, str | None]] = {}
    for path in SURFACE_SOURCES:
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.lstrip().startswith("(row "):
                continue
            m = ROW.match(line)
            if not m:
                fail(f"cannot parse {path}:{line_no}")
            domain, bits, _role, en_t, uk_t, san_t, _uk_status, _san_status = m.groups()
            key = (domain, bits)
            if key in out:
                fail(f"duplicate exact row {domain}:{bits}")
            out[key] = {"en": decode(en_t), "uk": decode(uk_t), "san": decode(san_t)}
    return out


def load_donor() -> dict[str, dict[str, str | None]]:
    out: dict[str, dict[str, str | None]] = {}
    for line in LEXICAL_DONOR.read_text(encoding="utf-8").splitlines():
        m = DONOR.match(line)
        if not m:
            continue
        en_t, uk_t, ukr_t, sa_t, sym_t = m.groups()
        en = decode(en_t)
        if en:
            out[en.lower()] = {
                "uk": decode(uk_t),
                "ukr": decode(ukr_t),
                "san": decode(sa_t),
                "sym": decode(sym_t),
            }
    return out


def lisp_name(domain: str, resident: str) -> str | None:
    if domain == "D1":
        return "NIL" if resident == "NO" else "T"
    if domain == "D2":
        return None
    if domain == "D3" and resident == "EMPTY":
        return "NIL"
    return resident


def build_rows(foundation: dict, exact: dict, donor: dict) -> list[dict]:
    rows: list[dict] = []
    for width in range(1, 7):
        domain = f"D{width}"
        residents = foundation["domains"][domain]["residents"]
        if len(residents) != (1 << width):
            fail(f"{domain}: expected {1 << width} residents")
        for bits, resident in sorted(residents.items(), key=lambda item: int(item[0], 2)):
            current = exact.get((domain, bits))
            if current is None:
                fail(f"{domain}:{bits}: missing exact surface row")
            en = current["en"]
            if en is None or en.upper() != resident:
                fail(f"{domain}:{bits}: en/resident drift")
            old = donor.get(en.lower(), {})
            rows.append(
                {
                    "bits": bits,
                    "ук": current["uk"],
                    "укр": old.get("ukr") if old.get("ukr") is not None else current["uk"],
                    "san": current["san"],
                    "en": en,
                    "LISP": lisp_name(domain, resident),
                    "sym": old.get("sym"),
                }
            )
    if len(rows) != 126:
        fail(f"expected 126 rows, got {len(rows)}")
    if len({row["bits"] for row in rows}) != 126:
        fail("exact-width binary keys must be unique by spelling")
    return rows


def render_lisp(rows: list[dict]) -> str:
    out = [
        "; GENERATED — DO NOT EDIT BY HAND",
        "; Self-describing exact-width domain table.",
        "; Binary key width is the domain address; no redundant semantic label is repeated.",
        "; Columns: ук → укр → san → en → LISP → sym",
        "; Empty/missing: ()",
        "",
        "(domains/1",
    ]
    for row in rows:
        out.append(
            f"  ({row['bits']}"
            + f" (ук {atom(row['ук'])})"
            + f" (укр {atom(row['укр'])})"
            + f" (san {atom(row['san'])})"
            + f" (en {atom(row['en'])})"
            + f" (LISP {atom(row['LISP'])})"
            + f" (sym {atom(row['sym'])}))"
        )
    out += [")", ""]
    return "\n".join(out)


def render_md(rows: list[dict]) -> str:
    out = [
        "# Exact-width domain table",
        "",
        "Binary key width identifies the domain. Rows repeat no domain or resident label.",
        "",
        "Columns: **ук → укр → san → en → LISP → sym**. Empty/missing: `()`.",
        "",
        "| bits | ук | укр | san | en | LISP | sym |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        cells = [row[name] for name in COLUMNS]
        rendered = " | ".join(f"`{atom(value)}`" for value in cells)
        out.append(f"| `{row['bits']}` | {rendered} |")
    return "\n".join(out) + "\n"


def write_or_check(path: Path, content: str, write: bool) -> None:
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
        return
    if not path.exists():
        fail(f"missing {path.relative_to(ROOT)}")
    if path.read_text(encoding="utf-8") != content:
        fail(f"stale {path.relative_to(ROOT)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    rows = build_rows(foundation, load_exact(), load_donor())
    write_or_check(LISP_OUTPUT, render_lisp(rows), args.write)
    write_or_check(MD_OUTPUT, render_md(rows), args.write)

    print("DOMAIN-TABLES-D1-D6: PASS")
    print("rows=126 columns=ук->укр->san->en->LISP->sym")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
