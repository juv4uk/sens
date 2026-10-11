#!/usr/bin/env python3
import json
from pathlib import Path

# У режимі -O Python прибирає assert: не можна підтверджувати D9 без перевірок.
if not __debug__:
    raise SystemExit("D9-CURRENT-AUTHORITY: BLOCKED — Python -O вимикає перевірки")

root=Path(__file__).resolve().parents[1]
d9=json.loads((root/"knowledge/d9-ratified.json").read_text(encoding="utf-8"))
source=json.loads((root/"knowledge/d9-v1-gauge-fixed-candidate.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
contract=(root/"contracts/d9-ratification.lisp").read_text(encoding="utf-8")
foundation_contract=(root/"contracts/d1-d9-foundation-ratification.lisp").read_text(encoding="utf-8")
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")
domain_identity=(root/"crates/sens/src/domain_identity.rs").read_text(encoding="utf-8")

assert d9["status"]=="owner-ratified"
assert d9["authority"]=="#4008"
assert d9["domain"]=="D9" and d9["width"]==9
assert d9["capacity"]==512 and d9["occupancy"]==512 and d9["distinct_residents"]==512
assert len(d9["residents"])==512
assert set(d9["residents"])=={f"{i:09b}" for i in range(512)}
assert len(set(d9["residents"].values()))==512

source_map={row["coordinate"]:row["semantic_name"] for row in source["rows"]}
assert d9["residents"]==source_map

assert d9["coordinate_basis"]=={
    "PROVED-SELECTOR-GENERATOR":128,
    "OWNER-RATIFIED-S4-GAUGE":384,
}

basis=[row["coordinate_basis"] for row in d9["rows"]]
assert basis.count("proved-selector-generator")==128
assert basis.count("owner-ratified-s4-gauge-choice")==384

assert foundation["authority"]=="#4008"
assert foundation["current_domains"]==["D1","D2","D3","D4","D5","D6","D7","D8","D9"]
assert foundation["research_domains"]==[]
assert foundation["domains"]["D9"]["residents"]==d9["residents"]

assert "(owner-ratification . #4008)" in contract
assert "(width . #d9)" in contract
assert "(capacity . #d512)" in contract
assert "(occupancy . #d512)" in contract
assert "(distinct-residents . #d512)" in contract
assert "(current-domains . (D1 D2 D3 D4 D5 D6 D7 D8 D9))" in foundation_contract

assert "(minor . 8)" in lang
assert "Contract 11.8" in lang
assert "Core.D9 is OWNER-RATIFIED 512/512 under #4008" in lang
assert "D9  full compact 512/512" in current

# Semantic authority, identity materialization and callability remain separate.
# W9 now materializes exact D9 identity, while generic callability remains
# explicitly fail-closed.
assert "D1-D9 мають чинну семантичну authority згідно з Contract 11.8" in domain_identity
assert "D9(CoreD9)" in domain_identity
assert "Self::D9(_) => None" in domain_identity
assert "W1-W8 keep the one-byte fast path; D9 uses the exact non-truncating W9 carrier." in domain_identity

print("D9-CURRENT-AUTHORITY: PASS")
print("occupancy=512/512 distinct=512 selector=128 s4-gauge=384")
print("runtime=W1-W9 exact identity; D9 generic callability=fail-closed")
