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

# Список зв'язаних із джерелом визначень — не список фізичних PASS.
# Генератор окремо звіряє цей Rust-покажчик з конкретними SENS DEFINE.
BINDINGS = "crates/sens/src/d10_definition_bindings_generated.rs"
BINDING_ENTRY = re.compile(
    r"^\s*D10DefinitionBinding \{ bits: 0b([01]{10}), names: &\[",
    re.MULTILINE,
)

def source_definition_codes(root):
    source = (root / BINDINGS).read_text(encoding="utf-8")
    codes = BINDING_ENTRY.findall(source)
    check_ok(bool(codes) and len(codes) == len(set(codes)),
             "missing or duplicate D10 concrete SENS bindings")
    return codes

def write_coverage(path, inventory, definitions):
    """1024 exact coordinates; UNKNOWN is not a verdict of non-executability."""
    header = (
        "coordinate\tstable_id\tsemantic_name\towner_ratified\t"
        "core4_epistemic_sens_definition\tmath_selector_shape\t"
        "native_positive\tnative_negative\tphysical_execution"
    )
    lines = [header]
    for row in sorted(inventory["rows"], key=lambda r: r["coordinate"]):
        name = row["semantic_name"]
        sid = row["stable_id"]
        check_ok(all("\t" not in str(x) and "\n" not in str(x)
                     for x in (name, sid)), "unsafe evidence TSV field")
        lines.append("\t".join((
            row["coordinate"], sid, name, "OWNER_RATIFIED",
            "SOURCE_FOUND" if row["coordinate"] in definitions
            else "NOT_IN_SCANNED_CORE4_EPISTEMIC",
            "SELECTOR_MODEL_FAMILY" if re.fullmatch(r"C[AD]{8}R", name)
            else "OTHER_DOMAIN_LAW",
            "NOT_RECORDED_IN_PINNED_INVENTORY",
            "NOT_RECORDED_IN_PINNED_INVENTORY",
            "NOT_ATTESTED_HERE_NOT_A_NONCALLABLE_VERDICT",
        )))
    check_ok(len(lines) == 1025, "coverage rows must be 1024")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def verify(m,ptr,inventory,definitions):
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
    definition_codes=set(definitions)
    check_ok(len(definitions)==len(definition_codes)
             and definition_codes.issubset(set(bits)),
             "duplicate or non-D10 SENS definition binding")
    # Ніякого global physical_executable=false: ця функція не запускає SENS.
    # Відсутність квитанції у pinned metadata не встановлює невикличність.
    return {"domain_owner_ratified":True,"semantics":1024,"codewords":1024,
            "execution_target_positions":1024,
            "known_concrete_SENS_source_definitions":len(definition_codes),
            "not_in_scanned_SENS_libraries":1024-len(definition_codes),
            "pinned_manifest_native_attestations":0,
            "physical_execution_tested_by_this_checker":False,
            "physical_status":"NOT_MEASURED_BY_RATIFICATION_CHECK",
            "fully_oracle_attested":False}

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
    definitions=source_definition_codes(root)
    result=verify(m,ptr,inv,definitions)
    if self_test:
        from copy import deepcopy
        for name,mutation in [
            ("duplicate-code",lambda i:i["rows"][1].update(coordinate=i["rows"][0]["coordinate"])),
            ("forged-physical",lambda i:i["rows"][0].update(physical_t5_authorized=True)),
            ("fake-resident",lambda i:i["rows"][0].update(ratified_resident=True)),
        ]:
            mutant=deepcopy(inv)
            mutation(mutant)
            try:verify(m,ptr,mutant,definitions)
            except ValueError: pass
            else:raise ValueError("D10_OWNER_RATIFICATION_BLOCK:mutant admitted "+name)
        for label,bad in (("duplicate-binding",definitions+[definitions[0]]),
                          ("unknown-binding",definitions+["11111111111"])):
            try:verify(m,ptr,inv,bad)
            except ValueError: pass
            else:raise ValueError("D10_OWNER_RATIFICATION_BLOCK:mutant admitted "+label)
    return result,inv,set(definitions)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--coverage-tsv",type=Path,
                   help="emit one line per D10 position, not a native PASS verdict")
    args=p.parse_args()
    summary,inventory,definitions=run(self_test=args.self_test)
    if args.coverage_tsv:
        write_coverage(args.coverage_tsv,inventory,definitions)
        summary["coverage_tsv"]=str(args.coverage_tsv)
    print(json.dumps(summary,sort_keys=True))
