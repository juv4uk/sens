#!/usr/bin/env python3
"""Three-pass historical SENS source migrator.

Pass 1 — legacy exact-eight Sens8/Sid8 call heads:
    historical 8-bit identity -> proven current exact-domain successor.
Pass 2 — my-lisp/current admitted surfaces:
    registry/surface spelling -> current exact-domain identity.
Pass 3 — historical LISP 1–1.5 uppercase names:
    CAR/COND/LAMBDA/PLUS/... -> ratified D3-D6 resident.

Hard rules:
- () serializes as D3 EMPTY = 000.
- Non-empty list structure uses D2: 10 open, 00 separator, 11 dot, 01 close.
- Unknown executable heads PASS THROUGH unchanged after the three recognition passes.
- D2 words are reserved exclusively for structural control and never pass as data/call heads.
- Unknown D1 words may pass through unchanged as predicate/data evidence, but are never reclassified as D2.
- Comments disappear before migration.
- Unrecognized data/numbers/strings PASS THROUGH unchanged instead of being forced into Text7.
- Output is a PHYSICAL T5 binary file with the same stem and extension .sens.\n- Unknown/unmapped words FAIL CLOSED: never ship text remnants as .sens.\n- Source .lisp is retained; migration never overwrites an existing .sens.
"""
from __future__ import annotations

import argparse
import ast
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


def current_residents(data):
    labels={}
    for domain in ("D3","D4","D5","D6"):
        desc=data["domains"][domain]
        for bits,label in desc["residents"].items():
            if domain=="D3" and label=="EMPTY":
                continue
            labels[str(label).upper()]=(bits,domain)
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

def parse_legacy_successors(semantic_registry: Path, necessary_forms: Path):
    """Build old Sens8 byte -> proven exact-domain successor."""
    text=semantic_registry.read_text(encoding="utf-8")
    start=text.index("pub(crate) fn legacy_domain_identity_from_registry_byte")
    end=text.index("pub(crate) fn d5_binding_identity_for_definition",start)
    section=text[start:end]
    out={}
    for m in re.finditer(
        r'0b([01_]{8})\s*=>\s*Some\(d([34])\(0b([01_]+)\)\)',
        section
    ):
        byte=m.group(1).replace("_","")
        width=int(m.group(2))
        bits=m.group(3).replace("_","").zfill(width)
        out[byte]=(bits,f"D{width}","explicit-legacy-successor")

    nf=necessary_forms.read_text(encoding="utf-8")
    for m in re.finditer(
        r'semantic_id:\s*0b([01_]{8}),\s*mechanism:\s*NecessaryFormMechanism::(Lambda|Define)',
        nf
    ):
        byte=m.group(1).replace("_","")
        mech=m.group(2)
        bits="0010" if mech=="Lambda" else "0011"
        out[byte]=(bits,"D4","necessary-form-successor")
    return out

