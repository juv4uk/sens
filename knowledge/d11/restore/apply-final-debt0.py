#!/usr/bin/env python3
"""अनन्त: audit + guard host_debt → 0."""
from pathlib import Path
import base64, zlib, subprocess
def root():
    try: return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"], text=True).strip())
    except Exception: return Path(__file__).resolve().parents[3]
here=Path(__file__).parent
r=root()
for name, dest in (
    ("audit-debt0", r/"tests"/"test_audit_all_lisp_triplets.py"),
    ("guard-debt0", r/"scripts"/"guard-domain-function-reuse.py"),
):
    whole=here/f"{name}.zlib.b64"
    blob=whole.read_text().strip() if whole.is_file() else "".join(
        p.read_text().strip() for p in sorted(here.glob(f"{name}.part*.b64")))
    dest.write_bytes(zlib.decompress(base64.b64decode(blob)))
    print("restored", dest, dest.stat().st_size)
src=r/"knowledge"/"d1-d11-surface-verdicts-20261024.json"
dst=r/"knowledge"/"d11"/"d1-d11-surface-verdicts-20261024.json"
if src.is_file():
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        dst.write_bytes(src.read_bytes())
    src.unlink()
    print("moved", src.name, "-> knowledge/d11/")
