#!/usr/bin/env python3
import json
import re
from pathlib import Path

from domain_tables import D7_TABLE, read_domain_table

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

# The Lisp table is the human projection of the ratified W7 coordinates, not
# an independent resident allocator. Compare every entry against owner #3572
# so a missing row, reused reserved slot, or label drift fails closed.
canonical_d7_rows = {}
row_pattern = re.compile(
    r"^\s*\(([01]{7})\s+\(ук\s+[^()]+\)\s+"
    r"\(укр\s+[^()]+\)\s+\(san\s+[^()]+\)\s+"
    r"\(en\s+([^()\s]+)\)"
)
table = (root / "lib/domains/d7.lisp").read_text(encoding="utf-8")
for line_number, line in enumerate(table.splitlines(), start=1):
    if not re.match(r"^\\s*\\([01]{7}\\s", line):
        continue
    match = row_pattern.match(line)
    assert match is not None, f"D7 malformed surface at line {line_number}"
    coordinate, projection = match.groups()
    assert coordinate not in canonical_d7_rows, f"D7 duplicate {coordinate}"
    canonical_d7_rows[coordinate] = projection

assert canonical_d7_rows == d["residents"], "D7 Lisp table drifted from owner-ratified 126/128"
assert len(d["rows"]) == 128
ratified_rows = {
    row["coordinate"]: row["report_name"]
    for row in d["rows"] if row["status"] == "OWNER-RATIFIED"
}
assert ratified_rows == canonical_d7_rows
assert {
    row["coordinate"] for row in d["rows"]
    if row["status"] == "OWNER-RESERVED-PINNED"
} == set(d["reserved_coordinates"])
digits = {
    row["report_name"] for row in d["rows"]
    if row.get("semantic_role") == "text-digit"
}
assert digits == {f"text.digit.{digit}" for digit in range(10)}

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

# The owner-ratified JSON owns coordinates and roles; lib/domains/d7.lisp is
# ONLY a human-readable projection. Every projected D7 row must be a real
# ratified resident at the same exact seven-bit coordinate. Reserved pins are
# neither empty allocation slots nor callable operations.
table_rows = read_domain_table(D7_TABLE)
ratified_bits = set(d["residents"])
projected_bits = [row.bits for row in table_rows]
assert len(table_rows) == d["occupancy"] == 126
assert projected_bits == sorted(ratified_bits), "D7 surface coordinate drift"
assert not (set(projected_bits) & set(d["reserved_coordinates"]))
assert len({row.bits for row in table_rows}) == len(table_rows)
for row in table_rows:
    assert row.width == 7 and len(row.bits) == 7
    assert row.en == d["residents"][row.bits], f"D7:{row.bits} owner map mismatch"
    assert row.lisp is None, f"D7:{row.bits} must not mint a Lisp callable"
    assert all(getattr(row, key) for key in ("uk", "ukr", "san")), (
        f"D7:{row.bits} missing human projection"
    )

# The row-wise evidence must stay a one-to-one projection of the ratified
# coordinates, not an alternative Rust/reader-generated semantic registry.
authority_rows = {row["coordinate"]: row for row in d["rows"]}
assert len(authority_rows) == len(d["rows"]) == 128
for row in table_rows:
    owner = authority_rows[row.bits]
    assert owner["status"] == "OWNER-RATIFIED"
    assert owner["report_name"] == row.en
for reserved in d["reserved_coordinates"]:
    assert authority_rows[reserved]["status"] != "OWNER-RATIFIED"


assert "(owner-ratification . #3572)" in contract
assert "(width . #d7)" in contract
assert "(capacity . #d128)" in contract
assert "(occupancy . #d126)" in contract
assert "(d7-coordinate-law . " in contract
assert "(identity . " not in contract
assert '(owner-reserved-pinned . ("0100001" "0101010"))' in contract
assert '(candidate-occupancy . #d124)' in contract
assert "(minor . 8)" in lang
assert "Contract 11.8" in lang
assert "Core.D7 is OWNER-RATIFIED 126/128 under #3572" in lang
assert "D7  owner-ratified 126/128" in current
assert "D8  full compact 256/256" in current
assert "D9  full compact 512/512" in current

# The human-readable D7 table must be a lossless projection of the
# Lisp-ratified coordinate ledger, never a second independently invented map.
# No Rust table of phonemes/roles/callability is introduced here.
import re

surface=(root/"lib/domains/d7.lisp").read_text(encoding="utf-8")
surface_rows=re.findall(r"^  \(([01]{7}) (.+)\)$",surface,flags=re.MULTILINE)
assert len(surface_rows)==d["occupancy"]==126, "D7 projection row count drift"
coordinates=[bits for bits,_ in surface_rows]
assert len(set(coordinates))==len(coordinates), "duplicate D7 coordinate"
assert set(coordinates)==set(d["residents"]), "D7 surface/resident map drift"
assert set(coordinates).isdisjoint(d["reserved_coordinates"]), "reserved D7 coordinates were allocated"
expected_columns=("ук","укр","san","en","LISP","sym")
for bits,body in surface_rows:
    for name in expected_columns:
        assert body.count(f"({name} ")==1, f"D7:{bits} missing or duplicated {name}"
    labels=re.findall(r"\((ук|укр|san|en|LISP|sym) ",body)
    assert tuple(labels)==expected_columns, f"D7:{bits} surface column order changed"
    en=re.search(r"\(en ([^()]*)\)",body)
    assert en is not None and en.group(1)==d["residents"][bits], f"D7:{bits} role projection drift"
    assert "(LISP ())" in body, f"D7:{bits} invented Lisp callable name"

print("D7-SURFACE-ROWS: PASS residents=126 reserved=2 no-Rust-law")

# The Lisp-owned human surface table must be an exact projection of the
# ratified coordinate registry, not an independent allocation authority.
surface=(root/"lib/domains/d7.lisp").read_text(encoding="utf-8")
surface_rows=re.findall(r"^\\s*\\(([01]{7})\\s+(.+)\\)\\s*$",surface,re.MULTILINE)
surface_coordinates=[bits for bits,_ in surface_rows]
assert len(surface_rows)==d["occupancy"], "D7 surface row count differs from owner-ratified occupancy"
assert len(set(surface_coordinates))==len(surface_coordinates), "duplicate D7 surface coordinate"
assert set(surface_coordinates)==set(d["residents"]), "D7 surface allocation differs from ratified registry"
assert surface_coordinates==sorted(surface_coordinates), "D7 rows must remain ordered by binary coordinate"

for bits,body in surface_rows:
    fields=re.findall(r"\\((ук|укр|san|en|LISP|sym)\\s+(\\(\\)|[^()]+)\\)",body)
    assert [name for name,_ in fields]==["ук","укр","san","en","LISP","sym"], f"D7:{bits} has invalid surface columns"
    row=dict(fields)
    for name in ("ук","укр","san","en"):
        assert row[name].strip() not in ("","()"), f"D7:{bits} missing {name}"
    assert row["en"]==d["residents"][bits], f"D7:{bits} diverges from the ratified resident name"
    assert row["LISP"]=="()", f"D7:{bits} must not invent a callable Lisp function"

assert not set(surface_coordinates).intersection(d["reserved_coordinates"]), "D7 owner-reserved pin was allocated"

print("D7-CURRENT-AUTHORITY: PASS")
print("occupancy=126/128 baseline=107 shiva-overlays=19 reserved-pinned=2 candidate-D=NOT-RATIFIED")
