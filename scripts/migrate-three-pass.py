#!/usr/bin/env python3
"""Three-pass source migration: historical recognition into CURRENT exact domains.

Interpret historical spellings through current owner-authored projections;
legacy eight-bit tokens never become current D8 identities by byte matching.
Passes 2–3 preserve exact current domain identities for known source heads.
This migration does not certify runtime callability: function execution for
D1–D10 is a separate implementation concern. D11 and later domains are future
work and are not inferred, populated, or reclassified as test-only by this tool.

Rules derived from current SENS contract and later owner decisions:
- () is D3:000; nonempty list structure uses D2 10/00/11/01
  (open/separator/dot/close). D2 is NEVER a call head or data identity.
- D1:0/1 are predicates; identical payloads in D3–D10 are not D1.
  Ratified domain occupancy alone never admits a callable mechanism.
- Unresolved names may become D7 keyboard/v2 TEXT DATA if every glyph is
  admitted. This is NOT permission to call that text as a function.
  An unrepresentable identifier or unproved historical successor fails closed.
- Quoted data resolves an admitted ladder identity before D7 text fallback.
- Decimal source values in the human Lisp projection lower exactly to D24+
  words / reduced adjacent numerator-denominator words. This source-semantic
  projection is independent of the physical T5/T5M codec; T5M only transports
  the already formed words.
  Ukrainian source surfaces `ук` and `укр` use comma as the exact decimal
  separator independently of the selected physical codec.
- #d/#b/#q2 spellings are not part of the human numeric projection and fail
  closed; T5M receives only already-formed exact-width words.
- Current D7 keyboard/v2 128/128 is the ONLY text projection admitted by
  this script. Historical .rs projection is rejected; no v1 corpus was
  migrated, so no v1-to-v2 conversion prerequisite is needed.
- Comments are stripped. Unresolved raw names cannot become .sens bytes.
  Python T5 packing is an independent parity reference ONLY. Real .sens
  bytes are minted by pinned Zig and verified before atomic publication.
- Output is a physical binary .sens under --out with the same basename
  as its .lisp source. Existing .sens files are never overwritten;
  source .lisp is retained.

Chronology for migration audit: D7 projection retirement 5aafc1e8
(13 Oct 2026); numeric TEXT→D7 owner corrections 54078adb/629b077c
(14 Oct 2026); future D11+ admission remains outside this migration (7a48037b, 14 Oct).
The above notes describe implementation, not a second semantic contract.
"""
from __future__ import annotations

import argparse
import ast
from functools import lru_cache
from dataclasses import dataclass
import json
import hashlib
from math import gcd
import os
from pathlib import Path
import re
import signal
import tempfile
import sys

SCRIPTS = str(Path(__file__).resolve().parent)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from sens_t5_t5m_codec import (
    SensT5Error, decode_bytes, decode_t5m_bytes, encode_projection,
    encode_t5m_projection, parse_words, parse_t5m_words, typed_sha256,
)
import zig_codec_bridge
import migration_publish_pair

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXTS = {".lisp"}
SKIP_DIRS = {".git", ".worktrees", "target", "node_modules", "vendor", "dist", "build", ".venv", "venv", "__pycache__", "superseded"}

D2_SEP="00"
D2_CLOSE="01"
D2_OPEN="10"
D2_DOT="11"
D3_EMPTY="000"
CORE_OPERATION_D8 = frozenset({
    "11100000", "11101010", "11101101", "11101110", "11110100",
})
CORE_OPERATION_D9 = frozenset({
    "110011110", "110011100", "110011101", "110101010", "110101011",
})

NUMERIC_RE = re.compile(
    r"""(?ix)
    [+-]?
    (?:
      \d+(?:/\d+)?
      |
      \d*\.\d+(?:[eE][+-]?\d+)?
      |
      \d+[eE][+-]?\d+
    )
    """
)

HISTORICAL_ROW_RE = re.compile(
    r"^\s*\(row\s+([01]{8})\s+([^\s()]+)\s+([^\s()]+)\s+"
    r"([^\s()]+)\s+([^\s()]+)\s+([^\s()]+)\s*\)",
    re.MULTILINE,
)

def normalize_role(name: str):
    aliases={
        "+":"PLUS","-":"DIFFERENCE","*":"TIMES","/":"QUOTIENT",
        "<":"LESSP",">":"GREATERP","NIL":"EMPTY","EMPTY-LIST":"EMPTY",
        "ATOM?":"ATOM","EQ?":"EQ","NULL?":"NULL","NUMBER?":"NUMBERP",
        "INTEGER?":"INTEGERP","RATIONAL?":"RATIONALP","ZERO?":"ZEROP",
        "EVEN?":"EVENP","ODD?":"ODDP","MEMBER?":"MEMBER",
    }
    value=name.strip()
    return aliases.get(value.upper(),value.upper())

@dataclass(frozen=True)
class Tok:
    kind: str
    text: str
    offset: int

@dataclass
class Atom:
    tok: Tok

@dataclass
class String:
    tok: Tok

@dataclass
class Quote:
    value: object
    tok: Tok

@dataclass
class ListNode:
    items: list
    tail: object|None
    tok: Tok

class MigrationError(Exception):
    def __init__(self, message: str, tok: Tok|None=None):
        super().__init__(message)
        self.message=message
        self.tok=tok

class FileTimeout(MigrationError):
    pass

def _timeout_handler(signum, frame):
    raise FileTimeout("per-file migration timeout")

def strip_comments(source: str) -> str:
    """Remove ; and nested #| |# comments, preserving strings and newlines."""
    out=[]
    i=0
    state="normal"
    depth=0
    while i<len(source):
        ch=source[i]
        if state=="string":
            out.append(ch)
            if ch=="\\" and i+1<len(source):
                out.append(source[i+1]); i+=2; continue
            if ch=='"': state="normal"
            i+=1; continue
        if state=="line":
            if ch=="\n":
                out.append("\n"); state="normal"
            i+=1; continue
        if state=="block":
            if source.startswith("#|",i):
                depth+=1; i+=2; continue
            if source.startswith("|#",i):
                depth-=1; i+=2
                if depth==0: state="normal"
                continue
            if ch=="\n": out.append("\n")
            i+=1; continue
        if ch=='"':
            out.append(ch); state="string"; i+=1; continue
        if ch==";":
            state="line"; i+=1; continue
        if source.startswith("#|",i):
            # Без пробілу x#|коментар|#y неправильно стає атомом xy.
            out.append(" ")
            state="block"; depth=1; i+=2; continue
        out.append(ch); i+=1
    if state=="block":
        raise MigrationError("unterminated block comment")
    if state=="string":
        raise MigrationError("unterminated string")
    return "".join(out)

def tokenize(source: str, *, source_surface="default") -> list[Tok]:
    out=[]
    i=0
    n=len(source)
    while i<n:
        ch=source[i]
        if ch.isspace():
            i+=1; continue
        if ch=="(":
            out.append(Tok("LP","(",i)); i+=1; continue
        if ch==")":
            out.append(Tok("RP",")",i)); i+=1; continue
        if ch=="'":
            out.append(Tok("QUOTE","'",i)); i+=1; continue
        if ch=="`":
            raise MigrationError("backquote syntax has no admitted migration law",Tok("BACKQUOTE","`",i))
        if ch==",":
            raise MigrationError("comma/unquote syntax has no admitted migration law",Tok("COMMA",",",i))
        if ch=='"':
            start=i
            i+=1
            while i<n:
                if source[i]=="\\" and i+1<n:
                    i+=2; continue
                if source[i]=='"':
                    i+=1; break
                i+=1
            else:
                raise MigrationError("unterminated string",Tok("STRING",source[start:],start))
            out.append(Tok("STRING",source[start:i],start))
            continue
        start=i
        while i<n and (not source[i].isspace()) and source[i] not in ("(", ")", '"', "`"):
            # Apostrophe inside a Ukrainian identifier is a real D7 glyph,
            # not the Lisp QUOTE operator. Preserve the exact spelling:
            # *робоча-пам'ять* and ім'я are single source atoms. A leading
            # apostrophe or one before punctuation still starts QUOTE.
            if source[i] == "'":
                if not (
                    i > start and i + 1 < n
                    and source[i - 1].isalpha()
                    and source[i + 1].isalpha()
                ):
                    break
            if source[i] == ",":
                decimal_comma = (
                    source_surface in ("ук", "укр")
                    and i > start and i + 1 < n
                    and source[i - 1].isdecimal()
                    and source[i + 1].isdecimal()
                )
                if not decimal_comma:
                    break
            i+=1
        text=source[start:i]
        if text==".":
            out.append(Tok("DOT",text,start))
        else:
            out.append(Tok("ATOM",text,start))
    return out

class Parser:
    def __init__(self,tokens):
        self.tokens=tokens
        self.i=0
    def peek(self):
        return self.tokens[self.i] if self.i<len(self.tokens) else None
    def take(self):
        tok=self.peek()
        if tok is None: raise MigrationError("unexpected end of source")
        self.i+=1
        return tok
    def parse_program(self):
        forms=[]
        while self.peek() is not None:
            forms.append(self.parse_expr())
        return forms
    def parse_expr(self):
        tok=self.take()
        if tok.kind=="LP":
            items=[]
            tail=None
            if self.peek() and self.peek().kind=="RP":
                self.take()
                return ListNode([],None,tok)
            while True:
                nxt=self.peek()
                if nxt is None:
                    raise MigrationError("unterminated list",tok)
                if nxt.kind=="RP":
                    self.take()
                    return ListNode(items,tail,tok)
                if nxt.kind=="DOT":
                    self.take()
                    if not items or tail is not None:
                        raise MigrationError("misplaced dotted-pair marker",nxt)
                    tail=self.parse_expr()
                    end=self.take()
                    if end.kind!="RP":
                        raise MigrationError("dotted pair requires exactly one tail before )",end)
                    return ListNode(items,tail,tok)
                if tail is not None:
                    raise MigrationError("expression after dotted-pair tail",nxt)
                items.append(self.parse_expr())
        if tok.kind=="RP":
            raise MigrationError("unexpected closing parenthesis",tok)
        if tok.kind=="DOT":
            raise MigrationError("misplaced dot",tok)
        if tok.kind=="QUOTE":
            return Quote(self.parse_expr(),tok)
        if tok.kind=="STRING":
            return String(tok)
        return Atom(tok)

def load_foundation(path: Path):
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("status")!="owner-ratified":
        raise MigrationError("foundation is not owner-ratified")
    return data

