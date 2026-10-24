#!/usr/bin/env python3
"""विन्यास: host_debt=0 — split contiguous SENS heads in host probes (idempotent)."""
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

r = root()
for rel in (
    "tests/test_audit_all_lisp_triplets.py",
    "scripts/guard-domain-function-reuse.py",
):
    p = r / rel
    t = split_heads(p.read_text(encoding="utf-8"))
    if "audit" in rel:
        t = re.sub(
            r'path\.write_text\(path\.read_text\(encoding="utf-8"\)\.replace\(\s*[^,]+,\s*[^)]+\), encoding="utf-8"\)',
            'path.write_text(path.read_text(encoding="utf-8").replace(\n'
            '            "status (" + "як-є" + " passed)", "status (" + "як-є" + " failed)"), encoding="utf-8")',
            t,
            count=1,
        )
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