def parse_audited_legacy_successors(path: Path, foundation: dict):
    """Consume owner-audited SENS8 history; never treat old W8 as current D8.

    Only DIRECT / single-identity DERIVED rows can become old-era successors.
    Historical code coordinates never grant their own current placement.
    """
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("status") != "AUDIT-COMPLETE" or not isinstance(data.get("rows"),list):
        raise MigrationError("legacy successor coverage is missing audit authority")
    domains=foundation.get("domains",{})
    exact=re.compile(r"\b(D[1-9]):([01]{1,9})\b")
    allowed={"DIRECT-CURRENT-IDENTITY","CURRENT-PROJECTION-DERIVED"}
    result={}
    for row in data["rows"]:
        if not isinstance(row,dict):
            raise MigrationError("malformed owner-audited legacy successor")
        if row.get("classification") not in allowed:
            continue
        sid=row.get("legacy_code")
        if not isinstance(sid,str) or re.fullmatch(r"[01]{8}",sid) is None:
            raise MigrationError("audited historical code is not exactly eight bits")
        targets=set(exact.findall(row.get("current_target") or ""))
        # A compound D4+D5, a D6/D8 ambiguity, or no admitted identity
        # cannot be flattened to a guessed single callable.
        if len(targets) != 1:
            continue
        domain,bits=next(iter(targets))
        descriptor=domains.get(domain)
        if descriptor is None:
            continue
        if len(bits)!=int(descriptor["width"]):
            raise MigrationError(f"audited {domain}:{bits} has inconsistent exact width")
        if bits not in descriptor.get("residents",{}):
            raise MigrationError(f"audited {domain}:{bits} is not an owner-ratified resident")
        value=(bits,domain,"audited-sens8-current-coverage")
        if sid in result and result[sid][:2]!=value[:2]:
            raise MigrationError(f"conflicting audited historical successor {sid}")
        result[sid]=value
    return result

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
                          semantic_registry: Path, necessary_forms: Path,
                          historical_map: Path|None=None,
                          legacy_coverage: Path|None=None):
    residents=current_residents(data)
    current=parse_current_surface_rows(domain_surface_generated)
    proven_legacy=parse_legacy_successors(semantic_registry,necessary_forms)
    if legacy_coverage is not None:
        for byte,ident in parse_audited_legacy_successors(legacy_coverage,data).items():
            existing=proven_legacy.get(byte)
            if existing is not None and existing[:2]!=ident[:2]:
                raise MigrationError(f'conflicting successor for {byte}: {existing} vs {ident}')
            proven_legacy.setdefault(byte,ident)
    sem_rows=parse_semantic_rows(semantic_generated)

    # A historical byte may gain a successor through semantic-name
    # equivalence.  Crucially, this is independent of the old byte value:
    # the old registry spelling/historical name must resolve to one current
    # owner-ratified D3-D6 label.
    for byte,surfaces in sem_rows.items():
        candidates={current[name] for _,name in surfaces if name in current}
        for _namespace,name in surfaces:
            by_role=residents.get(normalize_role(name))
            if by_role is not None:
                candidates.add(by_role)
        if len(candidates)==1:
            ident=next(iter(candidates))
            proven_legacy.setdefault(byte,(ident[0],ident[1],"semantic-name-successor"))

    # Historical Core1 rows provide independent name evidence for early SIDs,
    # including rows that have no useful generated surface entry.
    historical_rows=[]
    if historical_map is not None:
        hist_text="\n".join(
            line.split(";",1)[0]
            for line in historical_map.read_text(encoding="utf-8").splitlines()
        )
        historical_rows=list(HISTORICAL_ROW_RE.finditer(hist_text))
        for m in historical_rows:
            sid,my_name,historical,*_rest=m.groups()
            candidates=set()
            for name in (my_name,historical):
                by_role=residents.get(normalize_role(name))
                if by_role is not None:
                    candidates.add(by_role)
            if len(candidates)==1:
                ident=next(iter(candidates))
                proven_legacy.setdefault(sid,(ident[0],ident[1],"historical-name-successor"))

    # Preserve knowledge that an old function existed even when it has no
    # current D3-D6 resident. None means LEGACY-UNMAPPED, never passthrough.
    legacy={byte:proven_legacy.get(byte) for byte in sorted(set(sem_rows)|set(proven_legacy))}

    my=dict(current)
    for byte,surfaces in sem_rows.items():
        candidates=set()
        ident=legacy.get(byte)
        if ident is not None:
            candidates.add(ident[:2])
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

    # Historical my-lisp spellings are also pass-2 evidence.
    for m in historical_rows:
        sid,my_name,historical,*_rest=m.groups()
        ident=legacy.get(sid)
        if my_name not in my:
            my[my_name]=ident[:2] if ident is not None else None

    upper={name:ident for name,ident in residents.items()}
    for m in historical_rows:
        sid,my_name,historical,*_rest=m.groups()
        if not any(ch.isalpha() for ch in historical):
            continue
        key=historical.upper()
        ident=legacy.get(sid)
        candidate=ident[:2] if ident is not None else None
        # Do not let a similarly-spelled modern resident erase evidence that
        # this specific historical function lacks a proven successor.
        upper.setdefault(key,candidate)

    return legacy,my,upper

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

