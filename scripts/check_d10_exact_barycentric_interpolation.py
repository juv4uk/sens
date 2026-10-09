#!/usr/bin/env python3
"""Source/semantic gate for the NIST exact interpolation research donor.

A later traced SELECT is allowed; source research does not itself ratify D10.
"""
import argparse
import copy
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOSSIER = ROOT / "knowledge/d10-exact-barycentric-interpolation-research-v1.json"
INVENTORY = ROOT / "knowledge/d10-v1-semantic-inventory.json"
FOUNDATION = ROOT / "knowledge/d1-d9-foundation.json"
ORACLE = ROOT / "tests/oracles/d10_exact_barycentric_chez.ss"
NAME = "EXACT-BARYCENTRIC-INTERPOLATE"
DLMF = "https://dlmf.nist.gov/3.3"
SCIPY = "https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.BarycentricInterpolator.html"
IDS = (
    "QUAD_NODE","QUAD_HALF","QUAD_EXTRAP","LINEAR_MID","SINGLE_CONSTANT",
    "THREE_CONSTANT","REVERSE_ORDER","EXACT_NEGATIVE","EXACT_NODE",
    "VALUE_SHIFT","VALUE_SCALE","DUPLICATE_REJECT","EMPTY_REJECT",
    "INEXACT_NODE_REJECT","INEXACT_QUERY_REJECT"
)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def verify(d, inv, foundation, src):
    assert d["schema"] == "d10-exact-barycentric-interpolation-research/v1"
    assert d["status"] == "HOLD-CORE-VS-DERIVED-LIBRARY-PENDING-OWNER-REVIEW"
    assert d["name"] == NAME and d["domain"] == "D10"
    assert d["selected"] is False and d["ratified"] is False and d["coordinate"] is None
    assert d["physical_t5_authorized"] is False
    assert d["owner_approval_required_before_selection"] is True
    assert [r["url"] for r in d["primary_sources"]] == [DLMF, SCIPY]
    assert "unique" in d["primary_sources"][0]["scope"]
    assert d["uk"] and d["ukr"] and len(d["law"]) > 50
    assert len(d["examples"]) == 5 and len(d["falsifiers"]) >= 5
    assert d["signature"] and "HOLD" in d["dedup"]["core_classification"]
    assert len(d["user_hobbies"]) >= 5
    assert foundation["status"] == "owner-ratified"
    low = {str(x).upper() for dom in foundation["domains"].values()
           for x in dom["residents"].values()}
    assert NAME not in low
    assert inv["accounting"]["selected_semantic_candidates"] == len(inv["rows"])
    assert len(inv["rows"]) >= 634, "historical 634 donor baseline missing"
    assert inv["accounting"]["ratified_d10_residents"] == 0
    assert inv["accounting"]["law_forced_coordinates"] == 256
    assert inv["accounting"]["unplaced_selected_candidates"] == len(inv["rows"]) - 256
    assert inv["accounting"]["remaining_semantic_inventory"] == 1024 - len(inv["rows"])
    live = [r for r in inv["rows"] if r["semantic_name"] == NAME]
    assert len(live) <= 1
    if live:
        # Archive must remain historical, while admission gets its own source-
        # linked append-only and owner-review path. Do not freeze growth at 634.
        row = live[0]
        assert row.get("source_path") == str(DOSSIER.relative_to(ROOT))
        assert row.get("primary_url") == DLMF
        assert row.get("status") == "SELECTED-RESEARCH-CANDIDATE"
        assert row.get("proposal_status") == "pending-owner-review"
        assert row.get("coordinate") is None and row.get("ratified_resident") is False
        assert row.get("behavior") == d["law"]
        assert row.get("positive_witnesses") and row.get("falsifiers")
    observed = tuple(re.findall(r'\(observe\s+"([A-Z_]+)"', src))
    assert observed == IDS and len(set(observed)) == 15
    assert "(role research-only)" in src and "(semantic-authority-change none)" in src
    return {"dictionary_law": NAME, "live_selected": len(inv["rows"]),
            "source_attested": True, "selected_here": 0, "ratified_here": 0}

def negatives(d, inv, f, src):
    mutations = [
        (0,lambda x: x.update({"selected":True})),
        (0,lambda x: x.update({"coordinate":"0000000000"})),
        (0,lambda x: x.update({"ratified":True})),
        (0,lambda x: x.update({"name":"INVENTED-OPCODE"})),
        (0,lambda x: x.update({"status":"RATIFIED"})),
        (0,lambda x: x.update({"falsifiers":[]})),
        (0,lambda x: x.update({"law":"incorrect"})),
        (0,lambda x: x["primary_sources"][0].update({"url":"https://invalid.example"})),
        (3,lambda x: x.replace('"QUAD_HALF"','"FORGED_CASE"')),
        (1,lambda x: x["rows"].append({"semantic_name":NAME, "coordinate":"1010101010",
                                       "ratified_resident":True}))
    ]
    for n, (index, fn) in enumerate(mutations, 1):
        vals = [copy.deepcopy(d), copy.deepcopy(inv), copy.deepcopy(f), src]
        outcome = fn(vals[index])
        if outcome is not None:
            vals[index] = outcome
        try:
            verify(*vals)
        except (AssertionError, KeyError, ValueError, TypeError):
            continue
        raise AssertionError("mutant survived: " + str(n))
    print("D10 exact interpolation negative source/geometry controls PASS 10/10")

def run_chez(binary):
    p = subprocess.run([binary, "--script", str(ORACLE)],cwd=ROOT,
                       capture_output=True,text=True,timeout=120,check=False)
    if p.returncode:
        raise AssertionError(f"Chez error {p.returncode}:\n{p.stdout}\n{p.stderr}")
    obs = []
    summaries = []
    for line in p.stdout.splitlines():
        if line.startswith("OBS\t"):
            parts = line.split("\t")
            assert len(parts) == 3 and parts[2] == "PASS", line
            obs.append(parts[1])
        elif line.startswith("SUMMARY\t"):
            summaries.append(line)
        elif line.strip():
            raise AssertionError("unknown Chez output: "+line)
    assert tuple(obs) == IDS
    assert summaries == ["SUMMARY\tD10-EXACT-BARYCENTRIC-CHEZ-V1\t15"]
    print("Independent exact-rational Chez Scheme R6RS mathematical donor PASS 15/15")
    print("This does NOT prove native binary SENS runtime, astronomy, SDR, or hardware parity.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-chez",action="store_true")
    parser.add_argument("--scheme",default="scheme")
    opt=parser.parse_args()
    d, inv, f = read(DOSSIER), read(INVENTORY), read(FOUNDATION)
    src=ORACLE.read_text(encoding="utf-8")
    print("D10 BARYCENTRIC research source PASS",json.dumps(verify(d,inv,f,src)))
    negatives(d,inv,f,src)
    if opt.real_chez:
        run_chez(opt.scheme)
