#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
stable=json.loads((ROOT/"knowledge/d7-v2-stable-residents.json").read_text(encoding="utf-8"))
ledger=json.loads((ROOT/"knowledge/d7-v2-evidence-ledger.json").read_text(encoding="utf-8"))
geometry=json.loads((ROOT/"knowledge/d7-v2-geometry-ledger.json").read_text(encoding="utf-8"))

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


assert ledger["role_layers"]["local_ordinal"]["count"]==14
assert ledger["role_layers"]["local_ordinal"]["coordinate_effect"].startswith("NONE")
assert ledger["shiva_sound_projection"]["status"]=="OPEN-DONOR-STACK"

evaluation=ledger["migration_candidate"]["evaluation"]
assert evaluation["candidate"]=="D / UPC-14-derived Text7 geometry"
assert evaluation["measured"]["shared_with_pinned_hand_map"]=="43/46"
assert evaluation["measured"]["strict_panini_1_1_9_matrix"]=="1760/1764"
assert evaluation["measured"]["positive_class_f1"]==0.987
assert evaluation["measured"]["best_of_10000_permutations_f1"]==0.449

post=ledger["migration_candidate"]["post_migration_candidate"]
assert post["occupancy"]==124
assert post["free_coordinates"]==["0101111","0110100","1010001","1010011"]
assert [r["coordinate"] for r in post["additional_identity_retirement"]]==["1010001","1010011"]

assert geometry["status"]=="research-law-first-not-ratified"
assert geometry["accounting"]["baseline_rows"]==128
families={f["id"]:f for f in geometry["families"]}
assert families["varga"]["rows"]==25
assert families["varga"]["gauge_lower_bound"]==45158400
assert families["vowel-core"]["rows"]==28
assert families["vowel-core"]["residue_rows"]==4
assert families["vowel-core"]["axes"]["length_xor"]=="0000001"
assert families["vowel-core"]["axes"]["nasal_xor"]=="0000010"
assert families["vowel-core"]["absolute_quality_gauge_lower_bound"]==161280
assert families["non-varga"]["rows"]==18
assert families["sign-operator"]["rows"]==32
assert geometry["shiva_convention_geometry"]["text_digits"]["rows"]==10
assert geometry["candidate_D"]["candidate_occupancy"]==124
assert geometry["candidate_D"]["candidate_free"]==["0101111","0110100","1010001","1010011"]

d14=ledger["d14_pratyahara_boundary"]
assert d14["results"]["unique_sound_world"]==42
assert d14["results"]["canonical_pratyahara_items"]==43
assert d14["results"]["minimal_tucker_obstructions"]==84
assert d14["results"]["exact_contiguous_ceiling"]=="39/43"
assert d14["results"]["dual_h_contiguous"]=="43/43"
assert d14["d7_coordinate_effect"]=="NONE"

d14g=geometry["d14_pratyahara_boundary"]
assert d14g["verified"]["tucker_obstructions"]==84
assert d14g["verified"]["minimum_transversal_size"]==4
assert d14g["verified"]["ceiling_42_unique_sounds"]=="39/43"
assert d14g["verified"]["dual_h_43_node_path"]=="43/43"
assert d14g["d7_coordinate_status"]=="NO-EFFECT"
assert d14g["semantic_split"]["D7"].startswith("phonetic/text geometry")
assert d14g["semantic_split"]["D14"].startswith("grammar graph/path")

print("D7-V2-CONSOLIDATION: PASS")
print("baseline=107+21 overlay=19 migration-targets=2")
print("phonology=75 convention=32 pinned=21 authority=RESEARCH")
