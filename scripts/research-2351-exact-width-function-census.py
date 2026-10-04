#!/usr/bin/env python3
"""Current exact-width function-status census.

Consumes the v2 D1-D5 exact-width projection. Occupancy is already closed by
#3029; this research classifies derivability/independence only.

Only the four current D4 selectors are marked generated. D5 selector-looking
residents remain owner-admitted but derivationally UNKNOWN while #3209 is open.
"""

from __future__ import annotations
import argparse, csv, json
from pathlib import Path
from typing import Any

ROOTS = {"011", "100"}
STATUSES = ("root", "generated", "residue", "UNKNOWN")
CORPUS_SCHEMA = "exact-width-admitted-corpus/v2"
CENSUS_SCHEMA = "function-status-census/v2"

def load(path: Path) -> dict[str, Any]:
    data=json.loads(path.read_text(encoding="utf-8"))
    meta=data.get("meta",{})
    assert meta.get("schema")==CORPUS_SCHEMA
    assert meta.get("authority")=="projection-only"
    assert meta["status_counts"]["unallocated"] == 0
    return data

def cert(word: str) -> dict[str, Any]:
    root, path = word[:3], word[3:]
    assert root in ROOTS and path and set(path)<=set("01")
    assert root+path==word
    return {
        "root_basis":root,
        "law_path":path,
        "certificate_ref":"#2055/#3272",
        "search_grammar":"d3-selector-suffix-v2",
        "search_bound":len(path),
        "independence_status":"derived",
        "semantic_fact_refs":"#2055/#3202/#3272",
    }

def classify(data: dict[str, Any]):
    active=[r for r in data["rows"] if int(r["width"])>=3]
    rows=[]
    for r in active:
        if r["status"]=="generated":
            evidence=cert(r["word"])
            status="generated"
        else:
            evidence={
                "root_basis":None,
                "law_path":None,
                "certificate_ref":None,
                "search_grammar":None,
                "search_bound":None,
                "independence_status":"unknown",
                "semantic_fact_refs":None,
            }
            status="UNKNOWN"
        rows.append({
            "function_identity":r["word"],
            "width":int(r["width"]),
            "status":status,
            **evidence,
            "authority_ref":r["authority_ref"],
            "generator_ref":r["generator_ref"],
            "human_surface_optional":r["human_label_optional"],
        })

    counts={s:sum(r["status"]==s for r in rows) for s in STATUSES}
    assert len(rows)==56
    assert counts=={"root":0,"generated":4,"residue":0,"UNKNOWN":52}
    assert len({(r["width"],r["function_identity"]) for r in rows})==56

    for r in rows:
        if r["status"]=="generated":
            assert r["width"] == 4
            assert r["function_identity"]==r["root_basis"]+r["law_path"]
        else:
            assert r["certificate_ref"] is None

    summary={
        "schema":CENSUS_SCHEMA,
        "authority":"research-only",
        "input_schema":CORPUS_SCHEMA,
        "input_authority_refs":data["meta"]["authority_refs"],
        "active_function_rows":len(rows),
        "counts":counts,
        "generated_fraction_of_active_rows":counts["generated"]/len(rows),
        "registry_rows_potentially_derivable":counts["generated"],
        "unclassified_upper_bound":counts["UNKNOWN"],
        "proven_independent_root_count":0,
        "bounded_residue_count":0,
        "status_law":{
            "generated":"merged executable law + replayable certificate",
            "root":"requires independence evidence; placement is insufficient",
            "residue":"requires explicit bounded failure plus admitted necessity",
            "UNKNOWN":"default when derivation/independence evidence is insufficient",
        },
        "non_conclusions":[
            "generated fraction counts certified current D4 selector residents only",
            "D5 selector-looking residents are not classified generated while #3209 is unresolved",
            "UNKNOWN does not mean unoccupied or independent root",
            "no current D1-D8 coordinate is freed by this census",
        ],
    }
    return rows,summary

FIELDS=[
 "function_identity","width","status","root_basis","law_path","certificate_ref",
 "search_grammar","search_bound","independence_status","authority_ref",
 "generator_ref","semantic_fact_refs","human_surface_optional"
]

def render_json(rows,summary):
    return json.dumps({"summary":summary,"rows":rows},indent=2,ensure_ascii=False)+"\n"

def render_tsv(rows):
    import io
    out=io.StringIO()
    w=csv.DictWriter(out,fieldnames=FIELDS,delimiter="\t",lineterminator="\n")
    w.writeheader()
    for row in rows:
        w.writerow({k:("-" if row.get(k) is None else row.get(k)) for k in FIELDS})
    return out.getvalue()

def generate(corpus: Path):
    rows,summary=classify(load(corpus))
    return rows,summary,render_json(rows,summary),render_tsv(rows)

def write(corpus: Path,target: Path):
    _,summary,j,t=generate(corpus)
    target.mkdir(parents=True,exist_ok=True)
    (target/"function-status-census.json").write_text(j,encoding="utf-8")
    (target/"function-status-census.tsv").write_text(t,encoding="utf-8")
    (target/"function-status-census-summary.json").write_text(
        json.dumps(summary,indent=2)+"\n",encoding="utf-8")

def check(corpus: Path,target: Path):
    _,_,j,t=generate(corpus)
    expected={"function-status-census.json":j,"function-status-census.tsv":t}
    for name,content in expected.items():
        p=target/name
        actual = p.read_text(encoding="utf-8") if p.exists() else ""
        if actual != content:
            import difflib
            print("".join(difflib.unified_diff(
                actual.splitlines(True), content.splitlines(True),
                fromfile=str(p), tofile=f"generated/{name}", n=3,
            )))
            raise SystemExit(f"STALE-CENSUS={p}")

def main():
    ap=argparse.ArgumentParser()
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write",action="store_true")
    g.add_argument("--check",action="store_true")
    ap.add_argument("--corpus",type=Path,default=Path("knowledge/exact-width-admitted-corpus.json"))
    ap.add_argument("--target-dir",type=Path,default=Path("knowledge"))
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    if a.write: write(a.corpus,a.target_dir)
    else: check(a.corpus,a.target_dir)
    if a.out: write(a.corpus,a.out)
    _,summary,_,_=generate(a.corpus)
    print(json.dumps(summary,sort_keys=True))

if __name__=="__main__":
    main()
