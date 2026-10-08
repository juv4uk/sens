#!/usr/bin/env python3
"""Read canonical self-describing SENS domain tables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_TABLES = tuple(ROOT / "lib" / "domains" / f"d{width}.lisp" for width in range(1, 7))
D7_TABLE = ROOT / "lib" / "domains" / "d7.lisp"
D8_TABLE = ROOT / "lib" / "domains" / "d8.lisp"
D9_TABLE = ROOT / "lib" / "domains" / "d9.lisp"
CURRENT_HUMAN_TABLES = DOMAIN_TABLES + (D7_TABLE, D8_TABLE, D9_TABLE,)

TOKEN = r'(\(\)|"[^"]*"|[^()\s]+)'
ROW = re.compile(
    r'^\s*\(([01]{1,9})\s+'
    + r'\(ук\s+' + TOKEN + r'\)\s+'
    + r'\(укр\s+' + TOKEN + r'\)\s+'
    + r'\(san\s+' + TOKEN + r'\)\s+'
    + r'\(en\s+' + TOKEN + r'\)\s+'
    + r'\(LISP\s+' + TOKEN + r'\)\s+'
    + r'\(sym\s+' + TOKEN + r'\)\)\s*$'
)


@dataclass(frozen=True)
class DomainTableRow:
    domain: str
    width: int
    bits: str
    uk: str | None
    ukr: str | None
    san: str | None
    en: str | None
    lisp: str | None
    sym: str | None

    @property
    def role(self) -> str:
        if self.domain == "D2" or (self.domain == "D3" and self.bits == "000"):
            return "display"
        if self.en and self.en.endswith("?"):
            return "predicate"
        return "surface"


def decode(token: str) -> str | None:
    if token == "()":
        return None
    if token.startswith('"') and token.endswith('"'):
        return token[1:-1]
    return token


def read_domain_table(path: Path) -> list[DomainTableRow]:
    expected_width = int(path.stem.removeprefix("d"))
    rows: list[DomainTableRow] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if not stripped.startswith("(") or stripped.startswith("(domain-table/1"):
            continue
        match = ROW.match(line)
        if not match:
            if stripped.startswith(";") or stripped == ")":
                continue
            raise ValueError(f"{path}:{line_number}: malformed canonical domain-table row")
        bits, uk, ukr, san, en, lisp, sym = match.groups()
        if len(bits) != expected_width:
            raise ValueError(
                f"{path}:{line_number}: key width {len(bits)} != file domain width {expected_width}"
            )
        rows.append(
            DomainTableRow(
                domain=f"D{expected_width}",
                width=expected_width,
                bits=bits,
                uk=decode(uk),
                ukr=decode(ukr),
                san=decode(san),
                en=decode(en),
                lisp=decode(lisp),
                sym=decode(sym),
            )
        )
    expected = 126 if expected_width == 7 else 1 << expected_width
    if len(rows) != expected:
        raise ValueError(f"{path}: expected {expected} rows, found {len(rows)}")
    return rows


def read_domain_tables(paths=DOMAIN_TABLES) -> list[DomainTableRow]:
    rows: list[DomainTableRow] = []
    for path in paths:
        rows.extend(read_domain_table(Path(path)))
    return rows

def validate_ratified_ladder(data: dict, number_policy: dict | None = None) -> dict:
    """Audit current D1-D9 table authority before *any* historical migration.

    This is not an executable-head admission rule: D7 encodes text, D8/D9
    carry ratified residents but source-call admissibility is separate.
    """
    if data.get("status") != "owner-ratified":
        raise ValueError("domain ladder foundation is not owner-ratified")
    domains = data.get("domains", {})
    expected = {f"D{width}" for width in range(1, 10)}
    if not expected.issubset(domains):
        raise ValueError(f"missing ratified domains: {sorted(expected - set(domains))}")
    if "D10" in domains and domains["D10"].get("status") == "owner-ratified":
        raise ValueError("D10 has no ratified source authority")

    counts = {}
    for width in range(1, 10):
        label = f"D{width}"
        descriptor = domains[label]
        if int(descriptor["width"]) != width:
            raise ValueError(f"{label}: foundation bit width drift")
        residents = descriptor["residents"]
        if any(len(bits) != width or set(bits) - {"0", "1"} for bits in residents):
            raise ValueError(f"{label}: malformed exact-width resident")
        rows = read_domain_table(ROOT / "lib" / "domains" / f"d{width}.lisp")
        actual = [row.bits for row in rows]
        if len(set(actual)) != len(actual) or set(actual) != set(residents):
            raise ValueError(f"{label}: canonical table/foundation coordinate mismatch")
        counts[label] = len(actual)

    if domains["D1"]["residents"] != {"0": "NO", "1": "YES"}:
        raise ValueError("D1 predicate authority drift")
    if domains["D2"]["residents"] != {
        "00": "SEPARATOR", "01": "CLOSE", "10": "OPEN", "11": "DOT"
    }:
        raise ValueError("D2 structure authority drift")

    if number_policy is not None:
        if number_policy.get("status") != "owner-ratified":
            raise ValueError("Number width authority is not ratified")
        widths = number_policy.get("ratified_prefix_bits", [])
        if widths[:3] != [24, 48, 96] or any(
            later != prior * 2 for prior, later in zip(widths, widths[1:])
        ):
            raise ValueError("Number width ladder drift: expected D24/D48/D96 doubling")
        if number_policy.get("first_width_bits") != 24:
            raise ValueError("D24 Number initial width drift")
    return counts