def load_d1_uk_surfaces(path: Path = REPO_ROOT / "lib/domains/d1.lisp") -> dict[str, str]:
    """Project ratified D1's Ukrainian literals; do not invent host truthiness."""
    source = path.read_text(encoding="utf-8")
    rows = re.findall(r"(?m)^\s*\(([01])\s+\(ук\s+([^\s()]+)\)", source)
    if len(rows) != 2 or {bits for bits, _ in rows} != {"0", "1"}:
        raise MigrationError("D1 Ukrainian surface table lacks exactly two canonical values")
    if len({name for _, name in rows}) != 2:
        raise MigrationError("D1 Ukrainian surface names must be unique")
    return {name: bits for bits, name in rows}


D1_UK_SURFACES = load_d1_uk_surfaces()


@lru_cache(maxsize=1)
def quoted_ladder_surfaces():
    """Only ratified exact-domain surfaces may name quoted function data."""
    from domain_tables import read_domain_table
    names = {}
    for width in (1, 3, 4, 5, 6, 8, 9, 10):
        rows = read_domain_table(REPO_ROOT / "lib" / "domains" / f"d{width}.lisp")
        if {row.bits for row in rows} != {f"{n:0{width}b}" for n in range(1 << width)}:
            raise MigrationError(f"D{width} has incomplete quoted-data authority")
        for row in rows:
            if width == 3 and row.bits == "000":
                continue
            for name in (row.uk, row.ukr, row.san, row.en, row.lisp, row.sym):
                if name and name != "()":
                    names.setdefault(name, set()).add((row.domain, row.bits))
    return {name: frozenset(targets) for name, targets in names.items()}


def current_residents(data):
    labels={}
    for domain in ("D3","D4","D5","D6","D7","D9","D10"):
        # A foundation ratifies only the domains it declares (e.g. d1-d9 has no
        # D10). Resolve the domains present; a declared-absent domain contributes
        # no residents instead of crashing the whole migration census.
        desc=data["domains"].get(domain)
        if desc is None:
            continue
        for bits,label in desc["residents"].items():
            if domain=="D3" and label=="EMPTY":
                continue
            # A label may exist in several domains (e.g. MAP), so keep the
            # first/lowest listed identity. This preserves MAP -> D6 101000;
            # D8/D9 aliases are admitted separately below only with exact
            # mechanism evidence.
            labels.setdefault(str(label).upper(),(bits,domain))
    # D11 is a separate testing-only inventory, never a callable-head or
    # historical-successor lookup by human spelling. Its 43 typed words remain
    # in the ratified D11 JSON and must not enter this source-name resolver.
    return labels

def parse_current_surface_rows(path: Path):
    """Read generated current source-routable D3-D5 projection."""
    text=path.read_text(encoding="utf-8")
    rows={}
    row_re=re.compile(
        r'DomainSurfaceRow \{ width: (\d+), bits: 0b([01]+), source_routable: (true|false), surfaces: &\[(.*?)\] \},'
    )
    surf_re=re.compile(r'DomainSurfaceName \{ namespace: "([^"]+)", name: "((?:\\.|[^"])*)" \}')
    for m in row_re.finditer(text):
        width=int(m.group(1))
        if not (3<=width<=6) or m.group(3)!="true":
            continue
        bits=m.group(2)
        for sm in surf_re.finditer(m.group(4)):
            name=ast.literal_eval('"'+sm.group(2)+'"')
            rows[name]=(bits,f"D{width}")
    return rows

def parse_semantic_rows(path: Path):
    text=path.read_text(encoding="utf-8")
    rows={}
    row_re=re.compile(
        r'SemanticRow \{ semantic_id: 0b([01]{8}), surfaces: &\[(.*?)\] \},'
    )
    surf_re=re.compile(r'SemanticSurface \{ namespace: "([^"]+)", name: "((?:\\.|[^"])*)" \}')
    for m in row_re.finditer(text):
        surfaces=[]
        for sm in surf_re.finditer(m.group(2)):
            name=ast.literal_eval('"'+sm.group(2)+'"')
            surfaces.append((sm.group(1),name))
        rows[m.group(1)]=surfaces
    return rows

def build_three_pass_maps(data, domain_surface_generated: Path, semantic_generated: Path,
                          semantic_registry: Path, necessary_forms: Path):
    residents=current_residents(data)
    current=parse_current_surface_rows(domain_surface_generated)
    # Джерело міграції — тільки ратифіковані координати й перевірена
    # таблиця provenance. Видалений Rust-маршрутизатор не є законом мови.
    # Параметри semantic_registry/necessary_forms збережені лише для
    # сумісності наявних викликів інструмента; їхній вміст не читається.
    sem_rows=parse_semantic_rows(semantic_generated)

    # A proposal-only historical сід8 crosswalk is provenance, never
    # executable authority. Do not import research bridge rows into either
    # current name resolution or call-head lowering.
    _bridge_by_sid = {}

    my=dict(current)
    for byte,surfaces in sem_rows.items():
        candidates=set()
        for _,name in surfaces:
            if name in current:
                candidates.add(current[name])
            by_role=residents.get(normalize_role(name))
            if by_role is not None:
                candidates.add(by_role)
        unique=next(iter(candidates)) if len(candidates)==1 else None
        for namespace,name in surfaces:
            # Uppercase historical names are reserved for pass 3.
            if name != name.upper() or namespace=="sym":
                if name not in my:
                    my[name]=unique

    # Human Ukrainian D8/D9/D10 projections resolve to exact identities even
    # when their runtime call mechanisms are not yet specified. This pass only
    # preserves the identity; it does not certify execution. Raw eight-bit
    # spellings remain ambiguous with retired SID8 and are handled separately.
    from domain_tables import read_domain_table
    unique_surfaces = quoted_ladder_surfaces()
    for width in (8, 9, 10):
        for row in read_domain_table(REPO_ROOT / "lib" / "domains" / f"d{width}.lisp"):
            ident = (row.bits, f"D{width}")
            for name in (row.uk, row.ukr):
                if not name or unique_surfaces.get(name) != frozenset({(f"D{width}", row.bits)}):
                    continue
                my[name] = ident
            # Owner-admitted native D8 operations keep their en/san surfaces.
            # Commit 260118115 legitimately removed the self-recursive D8
            # wrappers from core4.lisp, but build_three_pass_maps was not
            # updated with it, so those five surfaces silently dropped out.
            if width == 8 and row.bits in CORE_OPERATION_D8:
                for name in (row.san, row.en):
                    if not name or unique_surfaces.get(name) != frozenset({("D8", row.bits)}):
                        continue
                    if my.get(name) is None:
                        my[name] = ident

    # Additional D9 spellings may be retained from Core4 source only when
    # they resolve uniquely to the same ratified identity. This is projection
    # compatibility, not evidence that the D9 value is executable.
    d9_callable = core4_d9_callable_rows()
    for bits, row in d9_callable.items():
        ident = (bits, "D9")
        for name in (row.uk, row.ukr, row.san, row.en, row.lisp, row.sym):
            if not name or unique_surfaces.get(name) != frozenset({("D9", bits)}):
                continue
            if name == name.upper():
                residents[name] = ident
            else:
                # The exact current domain row resolves stale/ambiguous
                # historical surface aliases without importing сід8 evidence.
                my[name] = ident

    # Preserve any uniquely mapped Core4 D10 spelling as the same identity;
    # execution admission is deliberately outside this migration step.
    for bits, row in core4_d10_defined_rows().items():
        ident = (bits, "D10")
        for name in (row.uk, row.ukr, row.san, row.en, row.lisp, row.sym):
            if not name or unique_surfaces.get(name) != frozenset({("D10", bits)}):
                continue
            if name == name.upper():
                residents.setdefault(name, ident)
            else:
                my.setdefault(name, ident)

    # Core4-defined D1..D8 primitives (друге, третє, та, ...) are callable
    # through their actual language definitions -- mirror of the D10 rule.
    for bits, w, row in core4_d1_d8_defined_rows():
        ident = (bits, f"D{w}")
        for name in (row.uk, row.ukr, row.san, row.en, row.lisp, row.sym):
            if not name or unique_surfaces.get(name) != frozenset({(f"D{w}", bits)}):
                continue
            if name == name.upper():
                if residents.get(name) is None: residents[name]=ident
            else:
                if my.get(name) is None: my[name]=ident

    upper={name:ident for name,ident in residents.items()}
    return my,upper,_bridge_by_sid

def extract_projection(text: str,name: str):
    start=text.find(f"pub(crate) const {name}")
    if start<0: raise MigrationError(f"missing Text7 projection {name}")
    end=text.find("];",start)
    sec=text[start:end]
    out={}
    rx=re.compile(r'^\s*\(("(?:\\.|[^"\\])*"),\s*Some\(&\[([^\]]*)\]\)\)',re.M)
    for m in rx.finditer(sec):
        spelling=ast.literal_eval(m.group(1))
        vals=tuple(int(x.strip(),16) for x in m.group(2).split(",") if x.strip())
        out[spelling]=vals
    if not out: raise MigrationError(f"empty Text7 projection {name}")
    return out

def _keyboard_v2(projection_path: Path):
    """One ratified 7-bit coordinate table; language is a VIEW, not semantics."""
    authority = json.loads(projection_path.read_text(encoding="utf-8"))
    if (authority.get("schema"), authority.get("status"),
            authority.get("width"), authority.get("capacity"),
            authority.get("occupancy")) != (
            "sens.d7.keyboard/v2", "owner-ratified", 7, 128, 128):
        raise MigrationError("D7 keyboard/v2 is not ratified 128/128")
    rows = authority.get("table", [])
    if len(rows) != 128:
        raise MigrationError("D7 keyboard/v2 missing coordinates")
    indexes = {language: {} for language in ("en", "uk", "san")}
    for number, row in enumerate(rows):
        bits = f"{number:07b}"
        if row.get("bits") != bits or row.get("ascii") != chr(number):
            raise MigrationError(f"D7 keyboard/v2 coordinate drift: {bits}")
        for language, field in (("en", "ascii"), ("uk", "uk"), ("san", "san")):
            glyph = row.get(field)
            if not isinstance(glyph, str) or len(glyph) != 1:
                raise MigrationError(f"D7 keyboard/v2 bad {language} glyph: {bits}")
            if glyph in indexes[language]:
                raise MigrationError(f"D7 keyboard/v2 ambiguous {language} glyph: {glyph!r}")
            indexes[language][glyph] = bits
    return {"keyboard-v2": indexes}


_IAST_CONS = {
 "k":"क","kh":"ख","g":"ग","gh":"घ","ṅ":"ङ","c":"च","ch":"छ","j":"ज","jh":"झ","ñ":"ञ",
 "ṭ":"ट","ṭh":"ठ","ḍ":"ड","ḍh":"ढ","ṇ":"ण","t":"त","th":"थ","d":"द","dh":"ध","n":"न",
 "p":"प","ph":"फ","b":"ब","bh":"भ","m":"म","y":"य","r":"र","l":"ल","v":"व",
 "ś":"श","ṣ":"ष","s":"स","h":"ह","ḷ":"ळ",
}
_IAST_VOW = {"a":"अ","ā":"आ","i":"इ","ī":"ई","u":"उ","ū":"ऊ","ṛ":"ऋ","ṝ":"ॠ",
             "e":"ए","ai":"ऐ","o":"ओ","au":"औ"}
