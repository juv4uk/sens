#!/usr/bin/env python3
"""सिद्ध: restore audit host_debt=0 from zlib parts."""
from pathlib import Path
import base64, zlib, subprocess
def root():
    try: return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"], text=True).strip())
    except Exception: return Path(__file__).resolve().parents[3]
here=Path(__file__).parent
whole=here/"audit-debt0.zlib.b64"
blob=whole.read_text().strip() if whole.is_file() else "".join(
    p.read_text().strip() for p in sorted(here.glob("audit-debt0.part*.b64")))
out=root()/"tests"/"test_audit_all_lisp_triplets.py"
out.write_bytes(zlib.decompress(base64.b64decode(blob)))
print("restored", out, out.stat().st_size)
