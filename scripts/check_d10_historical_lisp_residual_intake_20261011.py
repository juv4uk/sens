#!/usr/bin/env python3
"""Independent fail-closed audit of the D10 historical Lisp residual intake."""
import hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = "knowledge/d10-historical-lisp-residual-intake-20261011.json"
def need(p, why):
    if not p: raise ValueError(why)
def read(path): return json.loads((ROOT/path).read_text(encoding="utf-8"))
def sha(path):
    data = (ROOT/path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
def main():
    reg = read(PATH)
    need(reg["schema"] == "sens-d10-old-lisp-residual-candidates/v1", "schema")
    need(reg["state"] == "RESEARCH-NOT-SELECTED-NOT-RATIFIED", "state")
    for pin in reg["source_pins"] + reg["baseline_pins"]:
        need(sha(pin["path"]) == pin["sha"], "pin " + pin["path"])
    base = [p["path"] for p in reg["baseline_pins"]]
    current = {r["semantic_name"].upper() for r in read(base[0])["rows"]}
    queue1 = {r["semantic_name"].upper() for r in read(base[1])["provisional_candidates"]}
    queue2 = {r["semantic_name"].upper() for r in read(base[2])["candidates"]}
    lower = {str(s).upper() for v in read(base[3])["domains"].values() for s in v["residents"].values()}
    counted = reg["accounting"]
    need((len(current), len(queue1), len(queue2)) == (715, 96, 80), "baseline")
    candidates = reg["candidates"]
    need(len(candidates) == counted["new_distinct_unselected"] == 80, "count")
    names = set()
    for c in candidates:
        name = c["semantic_name"]
        need(re.fullmatch(r"[A-Z][A-Z0-9?!/+=*._:-]*", name) is not None, "spelling")
        need(name not in current | queue1 | queue2 | lower | names, "duplicate " + name)
        names.add(name)
        need(c["status"] == "RESEARCH-UNSELECTED" and c["selected"] is False and
             c["coordinate"] is None and c["ratified"] is False and
             c["physical_t5_authorized"] is False, "illegal promotion " + name)
        need(bool(c["traces"]), "missing provenance")
        for t in c["traces"]:
            need(sha(t["path"]) == t["blob_sha"], "trace blob")
            row = read(t["path"])[t["collection"]][t["index"]]
            origin = row.get("historical_names") or [row.get("semantic_name") or row.get("historical_name")]
            need(name in [str(v).upper() for v in origin], "trace identity")
    need((counted["selected_delta"], counted["coordinates_delta"], counted["ratified_delta"]) == (0,0,0), "counts")
    print("D10-OLD-LISP-INTAKE: PASS", json.dumps({"unselected":len(names),"selected_unchanged":715}))
if __name__=="__main__":
    try: main()
    except (OSError, ValueError, KeyError, TypeError, IndexError) as e:
        raise SystemExit("D10-OLD-LISP-INTAKE: BLOCK " + str(e))