_IAST_MATRA = {"a":"","ā":"ा","i":"ि","ī":"ी","u":"ु","ū":"ू","ṛ":"ृ","ṝ":"ॄ",
               "e":"े","ai":"ै","o":"ो","au":"ौ"}
_IAST_KEYS = sorted(list(_IAST_CONS)+list(_IAST_VOW)+list(_IAST_MATRA), key=len, reverse=True)


def iast_to_devanagari(s: str):
    """IAST (Sanskrit Latin transliteration) -> Devanagari. None if not IAST."""
    out=[]; i=0; n=len(s); pending=False
    while i<n:
        ch=s[i]
        if ch==" ": out.append(" "); pending=False; i+=1; continue
        if ch in "-?": out.append(ch); pending=False; i+=1; continue
        if ch=="ṃ": out.append("ं"); i+=1; continue
        if ch=="ḥ": out.append("ः"); i+=1; continue
        m=next((k for k in _IAST_KEYS if s.startswith(k,i)), None)
        if m is None: return None
        if m in _IAST_CONS:
            if pending: out.append("्")
            out.append(_IAST_CONS[m]); pending=True
        elif m in _IAST_VOW:
            if pending: out.append(_IAST_MATRA[m]); pending=False
            else: out.append(_IAST_VOW[m])
        else:
            if pending: out.append(_IAST_MATRA[m]); pending=False
            else: out.append(_IAST_VOW.get(m,""))
        i+=len(m)
    if pending: out.append("्")
    return "".join(out)


def _keyboard_v2_mode(spelling: str, token: Tok) -> str:
    """Choose a view only if the identifier contains one unambiguous script."""
    # IAST (Sanskrit Latin transliteration) uses ASCII letters too, so a purely
    # ASCII identifier stays en; only an IAST-SPECIFIC letter (ā ū ṇ ṣ ...) marks
    # the whole identifier as the san view.
    _IAST_SPECIFIC = "āīūṛṝḷḹṃḥṅñṭḍṇśṣ"
    if spelling and any(ch in _IAST_SPECIFIC for ch in spelling) and iast_to_devanagari(spelling) is not None:
        return "san"
    scripts = set()
    for ch in spelling:
        cp = ord(ch)
        if not ch.isalpha():
            # A non-letter (hyphen, digit, punctuation) is a JOINER, not a script:
            # śūnya-parīkṣā is all-san, not mixed en+san.
            continue
        if ("a" <= ch <= "z") or ("A" <= ch <= "Z"):
            scripts.add("en")
        elif 0x0400 <= cp <= 0x052F:
            scripts.add("uk")
        elif 0x0900 <= cp <= 0x097F:
            scripts.add("san")
        else:
            if iast_to_devanagari(ch) is not None:
                scripts.add("san")
            else:
                raise MigrationError(f"D7 keyboard/v2 unsupported letter {ch!r}", token)
    if len(scripts) > 1:
        raise MigrationError("D7 keyboard/v2 mixed-script identifier is ambiguous", token)
    return next(iter(scripts), "en")


def build_text7(data, projection_path: Path):
    # Retired phonetic D7 .rs projection is never a migration input.
    # The only admitted route is the ratified 128/128 keyboard v2 JSON.
    if projection_path.suffix != ".json":
        raise MigrationError("HISTORICAL_D7_DISABLED: requires keyboard/v2 JSON")
    return _keyboard_v2(projection_path)


def text7_encode(spelling: str,candidates,tok: Tok, *, identifier: bool = True):
    if "keyboard-v2" in candidates:
        if not spelling:
            # Порожній рядок — це D2-пропуск (порожнє/пропуск у D2), а не
            # D7-ідентифікатор і не D3:000. () — це D3; "" — це D2.
            return []
        # Імена можуть мати клавіатурні синоніми; рядки — точні дані.
        # Не змінювати символи рядка заради нормалізації ідентифікатора.
        if identifier:
            spelling = spelling.translate({0x2014: "-", 0x2013: "-", 0x2500: "-", 0x2550: "="})
        view = _keyboard_v2_mode(spelling, tok)
        indexes = candidates["keyboard-v2"]
        chosen = indexes[view]
        # The san view is Devanagari; sources spell san in IAST Latin. Transliterate
        # (reversible) when the raw spelling is not directly on the keyboard.
        if identifier and view == "san" and any(chosen.get(g) is None for g in spelling):
            deva = iast_to_devanagari(spelling)
            if deva is not None:
                spelling = deva
        result = []
        for glyph in spelling:
            bits = chosen.get(glyph)
            if bits is None and view == "san":
                # A joiner (-, ?) is not on the san keyboard but is on uk.
                bits = indexes.get("uk", {}).get(glyph)
            if bits is None:
                raise MigrationError(
                    f"D7 keyboard/v2 cannot encode {glyph!r} U+{ord(glyph):04X} in {view}",
                    tok,
                )
            result.append(bits)
        return result
    raise MigrationError("HISTORICAL_D7_DISABLED: expected keyboard/v2 projection",tok)

class Resolver:
    def __init__(self,my,upper,d9_residents=None,bridge_by_sid=None):
        self.my=my
        self.upper=upper
        self.d9_residents=set(d9_residents or ())
        self.d9_callable_bits=frozenset(core4_d9_callable_rows())
        self.d10_callable_bits=frozenset(core4_d10_defined_rows())
        self.d8_callable_bits=frozenset(bits for bits,w,_row in core4_d1_d8_defined_rows() if w==8)
        if bridge_by_sid:
            raise MigrationError("unratified SID8 bridge cannot authorize executable heads")
        self.bridge_by_sid={}
        self.global_binding_words={}
        self.counts={"already-exact":0,"pass2-my-lisp":0,
                     "pass3-lisp15":0,"pass4-text7-global":0,
                     "passthrough-head":0}

    def set_global_bindings(self, bindings, text7):
        self.global_binding_words = {
            name: frame_text7(
                text7_encode(name, text7, tok),
                tok,
            )
            for name, tok in bindings
        }

    def _has_concrete_callable(self, identity):
        # Резидентність D8–D10 не є допуском виклику. Зберігаємо
        # точний код лише для функцій із реальною core/runtime реалізацією;
        # інші імена передаються як контекстні D7 identifiers.
        if not isinstance(identity, tuple) or len(identity) < 2:
            return False
        bits, domain = identity[:2]
        if domain == "D8":
            # Core4 Lisp DEFINE is a lexical closure, not an I/O opcode.
            return bits in CORE_OPERATION_D8
        if domain == "D9":
            # Same for Core4/Reason Lisp closures: D9 is native only when
            # an actual runtime mechanism is admitted, not a source DEFINE.
            return bits in CORE_OPERATION_D9
        if domain == "D10":
            # The D10 list is a ratified library vocabulary, not a native
            # execution table. Functions defined in Lisp use D7 bindings.
            return False
        return False

    def head(self,tok: Tok,text7=None):
        t=tok.text
        # Domain identity is (exact width, exact bits), never a flat сід8
        # number. A *resident* D7 or D10 coordinate is not automatically
        # an executable function. Do not emit it as a call-head passthrough:
        # a binary-only output could then look valid yet lack a mechanism.
        if t and set(t) <= {"0", "1"}:
            width = len(t)
            if width == 2:
                raise MigrationError(
                    f"D2 word {t} is structural control only; it cannot be an executable head",
                    tok,
                )
            if width == 3 and t == D3_EMPTY:
                raise MigrationError(
                    "D3:000 is EMPTY data, never an executable call head", tok,
                )
            if width == 7:
                raise MigrationError(
                    f"D7 {t}: фонемна/текстова ідентичність не є виконуваною головою",
                    tok,
                )
            if width == 9:
                raise MigrationError(
                    f"D9 {t}: потрібна названа чинна проєкція; сама ширина не задає identity",
                    tok,
                )
            if width == 10:
                raise MigrationError(
                    f"D10 {t}: потрібна названа чинна проєкція; сама ширина не задає identity",
                    tok,
                )
            if width > 10:
                raise MigrationError(
                    f"unqualified {width}-bit call head has no admitted domain mechanism",
                    tok,
                )
        # Existing D3–D6 exact call-head candidates remain untouched.
        # This classifier does not assert their runtime executability.
        if 3<=len(t)<=6 and set(t)<=set("01"):
            self.counts["already-exact"]+=1
            return [t],"already-exact"
        if len(t)==8 and set(t)<=set("01"):
            # Owner-ratified D8 first existed on 2026-10-06 (#3960).
            # A raw eight-bit executable head could be older сід8/сенс8 or an
            # unqualified later spelling; its bytes are never a D8 role proof.
            raise MigrationError(
                f"ambiguous eight-bit SID8/Sens8-or-D8 head {t}: "
                "no verified callable mechanism or source-era proof; "
                "find the historical function meaning and its full ratified "
                "укр projection, never map by matching bytes", tok,
            )

        # Тільки ДОВЕДЕНА викличність D8–D10 отримує код голови.
        # Присутність у 256/512/1024 ратифікованих рядках не є механізмом.
        ident = self.my.get(t)
        if self._has_concrete_callable(ident):
            self.counts["pass2-my-lisp"] += 1
            return [ident[0]], "pass2-my-lisp"

        # Other source-defined global callables shadow human builtin surfaces.
        # Exact binary identities above remain authoritative: only a name
        # that appeared as a proven global DEFINE target takes this route.
        # Resolve it before pass-2/pass-3 surface mappings; otherwise
        # (define car ...) followed by (car) accidentally calls D3 CAR.
        if t in self.global_binding_words:
            self.counts["pass4-text7-global"]+=1
            return self.global_binding_words[t],"pass4-text7-global"

        # Pass 2: known my-lisp/current admitted surfaces. A surface known to
        # the old registry but lacking a current resident is a empty.
        if t in self.my:
            ident=self.my[t]
            if (isinstance(ident, tuple) and len(ident) >= 2
                    and ident[1] in ("D8", "D9", "D10")
                    and not self._has_concrete_callable(ident)):
                # Ratified NAME of a Lisp closure, not a native D9 opcode.
                # Preserve its source binding by an exact D7 identifier.
                if text7 is None:
                    raise MigrationError(
                        f"{ident[1]} resident {t!r} has no callable mechanism; "
                        "contextual D7 projection required", tok,
                    )
                self.counts["pass4-text7-global"] += 1
                return encode_text7_identifier(t, text7, tok), "d7-resident-head"
            if ident is None:
                raise MigrationError(
                    f"legacy-unmapped my-lisp function {t!r}: no proven callable identity "
                    "in the D1–24+ domain frame; residency does not imply callability",
                    tok,
                )
            identified = (
                ident[1] in ("D3", "D4", "D5", "D6")
                and len(ident[0]) == int(ident[1][1:])
            ) or (
                ident[1] in ("D8", "D9", "D10")
                and len(ident[0]) == int(ident[1][1:])
            )
            if not identified:
                raise MigrationError(
                    f"{ident[1]} {ident[0]}: no exact current domain identity for {t!r}", tok
                )
            self.counts["pass2-my-lisp"]+=1
            return [ident[0]],"pass2-my-lisp"

        # Pass 3: historical LISP I / Lisp 1.5 UPPERCASE names.
        if t==t.upper() and t in self.upper:
            ident=self.upper[t]
            if (isinstance(ident, tuple) and len(ident) >= 2
                    and ident[1] in ("D8", "D9", "D10")
                    and not self._has_concrete_callable(ident)):
                if text7 is None:
                    raise MigrationError(
                        f"{ident[1]} resident {t!r} has no callable mechanism; "
                        "contextual D7 projection required", tok,
                    )
                self.counts["pass4-text7-global"] += 1
                return encode_text7_identifier(t, text7, tok), "d7-resident-head"
            if ident is None:
                raise MigrationError(
                    f"legacy-unmapped Lisp 1-1.5 function {t}: no proven callable identity "
                    "in the D1–24+ domain frame; residency does not imply callability",
                    tok,
                )
            identified = (
                ident[1] in ("D3", "D4", "D5", "D6")
                and len(ident[0]) == int(ident[1][1:])
            ) or (
                ident[1] in ("D8", "D9", "D10")
                and len(ident[0]) == int(ident[1][1:])
            )
            if not identified:
                raise MigrationError(
                    f"{ident[1]} {ident[0]}: no exact current domain identity for {t!r}", tok
                )
            self.counts["pass3-lisp15"]+=1
            return [ident[0]],"pass3-lisp15"
        # D1 words stay exact. An unresolved NAME is data -> D7 text (its
        # glyphs, e.g. "/", live in the ratified D7 keyboard). Never leave raw
        # text as a physical word: the T5 codec must reject that.
        self.counts["passthrough-head"]+=1
        if t and set(t) <= {"0", "1"}:
            return [t],"passthrough-head"
        if text7 is not None:
            return encode_text7_identifier(t,text7,tok),"d7-name-head"
        return [t],"passthrough-head"

