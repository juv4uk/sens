#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ledger = json.loads((root / "knowledge/d6-mechanism-ledger.json").read_text(encoding="utf-8"))
ratified = json.loads((root / "knowledge/d6-ratified.json").read_text(encoding="utf-8"))
selector = (root / "crates/sens/src/eval/selector_law.rs").read_text(encoding="utf-8")
canon = (root / "crates/sens/src/eval/canon.rs").read_text(encoding="utf-8")
forms = (root / "crates/sens/src/eval/necessary_forms.rs").read_text(encoding="utf-8")
registry = (root / "crates/sens/src/semantic_registry.rs").read_text(encoding="utf-8")

assert ledger["schema"] == "d6-mechanism-ledger/v1"
assert ledger["domain"] == "D6"
assert ledger["identity_occupancy"] == 64
assert len(ledger["rows"]) == 64

rows = {row["coordinate"]: row for row in ledger["rows"]}
assert set(rows) == {f"{i:06b}" for i in range(64)}
assert {bits: row["resident"] for bits, row in rows.items()} == ratified["residents"]
assert all(row["identity_status"] == "RATIFIED" for row in rows.values())

counts = {key: 0 for key in ("DIRECT_LAW", "LOWER_DOMAIN_COMPOSITION", "LISP_OWNED", "MISSING")}
for row in rows.values():
    counts[row["mechanism_status"]] += 1
assert counts == ledger["status_counts"]
assert ledger["executable_coverage"] == {"count": 16, "total": 64, "basis": "current admitted exact-domain runtime routes"}
assert counts == {"DIRECT_LAW": 16, "LOWER_DOMAIN_COMPOSITION": 0, "LISP_OWNED": 0, "MISSING": 48}

selector_coords = {f"{i:06b}" for i in range(0b011000, 0b100000)} | {f"{i:06b}" for i in range(0b100000, 0b101000)}
assert {bits for bits, row in rows.items() if row["mechanism_status"] == "DIRECT_LAW"} == selector_coords
assert all(rows[bits]["negative_cross_domain_control"] for bits in selector_coords)

# D6 selector proof: the family-local decoder extends exactly one depth.
assert "if !(3..=6).contains(&width)" in selector
assert "let CoreDomainIdentity::D3(word) = identity else" in canon
assert "let CoreDomainIdentity::D4(word) = identity else" in forms
assert "5 => Some(CoreDomainIdentity::D5" in registry
assert "6 => Some(CoreDomainIdentity::D6" not in registry

print("D6-MECHANISM-LEDGER: PASS")
print("identity=64/64 executable=16/64 direct-selector=16 missing=48")
