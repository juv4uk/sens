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
- Unknown executable heads FAIL CLOSED; they are never silently emitted as D7 text.
- Comments disappear before migration.
- Ordinary spelling/data uses pinned Text7 cells.
- Decimal/rational numeric literals fail closed until the Number source framing law
  is admitted for the exact-width binary source.
- Output is extensionless and contains only 0/1 plus ASCII whitespace.
"""
from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
import json
from pathlib import Path
import re

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
        while i<n and (not source[i].isspace()) and source[i] not in "()'\"\`,": 
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
    legacy=parse_legacy_successors(semantic_registry,necessary_forms)
    sem_rows=parse_semantic_rows(semantic_generated)

    # A historical byte may also gain a proven successor through surface
    # equivalence: one of its registry spellings is a current exact-domain
    # spelling. This is not byte truncation.
    for byte,surfaces in sem_rows.items():
        candidates={current[name] for _,name in surfaces if name in current}
        if len(candidates)==1:
            ident=next(iter(candidates))
            legacy.setdefault(byte,(ident[0],ident[1],"surface-equivalence-successor"))

    my=dict(current)
    for byte,surfaces in sem_rows.items():
        candidates=set()
        if byte in legacy:
            candidates.add(legacy[byte][:2])
        for _,name in surfaces:
            if name in current:
                candidates.add(current[name])
        if len(candidates)==1:
            ident=next(iter(candidates))
            for namespace,name in surfaces:
                if name != name.upper() or namespace=="sym":
                    my.setdefault(name,ident)

    upper={name:ident for name,ident in residents.items()}
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
    return sorted(candidates.items(),key=lambda x:(-len(x[0]),x[0]))

def text7_encode(spelling: str,candidates,tok: Tok):
    words=[]
    i=0
    while i<len(spelling):
        for key,cells in candidates:
            if spelling.startswith(key,i):
                words.extend(cells); i+=len(key); break
        else:
            ch=spelling[i]
            raise MigrationError(f"Text7 cannot encode {ch!r} U+{ord(ch):04X}",tok)
    return words

class Resolver:
    def __init__(self,legacy,my,upper):
        self.legacy=legacy
        self.my=my
        self.upper=upper
        self.counts={"already-exact":0,"pass1-sens8":0,"pass2-my-lisp":0,"pass3-lisp15":0}
    def head(self,tok: Tok):
        t=tok.text
        if 3<=len(t)<=6 and set(t)<=set("01"):
            self.counts["already-exact"]+=1
            return [t],"already-exact"
        if len(t)==8 and set(t)<=set("01"):
            ident=self.legacy.get(t)
            if ident is None:
                raise MigrationError(f"pass1: legacy Sens8/Sid8 {t} has no proven exact-domain successor",tok)
            self.counts["pass1-sens8"]+=1
            return [ident[0]],"pass1-sens8"
        ident=self.my.get(t)
        if ident is not None:
            self.counts["pass2-my-lisp"]+=1
            return [ident[0]],"pass2-my-lisp"
        if t==t.upper() and t in self.upper:
            self.counts["pass3-lisp15"]+=1
            return [self.upper[t][0]],"pass3-lisp15"
        raise MigrationError(f"unknown executable head after 3 passes: {t!r}",tok)

def encode_atom_data(node: Atom,text7):
    t=node.tok.text
    if NUMERIC_RE.fullmatch(t):
        raise MigrationError(
            f"numeric literal {t!r} awaits admitted Number framing; refusing to encode it as Text7",
            node.tok,
        )
    if 1<=len(t)<=8 and set(t)<=set("01"):
        return [t]
    return text7_encode(t,text7,node.tok)

def encode_string(node: String,text7):
    return text7_encode(node.tok.text,text7,node.tok)

def encode_clause(node,resolver,text7):
    """COND clause is structural: the clause itself is not a function call.

    Nested list expressions inside it remain executable. Bare atoms at clause
    level (e.g. t) are data/control values, never function heads.
    """
    if not isinstance(node,ListNode):
        return encode(node,resolver,text7,quoted=False)
    if not node.items and node.tail is None:
        return [D3_EMPTY]
    words=[D2_OPEN]
    for idx,item in enumerate(node.items):
        if idx:
            words.append(D2_SEP)
        if isinstance(item,ListNode):
            words.extend(encode(item,resolver,text7,quoted=False))
        else:
            words.extend(encode(item,resolver,text7,quoted=True))
    if node.tail is not None:
        words.append(D2_DOT)
        words.extend(encode(node.tail,resolver,text7,quoted=True))
    words.append(D2_CLOSE)
    return words

def encode(node,resolver,text7,quoted=False):
    if isinstance(node,ListNode):
        if not node.items and node.tail is None:
            return [D3_EMPTY]

        words=[D2_OPEN]
        head_bits=None

        for idx,item in enumerate(node.items):
            if idx:
                words.append(D2_SEP)

            if idx==0 and not quoted and isinstance(item,Atom):
                head,_=resolver.head(item.tok)
                head_bits=head[0]
                words.extend(head)
                continue

            # Explicit QUOTE: every datum is data, never an executable head.
            if not quoted and head_bits=="001":
                words.extend(encode(item,resolver,text7,quoted=True))
                continue

            # LAMBDA: first argument is the parameter-list grammar.
            if not quoted and head_bits=="0010" and idx==1:
                words.extend(encode(item,resolver,text7,quoted=True))
                continue

            # DEFINE: a shorthand signature (define (f x) body) is data at the
            # signature level. A plain name is already encoded as atom data.
            if not quoted and head_bits=="0011" and idx==1 and isinstance(item,ListNode):
                words.extend(encode(item,resolver,text7,quoted=True))
                continue

            # COND: each clause is a grammar container, not a call itself.
            if not quoted and head_bits=="110":
                words.extend(encode_clause(item,resolver,text7))
                continue

            words.extend(encode(item,resolver,text7,quoted=quoted))

        if node.tail is not None:
            words.append(D2_DOT)
            words.extend(encode(node.tail,resolver,text7,quoted=True))
        words.append(D2_CLOSE)
        return words

    if isinstance(node,Quote):
        return [D2_OPEN,"001",D2_SEP,*encode(node.value,resolver,text7,quoted=True),D2_CLOSE]
    if isinstance(node,String):
        return encode_string(node,text7)
    if isinstance(node,Atom):
        return encode_atom_data(node,text7)
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

def extensionless(rel: Path):
    return rel.with_suffix("")

def migrate_file(source: str,resolver,text7):
    stripped=strip_comments(source)
    tokens=tokenize(stripped)
    forms=Parser(tokens).parse_program()
    all_words=[]
    for i,form in enumerate(forms):
        if i: all_words.append(D2_SEP)
        all_words.extend(encode(form,resolver,text7,quoted=False))
    text=" ".join(all_words)
    if text: text+="\n"
    if text and not re.fullmatch(r"[01\s]+",text):
        raise AssertionError("non-binary output")
    if any(not 1<=len(w)<=8 for w in text.split()):
        raise AssertionError("word width outside 1..8")
    return text

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--foundation",type=Path,required=True)
    ap.add_argument("--domain-surfaces",type=Path,required=True)
    ap.add_argument("--semantic-generated",type=Path,required=True)
    ap.add_argument("--semantic-registry",type=Path,required=True)
    ap.add_argument("--necessary-forms",type=Path,required=True)
    ap.add_argument("--text7",type=Path,required=True)
    ap.add_argument("--report",type=Path,required=True)
    args=ap.parse_args()

    data=load_foundation(args.foundation)
    legacy,my,upper=build_three_pass_maps(
        data,args.domain_surfaces,args.semantic_generated,args.semantic_registry,args.necessary_forms
    )
    text7=build_text7(data,args.text7)
    args.out.mkdir(parents=True,exist_ok=True)

    rows=[]
    written=0
    blocked=0
    totals={"already-exact":0,"pass1-sens8":0,"pass2-my-lisp":0,"pass3-lisp15":0}
    destinations={}

    root=args.root.resolve()
    for path in source_files(root):
        rel=path.resolve().relative_to(root)
        dest=extensionless(rel)
        if dest in destinations:
            rows.append({"path":str(rel),"status":"blocked","reason":f"extensionless collision with {destinations[dest]}"})
            blocked+=1
            continue
        resolver=Resolver(legacy,my,upper)
        source=path.read_text(encoding="utf-8")
        try:
            output=migrate_file(source,resolver,text7)
            if not output.strip():
                rows.append({"path":str(rel),"status":"empty","passes":resolver.counts})
                continue
            target=args.out/dest
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(output,encoding="ascii")
            destinations[dest]=str(rel)
            written+=1
            for k,v in resolver.counts.items(): totals[k]+=v
            rows.append({"path":str(rel),"output":str(dest),"status":"written","passes":resolver.counts})
        except MigrationError as e:
            blocked+=1
            row={"path":str(rel),"status":"blocked","reason":e.message,"passes":resolver.counts}
            if e.tok:
                line,col=line_col(source,e.tok.offset)
                row.update({"token":e.tok.text,"line":line,"column":col})
            rows.append(row)

    report={
        "schema":"sens-three-pass-migration/v1",
        "passes":{
            "1":"legacy Sens8/Sid8 -> proven current exact-domain successor",
            "2":"my-lisp/current admitted surface -> exact-domain identity",
            "3":"historical LISP 1-1.5 uppercase resident -> ratified D3-D6 identity",
        },
        "structure":{"empty":"000","open":"10","separator":"00","dot":"11","close":"01"},
        "output_naming":"source .lisp suffix removed; no new extension",
        "summary":{"files_written":written,"files_blocked":blocked,"resolved_heads":totals},
        "files":rows,
    }
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False))
    return 0 if written else 2

if __name__=="__main__":
    raise SystemExit(main())
