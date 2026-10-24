#!/usr/bin/env python3
"""मोक्ष: restore audit+guard host_debt=0; fallback to live patch."""
from pathlib import Path
import base64, zlib, subprocess, re, sys

def root():
    try:
        return Path(subprocess.check_output(["git","rev-parse","--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[3]

here = Path(__file__).parent
r = root()

def restore_zlib(name: str, dest: Path) -> bool:
    whole = here / f"{name}-debt0.zlib.b64"
    try:
        if whole.is_file():
            blob = whole.read_text().strip()
        else:
            parts = sorted(
                [p for p in here.glob(f"{name}-debt0.part*.b64") if "p2s" not in p.name],
                key=lambda p: int(re.search(r"part(\d+)", p.name).group(1)),
            )
            if not parts:
                return False
            blob = "".join(p.read_text().strip() for p in parts)
        dest.write_bytes(zlib.decompress(base64.b64decode(blob)))
        print("restored", dest, dest.stat().st_size)
        return True
    except Exception as e:
        print("zlib path failed for", name, e)
        return False

ok_audit = restore_zlib("audit", r / "tests" / "test_audit_all_lisp_triplets.py")
ok_guard = restore_zlib("guard", r / "scripts" / "guard-domain-function-reuse.py")
if not (ok_audit and ok_guard):
    live = here / "patch-host-debt-live.py"
    print("fallback:", live)
    subprocess.check_call([sys.executable, str(live)], cwd=str(r))

src = r / "knowledge" / "d1-d11-surface-verdicts-20261024.json"
dst = r / "knowledge" / "d11" / "d1-d11-surface-verdicts-20261024.json"
if src.is_file():
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        dst.write_bytes(src.read_bytes())
    src.unlink()
    print("moved verdicts json")
