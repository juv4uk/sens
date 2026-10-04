#!/usr/bin/env python3
"""#3170: inventory 3-field COND clauses without rewriting semantics."""
from __future__ import annotations
import argparse, json, pathlib, subprocess
from dataclasses import dataclass

COND_HEADS={"00000111","011","cond","за-умовою","anukrama","?:"}
PREDICATE_HEADS={"00000010","00000011","010","111","atom","eq","atom?","eq?","тотожне?",".?","=?"}
POLARITY={"t","nil","true","false","1","0","#t","#f"}

@dataclass(frozen=True)
class Atom:
    text:str
    line:int

@dataclass(frozen=True)
class Form:
    items:tuple
    line:int

def decode_tracked_paths(root, data):
    return [root/pathlib.Path(x.decode("utf-8")) for x in data.split(b"\0") if x]

def tracked(root):
    p=subprocess.run(
        ["git","-c","core.quotepath=false","ls-files","-z","--","*.lisp"],
        cwd=root,check=True,capture_output=True
    )
    return decode_tracked_paths(root, p.stdout)

def tokens(text):
    out=[]; i=0; line=1
    while i<len(text):
        c=text[i]
        if c in " \t\r": i+=1; continue
        if c=="\n": line+=1; i+=1; continue
        if c==";":
            while i<len(text) and text[i]!="\n": i+=1
            continue
        if c in "()'": out.append((c,line)); i+=1; continue
        if c=='"':
            start=line; buf=['"']; i+=1; esc=False
            while i<len(text):
                ch=text[i]; buf.append(ch); i+=1
                if ch=="\n": line+=1
                if esc: esc=False
                elif ch=="\\": esc=True
                elif ch=='"': break
            out.append(("".join(buf),start)); continue
        start=line; j=i
        while j<len(text) and text[j] not in "()'\"; \t\r\n": j+=1
        out.append((text[i:j],start)); i=j
    return out

def parse(ts):
    pos=0
    def one():
        nonlocal pos
        if pos>=len(ts): raise ValueError("unexpected EOF")
        tok,line=ts[pos]; pos+=1
        if tok=="(":
            xs=[]
            while True:
                if pos>=len(ts): raise ValueError(f"unterminated list from line {line}")
                if ts[pos][0]==")": pos+=1; return Form(tuple(xs),line)
                xs.append(one())
        if tok==")": raise ValueError(f"unexpected close at line {line}")
        if tok=="'": return Form((Atom("quote",line),one()),line)
        return Atom(tok,line)
    out=[]
    while pos<len(ts): out.append(one())
    return out

def atom(x): return x.text if isinstance(x,Atom) else None
def head(x): return atom(x.items[0]) if isinstance(x,Form) and x.items else None

def walk(x):
    if isinstance(x,Form):
        yield x
        for child in x.items: yield from walk(child)

def show(x,limit=120):
    s=x.text if isinstance(x,Atom) else "("+" ".join(show(y,limit) for y in x.items)+")"
    return s if len(s)<=limit else s[:limit-3]+"..."

def empty(x): return isinstance(x,Form) and not x.items
def singleton(x): return atom(x.items[0]) if isinstance(x,Form) and len(x.items)==1 else None

def source_role(rel):
    if rel.startswith("benchmarks/") and "/results/" in rel: return "benchmark-provenance"
    if rel.startswith("benchmarks/"): return "benchmark-source"
    if rel.startswith(("evidence/","docs/archive/","docs/research/","experiments/","external/","prototype/")):
        return "research-provenance"
    if rel.startswith("racket/"): return "external-runtime"
    if rel.startswith("lib/generated/") or "/generated/" in rel: return "generated"
    if rel.endswith("-experiment.lisp") or "/experiment" in rel: return "research-provenance"
    if rel=="mylisp-cml-export.lisp": return "generated-export"
    if rel.startswith("tests/") or (rel.startswith("crates/") and "/tests/" in rel): return "test-witness"
    if rel.startswith("contracts/") or rel=="language-contract.lisp" or "contract" in pathlib.PurePosixPath(rel).name:
        return "contract-data"
    if rel.startswith("knowledge/"): return "knowledge-data"
    if rel.startswith("lib/"): return "active-library"
    if rel.startswith("scripts/"): return "active-tooling"
    if rel.startswith("examples/"): return "example"
    return "repository-data"

def migration_active(rel):
    return source_role(rel) in {"active-library","active-tooling"}

def state(rel):
    role=source_role(rel)
    if role in {"research-provenance","benchmark-provenance","generated-export"}: return "historical-provenance"
    if role=="generated": return "generated"
    if migration_active(rel): return "active"
    return "support"

