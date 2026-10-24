#!/usr/bin/env python3
"""सूत्रधार: відновити всі host_debt=0 файли з bundle."""
from pathlib import Path
import base64, zlib, json, subprocess
def root():
    try: return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"], text=True).strip())
    except Exception: return Path(__file__).resolve().parents[3]
here=Path(__file__).parent
whole=here/"host-debt-bundle.zlib.b64"
blob=whole.read_text().strip() if whole.is_file() else "".join(
    p.read_text().strip() for p in sorted(here.glob("host-debt-bundle.part*.b64")))
data=json.loads(zlib.decompress(base64.b64decode(blob)).decode())
r=root()
for rel, b64 in data.items():
    path=r/rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(zlib.decompress(base64.b64decode(b64)))
    print("restored", rel, path.stat().st_size)
