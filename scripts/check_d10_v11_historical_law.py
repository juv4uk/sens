#!/usr/bin/env python3
"""D10 v11 research-only admission guard; no F2/F3, coordinates or ratification."""
import argparse
import csv
import hashlib
import io
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "knowledge/d10-historical-law-intake-v11-20261011.json"

def need(ok, reason):
    if not ok: raise ValueError("D10_V11_BLOCK:" + reason)

def sha(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def pinned(root, name, expected):
    file = (root / name).resolve()
    need(file.is_relative_to(root) and file.is_file(), "missing " + name)
    raw = file.read_bytes()
    need(sha(raw) == expected, "source drift " + name)
    return raw

def verify(v10, v11, manifest, catalog, foundation):
    need(v11["schema"] == "d10-v11-semantic-inventory/v1", "schema")
    need(v11["previous_inventory"]["git_blob"] == manifest["previous"]["git_blob"], "ancestor pin")
    need(len(v10["rows"]) == 799 and v11["rows"][:799] == v10["rows"], "append-only v10")
    need(len(v11["rows"]) == 823 and len(manifest["candidates"]) == 24, "batch count")
    need(v11["sources"][-1] == MANIFEST, "source chain")
    need(manifest["counts"] == {"prior_selected":799,"added_research_descriptions":24,
        "selected_after":823,"placed_after":719,"unplaced_after":104,"remaining":201,
        "ratified":0,"new_coordinates":0,"independent_F2_oracle_PASSES":0,
        "F3_semantic_proofs":0}, "manifest accounting")
    lower = {str(name).upper() for d in foundation["domains"].values()
             for name in d.get("residents",{}).values()}
    names = {row["semantic_name"].upper() for row in v10["rows"]}
    ids = {row["stable_id"] for row in v10["rows"]}
    source, by_name = {}, {}
    for item in csv.DictReader(io.StringIO(catalog.decode("utf-8")), delimiter="\t",strict=True):
        need(None not in item and all(x is not None for x in item.values()), "malformed index")
        key = item["candidate_id"]
        need(key not in source, "duplicate index id")
        source[key] = item
        by_name.setdefault(item["semantic_name"].upper(), []).append(item)
    need(len(source) == 1809, "index rows changed")
    columns = (
        ("semantic_law_variants","law_variants",None),
        ("donor_provenance_claims","donor_claims","donor_provenance_claims"),
        ("positive_witness_claims","positive_witness_claims","positive_witness_claims"),
        ("falsifier_claims","negative_witness_claims","negative_witness_claims"),
        ("source_records_sha_pinned","source_records_sha_pinned","source_records_sha_pinned"),
    )
    for row, proof in zip(v11["rows"][799:], manifest["candidates"]):
        name, ident = proof["name"], proof["id"]
        need((row["stable_id"],row["semantic_name"]) == (ident,name), "identity")
        need(name.upper() not in lower | names, "duplicate surface " + name)
        need(ident not in ids and ident.startswith("d10.name."), "reused ID")
        names.add(name.upper()); ids.add(ident)
        src = source.get(ident)
        need(src is not None and src["semantic_name"] == name and
             src["current_d10_selected"] == "NOT_SELECTED", "original source")
        alternative_ids = sorted(r["candidate_id"] for r in by_name[name.upper()]
                                 if r["candidate_id"] != ident and
                                 r["current_d10_selected"] == "NOT_SELECTED")
        need(sorted(proof["co_named_pending_candidate_ids"]) == alternative_ids and
             sorted(row["co_named_pending_candidate_ids"]) == alternative_ids,
             "same-name distinct IDs dropped")
        for col, dest, resident in columns:
            old = json.loads(src[col])
            need(isinstance(old,list) and old == proof[dest], "lost source claims " + col)
            if resident is not None:
                need(old == row[resident], "inventory claim changed " + col)
            if col == "semantic_law_variants":
                need(len(old) > 0 and old[0] == row["behavior"] == proof["law"], "law")
            if col == "donor_provenance_claims":
                need(len(old) > 0, "missing donor")
            if col == "source_records_sha_pinned":
                need(len(old) == int(src["source_record_count"]), "source loss")
        need(row["source_path"] == manifest["source"]["path"] and
             row["source_git_blob"] == manifest["source"]["git_blob"] and
             row["source_candidate_id"] == ident, "pin")
        need(row["coordinate"] is None and row["ratified_resident"] is False and
             row["physical_t5_authorized"] is False and
             row["independent_oracle"] == "NOT-EXECUTED" and
             row["witness_independence"] == "PENDING" and
             row["coordinate_basis"] == "NO-F2-F3-NO-PLACEMENT", "false admission")
        need(proof["F2"] == "HOLD_NOT_RUN" and
             proof["F3"] == "HOLD_DEDUP_UNPROVEN" and
             proof["F4"] == "NO_COORDINATE" and
             proof["ratified"] is False, "false witness")
    coordinates = [r["coordinate"] for r in v11["rows"] if r.get("coordinate") is not None]
    need(len(coordinates) == len(set(coordinates)) == 719, "coordinate collision")
    need(not any(r.get("ratified_resident") for r in v11["rows"]), "ratification")
    a = v11["accounting"]
    need((a["selected_semantic_candidates"],a["placed_selected_candidates"],
         a["unplaced_selected_candidates"],a["remaining_semantic_inventory"],
         a["ratified_d10_residents"],a["historical_text_claim_research_v11_added"]) ==
         (823,719,104,201,0,24), "inventory count")
    return {"selected":823,"placed":719,"unplaced":104,"remaining":201,
            "ratified":0,"research_added":24,"F2_oracles":0,"F3_proofs":0}

def check(root=ROOT, self_test=False):
    root = root.resolve()
    ptr = json.loads((root / "knowledge/d10-current-inventory.json").read_text())
    live, old = ptr["canonical_current"],ptr["historical_v10_research_inventory"]
    hook = ptr["current_v11_historical_law_selection"]
    need(live["path"] == "knowledge/d10-v11-semantic-inventory.json", "live pointer")
    need(old["path"] == "knowledge/d10-v10-semantic-inventory.json", "archive pointer")
    mp = hook["manifest"]
    need(mp["path"] == MANIFEST, "manifest pointer")
    m = json.loads(pinned(root,mp["path"],mp["git_blob"]))
    need(m["previous"]["git_blob"] == old["git_blob"], "previous mismatch")
    need(all(hook["source"][key] == m["source"][key] for key in ("path","git_blob")),
         "source pin mismatch")
    v10 = json.loads(pinned(root,old["path"],old["git_blob"]))
    v11 = json.loads(pinned(root,live["path"],live["git_blob"]))
    f = m["foundation"]
    foundation = json.loads(pinned(root,f["path"],f["git_blob"]))
    catalog = pinned(root,m["source"]["path"],m["source"]["git_blob"])
    result = verify(v10,v11,m,catalog,foundation)
    need((live["selected"],live["placed"],live["unplaced"],live["ratified"]) ==
         (823,719,104,0), "live accounting")
    if self_test:
        for field,bad in [("behavior","FORGED"),("coordinate","0000000000"),
                          ("ratified_resident",True),("source_candidate_id","FORGED")]:
            mutated = deepcopy(v11)
            mutated["rows"][799][field] = bad
            try: verify(v10,mutated,m,catalog,foundation)
            except ValueError: pass
            else: raise ValueError("D10_V11_BLOCK:bad mutant passed " + field)
    return result

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args = p.parse_args()
    print(json.dumps(check(self_test=args.self_test),sort_keys=True))
