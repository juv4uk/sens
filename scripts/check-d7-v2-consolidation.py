#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
stable=json.loads((ROOT/"knowledge/d7-v2-stable-residents.json").read_text(encoding="utf-8"))
ledger=json.loads((ROOT/"knowledge/d7-v2-evidence-ledger.json").read_text(encoding="utf-8"))

assert stable["status"]=="research-only"
assert stable["foundation"].startswith("#3393")
assert stable["summary"]=={
    "total":128,
    "recovered":107,
    "provenance_missing":21,
    "phonology_eligible":75,
    "non_phonological":32,
    "pinned_no_geometry":21,
}
rows=stable["rows"]
assert len(rows)==128
assert len({r["stable_resident_id"] for r in rows})==128
assert {r["current_bits"] for r in rows}=={f"{i:07b}" for i in range(128)}

assert ledger["status"]=="research-consolidated-not-ratified"
assert ledger["accounting"]=={
    "capacity":128,
    "baseline_recovered":107,
    "baseline_provenance_missing":21,
    "phonology_eligible":75,
    "convention_recovered":32,
    "shiva_same_coordinate_overlays_on_missing":19,
    "baseline_missing_without_same_coordinate_overlay":2,
}
assert ledger["shiva_overlay_classes"]=={
    "text_digits":10,
    "text_modifiers":2,
    "text_punctuation":7,
    "same_coordinate_total":19,
}
assert ledger["baseline_missing_without_same_coordinate_overlay"]==["0100001","0101010"]

lrows=ledger["rows"]
assert len(lrows)==128
over=[r for r in lrows if r["shiva_same_coordinate_overlay"] is not None]
assert len(over)==19
assert all(r["baseline_status"]=="PROVENANCE-MISSING" for r in over)

by_kind={}
for r in over:
    k=r["shiva_same_coordinate_overlay"]["kind"]
    by_kind[k]=by_kind.get(k,0)+1
assert by_kind=={"text-digit":10,"text-modifier":2,"text-punctuation":7}

digit_bits={
    "0011100":"0","0011111":"1","0011101":"2","0011110":"3",
    "0111000":"4","0111011":"5","0111001":"6","0111010":"7",
    "0011001":"8","0011010":"9",
}
for bits,label in digit_bits.items():
    row=next(r for r in over if r["coordinate"]==bits)
    assert row["shiva_same_coordinate_overlay"]["label"]==label
    assert row["shiva_same_coordinate_overlay"]["semantics"]=="Text, NOT Number"

punct={
    "0011011":"…","0101001":"«","0101011":"»",
    "0110001":"—","0110011":"–","0110110":"“","0110111":"”",
}
for bits,label in punct.items():
    row=next(r for r in over if r["coordinate"]==bits)
    assert row["shiva_same_coordinate_overlay"]["label"]==label

moves=ledger["migration_candidate"]["moves"]
assert moves==[
    {"semantic":"h","from":"0110100","to":"0100001"},
    {"semantic":"r","from":"0101110","to":"0101010"},
    {"semantic":"l","from":"0101111","to":"0101110"},
]
assert ledger["migration_candidate"]["status"]=="TEXT-IDENTITY-MIGRATION-CANDIDATE"

# Migration targets are never silently reclassified as provenance recovery.
for bits in ["0100001","0101010"]:
    row=next(r for r in lrows if r["coordinate"]==bits)
    assert row["baseline_status"]=="PROVENANCE-MISSING"
    assert row["shiva_same_coordinate_overlay"] is None
    assert row["shiva_identity_migration"]["role"]=="TARGET"

print("D7-V2-CONSOLIDATION: PASS")
print("baseline=107+21 overlay=19 migration-targets=2")
print("phonology=75 convention=32 pinned=21 authority=RESEARCH")
