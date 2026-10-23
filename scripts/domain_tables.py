#!/usr/bin/env python3
"""Read canonical self-describing SENS domain tables."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
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
NUMBER_RATIFICATION = ROOT / "contracts" / "numeric-domains-ratification.lisp"

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


# projection-human: explicit D12+ numeric/UI boundary; never a D1-D10 identity.
def human_number(word: str, *, domain_width: int) -> int:
    """Decode an explicitly typed exact-width signed D12+ integer.

    D1-D10 binary words and D7 text are not mathematical operands.
    This helper never constructs or infers a domain from bare bits.
    """
    if not is_number_width(domain_width):
        raise ValueError(f"D{domain_width} is not a numeric D12+ domain")
    if len(word) != domain_width or any(bit not in "01" for bit in word):
        raise ValueError(f"expected exactly {domain_width} admitted numeric bits")
    unsigned = int(word, 2)
    return unsigned - (1 << domain_width) if word[0] == "1" else unsigned


def number_domains(contract_path: Path = NUMBER_RATIFICATION) -> tuple[tuple[str, int], ...]:
    """Read the current D12+ owner law from Lisp, rejecting drift."""
    source = contract_path.read_text(encoding="utf-8")
    marker = "(schema . numeric-d12-start-extension-1)"
    if source.count(marker) != 1:
        raise ValueError("exactly one current numeric D12 extension is required")
    current = source.split(marker, 1)[1]
    first_domains = re.findall(r"\(first-domain\s*\.\s*([^()\s]+)\)", current)
    if first_domains != ["D12"]:
        raise ValueError(f"numeric D12 contract requires exactly one first-domain D12: {first_domains!r}")
    for required in (
        "(status . owner-ratified)",
        "(first-domain . D12)",
        "(initial-width . #d12)",
        "(next-width . double)",
        '(domain-rule . "D(12 * 2^n), n >= 0")',
        "(integer-law .",
        "(fraction-law .",
        "(identity-law .",
        "(transport-law .",
    ):
        if required not in current:
            raise ValueError(f"numeric D12 contract missing: {required}")
    match = re.search(r"\(canonical-domain-names\s*\.\s*\(([^()]*)\)\)", current)
    if not match:
        raise ValueError("numeric D12 contract has no canonical domains")
    names = match.group(1).split()
    widths = []
    for name in names:
        if not re.fullmatch(r"D[1-9][0-9]*", name):
            raise ValueError(f"invalid numeric domain name: {name!r}")
        widths.append(int(name[1:]))
    expected = [12 << shift for shift in range(len(names))]
    if widths != expected or len(widths) < 5:
        raise ValueError(f"numeric D12 doubling prefix drift: {widths!r}")
    return tuple(zip(names, widths))


@lru_cache(maxsize=1)
def _numeric_first_width() -> int:
    return number_domains()[0][1]


def is_number_width(width: int) -> bool:
    """An admitted mathematical width follows D(12 * 2^n), n >= 0."""
    first = _numeric_first_width()
    return (isinstance(width, int) and width >= first
            and width % first == 0
            and (width // first) & (width // first - 1) == 0)


def number_word(number: int, width: int) -> str:
    """Encode a signed integer as exact two's-complement D12+ bits."""
    if not is_number_width(width):
        raise ValueError(f"{width} is not a D12+ numeric domain width")
    if not -(1 << (width - 1)) <= number < (1 << (width - 1)):
        raise ValueError(f"{number} does not fit signed D{width}")
    return format(number % (1 << width), f"0{width}b")


def read_domain_table(path: Path) -> list[DomainTableRow]:
    expected_width = int(path.stem.removeprefix("d"))
    rows: list[DomainTableRow] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if not stripped.startswith("(") or stripped.startswith("(domain-table-1"):
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
