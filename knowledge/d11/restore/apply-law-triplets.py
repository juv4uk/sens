#!/usr/bin/env python3
"""Відновити трійки tests/semantic/закон-* (.sens + view). Ануграха — до релізу."""
from pathlib import Path
import base64, zlib, json, subprocess

def repo_root() -> Path:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True
        ).strip()
        return Path(out)
    except Exception:
        return Path(__file__).resolve().parents[3]

here = Path(__file__).parent
root = repo_root()
whole = here / "law-triplets.zlib.b64"
if whole.is_file():
    blob = whole.read_text().strip()
else:
    blob = (
        (here / "law-triplets.part1.b64").read_text().strip()
        + (here / "law-triplets.part2.b64").read_text().strip()
    )
data = json.loads(zlib.decompress(base64.b64decode(blob)).decode("utf-8"))
out = root / "tests" / "semantic"
out.mkdir(parents=True, exist_ok=True)
n = 0
for stem, item in data.items():
    (out / f"{stem}.sens").write_bytes(base64.b64decode(item["sens_b64"]))
    (out / stem).write_text(item["view"], encoding="utf-8")
    n += 1
print(f"restored {n} law triplets into {out}")
