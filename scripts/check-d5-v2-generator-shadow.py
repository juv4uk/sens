#!/usr/bin/env python3
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d5-v2-generator-shadow.json").read_text(encoding="utf-8"))
rows=d["coordinates"]
assert d["status"]=="research-shadow-not-authority"
assert len(rows)==32
assert len({r["coordinate"] for r in rows})==32
assert len({r["name"] for r in rows})==32
assert {r["coordinate"] for r in rows}=={f"{i:05b}" for i in range(32)}
assert "APPEND" not in {r["name"] for r in rows}
by={r["coordinate"]:r["name"] for r in rows}
assert by["10100"]=="REVERSE"
assert by["10101"]=="REVERSE-ONTO"
expected_selectors={
"01100":"CDAAR","01101":"CDADR","01110":"CDDAR","01111":"CDDDR",
"10000":"CAAAR","10001":"CAADR","10010":"CADAR","10011":"CADDR"}
for k,v in expected_selectors.items(): assert by[k]==v,(k,by[k],v)
assert d["metrics"]["lower_domain_duplicates"]==0
assert d["metrics"]["relation_classes"]=={
"SEMANTIC-GENERATOR":5,
"LOCAL-ALGEBRA":5,
"MULTI-DELTA-FAMILY":2,
"COORDINATE-HISTORICAL":4
}
lf=d["list_family"]
assert lf["bit0"]=="REVERSE" and lf["bit1"]=="REVERSE-ONTO"
print("D5-V2-GENERATOR-SHADOW: PASS")
print("occupancy=32/32 distinct=32 duplicate-append=0 generator-families=5")