def batch(rel):
    role=source_role(rel)
    if role=="test-witness": return "T-test-witness"
    if role in {"research-provenance","benchmark-provenance","generated-export"}: return "P-provenance"
    if role in {"benchmark-source","contract-data","knowledge-data","external-runtime","example","repository-data","generated"}:
        return "S-support"
    if rel in {"lib/core.lisp","lib/core4.lisp","lib/macro.lisp"}: return "A-core-bootstrap"
    if rel=="lib/meta-eval.lisp": return "D-meta-evaluator"
    if rel.startswith("lib/bridge/") or rel=="lib/life-1-scheduler.lisp": return "C-life-bridges"
    low=rel.lower()
    if rel=="lib/time.lisp" or any(k in low for k in ("utf","tcp","filesystem","/fs","protocol")): return "B-protocol-time"
    return "E-remaining"

def owner_lane(rel):
    b=batch(rel)
    if b=="A-core-bootstrap": return "blocked-overlap:#3130/#3146"
    if b=="D-meta-evaluator": return "exclusive:#3167"
    if b=="B-protocol-time": return "unclaimed:#3170-B"
    if b=="C-life-bridges": return "unclaimed:#3170-C"
    if b=="E-remaining": return "unclaimed:#3170-E-split-before-coding"
    if b=="T-test-witness": return "test-authority:#1708-review"
    return "not-active-migration"

def classify(test,expected,src_state):
    if src_state=="historical-provenance": return "historical-experiment","high","provenance-only path"
    th=(head(test) or "").lower(); ea=(atom(expected) or "").lower(); es=(singleton(expected) or "").lower()
    if th in PREDICATE_HEADS and (empty(expected) or es in {"0","1"}):
        return "structural-state","medium","predicate query with structural ()/(0)/(1)"
    if th in PREDICATE_HEADS and ea in POLARITY:
        return "predicate-polarity","medium","known predicate with polarity-like expected field"
    if ea in POLARITY: return "predicate-polarity","low","polarity-like expected field; producer unproven"
    if empty(expected) or es in {"0","1"}: return "structural-state","low","structural expected field; producer needs review"
    if show(expected) not in {"","()"}: return "ordinary-data-equality","low","non-polarity expected data; verify result-matching intent"
    return "unknown","none","no safe mechanical classification"

def scan_file(root,path):
    rel=path.relative_to(root).as_posix()
    try: forms=parse(tokens(path.read_text(encoding="utf-8",errors="replace")))
    except ValueError as e:
        return [{"kind":"parse-error","file":rel,"error":str(e),"batch":batch(rel),"source_state":state(rel),
            "source_role":source_role(rel),"migration_active":migration_active(rel),"owner_lane":owner_lane(rel)}]
    rows=[]
    for top in forms:
        for node in walk(top):
            h=head(node)
            if not h or h.lower() not in COND_HEADS: continue
            for idx,clause in enumerate(node.items[1:],1):
                if not isinstance(clause,Form) or len(clause.items)!=3: continue
                test,expected,expr=clause.items
                cls,conf,reason=classify(test,expected,state(rel))
                rows.append({"file":rel,"cond_line":node.line,"clause_line":clause.line,"clause_index":idx,
                    "cond_head":h,"batch":batch(rel),"source_state":state(rel),"source_role":source_role(rel),
                    "migration_active":migration_active(rel),"owner_lane":owner_lane(rel),"candidate_class":cls,
                    "confidence":conf,"reason":reason,"test":show(test),"expected":show(expected),"expression":show(expr)})
    return rows

def count(rows,key):
    out={}
    for r in rows:
        if r.get("kind")=="parse-error": continue
        v=str(r[key]); out[v]=out.get(v,0)+1
    return dict(sorted(out.items()))

def top_files(rows,limit=30):
    totals={}
    for r in rows:
        if r.get("kind")=="parse-error": continue
        totals[r["file"]]=totals.get(r["file"],0)+1
    return [{"file":k,"sites":v} for k,v in sorted(totals.items(),key=lambda kv:(-kv[1],kv[0]))[:limit]]

