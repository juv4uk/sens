#!/usr/bin/env python3
"""निर्वाह: restore audit+guard host_debt=0 from part*.b64 (mod4-safe)."""
from pathlib import Path
import base64, zlib, subprocess, re

def root():
    try:
        return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[3]

here = Path(__file__).parent
r = root()

def restore(name: str, dest: Path):
    whole = here / f"{name}-debt0.zlib.b64"
    if whole.is_file():
        blob = whole.read_text().strip()
    else:
        parts = sorted(
            [p for p in here.glob(f"{name}-debt0.part*.b64") if "p2s" not in p.name],
            key=lambda p: int(re.search(r"part(\d+)", p.name).group(1)),
        )
        blob = "".join(p.read_text().strip() for p in parts)
    dest.write_bytes(zlib.decompress(base64.b64decode(blob)))
    print("restored", dest, dest.stat().st_size)

restore("audit", r / "tests" / "test_audit_all_lisp_triplets.py")
restore("guard", r / "scripts" / "guard-domain-function-reuse.py")

src = r / "knowledge" / "d1-d11-surface-verdicts-20261024.json"
dst = r / "knowledge" / "d11" / "d1-d11-surface-verdicts-20261024.json"
if src.is_file():
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        dst.write_bytes(src.read_bytes())
    src.unlink()
    print("moved verdicts json")
