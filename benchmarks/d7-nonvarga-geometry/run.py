#!/usr/bin/env python3
"""#3122 — D7 non-varga semantic factors before geometry.

Consumes:
- stable D7 resident IDs;
- structured source semantic descriptors from knowledge/d7-full-map.json.

CURRENT bits are scored only after the relation graph is built.
"""

from __future__ import annotations
import argparse, csv, json, random
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
STABLE=ROOT/"knowledge/d3-d8-stable-residents.json"
FULL=ROOT/"knowledge/d7-full-map.json"
VARGA_PLACES={"K","C","T-retroflex","T-dental","P"}
SEED=3122
SAMPLES=4096

def ham(a,b): return sum(x!=y for x,y in zip(a,b))

def parse(name):
    p=name.split(".")
    if p[:2]==["non-varga","uk-ext"]:
        return {"family":"uk-ext","place":None,"manner":None,"local_role":".".join(p[2:])}
    if len(p)<3 or p[0]!="non-varga":
        raise ValueError(name)
    place=p[1]
    return {
        "family":"shared-varga-place" if place in VARGA_PLACES else "local-place",
        "place":place,
        "manner":".".join(p[2:]),
        "local_role":None,
    }

def pairs_same(rows,key):
    out=[]
    for a,b in combinations(rows,2):
        va,vb=a[key],b[key]
        if va is not None and va==vb: out.append((a["id"],b["id"]))
    return out

def score(mapping,pairs):
    return sum(ham(mapping[a],mapping[b])==1 for a,b in pairs)