def markdown(meta):
    rows=[r for r in meta["rows"] if r.get("kind")!="parse-error"]; errs=[r for r in meta["rows"] if r.get("kind")=="parse-error"]
    lines=["# Three-part COND migration inventory (#3170)","",
        "Generated mechanically. Candidate classes are hints, not semantic authority.",
        "Ambiguous rows stay blocked until their producer/result law is identified.","",
        f"- tracked Lisp files scanned: {meta['tracked_lisp_files']}",
        f"- three-field clauses found (all roles): {len(rows)}",
        f"- migration-active clauses: {meta['summary']['active_site_count']}",
        f"- parse errors (all roles): {len(errs)}",
        f"- migration-active parse errors: {meta['summary']['active_parse_error_count']}",
        "","## Active candidate classes",""]
    for k,v in meta["summary"]["active_by_candidate_class"].items(): lines.append(f"- {k}: {v}")
    lines+=["","## Source roles",""]
    for k,v in meta["summary"]["by_source_role"].items(): lines.append(f"- {k}: {v}")
    lines+=["","## Ownership batches",""]
    for k,v in meta["summary"]["by_batch"].items(): lines.append(f"- {k}: {v}")
    lines+=["","## Candidate classes (all roles)",""]
    for k,v in meta["summary"]["by_candidate_class"].items(): lines.append(f"- {k}: {v}")
    lines+=["","## Top migration-active files",""]
    for row in meta["summary"]["top_active_files"]: lines.append(f"- {row['file']}: {row['sites']}")
    lines+=["","## Sites","","| file:line | role | active? | batch | owner | candidate | conf | head | test | expected |",
        "|---|---|---|---|---|---|---|---|---|---|"]
    esc=lambda s:str(s).replace("|","\\|").replace("\n"," ")
    for r in rows:
        lines.append(f"| {r['file']}:{r['clause_line']} | {r['source_role']} | {str(r['migration_active']).lower()} | {r['batch']} | {r['owner_lane']} | {r['candidate_class']} | {r['confidence']} | {esc(r['cond_head'])} | {esc(r['test'])} | {esc(r['expected'])} |")
    if errs:
        lines+=["","## Parse errors",""]
        for r in errs: lines.append(f"- {r['file']} [{r['source_role']}; active={str(r['migration_active']).lower()}]: {r['error']}")
    lines+=["","## Migration rule","","- Never delete the middle field blindly.",
        "- predicate-polarity still requires an exact D1/EMPTY producer.",
        "- structural-state must be rewritten from the current producer law.",
        "- ordinary-data-equality needs an explicit D1-producing predicate before COND.",
        "- historical-experiment is provenance, not an active migration target.","- unknown stays blocked.",""]
    return "\n".join(lines)

def self_test():
    sample="(00000111 ((00000011 a b) 1 yes) ((00000010 x) () empty) ((classify x) foo data))"
    forms=parse(tokens(sample)); nodes=[n for top in forms for n in walk(top) if (head(n) or "").lower() in COND_HEADS]
    assert len(nodes)==1
    clauses=[x for x in nodes[0].items[1:] if isinstance(x,Form) and len(x.items)==3]
    got=[classify(c.items[0],c.items[1],"active")[0] for c in clauses]
    assert got==["predicate-polarity","structural-state","ordinary-data-equality"]
    assert parse(tokens("(cond ((eq 'x 'x) t 'ok))"))
    paths=decode_tracked_paths(pathlib.Path("."), "lib/core.lisp\0lib/українська.lisp\0".encode("utf-8"))
    assert [p.as_posix() for p in paths]==["lib/core.lisp","lib/українська.lisp"]
    assert migration_active("lib/core.lisp")
    assert migration_active("scripts/generate-function-table.lisp")
    assert not migration_active("benchmarks/sens-surface/results/old/program.lisp")
    assert source_role("tests/fixtures/conformance.lisp")=="test-witness"
    assert source_role("knowledge/agent-discoveries.lisp")=="knowledge-data"
    print("cond-three-part-inventory self-test: PASS")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",type=pathlib.Path,default=pathlib.Path("."))
    ap.add_argument("--json-out",type=pathlib.Path); ap.add_argument("--report-out",type=pathlib.Path); ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test: self_test(); return 0
    root=args.root.resolve(); files=tracked(root); rows=[]
    for path in files: rows.extend(scan_file(root,path))
    rows.sort(key=lambda r:(r["file"],r.get("clause_line",0),r.get("clause_index",0)))
    active=[r for r in rows if r.get("kind")!="parse-error" and r.get("migration_active")]
    meta={"schema":"cond-three-part-inventory/2","issue":3170,"tracked_lisp_files":len(files),
        "summary":{"site_count":sum(r.get("kind")!="parse-error" for r in rows),
            "active_site_count":sum(r.get("kind")!="parse-error" and r.get("migration_active") for r in rows),
            "parse_error_count":sum(r.get("kind")=="parse-error" for r in rows),
            "active_parse_error_count":sum(r.get("kind")=="parse-error" and r.get("migration_active") for r in rows),
            "by_batch":count(rows,"batch"),"active_by_batch":count(active,"batch"),
            "by_source_state":count(rows,"source_state"),"by_source_role":count(rows,"source_role"),
            "by_candidate_class":count(rows,"candidate_class"),"active_by_candidate_class":count(active,"candidate_class"),
            "by_confidence":count(rows,"confidence"),"top_active_files":top_files(active)},"rows":rows}
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    report=markdown(meta)
    if args.report_out:
        args.report_out.parent.mkdir(parents=True,exist_ok=True); args.report_out.write_text(report+"\n",encoding="utf-8")
    else: print(report)
    return 0

if __name__=="__main__": raise SystemExit(main())
