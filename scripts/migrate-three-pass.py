#!/usr/bin/env python3
"""Three-pass source migration: historical recognition into CURRENT exact domains.

Interpret all historical spellings and eight-bit tokens through audited
provenance; they are never themselves a current domain or call law.
Pass 2: current admitted source surfaces -> corresponding exact-domain words.
Pass 3: historical Lisp 1–1.5 names -> admitted current D3–D6 resident.

Rules derived from current SENS contract and later owner decisions:
- () is D3:000; nonempty list structure uses D2 10/00/11/01
  (open/separator/dot/close). D2 is NEVER a call head or data identity.
- D1:0/1 are predicates; identical payloads in D3–D10 are not D1.
  Ratified domain occupancy alone never admits a callable mechanism.
- Unresolved names may become D7 keyboard/v2 TEXT DATA if every glyph is
  admitted. This is NOT permission to call that text as a function.
  An unrepresentable identifier or unproved historical successor fails closed.
- Quoted data resolves an admitted ladder identity before D7 text fallback.
- Textual decimal tokens and #d/#b/#q2 textual forms project to D7 data,
  NOT implicit numerical values. Bare binary words in numeric-width D24+
  require an explicit admitted numeric domain/frame and fail closed here.
- Current D7 keyboard/v2 128/128 is the ONLY text projection admitted by
  this script. Historical .rs projection is rejected; no v1 corpus was
  migrated, so no v1-to-v2 conversion prerequisite is needed.
- Comments are stripped. Unresolved raw names cannot become .sens bytes.
  Python T5 packing is an independent parity reference ONLY. Real .sens
  bytes are minted by pinned Zig and verified before atomic publication.
- Output is a physical binary T5 .sens under --out with the same basename
  as its .lisp source. Existing .sens files are never overwritten;
  source .lisp is retained.

Chronology for migration audit: D7 projection retirement 5aafc1e8
(13 Oct 2026); numeric TEXT→D7 owner corrections 54078adb/629b077c
(14 Oct 2026); D11 test-only noncallable guard 7a48037b (14 Oct).
The above notes describe implementation, not a second semantic contract.
"""
from __future__ import annotations

import argparse
import ast
from functools import lru_cache
from dataclasses import dataclass
import json
import hashlib
import os
from pathlib import Path
import re
import signal
import tempfile
import sys

SCRIPTS = str(Path(__file__).resolve().parent)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from sens_t5_codec import SensT5Error, decode_bytes, encode_projection, parse_words, typed_sha256
import zig_codec_bridge
import migration_publish_pair

REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXTS = {".lisp"}
SKIP_DIRS = {".git","target","node_modules","vendor","dist","build",".venv","venv","__pycache__"}

D2_SEP="00"
D2_CLOSE="01"
D2_OPEN="10"
D2_DOT="11"
D3_EMPTY="000"

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
            state="block"; depth=1; i+=2; continue
        out.append(ch); i+=1
    if state=="block":
        raise MigrationError("unterminated block comment")
    if state=="string":
        raise MigrationError("unterminated string")
    return "".join(out)

def tokenize(source: str) -> list[Tok]:
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
        while i<n and (not source[i].isspace()) and source[i] not in ("(", ")", "'", '"', "`", ","):
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
            # A label may exist in several domains (e.g. MAP), so do not let one
            # TEXT-DATA likewise). The migration admits call-domains D3-D6, so the
            # LOWEST domain must win: first-wins keeps MAP -> D6 101000 instead of
            # overwrite another, which made en 'map' resolve to a non-D3-D6
            # resident and broke every my-lisp head resolution.
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

    _bridge_by_sid = {}
    # #2953 / sens8-bridge-proposal-v1: only EXACT-name matches are bridged.
    # A Sens8 name resolves to its ratified-ladder target coordinate.
    _bridge_path = REPO_ROOT / "research" / "sens8-bridge-proposal-v1.json"
    if _bridge_path.is_file():
        _bridge = json.loads(_bridge_path.read_text(encoding="utf-8"))
        for _row in _bridge.get("exact_bridge", []):
            _name = _row.get("sens8_name")
            _tgt = _row.get("target") or ""
            if _name and ":" in _tgt:
                _dom, _bits = _tgt.split(":", 1)
                current.setdefault(_name, (_bits, _dom))
            _sid = _row.get("sid8")
            if _sid and ":" in _tgt:
                _bridge_by_sid[_sid] = tuple(_tgt.split(":", 1))

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