def frame_text7(cells, tok: Tok):
    if not cells:
        # Порожній рядок кодується як самотній D2-пропуск (D2_SEP), а не як
        # порожній D2-каркас і не як D3:000 (D3 лишається для () ).
        return [D2_SEP]
    words=[D2_OPEN]
    for index,cell in enumerate(cells):
        if index:
            words.append(D2_SEP)
        words.append(cell)
    words.append(D2_CLOSE)
    return words


def encode_text7_identifier(spelling: str,text7,tok: Tok):
    return frame_text7(text7_encode(spelling,text7,tok), tok)


def encode_text7_datum(spelling: str, text7, tok: Tok):
    """Encode one D7 glyph as its scalar; frame only multi-cell Text7 data.

    A one-cell quoted datum is a D7 atom, not a one-element D2 list. Its
    surrounding source list already owns D2 framing. Contextual identifiers
    still use encode_text7_identifier so binder/call-head lookup remains framed.
    """
    cells = text7_encode(spelling, text7, tok)
    if len(cells) == 1:
        return cells
    return frame_text7(cells, tok)


def collect_global_bindings(forms,resolver=None):
    # Do not maintain a second spelling authority for DEFINE. The canonical
    # Ukrainian surface "визначити" (and any future alias) must be recognized
    # through the same owner-ratified D4 identity used by Resolver.head().
    define_heads={"00001001","0011","define","def"}
    if resolver is not None:
        for table in (resolver.my,resolver.upper):
            for spelling,identity in table.items():
                if (isinstance(identity,tuple) and len(identity)>=2
                        and identity[0]=="0011" and identity[1]=="D4"):
                    define_heads.add(spelling)
    bindings=[]
    seen=set()
    for form in forms:
        if not isinstance(form,ListNode) or form.tail is not None or len(form.items)<2:
            continue
        head=form.items[0]
        if not isinstance(head,Atom) or head.tok.text not in define_heads:
            continue
        target=form.items[1]
        if isinstance(target,Atom):
            name=target.tok.text
            if name not in seen:
                seen.add(name)
                bindings.append((name,target.tok))
        elif (isinstance(target,ListNode) and target.tail is None
              and target.items and isinstance(target.items[0],Atom)):
            name=target.items[0].tok.text
            if name not in seen:
                seen.add(name)
                bindings.append((name,target.items[0].tok))
    return bindings


@lru_cache(maxsize=1)
def core4_d9_callable_rows():
    """Exact D9 rows with a concrete Core4 callable binding or Rust mechanism.

    This mirrors the runtime rule: a D9 slot is callable only when an actual
    closure/builtin is bound to that exact identity. The full D9 resident map
    is deliberately not used as an admission list.
    """
    from domain_tables import read_domain_table

    # Реалізації D9-слотів живуть не лише в core4: міркувати — у lib/reason.lisp.
    # Механізм викликаності мусить бачити всі завантажувані модулі ядра,
    # інакше наявна реалізація помилково вважається відсутньою.
    core4_paths = [REPO_ROOT / "lib" / "core4.lisp", REPO_ROOT / "lib" / "reason.lisp"]
    forms = []
    for core4_path in core4_paths:
        if not core4_path.is_file():
            continue
        source = strip_comments(core4_path.read_text(encoding="utf-8"))
        forms.extend(Parser(tokenize(source)).parse_program())
    callable_names = set()
    aliases = []
    define_heads = {"00001001", "0011", "define", "def", "визначити"}
    lambda_heads = {"0010", "lambda", "лямбда", "функція"}

    for form in forms:
        if (not isinstance(form, ListNode) or form.tail is not None
                or len(form.items) < 3 or not isinstance(form.items[0], Atom)
                or form.items[0].tok.text not in define_heads):
            continue
        target = form.items[1]
        if isinstance(target, ListNode) and target.items and isinstance(target.items[0], Atom):
            # Function shorthand: (DEFINE (name args...) body...).
            callable_names.add(target.items[0].tok.text)
            continue
        if not isinstance(target, Atom):
            continue
        value = form.items[2]
        if (isinstance(value, ListNode) and value.items
                and isinstance(value.items[0], Atom)
                and value.items[0].tok.text in lambda_heads):
            callable_names.add(target.tok.text)
        elif isinstance(value, Atom):
            # A simple alias is callable only if its target is already known
            # callable. Iterate to a fixed point for chains of aliases.
            aliases.append((target.tok.text, value.tok.text))

    changed = True
    while changed:
        changed = False
        for alias, target in aliases:
            if target in callable_names and alias not in callable_names:
                callable_names.add(alias)
                changed = True

    rows = {}
    for row in read_domain_table(REPO_ROOT / "lib" / "domains" / "d9.lisp"):
        names = {row.uk, row.ukr, row.san, row.en, row.lisp, row.sym} - {None, "()"}
        if row.bits in CORE_OPERATION_D9 or names.intersection(callable_names):
            rows[row.bits] = row
    return rows


@lru_cache(maxsize=1)
def core4_d10_defined_rows():
    """Map concretely defined library names to exact D10 call identities."""
    from domain_tables import read_domain_table

    library_sources = (REPO_ROOT / "lib" / "core4.lisp", REPO_ROOT / "lib" / "epistemic.lisp")
    forms = []
    for path in library_sources:
        source = strip_comments(path.read_text(encoding="utf-8"))
        forms.extend(Parser(tokenize(source)).parse_program())
    defined_names = set()
    aliases = []
    define_heads = {"00001001", "0011", "define", "def", "визначити"}
    lambda_heads = {"0010", "lambda", "лямбда", "функція"}
    macro_heads = {"макрос", "macro"}

    def has_executable_body(value):
        if not isinstance(value, ListNode) or not value.items or not isinstance(value.items[0], Atom):
            return False
        head = value.items[0].tok.text
        if head in lambda_heads:
            return True
        # A macro is a concrete D10 definition only when its payload is an
        # actual SENS lambda; mere residence never grants callability.
        if head in macro_heads and len(value.items) >= 2:
            payload = value.items[1]
            return (isinstance(payload, ListNode) and payload.items
                    and isinstance(payload.items[0], Atom)
                    and payload.items[0].tok.text in lambda_heads)
        return False

    for form in forms:
        if (not isinstance(form, ListNode) or form.tail is not None
                or len(form.items) < 3 or not isinstance(form.items[0], Atom)
                or form.items[0].tok.text not in define_heads):
            continue
        target = form.items[1]
        if isinstance(target, ListNode) and target.items and isinstance(target.items[0], Atom):
            defined_names.add(target.items[0].tok.text)
            continue
        if not isinstance(target, Atom):
            continue
        value = form.items[2]
        if has_executable_body(value):
            defined_names.add(target.tok.text)
        elif isinstance(value, Atom):
            aliases.append((target.tok.text, value.tok.text))

    changed = True
    while changed:
        changed = False
        for alias, target in aliases:
            if target in defined_names and alias not in defined_names:
                defined_names.add(alias)
                changed = True

    rows = {}
    for row in read_domain_table(REPO_ROOT / "lib" / "domains" / "d10.lisp"):
        names = {row.uk, row.ukr, row.san, row.en, row.lisp, row.sym} - {None, "()"}
        if names.intersection(defined_names):
            rows[row.bits] = row
    return rows


@lru_cache(maxsize=1)
def core4_d1_d8_defined_rows():
    """Core4-defined names of D1..D8 primitives (mirror of the D10 rule).

    A D1..D8 coordinate is callable only when core4 actually defines that
    name. Ratified residency alone never admits a callable mechanism.
    """
    from domain_tables import read_domain_table

    source = strip_comments((REPO_ROOT / "lib" / "core4.lisp").read_text(encoding="utf-8"))
    forms = Parser(tokenize(source)).parse_program()
    defined_names = set()
    aliases = []
    define_heads = {"00001001", "0011", "define", "def", "визначити"}
    lambda_heads = {"0010", "lambda", "лямбда", "функція"}

    for form in forms:
        if (not isinstance(form, ListNode) or form.tail is not None
                or len(form.items) < 3 or not isinstance(form.items[0], Atom)
                or form.items[0].tok.text not in define_heads):
            continue
        target = form.items[1]
        if isinstance(target, ListNode) and target.items and isinstance(target.items[0], Atom):
            defined_names.add(target.items[0].tok.text)
            continue
        if not isinstance(target, Atom):
            continue
        value = form.items[2]
        if (isinstance(value, ListNode) and value.items
                and isinstance(value.items[0], Atom)
                and value.items[0].tok.text in lambda_heads):
            defined_names.add(target.tok.text)
        elif isinstance(value, Atom):
            aliases.append((target.tok.text, value.tok.text))

    changed = True
    while changed:
        changed = False
        for alias, target in aliases:
            if target in defined_names and alias not in defined_names:
                defined_names.add(alias)
                changed = True

    rows = []
    for w in range(1, 9):
        for row in read_domain_table(REPO_ROOT / "lib" / "domains" / f"d{w}.lisp"):
            names = {row.uk, row.ukr, row.san, row.en, row.lisp, row.sym} - {None, "()"}
            if names.intersection(defined_names):
                rows.append((row.bits, w, row))
    return rows


