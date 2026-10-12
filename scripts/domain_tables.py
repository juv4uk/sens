#!/usr/bin/env python3
"""Read canonical self-describing SENS domain tables."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_TABLES = tuple(ROOT / "lib" / "domains" / f"d{width}.lisp" for width in range(1, 7))
D7_TABLE = ROOT / "lib" / "domains" / "d7.lisp"
D8_TABLE = ROOT / "lib" / "domains" / "d8.lisp"
D9_TABLE = ROOT / "lib" / "domains" / "d9.lisp"
D10_TABLE = ROOT / "lib" / "domains" / "d10.lisp"
CURRENT_HUMAN_TABLES = DOMAIN_TABLES + (D7_TABLE, D8_TABLE, D9_TABLE, D10_TABLE,)

TOKEN_VALUE = r'(?:\(\)|"(?:[^"\\]|\\.)*"|[^()\s]+)'
TOKEN = rf'({TOKEN_VALUE})'
ROW = re.compile(
    r'^\s*\(([01]{1,10})\s+'
    + r'\(ук\s+' + TOKEN + r'\)\s+'
    + r'\(укр\s+' + TOKEN + r'\)\s+'
    + r'\(san\s+' + TOKEN + r'\)\s+'
    + r'\(en\s+' + TOKEN + r'\)\s+'
    + r'\(LISP\s+' + TOKEN + r'\)\s+'
    + r'\(sym\s+' + TOKEN + r'\)\)\s*$'
)

# D7 stores symbols by presentation surface inside the sym field. Other domain
# tables continue to use a single sym token; the reader supports both layouts.
SYMBOL_NAMES = ("ук", "укр", "san", "en", "LISP", "sym")
ROW_SYMBOL_MAP = re.compile(
    r'^\s*\(([01]{1,10})\s+'
    + r'\(ук\s+' + TOKEN + r'\)\s+'
    + r'\(укр\s+' + TOKEN + r'\)\s+'
    + r'\(san\s+' + TOKEN + r'\)\s+'
    + r'\(en\s+' + TOKEN + r'\)\s+'
    + r'\(LISP\s+' + TOKEN + r'\)\s+'
    + r'\(sym\s+\(\s*'
    + r'\(ук\s+' + TOKEN + r'\)\s+'
    + r'\(укр\s+' + TOKEN + r'\)\s+'
    + r'\(san\s+' + TOKEN + r'\)\s+'
    + r'\(en\s+' + TOKEN + r'\)\s+'
    + r'\(LISP\s+' + TOKEN + r'\)\s+'
    + r'\(sym\s+' + TOKEN + r'\)\s*'
    + r'\)\)\)\s*$'
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
    surface_symbols: dict[str, str | None] | None = None

    @property
    def role(self) -> str:
        if self.domain == "D2" or (self.domain == "D3" and self.bits == "000"):
            return "display"
        if self.en and self.en.endswith("?"):
            return "predicate"
        return "surface"


def decode(token: str, *, literal_empty: bool = False) -> str | None:
    if token == "()":
        return "()" if literal_empty else None
    if token.startswith('"') and token.endswith('"'):
        return ast.literal_eval(token)
    return token


def read_domain_table(path: Path) -> list[DomainTableRow]:
    expected_width = int(path.stem.removeprefix("d"))
    rows: list[DomainTableRow] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if not stripped.startswith("(") or stripped.startswith("(domain-table/1"):
            continue
        symbol_map_match = ROW_SYMBOL_MAP.match(line)
        match = symbol_map_match or ROW.match(line)
        if not match:
            if stripped.startswith(";") or stripped == ")":
                continue
            raise ValueError(f"{path}:{line_number}: malformed canonical domain-table row")
        groups = match.groups()
        bits, uk, ukr, san, en, lisp = groups[:6]
        # D3:000 is a literal structural value, not a missing projection.
        literal_empty = expected_width == 3 and bits == "000"
        if len(bits) != expected_width:
            raise ValueError(
                f"{path}:{line_number}: key width {len(bits)} != file domain width {expected_width}"
            )
        if symbol_map_match:
            glyph_values = groups[6:]
            if len(glyph_values) != len(SYMBOL_NAMES):
                raise ValueError(f"{path}:{line_number}: incomplete surface glyph map")
            symbols = {
                name: decode(value, literal_empty=literal_empty)
                for name, value in zip(SYMBOL_NAMES, glyph_values, strict=True)
            }
            rows.append(
                DomainTableRow(
                    domain=f"D{expected_width}",
                    width=expected_width,
                    bits=bits,
                    uk=decode(uk, literal_empty=literal_empty),
                    ukr=decode(ukr, literal_empty=literal_empty),
                    san=decode(san, literal_empty=literal_empty),
                    en=decode(en, literal_empty=literal_empty),
                    lisp=decode(lisp, literal_empty=literal_empty),
                    sym=symbols["sym"],
                    surface_symbols=symbols,
                )
            )
        else:
            sym = groups[6]
            rows.append(
                DomainTableRow(
                    domain=f"D{expected_width}",
                    width=expected_width,
                    bits=bits,
                    uk=decode(uk, literal_empty=literal_empty),
                    ukr=decode(ukr, literal_empty=literal_empty),
                    san=decode(san, literal_empty=literal_empty),
                    en=decode(en, literal_empty=literal_empty),
                    lisp=decode(lisp, literal_empty=literal_empty),
                    sym=decode(sym, literal_empty=literal_empty),
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
