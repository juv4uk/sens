#!/usr/bin/env python3
"""Validate knowledge/foundation-debt-ledger.json.

The checker is deliberately conservative. It validates accounting shape and
category separation; it does not promote any claim epistemically.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

REQUIRED_ROW = {
    "id","claim","origin","authority","layer","epistemic","phase",
    "historical_external_donor","exact_borrowed_admitted_premise",
    "current_witness","derivation_parents","internally_derived",
    "heritage_debt","premise_debt","discharge_condition","evidence_refs",
}

def fail(msg: str) -> None:
    raise SystemExit(f"foundation-debt-error: {msg}")

def validate(doc: dict) -> dict:
    if doc.get("schema") != "foundation-debt-ledger/v1":
        fail("unexpected schema")

    vocab = doc.get("vocabulary", {})
    required_vocab = {"origin","authority","layer","epistemic","phase","debt"}
    if set(vocab) != required_vocab:
        fail(f"vocabulary keys mismatch: {sorted(vocab)}")

    rows = doc.get("rows")
    if not isinstance(rows, list) or not rows:
        fail("rows must be a non-empty list")

    seen = set()
    for row in rows:
        missing = REQUIRED_ROW - set(row)
        extra = set(row) - REQUIRED_ROW
        if missing:
            fail(f"{row.get('id','?')}: missing fields {sorted(missing)}")
        if extra:
            fail(f"{row.get('id','?')}: unexpected fields {sorted(extra)}")

        rid = row["id"]
        if rid in seen:
            fail(f"duplicate id {rid}")
        seen.add(rid)

        for field in ("origin","authority","layer","epistemic","phase"):
            if row[field] not in vocab[field]:
                fail(f"{rid}: invalid {field}={row[field]!r}")

        for field in ("heritage_debt","premise_debt"):
            if row[field] not in vocab["debt"]:
                fail(f"{rid}: invalid {field}={row[field]!r}")

        if not isinstance(row["derivation_parents"], list):
            fail(f"{rid}: derivation_parents must be a list")
        if not isinstance(row["evidence_refs"], list) or not row["evidence_refs"]:
            fail(f"{rid}: evidence_refs must be non-empty")
        if not all(isinstance(x, str) and x.strip() for x in row["evidence_refs"]):
            fail(f"{rid}: evidence_refs contain empty/non-string values")
        if not isinstance(row["internally_derived"], bool):
            fail(f"{rid}: internally_derived must be bool")

        # The two-axis split is structural: values from one vocabulary may not
        # be smuggled into the other field.
        if row["origin"] in vocab["authority"]:
            fail(f"{rid}: origin contains authority token")
        if row["authority"] in vocab["origin"]:
            fail(f"{rid}: authority contains origin token")

        # OPEN/PARTIAL debts need a concrete named discharge path.
        if row["heritage_debt"] in {"OPEN","PARTIAL"} or row["premise_debt"] in {"OPEN","PARTIAL"}:
            if not isinstance(row["discharge_condition"], str) or len(row["discharge_condition"].strip()) < 20:
                fail(f"{rid}: open/partial debt lacks concrete discharge condition")

        # CLOSED-IRREDUCIBLE is a successful premise closeout, not derivation.
        if "CLOSED-IRREDUCIBLE" in {row["heritage_debt"], row["premise_debt"]} and row["internally_derived"]:
            fail(f"{rid}: irreducible premise cannot be marked internally derived")

        # DONOR-ONLY means the donor itself is not current SENS-derived authority.
        if row["authority"] == "DONOR-ONLY" and row["internally_derived"]:
            fail(f"{rid}: DONOR-ONLY row cannot be internally derived")

    # Dependency references must be internal ledger IDs.
    for row in rows:
        for parent in row["derivation_parents"]:
            if parent not in seen:
                fail(f"{row['id']}: unknown derivation parent {parent}")

    metrics = {
        "rows": len(rows),
        "open_heritage_debt": sum(r["heritage_debt"] == "OPEN" for r in rows),
        "partial_heritage_debt": sum(r["heritage_debt"] == "PARTIAL" for r in rows),
        "open_premise_debt": sum(r["premise_debt"] == "OPEN" for r in rows),
        "partial_premise_debt": sum(r["premise_debt"] == "PARTIAL" for r in rows),
        "internally_derived_foundations": sum(bool(r["internally_derived"]) for r in rows),
        "ratified_irreducible_premises": sum(
            r["authority"] == "SENS-RATIFIED"
            and "CLOSED-IRREDUCIBLE" in {r["heritage_debt"], r["premise_debt"]}
            for r in rows
        ),
        "retired_or_falsified": sum(
            r["authority"] == "SUPERSEDED" or r["epistemic"] == "falsified"
            for r in rows
        ),
        "origin_counts": dict(Counter(r["origin"] for r in rows)),
        "authority_counts": dict(Counter(r["authority"] for r in rows)),
    }
    return metrics

def self_test() -> None:
    base = {
        "schema":"foundation-debt-ledger/v1",
        "vocabulary":{
            "origin":["HISTORICAL-DONOR","SENS-PREMISE","SENS-DERIVED","EXTERNAL-THEOREM","UNKNOWN"],
            "authority":["DONOR-ONLY","RESEARCH","WITNESSED","SENS-RATIFIED","SUPERSEDED","NONE"],
            "layer":["SEMANTICS","STRUCTURE","MECHANISM","BOUNDARY"],
            "epistemic":["premise","conjecture","witness","theorem","falsified","unknown"],
            "phase":["HISTORICAL-INGEST","STRUCTURAL-DISCOVERY","SENS-DERIVATION"],
            "debt":["OPEN","PARTIAL","NONE","DISCHARGED-DERIVED","CLOSED-IRREDUCIBLE"],
        },
        "rows":[{
            "id":"T-1","claim":"test","origin":"SENS-PREMISE","authority":"SENS-RATIFIED",
            "layer":"SEMANTICS","epistemic":"premise","phase":"SENS-DERIVATION",
            "historical_external_donor":"none","exact_borrowed_admitted_premise":"test premise",
            "current_witness":"test witness","derivation_parents":[],"internally_derived":False,
            "heritage_debt":"NONE","premise_debt":"CLOSED-IRREDUCIBLE",
            "discharge_condition":"closed within the deliberately bounded self-test scope",
            "evidence_refs":["self-test"],
        }]
    }
    validate(base)

    bad = json.loads(json.dumps(base))
    bad["rows"][0]["origin"] = "SENS-RATIFIED"
    try:
        validate(bad)
    except SystemExit:
        pass
    else:
        fail("self-test failed to reject authority token in ORIGIN")

    bad = json.loads(json.dumps(base))
    bad["rows"][0]["authority"] = "SENS-DERIVED"
    try:
        validate(bad)
    except SystemExit:
        pass
    else:
        fail("self-test failed to reject origin token in AUTHORITY")

    bad = json.loads(json.dumps(base))
    bad["rows"][0]["premise_debt"] = "OPEN"
    bad["rows"][0]["discharge_condition"] = ""
    try:
        validate(bad)
    except SystemExit:
        pass
    else:
        fail("self-test failed to reject open debt without discharge condition")

    print("foundation-debt-self-test=PASS")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", type=Path, default=Path("knowledge/foundation-debt-ledger.json"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return 0

    doc = json.loads(args.ledger.read_text(encoding="utf-8"))
    metrics = validate(doc)
    print(json.dumps(metrics, sort_keys=True))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(metrics, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
