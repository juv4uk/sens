#!/usr/bin/env python3
"""D10: дослідний replay 19 архівних законів, без ратифікації або фізичної адреси."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def sha(raw):
    b = raw.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(b)).encode("ascii") + b"\x00" + b).hexdigest()

def check(ok, label):
    if not ok:
        raise SystemExit("D10-REPLAY FAIL: " + label)

def main():
    bundle = read("knowledge/d10-existing-research-batch-replay-20261011.json")
    inventory_path = "knowledge/d10-v1-semantic-inventory.json"
    inventory = read(inventory_path)
    history = read("knowledge/d10-selection-transition-history.json")
    state = read("knowledge/d10-fill-v1-state.json")
    transition = history["transitions"][-1]
    entries = bundle["entries"]
    ledger = list(csv.DictReader((ROOT / "knowledge/d10-proposal-ledger.tsv").open(encoding="utf-8"), delimiter="\t"))
    ledger_names = {x["semantic_name"]: x for x in ledger}
    check(bundle["schema"] == "d10-existing-research-batch-replay/v1", "manifest schema")
    check(len(entries) == 19 and bundle["verified_entry_count"] == 19, "manifest size")
    check(len(inventory["rows"]) == 667, "inventory rows")
    check(transition["id"] == "d10.replay.existing-studies-19.20261011", "transition tail")
    check(transition["previous_selected"] == 648 and transition["resulting_selected"] == 667, "transition arithmetic")
    check(transition["previous_inventory_blob_sha"] == "aef34c9c6d31f172059f3cf5d70136c77ffde0fc", "previous SHA")
    check(sha((ROOT / inventory_path).read_text(encoding="utf-8")) == transition["resulting_inventory_blob_sha"], "new SHA")
    check(len({x["stable_id"] for x in inventory["rows"]}) == 667, "stable ID collision")
    check([e["semantic_name"] for e in entries] == [r["semantic_name"] for r in inventory["rows"][-19:]], "append-only order")
    for j, (entry, row) in enumerate(zip(entries, inventory["rows"][-19:])):
        check(entry["source_path"].startswith("knowledge/d10-"), "source namespace")
        donor = (ROOT / entry["source_path"]).read_text(encoding="utf-8")
        check(sha(donor) == entry["donor_blob_sha"], "donor SHA " + entry["source_path"])
        check(row["source_path"] == entry["source_path"], "source link")
        check(row["coordinate"] is None and row["ratified_resident"] is False and row["physical_t5_authorized"] is False, "forged authority")
        check(row["status"] == "SELECTED-RESEARCH-CANDIDATE", "wrong row status")
        check(bool(row["positive_witnesses"]) and bool(row["falsifiers"]), "missing evidence")
        proposal = ledger_names.get(entry["semantic_name"])
        check(proposal is not None and proposal["proposal_id"] == "D10P-" + str(8001 + j), "proposal trace")
        check(proposal["ratified"] == "0" and proposal["status"] == "pending-review", "proposal ratification")
    a = inventory["accounting"]
    check((a["selected_semantic_candidates"], a["law_forced_coordinates"], a["unplaced_selected_candidates"], a["remaining_semantic_inventory"], a["ratified_d10_residents"]) == (667, 256, 411, 357, 0), "accounting drift")
    check(state["target"]["selected_semantic_candidates"] == 667, "state target")
    print("D10-REPLAY PASS: 19 SHA-pinned donors, 667/1024 selected, 0 ratified")

if __name__ == "__main__":
    main()
