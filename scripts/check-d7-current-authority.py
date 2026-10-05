#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d7-ratified.json").read_text(encoding="utf-8"))
ledger=json.loads((root/"knowledge/d7-v2-evidence-ledger.json").read_text(encoding="utf-8"))
contract=(root/"contracts/d7-ratification.lisp").read_text(encoding="utf-8")
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")

assert d["status"]=="owner-ratified"
assert d["authority"]=="#3572"
assert d["domain"]=="D7" and d["width"]==7
assert d["capacity"]==128 and d["occupancy"]==126
assert d["owner_reserved_pinned"]==2
assert d["reserved_coordinates"]==["0100001","0101010"]
assert len(d["residents"])==126
assert set(d["residents"]).isdisjoint(d["reserved_coordinates"])
assert set(d["residents"]) | set(d["reserved_coordinates"]) == {f"{i:07b}" for i in range(128)}

assert d["occupancy_basis"]=={
    "baseline_recovered":107,
    "owner_admitted_same_coordinate_shiva_overlays":19,
    "total_owner_ratified_residents":126,
    "owner_reserved_pinned":2,
}
assert d["role_counts"]=={
    "phonology_eligible_recovered":75,
    "baseline_non_phonological_recovered":32,
    "admitted_text_digits":10,
    "admitted_text_modifiers":2,
    "admitted_text_punctuation":7,
}

overlay_rows=[r for r in d["rows"] if r.get("baseline_residency")=="reserved" and r["status"]=="OWNER-RATIFIED"]
assert len(overlay_rows)==19
assert sum(r["semantic_role"]=="text-digit" for r in overlay_rows)==10
assert sum(r["semantic_role"]=="text-modifier" for r in overlay_rows)==2
assert sum(r["semantic_role"]=="text-punctuation" for r in overlay_rows)==7
assert all(r["coordinate"] not in d["reserved_coordinates"] for r in overlay_rows)

assert d["laws"]["text_digits_are_not_number"] is True
assert d["laws"]["local_ordinal_is_separate_role"] is True
assert d["laws"]["automatic_d6_prefix_inheritance"] is False
assert d["laws"]["candidate_d_migration_ratified"] is False
assert d["laws"]["d14_pratyahara_boundary"]=={
    "d7_coordinate_effect":"NONE",
    "unique_sound_ceiling":"39/43",
    "dual_h_grammar_path":"43/43",
    "dual_h_not_two_phonemes":True,
}

assert ledger["baseline_missing_without_same_coordinate_overlay"]==["0100001","0101010"]
assert ledger["migration_candidate"]["post_migration_candidate"]["occupancy"]==124
assert d["future_migration_boundary"]["status"]=="NOT-RATIFIED"
assert d["future_migration_boundary"]["candidate_occupancy"]==124

assert "(owner-ratification . #3572)" in contract
assert "(width . #d7)" in contract
assert "(capacity . #d128)" in contract
assert "(occupancy . #d126)" in contract
assert '(owner-reserved-pinned . ("0100001" "0101010"))' in contract
assert '(candidate-occupancy . #d124)' in contract
assert "(minor . 6)" in lang
assert "Contract 11.6" in lang
assert "D7 is owner-ratified 126/128 in #3572" in lang
assert "D7  owner-ratified 126/128" in current
assert "D8  UNRATIFIED / RESEARCH" in current

print("D7-CURRENT-AUTHORITY: PASS")
print("occupancy=126/128 baseline=107 shiva-overlays=19 reserved-pinned=2 candidate-D=NOT-RATIFIED")
