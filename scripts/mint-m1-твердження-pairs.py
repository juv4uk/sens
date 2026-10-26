#!/usr/bin/env python3
"""M1 твердження: materialize selftest .sens from knowledge/d11/restore/m1-твердження/.

View: якщо quarters відсутні —
  python3 scripts/migrate-one-to-sens.py tests/semantic/твердження-самотест-law.lisp
"""
from pathlib import Path
import base64, subprocess

def root():
    try:
        return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    except Exception:
        return Path(__file__).resolve().parents[1]

STEM = "твердження-самотест-law"
r = root()
src = r / "knowledge" / "d11" / "restore" / "m1-твердження"
sem = r / "tests" / "semantic"
sb = base64.b64decode((src / f"{STEM}.sens.b64").read_text().strip())
(sem / f"{STEM}.sens").write_bytes(sb)
print("minted", STEM, ".sens", len(sb))
parts = ["part1a", "part1b", "part2a", "part2b"]
if all((src / f"{STEM}.view.{p}.b64").is_file() for p in parts):
    vb = base64.b64decode("".join(
        (src / f"{STEM}.view.{p}.b64").read_text().strip() for p in parts
    ))
    (sem / STEM).write_bytes(vb)
    print("minted", STEM, "view", len(vb))
else:
    print("view quarters відсутні — migrate-one-to-sens.py для extensionless view")