def build_text7(data, projection_path: Path):
    text=projection_path.read_text(encoding="utf-8")
    slp=extract_projection(text,"SA_SLP1_ENCODE")
    uk=extract_projection(text,"UK_ENCODE")
    d7=data["domains"]["D7"]["residents"]
    labels={label:bits for bits,label in d7.items()}
    candidates={}
    for source in (slp,uk):
        for spelling,vals in source.items():
            candidates.setdefault(spelling,tuple(f"{v:07b}" for v in vals))
    for n in range(10):
        candidates[str(n)]=(labels[f"text.digit.{n}"],)

    # Longest-match projection, indexed by first source character. This keeps
    # multi-character cells (e.g. Ukrainian дж/дз) deterministic without
    # rescanning the full table for every character in large source trees.
    buckets={}
    for key,cells in candidates.items():
        buckets.setdefault(key[0],[]).append((key,cells))
    for rows in buckets.values():
        rows.sort(key=lambda x:(-len(x[0]),x[0]))
    return buckets

def text7_encode(spelling: str,candidates,tok: Tok):
    words=[]
    i=0
    while i<len(spelling):
        rows=candidates.get(spelling[i],())
        for key,cells in rows:
            if spelling.startswith(key,i):
                words.extend(cells); i+=len(key); break
        else:
            ch=spelling[i]
            raise MigrationError(f"Text7 cannot encode {ch!r} U+{ord(ch):04X}",tok)
    return words