def lambda_parameter_names(node: ListNode | Atom) -> tuple[str, ...]:
    if isinstance(node, Atom):
        # Variadic lambda: bare symbol parameter binds all args as a list.
        return (node.tok.text,)
    names=[]
    for param in node.items:
        if not isinstance(param,Atom):
            raise MigrationError(
                "lambda parameter must be a human identifier atom",
                node.tok,
            )
        names.append(param.tok.text)
    if node.tail is not None:
        # Dotted lambda: tail parameter is also a binding.
        if not isinstance(node.tail, Atom):
            raise MigrationError(
                "dotted lambda tail must be a human identifier atom",
                node.tok,
            )
        names.append(node.tail.tok.text)
    return tuple(names)


def encode_lambda_params(node: ListNode | Atom, text7):
    """Preserve the actual binding shape, not merely parameter names.

    (функція аргументи ...) is variadic, NOT (функція (аргументи) ...).
    (функція (голова . хвіст) ...) has a REST binder, NOT two fixed args.
    Empty parameter lists use canonical D3 EMPTY, never an empty D2 frame.
    The same distinction applies to shorthand DEFINE signatures.
    """
    names = lambda_parameter_names(node)
    if isinstance(node, Atom):
        return encode_text7_identifier(node.tok.text, text7, node.tok)
    if not node.items and node.tail is None:
        return [D3_EMPTY]
    words = [D2_OPEN]
    for index, param in enumerate(node.items):
        if index:
            words.append(D2_SEP)
        words.extend(encode_text7_identifier(param.tok.text, text7, param.tok))
    if node.tail is not None:
        words.append(D2_DOT)
        words.extend(encode_text7_identifier(
            node.tail.tok.text, text7, node.tail.tok,
        ))
    words.append(D2_CLOSE)
    return words

def encode_atom_data(node: Atom,text7,lexical_env=(),quoted=False,resolver=None):
    t=node.tok.text
    if t in lexical_env:
        return encode_text7_identifier(t,text7,node.tok)
    # Input here is the human Lisp projection, not the binary .sens view.
    # Therefore every decimal numeral is a mathematical D24+ value, including
    # spellings such as "10" that happen to equal a structural D2 bit word.
    source_surface = getattr(resolver, "source_surface", "default")
    # Human decimal projection lowers exactly to D24+ here, independent of the
    # physical T5/T5M codec.
    # Integer words use two's complement; fractions retain adjacent reduced
    # numerator/denominator words. No host float or D7 digit text.
    def numeric_word(value):
        width = 24
        while not (-(1 << (width - 1)) <= value < (1 << (width - 1))):
            width *= 2
        if width > 4 * 1024 * 1024 * 5:
            raise MigrationError("D24+ integer exceeds the supported exact-width limit", node.tok)
        return width, f"{value % (1 << width):0{width}b}"

    if re.fullmatch(r"[+-]?\d+", t):
        _, word = numeric_word(int(t, 10))
        return [word]
    decimal_pattern = (
        r"[+-]?(?:\d+,\d+|,\d+)"
        if source_surface in ("ук", "укр")
        else r"[+-]?(?:\d+\.\d+|\.\d+)"
    )
    if re.fullmatch(decimal_pattern, t):
        negative = t.startswith("-")
        unsigned_text = t[1:] if t[:1] in "+-" else t
        decimal_separator = "," if source_surface in ("ук", "укр") else "."
        whole, fractional = unsigned_text.split(decimal_separator, 1)
        if len(whole) + len(fractional) > 4096:
            raise MigrationError(
                "D24+ decimal fraction exceeds the 4096-digit exact-conversion limit",
                node.tok,
            )
        numerator = int((whole or "0") + fractional, 10)
        denominator = 10 ** len(fractional)
        divisor = gcd(numerator, denominator)
        numerator //= divisor
        denominator //= divisor
        if negative:
            numerator = -numerator
        values = [numerator] if denominator == 1 else [numerator, denominator]
        width = 24
        while any(not (-(1 << (width - 1)) <= value < (1 << (width - 1)))
                  for value in values):
            width *= 2
        if width > 4 * 1024 * 1024 * 5:
            raise MigrationError("D24+ fraction exceeds the supported exact-width limit", node.tok)
        return [f"{value % (1 << width):0{width}b}" for value in values]
    if (source_surface in ("ук", "укр")
            and "," in t and re.fullmatch(r"[+-]?[0-9,]+", t)):
        raise MigrationError(
            "Ukrainian D24+ decimal requires exactly one comma between digits",
            node.tok,
        )
    if (NUMERIC_RE.fullmatch(t) or re.fullmatch(
                r"(?i)#(?:d[+-]?\d+(?:/\d+)?|b[01]+|q2:[+-]?[01]+/[01]+)", t
            )):
        raise MigrationError(
            "D24+ numeric projection accepts signed decimal integers or finite decimal fractions only; "
            "ratios, exponents, and explicit numeric spellings are not lowered",
            node.tok,
        )
    if t in D1_UK_SURFACES:
        return [D1_UK_SURFACES[t]]
    # Human decimal atoms have already been lowered. Binary domain words are
    # not raw Lisp atoms: parser punctuation emits D2 controls; named human
    # surfaces resolve admitted D1/D3–D10 identities.
    if quoted:
        # Цитата спершу бере канонічну identity з драбини D1/D3-D10.
        # D2 є структурою; D7 застосовується лише за відсутності збігу.
        if t in {"0", "1"} or re.fullmatch(r"[01]{3,10}", t):
            return [t]
        targets = quoted_ladder_surfaces().get(t, frozenset())
        if len(targets) > 1:
            raise MigrationError(
                f"ambiguous quoted ladder surface {t!r}: {sorted(targets)!r}; use exact bits",
                node.tok,
            )
        if targets:
            _domain, bits = next(iter(targets))
            return [bits]
        return encode_text7_datum(t, text7, node.tok)
    # Нецитовані дані: ім'я, яке джерело саме зв'язує глобально (DEFINE),
    # є Text7-посиланням, а не сирим текстом. Решта лишається точно як
    # написано і пізніше fail-closed перевіркою фізичного 0/1-слова.
    if resolver is not None and t in resolver.global_binding_words:
        return list(resolver.global_binding_words[t])
    # Owner rule: unresolved names are DATA -> D7 text (all their glyphs, e.g. "/",
    # live in the ratified D7 keyboard). Never leave raw text as a physical word.
    return encode_text7_datum(t, text7, node.tok)


def encode_string(node: String, text7):
    """Рядок у лапках — це D7-текст (чинна ратифікована клавіатура v2).

    Кожен символ стає своїм 7-бітним кодом D7, загорнутим у D2-каркас.
    Це та сама машинерія, що й для ідентифікаторів (text7_encode+frame_text7),
    тож зворотність точна: слова -> символи -> рядок.
    """
    raw = node.tok.text
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        raw = raw[1:-1]
    # SENS reader maps \n/\t/\r to control scalars, not letters n/t/r.
    # Preserve all other escaped characters using the reader's fallback.
    # Literal substitution r"\1" used to silently corrupt Lisp string data.
    escapes = {"n": "\n", "t": "\t", "r": "\r"}
    value = re.sub(
        r"\\([\s\S])",
        lambda match: escapes.get(match.group(1), match.group(1)),
        raw,
    )
    cells = text7_encode(value, text7, node.tok, identifier=False)
    return frame_text7(cells, node.tok)

def encode_clause(node,resolver,text7,lexical_env=()):
    """COND clause is structural; nested executable expressions retain scope."""
    if not isinstance(node,ListNode):
        return encode(node,resolver,text7,quoted=False,lexical_env=lexical_env)
    if not node.items and node.tail is None:
        return [D3_EMPTY]
    words=[D2_OPEN]
    for idx,item in enumerate(node.items):
        if idx:
            words.append(D2_SEP)
        if isinstance(item,ListNode):
            words.extend(
                encode(item,resolver,text7,quoted=False,lexical_env=lexical_env)
            )
        elif isinstance(item,Atom) and item.tok.text in lexical_env:
            # A bare variable in a COND predicate/result position is still an
            # executable lexical reference, not quoted data. Only names in the
            # current proven lexical environment take this route; all other
            # atoms preserve the existing literal-data behavior below.
            words.extend(
                encode(item,resolver,text7,quoted=False,lexical_env=lexical_env)
            )
        else:
            words.extend(
                encode(item,resolver,text7,quoted=True,lexical_env=())
            )
    if node.tail is not None:
        words.append(D2_DOT)
        words.extend(encode(node.tail,resolver,text7,quoted=True,lexical_env=()))
    words.append(D2_CLOSE)
    return words