def text7_encode(spelling: str,candidates,tok: Tok):
    if "keyboard-v2" in candidates:
        if not spelling:
            raise MigrationError("empty D7 keyboard/v2 identifier", tok)
        # lisp-symbol-replacement-plan.uk.md: em/en dash and box glyphs used in an
        # identifier map to keyboard glyphs. Scoped to the identifier path only.
        spelling = spelling.translate({0x2014: "-", 0x2013: "-", 0x2500: "-", 0x2550: "="})
        view = _keyboard_v2_mode(spelling, tok)
        indexes = candidates["keyboard-v2"]
        chosen = indexes[view]
        # The san view is Devanagari; sources spell san in IAST Latin. Transliterate
        # (reversible) when the raw spelling is not directly on the keyboard.
        if view == "san" and any(chosen.get(g) is None for g in spelling):
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
        self.bridge_by_sid=dict(bridge_by_sid or {})
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

    def head(self,tok: Tok,text7=None):
        t=tok.text
        # Domain identity is (exact width, exact bits), never a flat SID8
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
            if width in (7, 9, 10):
                if width == 9 and t in self.d9_residents:
                    # Ratified D9 functions are executable
                    pass
                else:
                    role = {7: "D7 keyboard text/data",
                            9: "D9 owner residency without a verified callable route",
                            10: "D10 owner codebook without runtime admission"}[width]
                    raise MigrationError(
                        f"exact D{width}:{t} is {role}; executable mechanism required",
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
            _tgt = self.bridge_by_sid.get(t)
            if _tgt is not None:
                self.counts["already-exact"]+=1
                return [ _tgt[1] ],"already-exact"
            raise MigrationError(
                f"retired SID8-era head {t}: no current named D3-D6 resident",
                tok,
            )

        # D7 є текстовою/фонемною ідентичністю, не викликаною функцією.
        # Для D9 таблиця резидентів сама по собі не доводить виконуваність.
        # Без окремого допущеного механізму забороняємо обидві голови.
        if len(t) in (7, 9) and set(t) <= set("01"):
            if len(t) == 7:
                raise MigrationError(
                    f"D7 {t}: фонемна/текстова ідентичність не є виконуваною головою",
                    tok,
                )
            # An admitted D9 resident IS the ratified callable route (the earlier
            # width-9 check already accepted it); only a NON-resident 9-bit head
            # lacks a proven mechanism. Keep the two checks consistent.
            if t in self.d9_residents:
                self.counts["already-exact"]+=1
                return [t],"already-exact"
            raise MigrationError(
                f"D9 {t}: відсутній доказ допущеного механізму виклику",
                tok,
            )

        # Source-defined global callables shadow human builtin surfaces.
        # Exact binary identities above remain authoritative: only a name
        # that appeared as a proven global DEFINE target takes this route.
        # Resolve it before pass-2/pass-3 surface mappings; otherwise
        # (define car ...) followed by (car) accidentally calls D3 CAR.
        if t in self.global_binding_words:
            self.counts["pass4-text7-global"]+=1
            return self.global_binding_words[t],"pass4-text7-global"

        # Pass 2: known my-lisp/current admitted surfaces. A surface known to
        # the old registry but lacking a current resident is a blocker.
        if t in self.my:
            ident=self.my[t]
            if ident is None:
                raise MigrationError(
                    f"legacy-unmapped my-lisp function {t!r}: no current D3-D6 resident",
                    tok,
                )
            self.counts["pass2-my-lisp"]+=1
            return [ident[0]],"pass2-my-lisp"

        # Pass 3: historical LISP I / Lisp 1.5 UPPERCASE names.
        if t==t.upper() and t in self.upper:
            ident=self.upper[t]
            if ident is None:
                raise MigrationError(
                    f"legacy-unmapped Lisp 1-1.5 function {t}: no current D3-D6 resident",
                    tok,
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
        raise MigrationError("empty Text7 identifier is not admissible",tok)
    words=[D2_OPEN]
    for index,cell in enumerate(cells):
        if index:
            words.append(D2_SEP)
        words.append(cell)
    words.append(D2_CLOSE)
    return words


def encode_text7_identifier(spelling: str,text7,tok: Tok):
    return frame_text7(text7_encode(spelling,text7,tok), tok)


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


def encode_lambda_params(node: ListNode,text7):
    names=lambda_parameter_names(node)
    words=[D2_OPEN]
    for index,name in enumerate(names):
        if index:
            words.append(D2_SEP)
        words.extend(
            encode_text7_identifier(
                name,
                text7,
                Tok("ATOM",name,node.tok.offset),
            )
        )
    words.append(D2_CLOSE)
    return words


def encode_atom_data(node: Atom,text7,lexical_env=(),quoted=False,resolver=None):
    t=node.tok.text
    if t in lexical_env:
        return encode_text7_identifier(t,text7,node.tok)
    if len(t)==2 and set(t)<=set("01"):
        raise MigrationError(
            f"D2 word {t} is structural control only; it cannot be ordinary data",
            node.tok,
        )
    if t in D1_UK_SURFACES:
        return [D1_UK_SURFACES[t]]
    # D24/D48/... are qualified numeric domains. A historical decimal, sign,
    # ratio, #d or #b source token is NOT a raw D1-D9 identity and has no
    # admitted literal->Dn physical-source lowering. Never transcode a number
    # into a function address or Text7 glyphs by matching its spelling.
    # Bare bit words outside 0/1 remain domain addresses, *not* numerals;
    # exact D24+ payload words also require an explicit domain-bearing envelope.
    from domain_tables import is_number_width
    binary_word = bool(re.fullmatch(r"[01]+", t))
    numeric_width = len(t)
    domain_width = is_number_width(numeric_width)
    # Owner rule: the language is binary by default; a *textual* numeral is D7
    # text, not a number. Mathematical values are explicit D24+ envelopes only.
    # So a plain decimal source token is admitted as D7 text (no binary<->decimal
    # redefinition); explicit #d/#b/#q2 and number-width bit words stay blocked.
    # Owner rule: math is D24+ only. A source numeric token (plain decimal,
    # #d/#b/#q2 literal) is a textual projection -> D7 text, never a number.
    # Only a bare 0/1 word whose width IS a numeric D24+ domain is numeric.
    if (NUMERIC_RE.fullmatch(t) and not binary_word
            or re.fullmatch(r"(?i)#(?:d[+-]?\d+(?:/\d+)?|b[01]+|q2:[+-]?[01]+/[01]+)", t)):
        return encode_text7_identifier(t, text7, node.tok)
    if binary_word and domain_width:
        raise MigrationError(
            "unqualified numeric literal blocked: requires explicit D24+ "
            "numeric-domain identity and admitted physical encoding",
            node.tok,
        )
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
        return encode_text7_identifier(t, text7, node.tok)
    # Нецитовані дані: ім'я, яке джерело саме зв'язує глобально (DEFINE),
    # є Text7-посиланням, а не сирим текстом. Решта лишається точно як
    # написано і пізніше fail-closed перевіркою фізичного 0/1-слова.
    if resolver is not None and t in resolver.global_binding_words:
        return list(resolver.global_binding_words[t])
    # Owner rule: unresolved names are DATA -> D7 text (all their glyphs, e.g. "/",
    # live in the ratified D7 keyboard). Never leave raw text as a physical word.
    return encode_text7_identifier(t, text7, node.tok)


def encode_string(node: String,text7):
    # A string literal is DATA, not a machine identity: its content is not
    # keyboard-encoded (owner 2026-10-15: the script does not need comments/docs,
    # and a quoted citation is data). It is carried as an opaque empty data cell.
    content = node.tok.text[1:-1]  # strip surrounding quotes
    content = content.replace('\\"', '"').replace('\\\\', '\\')
    return [D2_OPEN, D3_EMPTY, D2_CLOSE]
    cells = text7_encode(content, text7, node.tok)
    # Frame as D7 data: D2_OPEN + D2_OPEN + cells + D2_CLOSE + D2_CLOSE
    words = [D2_OPEN, D2_OPEN]
    for cell in cells:
        words.append(cell)
    words.append(D2_CLOSE)
    words.append(D2_CLOSE)
    return words


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
                    # Variadic lambda: single parameter name
                    lambda_names = (item.tok.text,)
                    words.append(D2_OPEN)
                    words.extend(
                        encode_text7_identifier(
                            item.tok.text,
                            text7,
                            Tok("ATOM", item.tok.text, item.tok.offset),
                        )
                    )
                    words.append(D2_CLOSE)
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
    ("domain-table", "knowledge/migration-nonprogram-domain-tables-2026-10-08.json", 9),
    ("comment-only-loader", "knowledge/migration-nonprogram-comment-only-loaders-2026-10-08.json", 2),
    ("isa", "knowledge/migration-nonprogram-isa-manifest-2026-10-08.json", 25),
    ("schema", "knowledge/migration-nonprogram-schema-manifest-2026-10-08.json", 21),
    ("evidence", "knowledge/migration-nonprogram-evidence-manifest-2026-10-08.json", 8),
    ("expr-record", "knowledge/migration-nonprogram-expr-records-2026-10-08.json", 13),
    ("knowledge-record", "knowledge/migration-nonprogram-knowledge-records-2026-10-08.json", 14),
)


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
    for cohort, name, expected_count in NONPROGRAM_MANIFESTS:
        manifest = root / name
        if not manifest.is_file() or manifest.is_symlink():
            raise SensT5Error(f"NONPROGRAM_MANIFEST_UNAVAILABLE layer=encode {name}")
        try:
            record = json.loads(manifest.read_text(encoding="utf-8"))
        except (UnicodeError, OSError, ValueError) as exc:
            raise SensT5Error(f"NONPROGRAM_MANIFEST_INVALID layer=encode {name}: {exc}") from exc
        if (record.get("schema") != "sens-migration-nonprogram-manifest/1"
                or record.get("issue") != 4460
                or record.get("automatic_sens_companion") is not False
                or not isinstance(record.get("entries"), list)
                or len(record["entries"]) != expected_count):
            raise SensT5Error(f"NONPROGRAM_MANIFEST_UNTRUSTED layer=encode {name}")
        for entry in record["entries"]:
            if not isinstance(entry, dict) or entry.get("path") != relative:
                continue
            scoped = (
                (cohort == "domain-table" and bool(re.fullmatch(r"lib/domains/d[1-9]\.lisp", relative)))
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


def zig_mint_verified_t5(projection: str, reference: bytes, binary: Path, bridge):
    """Keep SENS word identities upstream; Zig alone mints physical T5 bytes.

    The Python bytes are a parity witness, NEVER the published carrier. This
    receipt certifies physical byte integrity only, not SENS semantics.
    """
    expected = hashlib.sha256(reference).hexdigest()
    physical = bridge.carry_t5(
        binary, projection, trusted_source_sha256=expected,
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
    receipt = bridge.verify_t5(binary, physical, trusted_source_sha256=expected)
    if (receipt.get("physical_sha256") != expected or
            receipt.get("source_pin_status") != "MATCHED_CALLER_SUPPLIED_SHA256" or
            not receipt.get("zig_binary_sha256")):
        raise SensT5Error("ZIG_CARRY_UNATTESTED_RECEIPT layer=transport")
    return physical, receipt


def migrate_file(source: str,resolver,text7):
    stripped=strip_comments(source)
    tokens=tokenize(stripped)
    forms=Parser(tokens).parse_program()
    resolver.set_global_bindings(collect_global_bindings(forms, resolver), text7)
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
    ap.add_argument("--foundation", type=Path, default=REPO_ROOT / "knowledge/d1-d9-foundation.json")
    ap.add_argument("--domain-surfaces", type=Path, default=REPO_ROOT / "crates/sens/src/domain_surface_registry_generated.rs")
    ap.add_argument("--semantic-generated", type=Path, default=REPO_ROOT / "crates/sens/src/semantic_registry_generated.rs")
    ap.add_argument("--semantic-registry", type=Path, default=REPO_ROOT / "crates/sens/src/semantic_registry.rs")
    ap.add_argument("--necessary-forms", type=Path, default=REPO_ROOT / "crates/sens/src/eval/necessary_forms_generated.rs")
    ap.add_argument("--text7", type=Path, default=REPO_ROOT / "knowledge/d7-keyboard-v2-ratified.json",
                    help="only current owner-ratified D7 keyboard/v2 JSON (128/128); historical .rs projections are rejected")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="переклад/перевірка без запису фізичних файлів")
    ap.add_argument("--unpaired-only", action="store_true",
                    help="мігрувати лише .lisp без однойменного наявного .sens")
    args = ap.parse_args()
    if args.report is None:
        args.report = args.out.with_name(args.out.name + ".report.json")

    data = load_foundation(args.foundation)
    # NOTE: knowledge/d8-*.json is SID8/Sens8, not a domain. It is never wired
    # as one; an eight-bit head is not executable.
    d9_residents = set(data["domains"].get("D9",{}).get("residents",{}).keys())
    my, upper, bridge_by_sid = build_three_pass_maps(
        data, args.domain_surfaces, args.semantic_generated,
        args.semantic_registry, args.necessary_forms
    )
    text7 = build_text7(data, args.text7)
    rows = []
    written = 0
    blocked = 0
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
    zig_temp = tempfile.TemporaryDirectory(prefix="sens-three-pass-zig-") if not args.dry_run else None
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
            if target.exists() or target.is_symlink():
                raise SensT5Error(f"target already exists; not overwriting {dest}")
            source = path.read_text(encoding="utf-8")
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(5)
            try:
                projection = migrate_file(source, resolver, text7)
            finally:
                signal.alarm(0)
            # Strict physical T5: any historic name, passthrough or unencoded
            # value still visible is a blocker, never a falsely binary file.
            words = parse_words(projection)
            reference = encode_projection(projection)
            if decode_bytes(reference) != words:
                raise SensT5Error("byte roundtrip changes source word identities")
            zig_receipt = None
            if zig_binary is not None:
                payload, zig_receipt = zig_mint_verified_t5(
                    projection, reference, zig_binary, zig_codec_bridge,
                )
                # The extensionless spaced-bit view is not an executable .sens.
                migration_publish_pair.publish_pair(
                    write_atomic_no_clobber, target, payload,
                    target.with_suffix(""), projection.encode("ascii"),
                )
            else:
                payload = reference  # dry-run only, NEVER published
            for key, value in resolver.counts.items():
                totals[key] += value
            status = "would-write" if args.dry_run else "written"
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
            blocked += 1
            row = {
                "path": str(rel), "output": str(dest),
                "status": "blocked", "reason": getattr(error, "message", str(error)),
                "passes": resolver.counts,
            }
            token = getattr(error, "tok", None)
            if token is not None:
                text = locals().get("source", "")
                line, column = line_col(text, token.offset)
                row.update({"token": token.text, "line": line, "column": column})
            rows.append(row)
        if (written + blocked) % 25 == 0:
            print(f"PROGRESS seen={written + blocked} written={written} blocked={blocked}",
                  flush=True)

    if zig_temp is not None:
        zig_temp.cleanup()
    report = {
        "schema": "sens-three-pass-t5-migration/v3",
        "naming_law": "SOURCE/name.lisp -> OUT/name.sens; the extensionless 0/1 view (name, spaced bits + one LF) is now REQUIRED alongside each .sens (#4694)",
        "file_format": {
            "suffix": ".sens", "physical": "binary-T5-five-trits-per-byte",
            "language": "D1..D9 exact-width 0/1 words",
            "transport_separator": "logical trit 2 strictly between words",
            "file_eof": "physical byte length; no terminal 22",
            "padding": "zero through four final trits 2",
            "ascii_text": False,
        },
        "passes": {
            "1": "historical 8-bit head -> admitted current successor",
            "2": "my-lisp / current admitted name -> exact current domain",
            "3": "Lisp-I/1.5 head -> proven current D3-D6",
        },
        "blocked_policy": "no unresolved textual source can become physical .sens",
        "only_unpaired": args.unpaired_only,
        "skipped_paired_paths": skipped_paired,
        "sid8_law": "SID8/Sens8 retired; no source-era, historical map or legacy coverage is accepted; an eight-bit head is executable only as a current named D3-D6 resident, else it fails closed",
        "source_policy": "input .lisp never rewritten; existing .sens never overwritten",
        "mode": "dry-run" if args.dry_run else "write-new-only-zig-minted",
        "semantic_admitted": False,
        "physical_producer": "PYTHON_REFERENCE_ONLY" if args.dry_run else "PINNED_ZIG_T5_CARRY",
        "summary": {
            "files_seen": len(paths),
            "files_skipped_paired": len(skipped_paired),
            "files_written": written if not args.dry_run else 0,
            "files_would_write": written if args.dry_run else 0,
            "files_blocked": blocked, "resolved_heads": totals,
        },
        "files": rows,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0 if written else 2


if __name__ == "__main__":
    raise SystemExit(main())
