#!/usr/bin/env python3
import json
import re
from pathlib import Path

root=Path(__file__).resolve().parents[1]
coverage=json.loads((root/"knowledge/sens8-current-coverage-v1.json").read_text(encoding="utf-8"))
d10=json.loads((root/"knowledge/d10-v1-semantic-inventory.json").read_text(encoding="utf-8"))
state=json.loads((root/"knowledge/d10-fill-v1-state.json").read_text(encoding="utf-8"))
table=(root/"lib/generated/function-table.lisp").read_text(encoding="utf-8")

assert coverage["schema"]=="sens8-current-coverage-v1/v1"
assert coverage["status"]=="AUDIT-COMPLETE"
assert coverage["authority"]=="#4021"
assert coverage["doctrine"]["placement_authority"]=="NONE"

rows=coverage["rows"]
assert len(rows)==256
assert len({row["legacy_code"] for row in rows})==256
assert {row["legacy_code"] for row in rows}=={f"{i:08b}" for i in range(256)}
assert all(row["legacy_coordinate_authority"]=="NONE" for row in rows)

# Replay old generated-table shape independently.
parsed=[]
for m in re.finditer(r'^\s*\(([01]{8})\s+([^\s()]+)([^\n]*?)\(en\s+([^()\s]+|\(\))\)', table, re.MULTILINE):
    parsed.append((m.group(1),None if m.group(4)=="()" else m.group(4)))
assert len(parsed)==256
assert sum(name is not None for _,name in parsed)==182
assert parsed[0][0]=="00000000" and parsed[0][1] is None

counts={}
for row in rows:
    counts[row["classification"]]=counts.get(row["classification"],0)+1
assert counts=={
    "DIRECT-CURRENT-IDENTITY":153,
    "CURRENT-PROJECTION-DERIVED":20,
    "INTERNAL-NO-SEMANTIC-SLOT":4,
    "D10-RECOVERY-CANDIDATE":4,
    "MECHANISM-HOLD":1,
    "UNNAMED-LEGACY-IDENTITY":1,
    "BLANK-UNUSED-CELL":73,
}

assert coverage["accounting"]=={
    "total_legacy_cells":256,
    "named_legacy_semantic_rows":182,
    "unnamed_legacy_identity_cells":1,
    "blank_unused_cells":73,
    "direct_current_identity":153,
    "current_projection_or_derived":20,
    "internal_no_semantic_slot":4,
    "d10_recovery_candidates":4,
    "mechanism_hold":1,
    "named_rows_accounted":182,
    "identity_bearing_or_assigned_including_unnamed_zero":183,
    "donor_coverage_percent":100,
}

by_name={row["legacy_name"].lower():row for row in rows if row["legacy_name"]}

for name,target in {
    "atom?":"D3:010 ATOM",
    "eq?":"D3:101 EQ",
    "lessp?":"D5:11010 LESSP",
    "greaterp?":"D5:11011 GREATERP",
    "equalp?":"D8:11110111 EQUAL",
    "not-greaterp?":"D6:110100 LEQ",
    "not-lessp?":"D6:110110 GEQ",
    "not?":"D4:0100 NOT",
    "equal?":"D8:11110111 EQUAL",
    "member?":"D5:11101 MEMBER",
    "second":"D4:1001 CADR",
    "third":"D5:10011 CADDR",
    "fourth":"D6:100111 CADDDR",
    "env":"D8:11100111 ENV-REFLECTION",
    "null?":"D4:0101 NULL",
}.items():
    row=by_name[name]
    assert row["classification"]=="CURRENT-PROJECTION-DERIVED"
    assert row["current_target"]==target

assert by_name["defmacro"]["classification"]=="CURRENT-PROJECTION-DERIVED"
assert "D5:00011 MACRO" in by_name["defmacro"]["current_target"]
assert by_name["codepoint->string"]["current_target"]=="D8:00000000 CODE-CHAR"
assert by_name["string->codepoint"]["current_target"]=="D8:11100000 CHAR-CODE"

for name in ("largest-chunk","nondecreasing-from?","nonincreasing-from?","digit->string"):
    assert by_name[name]["classification"]=="INTERNAL-NO-SEMANTIC-SLOT"

assert by_name["invoke"]["classification"]=="MECHANISM-HOLD"

d10_names={row["semantic_name"] for row in d10["rows"]}
for name in ("MONO-NS","UNIX-TIME-NOW","NTP-QUERY-RAW","TIMEZONE-DECLARATIONS-RAW"):
    assert name in d10_names
    row=by_name[name.lower()]
    assert row["classification"]=="D10-RECOVERY-CANDIDATE"
    assert row["legacy_coordinate_authority"]=="NONE"

audit=state["donor_audits"]["sens8"]
assert audit["artifact"]=="knowledge/sens8-current-coverage-v1.json"
assert audit["named_rows_accounted"]==182
assert audit["donor_exhausted"] is True
assert audit["new_d10_candidates_added_by_this_audit"]==0

print("SENS8-CURRENT-COVERAGE-V1=PASS")
print("cells=256 named=182 direct=153 projection=20 internal=4 d10=4 mechanism=1 blank=73")
print("donor-exhausted=yes legacy-placement-authority=none")
