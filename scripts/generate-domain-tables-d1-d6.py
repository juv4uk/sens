#!/usr/bin/env python3
"""Generate/check SENS8-like D1-D6 human tables from current exact-domain authority.

Semantic identity comes only from knowledge/d1-d7-foundation.json.
Legacy semantic-registry.lisp is used only as a lexical donor; its 8-bit rows
never select or renumber a current domain identity.

Canonical human column order:
    ук -> укр -> san -> eng -> LISP -> SUM
"""

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
)
LEGACY_DONOR = ROOT / "lib/surface/semantic-registry.lisp"
OUTPUT = ROOT / "docs/generated/domain-tables-d1-d6.md"

EXACT_ROW = re.compile(
    r'^\\s*\\(row\\s+(D[1-5])\\s+"([01]+)"\\s+(\\S+)\\s+'
    r'"([^"]+)"\\s+"([^"]+)"\\s+"([^"]+)"\\s+(\\S+)\\s+(\\S+)\\)\\s*$'
)
ATOM_TOKEN = r'(\\(\\)|"[^"]*"|[^()\\s]+)'
LEGACY_ROW = re.compile(
    r'^\\s*\\([01]{8}\\s+'
    + r'\\(en\\s+' + ATOM_TOKEN + r'\\)\\s+'
    + r'\\(ук\\s+' + ATOM_TOKEN + r'\\)\\s+'
    + r'\\(укр\\s+' + ATOM_TOKEN + r'\\)\\s+'
    + r'\\(sa\\s+' + ATOM_TOKEN + r'\\)'
)

HEADER = "| bits | ук | укр | san | eng | LISP | SUM |"
DIVIDER = "|---|---|---|---|---|---|---|"

D6_DONOR_ALIASES = {
    "LEQ": "not-greaterp?",
    "GEQ": "not-lessp?",
    "REMAINDER": "mod",
}


def atom(value: str) -> str | None:
    value = value.strip()
    if value == "()":
        return None
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def parse_exact() -> dict[tuple[str, str], dict[str, str]]:
    out: dict[tuple[str, str], dict[str, str]] = {}
    for path in SURFACE_SOURCES:
        for line in path.read_text(encoding="utf-8").splitlines():
            m = EXACT_ROW.match(line)
            if not m:
                continue
            domain, bits, role, eng, uk, san, _uk_status, _san_status = m.groups()
            out[(domain, bits)] = {"role": role, "eng": eng, "uk": uk, "san": san}
    return out


def parse_legacy_donor() -> dict[str, dict[str, str | None]]:
    out: dict[str, dict[str, str | None]] = {}
    for line in LEGACY_DONOR.read_text(encoding="utf-8").splitlines():
        m = LEGACY_ROW.match(line)
        if not m:
            continue
        eng, uk, ukr, san = (atom(x) for x in m.groups())
        if eng:
            out[eng.lower()] = {"uk": uk, "ukr": ukr, "san": san}
    return out


def lisp_label(domain: str, resident: str) -> str:
    if domain == "D1":
        return {"NO": "NIL", "YES": "T"}[resident]
    if domain == "D2":
        return "—"
    if domain == "D3" and resident == "EMPTY":
        return "NIL"
    return resident


def fallback_eng(resident: str) -> str:
    return resident.lower()


def render() -> str:
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    exact = parse_exact()
    legacy = parse_legacy_donor()

    lines = [
        "# Domain tables D1–D6",
        "",
        "**Authority:** `knowledge/d1-d7-foundation.json` (#3572).",
        "",
        "These are human projections only. Exact identity remains `bits + domain + ratified law`.",
        "The historical 8-bit registry is consulted only as a lexical donor and never as coordinate authority.",
        "",
        "Canonical surface order: **ук → укр → san → eng → LISP → SUM**.",
        "",
    ]

    total = 0
    for width in range(1, 7):
        domain = f"D{width}"
        info = foundation["domains"][domain]
        name = info["sanskrit_name"]
        residents = info["residents"]
        expected = 1 << width
        if len(residents) != expected:
            raise SystemExit(f"{domain}: expected {expected} residents, found {len(residents)}")

        lines += [f"## {name} ({domain})", "", HEADER, DIVIDER]

        for bits, resident in sorted(residents.items(), key=lambda item: int(item[0], 2)):
            current = exact.get((domain, bits))
            if current:
                eng = current["eng"]
                uk = current["uk"]
                san = current["san"]
            else:
                eng = fallback_eng(resident)
                uk = None
                san = None

            donor_key = D6_DONOR_ALIASES.get(resident, eng).lower()
            donor = legacy.get(donor_key, {})

            if not uk:
                uk = donor.get("uk")
            ukr = donor.get("ukr") or uk
            if not san:
                san = donor.get("san")

            uk = uk or "—"
            ukr = ukr or "—"
            san = san or "—"
            eng = eng or "—"
            lisp = lisp_label(domain, resident)
            summary = f"{name}:{bits}={resident}"

            lines.append(
                f"| `{bits}` | `{uk}` | `{ukr}` | `{san}` | "
                f"`{eng}` | `{lisp}` | `{summary}` |"
            )
            total += 1
        lines.append("")

    if total != 126:
        raise SystemExit(f"expected 126 D1-D6 rows, found {total}")

    text = "\n".join(lines).rstrip() + "\n"
    if HEADER not in text:
        raise SystemExit("canonical header missing")
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    generated = render()
    if args.write:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(generated, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        return 0

    if not OUTPUT.exists():
        raise SystemExit(f"missing generated file: {OUTPUT.relative_to(ROOT)}")
    current = OUTPUT.read_text(encoding="utf-8")
    if current != generated:
        raise SystemExit(
            "domain table drift: run python3 scripts/generate-domain-tables-d1-d6.py --write"
        )

    print("DOMAIN-TABLES-D1-D6: PASS")
    print("rows=126 order=ук->укр->san->eng->LISP->SUM identity=unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
