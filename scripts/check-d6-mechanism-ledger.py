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
identity = (root / "crates/sens/src/domain_identity.rs").read_text(encoding="utf-8")
d6_arithmetic = (root / "crates/sens/src/eval/d6_arithmetic.rs").read_text(encoding="utf-8")
witness = (root / "crates/sens/tests/d6_add1_sub1_mechanisms.rs").read_text(encoding="utf-8")

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
assert ledger["executable_coverage"] == {"count": 2, "total": 64, "basis": "current admitted exact-domain runtime routes"}
assert counts["LOWER_DOMAIN_COMPOSITION"] == 2
assert counts["MISSING"] == 62
assert {
    bits for bits, row in rows.items()
    if row["mechanism_status"] == "LOWER_DOMAIN_COMPOSITION"
} == {"001110", "001111"}

# Current proof: exactly two D6 residents have callable/mechanism admission.
assert "0b001110 | 0b001111" in identity
assert "mod d6_arithmetic;" in (root / "crates/sens/src/eval/mod.rs").read_text(encoding="utf-8")
assert "super::d6_arithmetic::invoke" in canon
assert "0b001110 => d5(0b01010)" in d6_arithmetic
assert "0b001111 => d5(0b01011)" in d6_arithmetic
assert "only_d6_add1_and_sub1_project_to_callable_core" in witness
assert "equal_payloads_in_other_domains_do_not_inherit_d6_mechanisms" in witness

# No unrelated D6 mechanism is admitted through old selector/registry paths.
assert "if !(3..=5).contains(&width)" in selector
assert "let CoreDomainIdentity::D4(word) = identity else" in forms
assert "6 => Some(CoreDomainIdentity::D6" not in registry

print("D6-MECHANISM-LEDGER: PASS")
print("identity=64/64 executable=2/64 lower-domain-composition=2 missing=62")
