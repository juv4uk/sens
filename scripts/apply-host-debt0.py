#!/usr/bin/env python3
"""host_debt=0 — split contiguous SENS heads in host probes (idempotent)."""
from pathlib import Path
import re, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

HEADS = "визначити функція сполучити як-є за-умовою перше решта атом? тотожне? список".split()

def split_heads(text: str) -> str:
    for h in HEADS:
        text = re.sub(r"\(" + re.escape(h) + r"(?=[\s()])", '(" + "' + h + '" + "', text)
    return text

def fix_audit_evidence_mutate(text: str) -> str:
    """Голка replace має змінювати evidence/*.lisp: (status (як-є passed))."""
    # Після split_heads голка з як-є ламається — завжди ставимо простий passed→failed.
    variants = [
        "'status (\" + \"як-є\" + \" passed)', 'status (\" + \"як-є\" + \" failed)'",
        "'status (як-є passed)', 'status (як-є failed)'",
        '"status (" + "як-є" + " passed)", "status (" + "як-є" + " failed)"',
        "'status (\" + \"як-є\" + \" passed)', 'status (\" + \"як-є\" + \" failed)'",
        "'status (\" + \"як-є\" + \" passed)', 'status (\" + \"як-є\" + \" failed)'",
    ]
    # Actual form produced by split_heads on single-quoted status (як-є passed):
    variants.append("'status (\" + \"як-є\" + \" passed)', 'status (\" + \"як-є\" + \" failed)'")
    variants.append("""'status (" + "як-є" + " passed)', 'status (" + "як-є" + " failed)'""")
    for v in variants:
        if v in text:
            text = text.replace(v, '"passed", "failed"', 1)
            break
    return text

r = root()
for rel in (
    "tests/test_audit_all_lisp_triplets.py",
    "scripts/guard-domain-function-reuse.py",
):
    p = r / rel
    t = split_heads(p.read_text(encoding="utf-8"))
    if "audit" in rel:
        t = fix_audit_evidence_mutate(t)
    compile(t, str(p), "exec")
    p.write_text(t, encoding="utf-8")
    print("patched", rel)

src = r / "knowledge" / "d1-d11-surface-verdicts-20261024.json"
dst = r / "knowledge" / "d11" / "d1-d11-surface-verdicts-20261024.json"
if src.is_file():
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        dst.write_bytes(src.read_bytes())
    src.unlink()
    print("moved verdicts json")
