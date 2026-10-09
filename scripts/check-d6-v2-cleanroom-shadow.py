#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d6-v2-cleanroom-shadow.json").read_text(encoding="utf-8"))

assert d["status"]=="research-shadow-not-authority"
assert d["lower_authority"]["d5"].startswith("#3305")
assert d["metrics"]=={
    "capacity":64,
    "generated_selectors":16,
    "unknown_coordinates":48,
    "donor_candidates_unplaced":43,
    "mutation_donors_excluded":5,
    "lower_domain_duplicates":0,
}
coords=d["coordinates"]
assert len(coords)==64
assert len({r["coordinate"] for r in coords})==64
assert sum(r["status"]=="GENERATED" for r in coords)==16
assert sum(r["status"]=="UNKNOWN" for r in coords)==48
expected={
"011000":"CDAAAR","011001":"CDAADR","011010":"CDADAR","011011":"CDADDR",
"011100":"CDDAAR","011101":"CDDADR","011110":"CDDDAR","011111":"CDDDDR",
"100000":"CAAAAR","100001":"CAAADR","100010":"CAADAR","100011":"CAADDR",
"100100":"CADAAR","100101":"CADADR","100110":"CADDAR","100111":"CADDDR",
}
by={r["coordinate"]:r["name"] for r in coords}
for k,v in expected.items(): assert by[k]==v,(k,by[k],v)
excluded={r["name"] for r in d["excluded_mutation_donors"]}
assert excluded=={"RPLACA","RPLACD","SETF","NCONC","NREVERSE"}
print("D6-V2-CLEANROOM-SHADOW: PASS")
print("generated=16 unknown=48 donor-candidates=43 mutation-excluded=5 duplicates=0")