def pct(xs,p):
    s=sorted(xs); return s[min(len(s)-1,int((len(s)-1)*p))]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True); a=ap.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    stable=json.loads(STABLE.read_text())
    full=json.loads(FULL.read_text())
    stable_by_bits={r["current_bits"]:r for r in stable["rows"] if r["current_domain"]=="D7"}
    src=[r for r in full["coordinates"] if r["class"]=="non-varga" and r["residency"]=="assigned"]
    varga_src=[r for r in full["coordinates"] if r["class"]=="varga" and r["residency"]=="assigned"]
    rows=[]
    for cell in src:
        s=stable_by_bits[cell["coordinate"]]
        f=parse(cell["name"])
        rows.append({"id":s["stable_resident_id"],"bits":cell["coordinate"],"name":cell["name"],**f})
    assert len(rows)==18
    shared=[r for r in rows if r["family"]=="shared-varga-place"]
    glottal=[r for r in rows if r["family"]=="local-place"]
    uk=[r for r in rows if r["family"]=="uk-ext"]
    assert (len(shared),len(glottal),len(uk))==(11,2,5)

    varga=[]
    for cell in varga_src:
        parts=cell["name"].split(".")
        s=stable_by_bits[cell["coordinate"]]
        varga.append({"id":s["stable_resident_id"],"bits":cell["coordinate"],"place":parts[1]})
    assert len(varga)==25

    same_place=pairs_same(rows,"place")
    same_manner=pairs_same(rows,"manner")
    cross=[]
    for n in shared:
        for v in varga:
            if n["place"]==v["place"]: cross.append((n["id"],v["id"]))
    assert len(cross)==55

    mapping={r["id"]:r["bits"] for r in rows+varga}
    current={"same_place_h1":score(mapping,same_place),"same_manner_h1":score(mapping,same_manner),"cross_varga_place_h1":score(mapping,cross)}

    rng=random.Random(SEED)
    coords=[r["bits"] for r in rows]
    null={k:[] for k in current}
    for _ in range(SAMPLES):
        perm=coords[:]; rng.shuffle(perm)
        m={**{r["id"]:r["bits"] for r in varga}, **{r["id"]:b for r,b in zip(rows,perm)}}
        null["same_place_h1"].append(score(m,same_place))
        null["same_manner_h1"].append(score(m,same_manner))
        null["cross_varga_place_h1"].append(score(m,cross))

    null_summary={}
    for k,xs in null.items():
        obs=current[k]
        null_summary[k]={
            "observed":obs,"mean":sum(xs)/len(xs),"p50":pct(xs,.5),"p95":pct(xs,.95),
            "exceedance_rate":sum(x>=obs for x in xs)/len(xs)
        }

    # False collapse: uk-ext rows have no source-backed varga place.
    assert all(r["place"] is None for r in uk)
    # Varga manner vocabulary does not equal the non-varga manner vocabulary.
    varga_manners={r["name"].split(".")[2] for r in [{"name":c["name"]} for c in varga_src]}
    nv_manners={r["manner"] for r in rows if r["manner"]}
    assert varga_manners.isdisjoint(nv_manners)

    with (a.out/"nonvarga-residents.tsv").open("w",newline="",encoding="utf-8") as fh:
        fields=["id","name","family","place","manner","local_role","bits"]
        w=csv.DictWriter(fh,fieldnames=fields,delimiter="\t",lineterminator="\n"); w.writeheader(); w.writerows(rows)

    artifact={
      "schema":"d7-nonvarga-factors/s1-v1","authority":"research-only",
      "scope":{"assigned_nonvarga":18,"shared_varga_place":11,"local_glottal_place":2,"uk_extension_local":5},
      "relations":{"same_place_pairs":len(same_place),"same_manner_pairs":len(same_manner),"cross_varga_same_place_pairs":len(cross)},
      "current_score":current,"matched_null":null_summary,
      "semantic_result":{
        "varga_place_factor_reusable_for_rows":11,
        "nonvarga_manner_is_local":True,
        "glottal_is_local_place_extension":True,
        "uk_ext_requires_local_laws":True
      },
      "false_controls":{
        "uk_ext_forced_into_varga_place":False,
        "varga_and_nonvarga_manner_vocabularies_disjoint":True
      },
      "geometry_status":"NOT-FORCED-BY-SEMANTIC-FACTOR-ALONE",
      "non_conclusions":[
        "semantic place reuse does not force absolute D7 bits",
        "matched-null score may support or weaken CURRENT geometry but cannot create a phonological relation",
        "uk-ext rows are not assigned a place merely to complete a product",
        "no production D7 remap is performed"
      ]
    }
    (a.out/"result.json").write_text(json.dumps(artifact,indent=2,sort_keys=True)+"\n")
    report=[
      "# D7 non-varga factors — #3122","",
      f"Assigned non-varga residents: **18**",
      f"- shared varga place vocabulary: **11**",
      f"- local glottal place: **2**",
      f"- explicit uk-ext/local roles: **5**","",
      f"Same-place relation pairs: **{len(same_place)}**",
      f"Same-manner relation pairs: **{len(same_manner)}**",
      f"Cross-family same-place relations to varga: **{len(cross)}**","",
      "Semantic result:",
      "- place factor is reusable only where the source descriptor names the same varga place;",
      "- non-varga manner vocabulary is local, not the varga stop/nasal manner axis;",
      "- glottal is a local place extension;",
      "- uk-ext remains local residue/extension rather than forced varga geometry.","",
      "Matched-null geometry check (4096 deterministic within-slice permutations):",
      f"- same-place Hamming-1: observed={null_summary['same_place_h1']['observed']}, null mean={null_summary['same_place_h1']['mean']:.3f}, p95={null_summary['same_place_h1']['p95']}, exceedance={null_summary['same_place_h1']['exceedance_rate']:.4f};",
      f"- same-manner Hamming-1: observed={null_summary['same_manner_h1']['observed']}, null mean={null_summary['same_manner_h1']['mean']:.3f}, p95={null_summary['same_manner_h1']['p95']}, exceedance={null_summary['same_manner_h1']['exceedance_rate']:.4f};",
      f"- cross-varga same-place Hamming-1: observed={null_summary['cross_varga_place_h1']['observed']}, null mean={null_summary['cross_varga_place_h1']['mean']:.3f}, p95={null_summary['cross_varga_place_h1']['p95']}, exceedance={null_summary['cross_varga_place_h1']['exceedance_rate']:.4f};","",
      "Geometry status: **NOT-FORCED-BY-SEMANTIC-FACTOR-ALONE**.","",
      "CURRENT bits never define the features."
    ]
    (a.out/"report.md").write_text("\n".join(report)+"\n")
    print("\n".join(report))
if __name__=="__main__": main()
