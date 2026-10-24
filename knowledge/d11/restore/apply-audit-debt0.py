#!/usr/bin/env python3
"""सिद्ध: restore audit host_debt=0."""
from pathlib import Path
import base64, zlib, subprocess
def root():
    try: return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"], text=True).strip())
    except Exception: return Path(__file__).resolve().parents[3]
here=Path(__file__).parent
whole=here/"audit-debt0.zlib.b64"
if whole.is_file():
    blob=whole.read_text().strip()
else:
    p1=(here/"audit-debt0.part1.b64").read_text().strip()
    p2s="".join(p.read_text().strip() for p in sorted(here.glob("audit-debt0.p2s*.b64")))
    if not p2s:
        p2=(here/"audit-debt0.part2.b64")
        p2s=p2.read_text().strip() if p2.is_file() else ""
    blob=p1+p2s
out=root()/"tests"/"test_audit_all_lisp_triplets.py"
out.write_bytes(zlib.decompress(base64.b64decode(blob)))
print("restored", out, out.stat().st_size)
