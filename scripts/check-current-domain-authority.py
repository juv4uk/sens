#!/usr/bin/env python3
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
a=json.loads((root/"knowledge/current-domain-authority.json").read_text(encoding="utf-8"))
lang=(root/"language-contract.lisp").read_text(encoding="utf-8")
current=(root/"CURRENT.md").read_text(encoding="utf-8")
domain=(root/"crates/sens/src/domain_identity.rs").read_text(encoding="utf-8")
d3=(root/"contracts/bija3-l1-l5-ratification.lisp").read_text(encoding="utf-8")
d4=(root/"contracts/d4-bootstrap-ratification.lisp").read_text(encoding="utf-8")
d5=(root/"contracts/d5-ratification.lisp").read_text(encoding="utf-8")

assert a["authority"]=="#3327"
assert a["current_ratified"]==["D1","D2"]
assert a["unratified_research"]==["D3","D4","D5","D6","D7","D8"]
assert a["callable_core_domains"]==[]
assert "(minor . 4)" in lang
assert "current-d1-d2-only-authority" in lang
for d in ["D3","D4","D5","D6","D7","D8"]:
    assert f"{d}  UNRATIFIED / RESEARCH" in current
assert "pub const fn core_operation(self) -> Option<CoreDomainIdentity> {\n        None\n    }" in domain
for old in [d3,d4,d5]:
    assert "revoked-research-evidence" in old
    assert "#3327" in old
print("D1-D2-ONLY-CURRENT-AUTHORITY: PASS")