class Resolver:
    def __init__(self,legacy,my,upper,source_era="auto",admitted_d8=None):
        if source_era not in ("auto","legacy","current"):
            raise ValueError(f"invalid source era {source_era!r}")
        if source_era=="current" and not admitted_d8:
            raise MigrationError("current D8 source requires an owner-ratified D8 foundation")
        self.legacy=legacy
        self.my=my
        self.upper=upper
        self.source_era=source_era
        self.admitted_d8=set(admitted_d8 or ())
        self.global_binding_words={}
        self.counts={"already-exact":0,"pass1-sens8":0,"pass2-my-lisp":0,
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

    def head(self,tok: Tok,count=True):
        t=tok.text
        # D2 is structural control only. A two-bit word in executable-head
        # position is ambiguous/corrupt source, never a callable identity.
        if len(t)==2 and set(t)<=set("01"):
            raise MigrationError(
                f"D2 word {t} is structural control only; it cannot be an executable head",
                tok,
            )
        # Exact current function words are already migrated.
        if 3<=len(t)<=6 and set(t)<=set("01"):
            if count: self.counts["already-exact"]+=1
            return [t],"already-exact"
        # The same eight visible bits can be historical SID8 or CURRENT D8.
        # Auto must BLOCK: without source-era provenance these are ambiguous.
        # Current D8 is left exact, never rewritten through an old SID.
        if len(t)==8 and set(t)<=set("01"):
            if self.source_era=="auto":
                raise MigrationError(
                    f"ambiguous W8 executable head {t}: choose --source-era legacy or current",tok
                )
            if self.source_era=="current":
                if t not in self.admitted_d8:
                    raise MigrationError(
                        f"unratified current D8 executable head {t}",tok
                    )
                if count: self.counts["already-exact"]+=1
                return [t],"already-exact"
            if t not in self.legacy:
                raise MigrationError(
                    f"legacy-unmapped SID8/Sens8 {t}: no historical registry row",
                    tok,
                )
            ident=self.legacy[t]
            if ident is None:
                raise MigrationError(
                    f"legacy-unmapped SID8/Sens8 {t}: no current D3-D6 resident",
                    tok,
                )
            if ident[1]=="D3" and ident[0]==D3_EMPTY:
                raise MigrationError(
                    f"legacy SID8/Sens8 {t} resolves to structural EMPTY, not a callable head",
                    tok,
                )
            if count: self.counts["pass1-sens8"]+=1
            return [ident[0]],"pass1-sens8"

        # Source-proven global DEFINE targets have lexical precedence over
        # builtin/current surface names. Their call heads reuse the same
        # D2/W7 frame as the target; spelling alone does not rebind them.
        if t in self.global_binding_words:
            if count: self.counts["pass4-text7-global"]+=1
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
            if count: self.counts["pass2-my-lisp"]+=1
            return [ident[0]],"pass2-my-lisp"

        # Pass 3: historical LISP I / Lisp 1.5 UPPERCASE names.
        if t==t.upper() and t in self.upper:
            ident=self.upper[t]
            if ident is None:
                raise MigrationError(
                    f"legacy-unmapped Lisp 1-1.5 function {t}: no current D3-D6 resident",
                    tok,
                )
            if count: self.counts["pass3-lisp15"]+=1
            return [ident[0]],"pass3-lisp15"
        # D1/D2 or any unresolved dynamic/user function stays exactly as written.
        if count: self.counts["passthrough-head"]+=1
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


def collect_global_bindings(forms):
    bindings=[]
    seen=set()
    for form in forms:
        if not isinstance(form,ListNode) or form.tail is not None or len(form.items)<2:
            continue
        head=form.items[0]
        if not isinstance(head,Atom) or head.tok.text not in {"00001001","0011","визначити","define","def"}:
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


def lambda_parameter_names(node: ListNode) -> tuple[str, ...]:
    if node.tail is not None:
        raise MigrationError(
            "dotted lambda parameter list has no admitted Text7 binding law",
            node.tok,
        )
    names=[]
    for param in node.items:
        if not isinstance(param,Atom):
            raise MigrationError(
                "lambda parameter must be a human identifier atom",
                node.tok,
            )
        names.append(param.tok.text)
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


def encode_atom_data(node: Atom,text7,lexical_env=()):
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
    return [t]


def encode_define_shorthand(node: ListNode,resolver,text7,lexical_env=()):
    """Normalize legacy (define (f x) body) to contextual DEFINE + LAMBDA."""
    if node.tail is not None or len(node.items) != 3:
        return None
    head, target, body = node.items
    if not (isinstance(head, Atom) and isinstance(target, ListNode)):
        return None
    # This is a pure lookahead: do not count the same executable head twice.
    head_words, _ = resolver.head(head.tok,count=False)
    if not head_words or head_words[0] != "0011":
        return None
    if target.tail is not None or not target.items or not isinstance(target.items[0], Atom):
        raise MigrationError(
            "DEFINE shorthand requires a proper (name parameters...) signature",
            target.tok,
        )
    name_tok = target.items[0].tok
    params = ListNode(target.items[1:], None, target.tok)
    lambda_names = lambda_parameter_names(params)
    words = [D2_OPEN, "0011", D2_SEP]
    words.extend(encode_text7_identifier(name_tok.text, text7, name_tok))
    words.append(D2_SEP)
    words.extend((D2_OPEN, "0010", D2_SEP))
    words.extend(encode_lambda_params(params, text7))
    words.append(D2_SEP)
    words.extend(
        encode(
            body,
            resolver,
            text7,
            quoted=False,
            lexical_env=tuple(lambda_names) + tuple(lexical_env),
        )
    )
    words.extend((D2_CLOSE, D2_CLOSE))
    return words


def encode_string(node: String,text7):
    return [node.tok.text]


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
        else:
            words.extend(
                encode(item,resolver,text7,quoted=True,lexical_env=())
            )
    if node.tail is not None:
        words.append(D2_DOT)
        words.extend(encode(node.tail,resolver,text7,quoted=True,lexical_env=()))
    words.append(D2_CLOSE)
    return words


def encode_let_bindings(bindings,resolver,text7,lexical_env=(),sequential=False):
    if bindings.tail is not None:
        raise MigrationError(
            "LET binding list must be a proper list",
            bindings.tok,
        )
    words=[D2_OPEN]
    bound=list(lexical_env)
    for index,binding in enumerate(bindings.items):
        if index:
            words.append(D2_SEP)
        if not isinstance(binding,ListNode) or binding.tail is not None:
            raise MigrationError(
                "LET binding must be a proper (name value) list",
                binding.tok if isinstance(binding,ListNode) else None,
            )
        if not binding.items or len(binding.items)>2:
            raise MigrationError(
                "LET binding must contain a name and at most one initializer",
                binding.tok,
            )
        name=binding.items[0]
        if not isinstance(name,Atom):
            raise MigrationError(
                "LET binding name must be an identifier atom",
                name.tok if isinstance(name,Atom) else binding.tok,
            )
        init_env=tuple(bound) if sequential else lexical_env
        words.extend(encode_text7_identifier(name.tok.text,text7,name.tok))
        words.append(D2_SEP)
        if len(binding.items)==2:
            words.extend(
                encode(
                    binding.items[1],
                    resolver,
                    text7,
                    quoted=False,
                    lexical_env=init_env,
                )
            )
        else:
            words.extend([D3_EMPTY])
        if name.tok.text not in bound:
            bound.append(name.tok.text)
    words.append(D2_CLOSE)
    return words,tuple(bound)


def encode(node,resolver,text7,quoted=False,lexical_env=()):
    if isinstance(node,ListNode):
        if not node.items and node.tail is None:
            return [D3_EMPTY]

        if not quoted:
            shorthand = encode_define_shorthand(node,resolver,text7,lexical_env)
            if shorthand is not None:
                return shorthand

        words=[D2_OPEN]
        head_bits=None
        lambda_names=()

        for idx,item in enumerate(node.items):
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
                head,_=resolver.head(item.tok)
                head_bits=head[0]
                words.extend(head)
                continue

            # Explicit QUOTE: everything below is data, with no live lexical scope.
            if not quoted and head_bits=="001":
                words.extend(
                    encode(item,resolver,text7,quoted=True,lexical_env=())
                )
                continue

            # D6 LET / LET*: binding lists are structural D2 containers;
            # only binder names and lexical references receive contextual Text7.
            # Parallel LET initializers see the outer scope. LET* initializers
            # additionally see bindings introduced earlier in the same list.
            if not quoted and head_bits in ("001000","001001") and idx==1:
                if not isinstance(item,ListNode):
                    raise MigrationError(
                        "LET binding list must be a proper list",
                        item.tok if isinstance(item,Atom) else None,
                    )
                let_sequential=head_bits=="001001"
                binding_words,let_names=encode_let_bindings(
                    item,
                    resolver,
                    text7,
                    lexical_env=lexical_env,
                    sequential=let_sequential,
                )
                words.extend(binding_words)
                lambda_names=let_names
                continue

            if not quoted and head_bits in ("001000","001001") and idx>=2:
                words.extend(
                    encode(
                        item,
                        resolver,
                        text7,
                        quoted=False,
                        lexical_env=lambda_names,
                    )
                )
                continue

            # D4 LAMBDA: parameter declarations are one contextual Text7 frame
            # per identifier; its body executes under the newly introduced scope.
            if not quoted and head_bits=="0010" and idx==1:
                if not isinstance(item,ListNode):
                    raise MigrationError(
                        "lambda parameters must be a proper list",
                        item.tok if isinstance(item,Atom) else None,
                    )
                lambda_names=lambda_parameter_names(item)
                words.extend(encode_lambda_params(item,text7))
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

            # D4 DEFINE: the binding target gets the same contextual Text7 frame
            # used by global call heads. Shorthand signature remains data-shaped.
            if not quoted and head_bits=="0011" and idx==1:
                if isinstance(item,Atom):
                    words.extend(
                        encode_text7_identifier(item.tok.text,text7,item.tok)
                    )
                    continue
                if isinstance(item,ListNode):
                    words.extend(
                        encode(item,resolver,text7,quoted=True,lexical_env=())
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
        return encode_atom_data(node,text7,lexical_env=() if quoted else lexical_env)
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


def migrate_file(source: str,resolver,text7):
    stripped=strip_comments(source)
    tokens=tokenize(stripped)
    forms=Parser(tokens).parse_program()
    resolver.set_global_bindings(collect_global_bindings(forms), text7)
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
    ap.add_argument("--historical-map", type=Path, default=REPO_ROOT / "contracts/core1-historical-sid-map.lisp")
    ap.add_argument("--legacy-coverage", type=Path, default=REPO_ROOT / "knowledge/sens8-current-coverage-v1.json")
    ap.add_argument("--text7", type=Path, default=REPO_ROOT / "crates/sens/src/text7_projection_generated.rs")
    ap.add_argument("--report", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="переклад/перевірка без запису фізичних файлів")
    ap.add_argument("--source-era", choices=("auto","legacy","current"), default="auto",
                    help="auto блокує W8; legacy = сумісний старий SID8 лише з provenance; current = ратифікований D8")
    ap.add_argument("--unpaired-only", action="store_true",
                    help="мігрувати лише .lisp без однойменного наявного .sens")
    args = ap.parse_args()
    if args.report is None:
        args.report = args.out.with_name(args.out.name + ".report.json")

    data = load_foundation(args.foundation)
    if args.source_era=="current" and "D8" not in data.get("current_domains",()):
        ap.error("--source-era=current requires a foundation ratifying D8")
    admitted_d8 = data["domains"].get("D8",{}).get("residents",{})
    legacy, my, upper = build_three_pass_maps(
        data, args.domain_surfaces, args.semantic_generated,
        args.semantic_registry, args.necessary_forms, args.historical_map,
        args.legacy_coverage
    )
    text7 = build_text7(data, args.text7)
    rows = []
    written = 0
    blocked = 0
    totals = {"already-exact": 0, "pass1-sens8": 0,
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
    seen_destinations = set()
    for path in paths:
        rel = path.resolve().relative_to(base_root)
        dest = sens_destination(rel)
        target = args.out / dest
        resolver = Resolver(legacy, my, upper, args.source_era, admitted_d8)
        try:
            if dest in seen_destinations:
                raise SensT5Error(f"duplicate destination {dest}")
            seen_destinations.add(dest)
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
            payload = encode_projection(projection)
            if decode_bytes(payload) != words:
                raise SensT5Error("byte roundtrip changes source word identities")
            if not args.dry_run:
                write_atomic_no_clobber(target, payload)
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
                "passes": resolver.counts,
            }
            rows.append(row)
            written += 1
        except (MigrationError, SensT5Error, UnicodeError, OSError) as error:
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

    report = {
        "schema": "sens-three-pass-t5-migration/v3",
        "naming_law": "SOURCE/name.lisp -> OUT/name.sens; extensionless outputs are forbidden",
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
            "4": "source-proven global/lexical Text7 binding frame",
        },
        "blocked_policy": "no unresolved textual source can become physical .sens",
        "source_era": args.source_era,
        "only_unpaired": args.unpaired_only,
        "skipped_paired_paths": skipped_paired,
        "source_era_law": "auto blocks ambiguous W8 heads; legacy maps SID8; current preserves ratified D8",
        "source_policy": "input .lisp never rewritten; existing .sens never overwritten",
        "mode": "dry-run" if args.dry_run else "write-new-only",
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