#!/usr/bin/env python3
import json
import re
from pathlib import Path

# Під -O Python усуває assert: жодної удаваної атестації D8.
if not __debug__:
    raise SystemExit("D8-CURRENT-AUTHORITY: BLOCKED — Python -O вимикає перевірки")

root=Path(__file__).resolve().parents[1]
d=json.loads((root/"knowledge/d8-ratified.json").read_text(encoding="utf-8"))
source=json.loads((root/"knowledge/d8-v2-gauge-fixed-candidate.json").read_text(encoding="utf-8"))
foundation=json.loads((root/"knowledge/d1-d9-foundation.json").read_text(encoding="utf-8"))
contract=(root/"contracts/d8-ratification.lisp").read_text(encoding="utf-8")
foundation_contract=(root/"contracts/d1-d9-foundation-ratification.lisp").read_text(encoding="utf-8")
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")
domain_identity=(root/"crates/sens/src/domain_identity.rs").read_text(encoding="utf-8")

assert d["status"]=="owner-ratified"
assert d["authority"]=="#3960"
assert d["domain"]=="D8" and d["width"]==8
assert d["capacity"]==256 and d["occupancy"]==256 and d["distinct_residents"]==256
assert len(d["residents"])==256
assert set(d["residents"])=={f"{i:08b}" for i in range(256)}
assert len(set(d["residents"].values()))==256

source_map={row["coordinate"]:row["semantic_name"] for row in source["rows"]}
assert d["residents"]==source_map

assert d["coordinate_basis"]=={
    "PROVED-SELECTOR-GENERATOR":64,
    "OWNER-RATIFIED-PRODUCT-INVARIANT":8,
    "OWNER-RATIFIED-ORBIT-GAUGE":7,
    "OWNER-RATIFIED-S4-GAUGE":177,
}

basis=[row["coordinate_basis"] for row in d["rows"]]
assert basis.count("proved-selector-generator")==64
assert basis.count("owner-ratified-product-invariant")==8
assert basis.count("owner-ratified-orbit-gauge-choice")==7
assert basis.count("owner-ratified-s4-gauge-choice")==177

assert foundation["authority"]=="#4008"
assert foundation["current_domains"]==["D1","D2","D3","D4","D5","D6","D7","D8","D9"]
assert foundation["research_domains"]==[]
assert foundation["domains"]["D8"]["residents"]==d["residents"]

assert "(owner-ratification . #3960)" in contract
assert "(width . #d8)" in contract
assert "(capacity . #d256)" in contract
assert "(occupancy . #d256)" in contract
assert "(distinct-residents . #d256)" in contract
assert "(current-domains . (D1 D2 D3 D4 D5 D6 D7 D8 D9))" in foundation_contract

assert '(minor . "0")' in lang  # оновлено: Contract 12.0 (було (minor . 9))
assert "Контракт 12.0" in lang  # оновлено: чинний коментар у Contract 12.0 (було Контракт 11.8)
assert "Core.D8 is OWNER-RATIFIED 256/256 under #3960" in lang
assert "D8  full compact — exact 8-bit keys (256/256)" in current

# Residency and callability remain separate. Ratification must not silently
# turn every D8 resident into a generic callable mechanism.
# rustfmt може перенести арму `=> { None }` на кілька рядків — звіряємо
# саму множину доменів у no-callability-армі, без залежності від формату.
_norm_ident = re.sub(r"\s+", " ", domain_identity)
assert "Self::D1(_) | Self::D2(_) | Self::D6(_) | Self::D7(_) | Self::D8(_) | Self::D10(_) =>" in _norm_ident
assert "D8 так само OWNER-RATIFIED #3960" in domain_identity

print("D8-CURRENT-AUTHORITY: PASS")
print("occupancy=256/256 distinct=256 selector=64 product=8 orbit-gauge=7 s4-gauge=177")
print("callability=separate/fail-closed")