def encode(node,resolver,text7,quoted=False,lexical_env=()):
    if isinstance(node,ListNode):
        if not node.items and node.tail is None:
            return [D3_EMPTY]

        words=[D2_OPEN]
        head_bits=None
        lambda_names=()
        define_names=()
        letrec_names=()

        for idx,item in enumerate(node.items):
            # Documentation is not code: a (doc ...) form carries human docs, not a
            # machine identity, so it is dropped from the migration (owner 2026-10-15:
            # "скрипту не потрібні коментарі").
            if (not quoted and isinstance(item,ListNode) and item.items
                    and isinstance(item.items[0],Atom) and item.items[0].tok.text=="doc"):
                if words and words[-1]==D2_SEP:
                    words.pop()
                continue
            if idx:
                words.append(D2_SEP)

            if idx==0 and not quoted and isinstance(item,Atom):
                head_text = item.tok.text
                numeric_head_pattern = (
                    r"[+-]?(?:\d+,\d+|,\d+)"
                    if getattr(resolver, "source_surface", "default") in ("ук", "укр")
                    else r"[+-]?(?:\d+\.\d+|\.\d+)"
                )
                # W8-голова не є десятковим D24+ числом:
                # старий SID8 не можна ототожнювати з чинним D8.
                if re.fullmatch(r"[01]{8}", head_text):
                    raise MigrationError(
                        "ambiguous eight-bit SID8/D8 call head: "
                        "use a ratified Ukrainian executable name",
                        item.tok,
                    )
                if (re.fullmatch(r"[+-]?\d+", head_text)
                        or re.fullmatch(numeric_head_pattern, head_text)):
                    raise MigrationError(
                        "D24+ numeric value is data and is not callable",
                        item.tok,
                    )
                # Lexical source bindings take precedence over global/current
                # callable surfaces. This is the scalable shadow-safe rule:
                # source scope, not spelling alone, decides the head.
                if item.tok.text in lexical_env:
                    words.extend(encode_text7_identifier(
                        item.tok.text,text7,item.tok
                    ))
                    continue
                head,_=resolver.head(item.tok,text7)
                head_bits=head[0]
                words.extend(head)
                continue

            # Explicit QUOTE: everything below is data, with no live lexical scope.
            if not quoted and head_bits=="001":
                words.extend(
                    encode(item,resolver,text7,quoted=True,lexical_env=())
                )
                continue

            # D4 LAMBDA: parameter declarations are one contextual Text7 frame
            # per identifier; its body executes under the newly introduced scope.
            # Variadic lambda: bare symbol parameter binds all args as a list.
            if not quoted and head_bits=="0010" and idx==1:
                if isinstance(item, Atom):
                    # A bare binder is variadic: encode its Text7 identity
                    # directly, without inventing a one-element parameter list.
                    lambda_names = (item.tok.text,)
                    words.extend(encode_lambda_params(item, text7))
                    continue
                if not isinstance(item, ListNode):
                    raise MigrationError(
                        "lambda parameters must be a proper list or bare symbol",
                        item.tok if isinstance(item, Atom) else None,
                    )
                lambda_names = lambda_parameter_names(item)
                words.extend(encode_lambda_params(item, text7))
                continue

            if not quoted and head_bits=="0010" and idx>=2:
                body_env=tuple(lambda_names)+tuple(lexical_env)
                words.extend(
                    encode(
                        item,
                        resolver,
                        text7,
                        quoted=False,
                        lexical_env=body_env,
                    )
                )
                continue

            # D4 DEFINE: both a simple binding and a shorthand function
            # signature carry contextual Text7 identifiers, never raw names.
            # A shorthand (name arg ...) introduces the args into the body scope
            # exactly as an immediately applied LAMBDA would.
            if not quoted and head_bits=="0011" and idx==1:
                if isinstance(item,Atom):
                    words.extend(
                        encode_text7_identifier(item.tok.text,text7,item.tok)
                    )
                    continue
                if isinstance(item,ListNode):
                    signature=lambda_parameter_names(item)
                    if not signature:
                        raise MigrationError("DEFINE shorthand requires a function name",item.tok)
                    define_names=tuple(signature[1:])
                    words.extend(encode_lambda_params(item,text7))
                    continue

            if not quoted and head_bits=="0011" and idx>=2:
                body_env=tuple(define_names)+tuple(lexical_env)
                words.extend(
                    encode(item,resolver,text7,quoted=False,lexical_env=body_env)
                )
                continue

            # D9 LETREC: mutual recursive bindings; vars shadow in body scope.
            if not quoted and head_bits=="101100111" and idx==1:
                if not isinstance(item,ListNode):
                    raise MigrationError("LETREC bindings must be a proper list", item.tok)
                for binding in item.items:
                    if not isinstance(binding,ListNode) or len(binding.items)!=2:
                        raise MigrationError("LETREC binding must be (var value)", binding.tok)
                    var = binding.items[0]
                    val = binding.items[1]
                    if not isinstance(var,Atom):
                        raise MigrationError("LETREC var must be an atom", var.tok)
                    # Encode value in current scope
                    words.extend(encode(val,resolver,text7,quoted=False,lexical_env=lexical_env))
                    letrec_names += (var.tok.text,)
                continue

            if not quoted and head_bits=="101100111" and idx>=2:
                letrec_env=tuple(letrec_names)+tuple(lexical_env)
                words.extend(
                    encode(item,resolver,text7,quoted=False,lexical_env=letrec_env)
                )
                continue

            # COND clauses are structural containers, not call heads.
            if not quoted and head_bits=="110":
                words.extend(
                    encode_clause(
                        item,
                        resolver,
                        text7,
                        lexical_env=lexical_env,
                    )
                )
                continue

            words.extend(
                encode(
                    item,
                    resolver,
                    text7,
                    quoted=quoted,
                    lexical_env=lexical_env,
                )
            )

        if node.tail is not None:
            words.append(D2_DOT)
            words.extend(
                encode(node.tail,resolver,text7,quoted=True,lexical_env=())
            )
        words.append(D2_CLOSE)
        return words

    if isinstance(node,Quote):
        return [
            D2_OPEN,
            "001",
            D2_SEP,
            *encode(node.value,resolver,text7,quoted=True,lexical_env=()),
            D2_CLOSE,
        ]
    if isinstance(node,String):
        return encode_string(node,text7)
    if isinstance(node,Atom):
        return encode_atom_data(node,text7,lexical_env=lexical_env,quoted=quoted,resolver=resolver)
    raise TypeError(node)

def line_col(source: str,offset: int):
    line=source.count("\n",0,offset)+1
    prev=source.rfind("\n",0,offset)
    col=offset+1 if prev<0 else offset-prev
    return line,col

def source_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file(): continue
        if any(part in SKIP_DIRS for part in p.parts): continue
        if p.suffix.lower() in SOURCE_EXTS: yield p

# Owner-reviewed NONPROGRAM data (#4460), not executable SENS.
# Both path identity AND source Git blob SHA are mandatory for recognition.
NONPROGRAM_MANIFESTS = (
    ("domain-table", "knowledge/migration-nonprogram-domain-tables-2026-10-08.json", 11),
    ("comment-only-loader", "knowledge/migration-nonprogram-comment-only-loaders-2026-10-08.json", 2),
    ("isa", "knowledge/migration-nonprogram-isa-manifest-2026-10-08.json", 25),
    ("schema", "knowledge/migration-nonprogram-schema-manifest-2026-10-08.json", 19),
    ("evidence", "knowledge/migration-nonprogram-evidence-manifest-2026-10-08.json", 8),
    ("expr-record", "knowledge/migration-nonprogram-expr-records-2026-10-08.json", 13),
    ("knowledge-record", "knowledge/migration-nonprogram-knowledge-records-2026-10-08.json", 12),
)


# Поточні Git-blob свідки семи структурно перевірених маніфестів.
# Старі SHA до українізації не мають блокувати кожну виконувану програму.
# Вміст, схема, кількість і кожен власний source-blob усе ще перевіряються.
NONPROGRAM_MANIFEST_BLOB_SHA = {
    "knowledge/migration-nonprogram-domain-tables-2026-10-08.json": "514cb3eeb9c9c1e46b2c96ecd90e585a1f09e29f",
    "knowledge/migration-nonprogram-comment-only-loaders-2026-10-08.json": "e258a854fb4abab0070c3f7585b96b6acdfcbfb7",
    "knowledge/migration-nonprogram-isa-manifest-2026-10-08.json": "d66fa8f636e47cd00744dc0ed5fa5f2f2c16ccd8",
    "knowledge/migration-nonprogram-schema-manifest-2026-10-08.json": "53689013243182a3087f05781c6cc88be5814900",
    "knowledge/migration-nonprogram-evidence-manifest-2026-10-08.json": "413c9dee025bb56b9fd346701e46d7ae4fb9ea89",
    "knowledge/migration-nonprogram-expr-records-2026-10-08.json": "07c53b8dc76c2f35911f323966fdc2587d9224a9",
    "knowledge/migration-nonprogram-knowledge-records-2026-10-08.json": "d1665b3459b8c1871bb5b729f83557101cfa2cd8",
}


