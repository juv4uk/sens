#!/usr/bin/env python3
from pathlib import Path
import re
import sys

root = Path(__file__).resolve().parents[1]
authority = (root / "contracts/core1-historical-sid-map.lisp").read_text()
resolver = (root / "lib/core1-compiler-sid-resolver.lisp").read_text()

row_re = re.compile(
    r"^\s*\(row\s+([01]{8})\s+([^\s()]+)\s+([^\s()]+)\s+",
    re.MULTILINE,
)
authority_pairs = set()
for sid, my_name, historical_name in row_re.findall(authority):
    authority_pairs.add((my_name, sid))
    authority_pairs.add((historical_name, sid))

entry_re = re.compile(
    r"\(\(EQ NAME \(QUOTE ([^\s()]+)\)\)\s+([01]{8})\)"
)
entries = entry_re.findall(resolver)
if not entries:
    sys.exit("ERROR: Core1 compiler SID resolver has no exact SID8 entries")

required_surfaces = {
    "ATOM", "atom", "EQ", "eq", "CONS", "cons", "CAR", "car", "CDR", "cdr",
    "+", "-", "NOT", "not", "LIST", "list",
}
actual_surfaces = {surface for surface, _sid in entries}
missing = sorted(required_surfaces - actual_surfaces)
if missing:
    sys.exit(f"ERROR: resolver missing required compiler surfaces: {missing}")

for surface, sid in entries:
    if (surface, sid) not in authority_pairs:
        sys.exit(
            f"ERROR: resolver row {surface}->{sid} is not owned by "
            "contracts/core1-historical-sid-map.lisp"
        )

if re.search(r'\(QUOTE\s+[01]{8}\)', resolver, re.IGNORECASE):
    sys.exit("ERROR: quoted SID8 wrapper is forbidden")
if re.search(r'"[01]{8}"', resolver):
    sys.exit("ERROR: string SID8 wrapper is forbidden")

print(f"CORE1-SID8-RESOLVER-AUTHORITY-PASS rows={len(entries)}")
