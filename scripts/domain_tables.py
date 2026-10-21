#!/usr/bin/env python3
"""Read canonical self-describing SENS domain tables."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOMAIN_TABLES = tuple(ROOT / "lib" / "domains" / f"d{width}.lisp" for width in range(1, 7))
D7_TABLE = ROOT / "lib" / "domains" / "d7.lisp"
D8_TABLE = ROOT / "lib" / "domains" / "d8.lisp"
D9_TABLE = ROOT / "lib" / "domains" / "d9.lisp"
D10_TABLE = ROOT / "lib" / "domains" / "d10.lisp"
CURRENT_HUMAN_TABLES = DOMAIN_TABLES + (D7_TABLE, D8_TABLE, D9_TABLE, D10_TABLE,)
NUMBER_RATIFICATION = ROOT / "knowledge" / "number-width-ratified.json"

TOKEN = r'(\(\)|"(?:\\.|[^"\\])*"|[^()\s]+)'
ROW = re.compile(
    r'^\s*\(([01]{1,10})\s+'
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


def decode(token: str, *, literal_empty: bool = False, d7_surface: bool = False, d7_iast: bool = False) -> str | None:
    if token == "()":
        return "()" if literal_empty else None
    if d7_surface:
        if token.startswith('"') and token.endswith('"'):
            try:
                glyph = json.loads(token)
            except json.JSONDecodeError:
                # The canonical D7 S-expression has one literal tab glyph in
                # its en projection. Preserve that display scalar as written;
                # do not broadly forgive malformed escape sequences.
                payload = token[1:-1]
                if payload != "\t":
                    raise
                glyph = payload
            # A quoted D7 projection is display data, not a machine token:
            # sanctioned views include Devanagari letters and multi-letter
            # transliterations such as "kh". Exact identity remains the
            # seven-bit row key, independent of the projection's spelling.
            if not glyph:
                raise ValueError(f"D7 quoted surface must not be empty: {token!r}")
            return glyph
        # Only the D7 san HUMAN display accepts IAST digraphs like kh.
        # Exact machine identity is still a seven-bit coordinate, never
        # a new variable-width machine token.
        if not token.isalpha() or (len(token) != 1 and not d7_iast):
            raise ValueError(f"invalid unquoted D7 letter: {token!r}")
        return token
    if token.startswith('"') and token.endswith('"'):
        # Escaped punctuation, whitespace and quotes belong to the glyph,
        # not to D7 binary identity.
        return json.loads(token)
    return token


def machine_word(number: int, width: int) -> str:
    """Generate a fixed-width binary table coordinate; not a semantic number."""
    if number < 0:
        raise ValueError(f"a machine word needs a non-negative number: {number}")
    word = format(number, "b")
    if len(word) > width:
        raise ValueError(f"{number} does not fit in a {width}-bit word")
    return word.zfill(width)


# projection-human: explicit D24+ numeric/UI boundary; never a D1-D10 identity.
def human_number(word: str, *, domain_width: int) -> int:
    """Decode an explicitly typed exact-width signed D24+ integer.

    D1-D10 binary words and D7 text are not mathematical operands.
    This helper never constructs or infers a domain from bare bits.
    """
    if not is_number_width(domain_width):
        raise ValueError(f"D{domain_width} is not a numeric D24+ domain")
    if len(word) != domain_width or any(bit not in "01" for bit in word):
        raise ValueError(f"expected exactly {domain_width} admitted numeric bits")
    unsigned = int(word, 2)
    return unsigned - (1 << domain_width) if word[0] == "1" else unsigned


def number_domains() -> tuple[tuple[str, int], ...]:
    """The owner-ratified D24+ numeric ladder: exact domain name and exact width."""
    policy = json.loads(NUMBER_RATIFICATION.read_text(encoding="utf-8"))
    return tuple(zip(policy["ratified_domains"], policy["ratified_prefix_bits"]))


def is_number_width(width: int) -> bool:
    """The numeric domain law D(24 * 2^n), n >= 0 — the only widths a number may live in."""
    return width >= 24 and width % 24 == 0 and (width // 24) & (width // 24 - 1) == 0


def number_word(number: int, width: int) -> str:
    """Encode a signed integer as exact two's-complement D24+ bits."""
    if not is_number_width(width):
        raise ValueError(f"{width} is not a D24+ numeric domain width")
    if not -(1 << (width - 1)) <= number < (1 << (width - 1)):
        raise ValueError(f"{number} does not fit signed D{width}")
    return format(number % (1 << width), f"0{width}b")


def read_domain_table(path: Path) -> list[DomainTableRow]:
    expected_width = int(path.stem.removeprefix("d"))
    rows: list[DomainTableRow] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if not stripped.startswith("(") or stripped.startswith("(domain-table"):
            continue
        match = ROW.match(line)
        if not match:
            if stripped.startswith(";") or stripped == ")":
                continue
            raise ValueError(f"{path}:{line_number}: malformed canonical domain-table row")
        bits, uk, ukr, san, en, lisp, sym = match.groups()
        # D3:000 is a literal structural value, not a missing projection.
        literal_empty = expected_width == 3 and bits == "000"
        if len(bits) != expected_width:
            raise ValueError(
                f"{path}:{line_number}: key width {len(bits)} != file domain width {expected_width}"
            )
        rows.append(
            DomainTableRow(
                domain=f"D{expected_width}",
                width=expected_width,
                bits=bits,
                uk=decode(uk, literal_empty=literal_empty, d7_surface=expected_width == 7),
                ukr=decode(ukr, literal_empty=literal_empty, d7_surface=expected_width == 7),
                san=decode(san, literal_empty=literal_empty, d7_surface=expected_width == 7,
                           d7_iast=expected_width == 7),
                en=decode(en, literal_empty=literal_empty, d7_surface=expected_width == 7),
                lisp=decode(lisp, literal_empty=literal_empty),
                sym=decode(sym, literal_empty=literal_empty, d7_surface=expected_width == 7),
            )
        )
    expected = 1 << expected_width
    if len(rows) != expected:
        raise ValueError(f"{path}: expected {expected} rows, found {len(rows)}")
    return rows


def read_domain_tables(paths=DOMAIN_TABLES) -> list[DomainTableRow]:
    rows: list[DomainTableRow] = []
    for path in paths:
        rows.extend(read_domain_table(Path(path)))
    return rows