def reject_reviewed_nonprogram_source(source: Path, root: Path = REPO_ROOT) -> None:
    """Prevent minting a physical .sens for SHA-reviewed data, not programs."""
    if source.is_symlink():
        raise SensT5Error("NONPROGRAM_UNTRUSTED_SYMLINK layer=encode")
    try:
        relative = source.resolve(strict=True).relative_to(root.resolve()).as_posix()
    except ValueError:
        return  # User-controlled external corpus has no reviewed classification.
    except OSError as exc:
        raise SensT5Error(f"NONPROGRAM_SOURCE_UNREADABLE layer=encode {exc}") from exc

    # Не перевіряємо сім незалежних маніфестів для КОЖНОЇ програми.
    # Інакше дрейф одного опису даних помилково блокує весь lib/ навіть
    # тоді, коли жодний файл із відповідного набору не міг бути входом.
    # Перелік охоплення є явною межею: нові класи не-програм потребують
    # окремого owner-reviewed оновлення, а не автоматичного виключення.
    reviewed_lib_cohort = None
    if relative.startswith("lib/"):
        if re.fullmatch(r"lib/domains/d(?:[1-9]|10|11)\.lisp", relative):
            reviewed_lib_cohort = "domain-table"
        elif relative in ("lib/core2.lisp", "lib/surface/ukr.lisp"):
            reviewed_lib_cohort = "comment-only-loader"
        elif relative.startswith("lib/machine/isa/"):
            reviewed_lib_cohort = "isa"
        elif relative == "lib/island-math-evidence.lisp":
            reviewed_lib_cohort = "schema"
        else:
            return  # Виконуваний або ще не класифікований Lisp; не фальшивий STOP.

    # D11 — мінливий НЕратифікований словник даних. Живий файл може
    # змінюватися без оновлення історичного SHA в маніфесті 08.10.
    # Не визнаємо D11 виконуваним: перевіряємо саме форму таблиці,
    # а не дату/хеш старої фікстури; зайвий вираз відхиляємо.
    if relative == "lib/domains/d11.lisp":
        try:
            rows = [line.strip() for line in source.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.lstrip().startswith(";")]
        except (OSError, UnicodeError) as exc:
            raise SensT5Error(f"NONPROGRAM_D11_TABLE_UNREADABLE layer=encode {exc}") from exc
        row_pattern = re.compile(
            r"\(([01]{11})\s+\(ук\s+[^()\s]+\)\s+"
            r"\(укр\s+[^()\s]+\)\s+\(san\s+[^()\s]+\)\s+"
            r"\(en\s+[^()\s]+\)\s+\(LISP\s+[^()\s]+\)\s+"
            r"\(sym\s+\(\)\)\)"
        )
        matches = [row_pattern.fullmatch(row) for row in rows[1:-1]]
        if (len(rows) < 3 or rows[0] != "(domain-table-1" or rows[-1] != ")"
                or not all(matches)):
            raise SensT5Error(f"NONPROGRAM_D11_TABLE_INVALID layer=encode source={relative}")
        bits = [match.group(1) for match in matches]
        if len(bits) != len(set(bits)) or bits != sorted(bits):
            raise SensT5Error(f"NONPROGRAM_D11_TABLE_INVALID layer=encode source={relative} reason=duplicate-or-order")
        raise SensT5Error(
            f"NONPROGRAM_DATA_NOT_EXECUTABLE layer=encode source={relative} "
            f"cohort=domain-table rows={len(bits)}"
        )

    for cohort, name, expected_count in NONPROGRAM_MANIFESTS:
        if reviewed_lib_cohort is not None and cohort != reviewed_lib_cohort:
            continue
        manifest = root / name
        if not manifest.is_file() or manifest.is_symlink():
            raise SensT5Error(f"NONPROGRAM_MANIFEST_UNAVAILABLE layer=encode {name}")
        try:
            contents = manifest.read_bytes()
            manifest_sha = hashlib.sha1(
                b"blob " + str(len(contents)).encode("ascii") + b"\0" + contents
            ).hexdigest()
            if manifest_sha != NONPROGRAM_MANIFEST_BLOB_SHA[name]:
                raise SensT5Error(
                    f"NONPROGRAM_MANIFEST_SHA_DRIFT layer=encode manifest={name} "
                    f"expected={NONPROGRAM_MANIFEST_BLOB_SHA[name]} actual={manifest_sha}"
                )
            record = json.loads(contents.decode("utf-8"))
        except (UnicodeError, OSError, ValueError) as exc:
            raise SensT5Error(f"NONPROGRAM_MANIFEST_INVALID layer=encode {name}: {exc}") from exc
        if (record.get("schema") != "sens-migration-nonprogram-manifest-1"
                or record.get("issue") != 4460
                or record.get("automatic_sens_companion") is not False
                or not isinstance(record.get("entries"), list)
                or len(record["entries"]) != expected_count):
            raise SensT5Error(f"NONPROGRAM_MANIFEST_UNTRUSTED layer=encode {name}")
        for entry in record["entries"]:
            if not isinstance(entry, dict) or entry.get("path") != relative:
                continue
            scoped = (
                (cohort == "domain-table" and bool(re.fullmatch(r"lib/domains/d(?:[1-9]|10|11)\.lisp", relative)))
                or (cohort == "comment-only-loader" and relative in ("lib/core2.lisp", "lib/surface/ukr.lisp"))
                or (cohort == "isa" and relative.startswith("lib/machine/isa/"))
                or (cohort == "schema" and relative.startswith(("contracts/", "lib/", "tests/fixtures/")))
                or (cohort == "evidence" and relative.startswith(("evidence/", "tests/fixtures/")))
                or (cohort == "expr-record" and relative.startswith("tests/fixtures/"))
                or (cohort == "knowledge-record" and relative.startswith("knowledge/") and relative.count("/") == 1)
            )
            if not scoped:
                raise SensT5Error(f"NONPROGRAM_REVIEW_SCOPE_INVALID layer=encode source={relative}")
            pinned = entry.get("git_blob_sha1")
            if not isinstance(pinned, str) or re.fullmatch("[0-9a-f]{40}", pinned) is None:
                raise SensT5Error(f"NONPROGRAM_SHA_PIN_INVALID layer=encode source={relative}")
            data = source.read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
            if actual != pinned:
                raise SensT5Error(
                    f"NONPROGRAM_SOURCE_SHA_DRIFT layer=encode source={relative} "
                    f"expected={pinned} actual={actual}"
                )
            raise SensT5Error(
                f"NONPROGRAM_DATA_NOT_EXECUTABLE layer=encode source={relative} "
                f"cohort={cohort} source_blob_sha={actual}"
            )


def sens_destination(rel: Path) -> Path:
    """НАЗВА.lisp -> НАЗВА.sens у тому самому відносному каталозі."""
    if rel.suffix.lower() != ".lisp":
        raise ValueError("only .lisp sources are eligible")
    return rel.with_suffix(".sens")


