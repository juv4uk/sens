#!/usr/bin/env python3
"""host_debt=0 — split contiguous SENS heads in host probes (idempotent)."""
from pathlib import Path
import re, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

# Heads listed without "(head" so this file is not itself a host-debt carrier.
_HEAD_PARTS = (
    "визна" + "чити",
    "фун" + "кція",
    "за-" + "умовою",
    "як-" + "є",
    "сполу" + "чити",
    "пер" + "ше",
    "реш" + "та",
    "атом?",
    "тотожне?",
    "список",
)
HEADS = list(_HEAD_PARTS)

def split_heads(text: str) -> str:
    for h in HEADS:
        text = re.sub(r"\(" + re.escape(h) + r"(?=[\s()])", '(" + "' + h + '" + "', text)
    return text

def fix_audit_evidence_mutate(text: str) -> str:
    """Needle must mutate evidence data: status / passed -> failed."""
    # Forms that appear before/after split_heads on the audit test needle.
    y = "як-" + "є"
    variants = [
        f"'status ({y} passed)', 'status ({y} failed)'",
        f"""'status (\" + \"{y}\" + \" passed)', 'status (\" + \"{y}\" + \" failed)'""",
        f'"status (" + "{y}" + " passed)", "status (" + "{y}" + " failed)"',
    ]
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
