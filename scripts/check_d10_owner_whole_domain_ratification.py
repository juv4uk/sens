#!/usr/bin/env python3
"""Check domain-level owner ratification without forging per-row/runtime evidence."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST="knowledge/d10-owner-whole-domain-ratification-20261012.json"

def check_ok(value,reason):
    if not value: raise ValueError("D10_OWNER_RATIFICATION_BLOCK:"+reason)

def blob(b):
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def verify(m,ptr,inventory):
    check_ok(m["schema"]=="sens-d10-whole-domain-owner-ratification/v1","schema")
    check_ok(m["decision"]=="RATIFY_D10_AS_ONE_COMPLETE_DOMAIN" and
             m["ratification_mode"]=="ATOMIC_WHOLE_DOMAIN_NOT_PER_RESIDENT" and
             m["ratified"] is True,"owner decision")
    check_ok(ptr["owner_whole_domain_ratification"]["path"]==MANIFEST and
             ptr["owner_whole_domain_ratification"]["status"]=="RATIFIED_BY_OWNER",
             "current owner decision")
    check_ok(ptr["canonical_current"]["path"]==m["inventory"]["path"] and
             ptr["canonical_current"]["git_blob"]==m["inventory"]["git_blob"],"codebook pin")
    check_ok(len(inventory["rows"])==1024 and
             inventory["width"]==10 and inventory["capacity"]==1024,"capacity")
    bits=[r["coordinate"] for r in inventory["rows"]]
    names=[r["semantic_name"].casefold() for r in inventory["rows"]]
    ids=[r["stable_id"] for r in inventory["rows"]]
    check_ok(all(isinstance(b,str) and re.fullmatch("[01]{10}",b) for b in bits)
             and len(set(bits))==1024 and set(bits)=={format(i,"010b") for i in range(1024)}
             and len(set(names))==1024 and len(set(ids))==1024,
             "bijection or duplicate")
    check_ok(m["inventory"]["rows"]==1024 and
             m["inventory"]["unique_binary_codewords"]==1024 and
             m["inventory"]["unique_stable_ids"]==1024 and
             m["inventory"]["unique_semantic_names"]==1024 and
             ptr["canonical_current"]["selected"]==1024 and
             ptr["canonical_current"]["placed"]==1024 and
             ptr["canonical_current"]["unplaced"]==0,"count")
    evidence=m["evidence_separation"]
    check_ok(evidence["owner_domain_ratification"] is True and
             evidence["physical_runtime_t5_opcode_admission"] is False and
             evidence["all_semantic_laws_independently_verified"] is False and
             evidence["positive_and_negative_witnesses_all_replayed"] is False and
             evidence["d1_d9_d10_behavioral_independence_all_proved"] is False and
             evidence["independent_execution_claims_added"]==0,
             "fabricated evidence or admission")
    check_ok(not any(r.get("ratified_resident") is True or
                     r.get("physical_t5_authorized") is True for r in inventory["rows"])
             and ptr["canonical_current"]["ratified"]==0,
             "unreviewed per-row/runtime admission")
    return {"domain_owner_ratified":True,"semantics":1024,"codewords":1024,
            "physical_executable":False,"fully_oracle_attested":False}

def run(root=ROOT,self_test=False):
    root=root.resolve()
    m=json.loads((root/MANIFEST).read_text(encoding="utf-8"))
    ptr=json.loads((root/"knowledge/d10-current-inventory.json").read_text(encoding="utf-8"))
    pin=m["inventory"]
    path=(root/pin["path"]).resolve()
    check_ok(path.is_relative_to(root) and path.is_file(),"missing inventory")
    raw=path.read_bytes()
    check_ok(blob(raw)==pin["git_blob"],"git blob mismatch")
    inv=json.loads(raw)
    result=verify(m,ptr,inv)
    if self_test:
        from copy import deepcopy
        for name,mutation in [
            ("duplicate-code",lambda i:i["rows"][1].update(coordinate=i["rows"][0]["coordinate"])),
            ("forged-physical",lambda i:i["rows"][0].update(physical_t5_authorized=True)),
            ("fake-resident",lambda i:i["rows"][0].update(ratified_resident=True)),
        ]:
            mutant=deepcopy(inv)
            mutation(mutant)
            try:verify(m,ptr,mutant)
            except ValueError: pass
            else:raise ValueError("D10_OWNER_RATIFICATION_BLOCK:mutant admitted "+name)
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    print(json.dumps(run(self_test=args.self_test),sort_keys=True))