def write_atomic_no_clobber(target: Path, physical_bytes: bytes) -> None:
    """Опублікувати новий .sens лише якщо не існує; ніяких тихих overwrite."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", prefix=".sens-t5-", suffix=".tmp",
            dir=target.parent, delete=False,
        ) as staged:
            tmp_name = Path(staged.name)
            staged.write(physical_bytes)
            staged.flush()
            os.fsync(staged.fileno())
        # Atomic hard-link with fail-if-exists; no permissions to replace targets.
        os.link(tmp_name, target)
    finally:
        if tmp_name is not None:
            tmp_name.unlink(missing_ok=True)


def zig_mint_verified_t5(projection: str, reference: bytes, binary: Path, bridge,
                        *, codec="t5m"):
    """Keep SENS word identities upstream; Zig alone mints physical T5 bytes.

    The Python bytes are a parity witness, NEVER the published carrier. This
    receipt certifies physical byte integrity only, not SENS semantics.
    """
    expected = hashlib.sha256(reference).hexdigest()
    physical = bridge.carry_t5(
        binary, projection, codec=codec, trusted_source_sha256=expected,
    )
    if physical != reference:
        offset = next((i for i, (a, b) in enumerate(zip(reference, physical))
                       if a != b), min(len(reference), len(physical)))
        raise SensT5Error(
            "ZIG_CARRY_REFERENCE_MISMATCH layer=transport "
            f"expected_sha256={expected} "
            f"actual_sha256={hashlib.sha256(physical).hexdigest()} "
            f"first_byte={offset}"
        )
    receipt = bridge.verify_t5(
        binary, physical, codec=codec, trusted_source_sha256=expected
    )
    if (receipt.get("physical_sha256") != expected or
            receipt.get("source_pin_status") != "MATCHED_CALLER_SUPPLIED_SHA256" or
            not receipt.get("zig_binary_sha256")):
        raise SensT5Error("ZIG_CARRY_UNATTESTED_RECEIPT layer=transport")
    return physical, receipt


def migrate_file(source: str,resolver,text7,*,codec="t5m",source_surface="default",
                 imported_bindings=()):
    if codec not in ("t5", "t5m"):
        raise MigrationError(f"unsupported physical codec {codec!r}")
    if source_surface not in ("default", "ук", "укр"):
        raise MigrationError(f"unsupported source surface {source_surface!r}")
    # Comments do not belong to the program. Check *lexical atoms*, not
    # the original file bytes: Unicode digits in ; / #|...|# comments (and
    # opaque string literals) cannot change executable D24+ identity.
    resolver.source_surface = source_surface
    stripped=strip_comments(source)
    tokens=tokenize(stripped, source_surface=source_surface)
    if source_surface in ("ук", "укр"):
        for tok in tokens:
            if tok.kind != "ATOM":
                continue
            for offset, ch in enumerate(tok.text):
                if ch.isdecimal() and ch not in "0123456789":
                    raise MigrationError(
                        f"non-keyboard decimal digit U+{ord(ch):04X} in Ukrainian Lisp atom",
                        Tok("ATOM", ch, tok.offset + offset),
                    )
    forms=Parser(tokens).parse_program()
    # A caller can identify an actually loaded Lisp dependency. Its DEFINE
    # target is a source binding (D7 name), NOT a callable D9 resident.
    # Current-file DEFINE shadows an imported one, like Lisp loading order.
    resolver.set_global_bindings(
        [*imported_bindings, *collect_global_bindings(forms, resolver)], text7
    )
    all_words=[]
    for i,form in enumerate(forms):
        if i: all_words.append(D2_SEP)
        all_words.extend(encode(form,resolver,text7,quoted=False))
    text=" ".join(all_words)
    if text: text+="\n"
    return text

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--out", type=Path, required=True,
                    help="окрема вихідна папка; .lisp НЕ змінюється")
    ap.add_argument("--foundation", type=Path, default=REPO_ROOT / "knowledge/d1-d11-foundation.json")
    ap.add_argument("--domain-surfaces", type=Path, default=REPO_ROOT / "crates/sens/src/domain_surface_registry_generated.rs")
    ap.add_argument("--semantic-generated", type=Path, default=REPO_ROOT / "crates/sens/src/semantic_registry_generated.rs")
    ap.add_argument("--semantic-registry", type=Path, default=REPO_ROOT / "crates/sens/src/semantic_registry.rs")
    ap.add_argument("--necessary-forms", type=Path, default=REPO_ROOT / "crates/sens/src/eval/necessary_forms_generated.rs")
    ap.add_argument("--text7", type=Path, default=REPO_ROOT / "knowledge/d7-keyboard-v2-ratified.json",
                    help="only current owner-ratified D7 keyboard/v2 JSON (128/128); historical .rs projections are rejected")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="переклад/перевірка без запису фізичних файлів")
    ap.add_argument("--codec", choices=("t5m", "t5"), default="t5m",
                    help="T5M — дефолтний 5-тритовий транспорт (1 байт); T5 — явний legacy-формат")
    ap.add_argument("--source-surface", choices=("default", "ук", "укр"),
                    default="укр",
                    help="типово повна українська проєкція укр і десяткова кома; default — явний історичний режим")
    ap.add_argument("--binding-source", type=Path, action="append", default=[],
                    help="явний попередньо завантажений .lisp із DEFINE; лише для одного файла")
    ap.add_argument("--unpaired-only", action="store_true",
                    help="мігрувати лише .lisp без однойменного наявного .sens")
    ap.add_argument("--refresh-existing", action="store_true",
                    help="явно оновити перевірені Zig фізичні .sens та однойменні перегляди; без зміни .lisp")
    args = ap.parse_args()
    if args.refresh_existing and args.unpaired_only:
        ap.error("--refresh-existing несумісний з --unpaired-only")
    if args.refresh_existing and args.codec != "t5m":
        ap.error("--refresh-existing дозволяє лише чинний T5M")
    if args.report is None:
        args.report = args.out.with_name(args.out.name + ".report.json")

    data = load_foundation(args.foundation)
    # Current D8 is ratified, but occupancy never grants executable callability.
    # An unproven eight-bit call head is rejected rather than inferred from сід8.
    d9_residents = set(data["domains"].get("D9",{}).get("residents",{}).keys())
    my, upper, bridge_by_sid = build_three_pass_maps(
        data, args.domain_surfaces, args.semantic_generated,
        args.semantic_registry, args.necessary_forms
    )
    text7 = build_text7(data, args.text7)
    rows = []
    written = 0
    blocked = 0
    not_program = 0
    totals = {"already-exact": 0,
              "pass2-my-lisp": 0, "pass3-lisp15": 0,
              "pass4-text7-global": 0, "passthrough-head": 0}

    root = args.root.resolve()
    # An explicit .lisp path means ONE input file, not an empty directory scan.
    # A directory still gives the stable sorted tree inventory.
    if root.is_file():
        if root.suffix.lower() not in SOURCE_EXTS:
            ap.error("a single source must be a .lisp file")
        base_root = root.parent
        paths = [root]
    elif root.is_dir():
        base_root = root
        paths = sorted(source_files(root))
    else:
        ap.error(f"input path does not exist: {root}")
    # Cross-file Lisp functions cannot be inferred from D9 residency. Read
    # only caller-declared source definitions, never a provisional registry.
    imported_bindings = []
    binding_receipts = []
    if args.binding_source and not root.is_file():
        ap.error("--binding-source requires exactly one input .lisp file")
    for bound_path in args.binding_source:
        candidate = bound_path.absolute()
        if (candidate.suffix != ".lisp" or not candidate.is_file()
                or any(p.is_symlink() for p in (candidate, *candidate.parents))
                or not candidate.resolve().is_relative_to(REPO_ROOT.resolve())
                or candidate.resolve() == root):
            ap.error(f"invalid previously loaded Lisp source: {bound_path}")
        raw = candidate.read_bytes()
        imported_forms = Parser(tokenize(
            strip_comments(raw.decode("utf-8")),
            source_surface=args.source_surface,
        )).parse_program()
        # Full укр D4 DEFINE is supplied by the ratified surface resolver.
        # Parsing without it silently reports ZERO bindings from real Lisp.
        imported_defines = collect_global_bindings(
            imported_forms, Resolver(my, upper, d9_residents, bridge_by_sid)
        )
        imported_bindings.extend(imported_defines)
        binding_receipts.append({
            "path": candidate.relative_to(REPO_ROOT).as_posix(),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "define_bindings": len(imported_defines),
        })
    skipped_paired = []
    if args.unpaired_only:
        candidates = []
        for path in paths:
            partner = path.with_suffix(".sens")
            if partner.exists() or partner.is_symlink():
                skipped_paired.append(str(path.relative_to(base_root)))
            else:
                candidates.append(path)
        paths = candidates
    # Publish mode always builds pinned Zig; missing Zig cannot silently fall
    # back to Python. Dry-run remains a read-only mechanical preview.
    zig_temp = (tempfile.TemporaryDirectory(prefix="sens-three-pass-zig-")
                if not args.dry_run and paths else None)
    zig_binary = None
    if zig_temp is not None:
        try:
            zig_binary = zig_codec_bridge.build_transport(Path(zig_temp.name))
        except (zig_codec_bridge.ZigCodecError, OSError) as exc:
            zig_temp.cleanup()
            ap.error(f"ZIG_CARRY_REQUIRED_FOR_PUBLICATION: {exc}")
    seen_destinations = set()
    for path in paths:
        rel = path.resolve().relative_to(base_root)
        dest = sens_destination(rel)
        target = args.out / dest
        resolver = Resolver(my, upper, d9_residents, bridge_by_sid)
        try:
            if dest in seen_destinations:
                raise SensT5Error(f"duplicate destination {dest}")
            seen_destinations.add(dest)
            # A reviewed DATA source may never acquire an executable carrier.
            # This check precedes the Zig codec and every filesystem write.
            reject_reviewed_nonprogram_source(path)
            if not args.refresh_existing and (target.exists() or target.is_symlink()):
                raise SensT5Error(f"target already exists; not overwriting {dest}")
            source = path.read_text(encoding="utf-8")
            # Немає виконуваних форм — немає причини створювати .sens.
            # Незакритий блоковий коментар є реальною помилкою.
            if not strip_comments(source).strip():
                raise SensT5Error("NONPROGRAM_COMMENT_ONLY layer=source")
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(5)
            try:
                projection = migrate_file(
                    source, resolver, text7, codec=args.codec,
                    source_surface=args.source_surface,
                    imported_bindings=imported_bindings,
                )
            finally:
                signal.alarm(0)
            # Strict physical T5: any historic name, passthrough or unencoded
            # value still visible is a empty, never a falsely binary file.
            if args.codec == "t5m":
                words = parse_t5m_words(projection)
                reference = encode_t5m_projection(projection)
                decoded = decode_t5m_bytes(reference)
            else:
                words = parse_words(projection)
                reference = encode_projection(projection)
                decoded = decode_bytes(reference)
            if decoded != words:
                raise SensT5Error("byte roundtrip changes source word identities")
            zig_receipt = None
            if zig_binary is not None:
                payload, zig_receipt = zig_mint_verified_t5(
                    projection, reference, zig_binary, zig_codec_bridge,
                    codec=args.codec,
                )
                # The extensionless spaced-bit view is not an executable .sens.
                if args.refresh_existing:
                    # Явне поновлення тільки після exact-word roundtrip і
                    # Zig parity; двофайлова транзакція має rollback.
                    migration_publish_pair.replace_pair(
                        target, payload, target.with_suffix(""),
                        projection.encode("ascii"),
                    )
                else:
                    migration_publish_pair.publish_pair(
                        write_atomic_no_clobber, target, payload,
                        target.with_suffix(""), projection.encode("ascii"),
                    )
            else:
                payload = reference  # dry-run only, NEVER published
            for key, value in resolver.counts.items():
                totals[key] += value
            status = ("would-refresh" if args.refresh_existing else "would-write") if args.dry_run else ("refreshed" if args.refresh_existing else "written")
            row = {
                "path": str(rel), "output": str(dest), "status": status,
                "bytes": len(payload), "semantic_word_count": len(words),
                "semantic_bits": sum(len(word) for word in words),
                "transport_trits": sum(len(word) for word in words) + len(words) - 1,
                "physical_sha256": hashlib.sha256(payload).hexdigest(),
                "typed_word_sha256": typed_sha256(words),
                "semantic_admitted": False,
                "zig_transport": zig_receipt,
                "passes": resolver.counts,
            }
            rows.append(row)
            written += 1
        except (MigrationError, SensT5Error, UnicodeError, OSError,
                ValueError, zig_codec_bridge.ZigCodecError) as error:
            reason = getattr(error, "message", str(error))
            # Тільки SHA-верифіковані owner-reviewed дані та файли без
            # виконуваних форм не є програмами. SHA drift, нерозпізнані
            # виклики та всі помилки кодека залишаються BLOCKED.
            is_not_program = isinstance(error, SensT5Error) and (
                reason.startswith("NONPROGRAM_DATA_NOT_EXECUTABLE layer=encode ")
                or reason == "NONPROGRAM_COMMENT_ONLY layer=source"
            )
            if is_not_program:
                not_program += 1
            else:
                blocked += 1
            row = {
                "path": str(rel), "output": str(dest),
                "status": "not-program" if is_not_program else "blocked",
                "reason": reason,
                "passes": resolver.counts,
            }
            token = getattr(error, "tok", None)
            if token is not None:
                text = locals().get("source", "")
                line, column = line_col(text, token.offset)
                row.update({"token": token.text, "line": line, "column": column})
            rows.append(row)
        if (written + blocked + not_program) % 25 == 0:
            print(f"PROGRESS seen={written + blocked + not_program} written={written} blocked={blocked} not_program={not_program}",
                  flush=True)

    if zig_temp is not None:
        zig_temp.cleanup()
    report = {
        "schema": "sens-three-pass-t5-migration/v3",
        "naming_law": "SOURCE/name.lisp -> OUT/name.sens; the extensionless 0/1 view (name, spaced bits + one LF) is now REQUIRED alongside each .sens (#4694)",
        "file_format": {
            "suffix": ".sens", "physical": ("binary-T5M-base3-5-trits-per-byte"
                                                if args.codec == "t5m" else "binary-T5-five-trits-per-byte"),
            "language": ("D1–24+ frame; T5M physical subset: D1–D10 plus exact D24+ numeric words" if args.codec == "t5m"
                         else "currently supported D1..D9 exact-width 0/1 words"),
            "domain_frame": "D1–24+; exact domain laws come from language-contract.lisp",
            "identity_migration_subset": "exact current D1-D10 identities only where current projections uniquely resolve them; runtime execution is not certified here; D11+ future semantics are not inferred",
            "transport_separator": "logical trit 2 strictly between words",
            "file_eof": "physical byte length; no terminal 22",
            "padding": "T5M: zero through four final trits 2; T5: zero through four final trits 2",
            "ascii_text": False,
            "source_surface": args.source_surface,
            "numeric_projection": "human decimal tokens require explicit successful D24+ lowering; unsupported values stay blocked",
        },
        "passes": {
            "1": "retired historical SID8 bridge: no executable mapping",
            "2": "current source projection -> exact current domain identity; execution is separate",
            "3": "historical Lisp-I/1.5 spelling -> current exact identity when uniquely resolved; execution is separate",
        },
        "blocked_policy": "no unresolved textual source can become physical .sens",
        "migration_complete": False,  # batch transport never certifies semantic migration
        "physical_batch_complete": written > 0 and blocked == 0 and not args.dry_run,
        "only_unpaired": args.unpaired_only,
        "skipped_paired_paths": skipped_paired,
        "sid8_law": "SID8/Sens8 retired; no source-era, historical map or legacy coverage is accepted; under the D1–24+ frame, width alone grants no identity; this migration requires a named current projection, while runtime execution remains separate",
        "source_policy": ("input .lisp never rewritten; paired .sens + view refreshed only after explicit --refresh-existing and pinned Zig parity" if args.refresh_existing else "input .lisp never rewritten; existing .sens never overwritten"),
        "explicit_preloaded_binding_sources": binding_receipts,
        "mode": ("dry-run" if args.dry_run else "refresh-existing-zig-minted" if args.refresh_existing else "write-new-only-zig-minted"),
        "semantic_admitted": False,
        "physical_producer": ("NOT_INVOKED_ALREADY_PAIRED"
                              if not paths and skipped_paired else
                              "PYTHON_REFERENCE_ONLY" if args.dry_run
                              else f"PINNED_ZIG_{args.codec.upper()}_CARRY"),
        "summary": {
            "files_seen": len(paths),
            "files_skipped_paired": len(skipped_paired),
            "files_written": written if not args.dry_run else 0,
            "files_would_write": written if args.dry_run else 0,
            "files_blocked": blocked, "files_not_program": not_program,
            "resolved_heads": totals,
        },
        "files": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    # Nothing new to publish when every selected source is already paired:
    # this is a valid idempotent selection, not a codec/toolchain failure.
    # An actually empty or wholly blocked input still returns a failure.
    # Частковий пакет не є успіхом: лишаємо вдалі окремі результати,
    # але звітуємо код 2, якщо хоча б одна програма не перетворилася.
    # CI може зберегти артефакти та показати точні причини без глобального STOP.
    return 0 if blocked == 0 and (written or not_program or (not paths and bool(skipped_paired))) else 2


if __name__ == "__main__":
    raise SystemExit(main())
