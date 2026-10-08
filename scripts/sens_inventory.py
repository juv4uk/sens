#!/usr/bin/env python3
"""#4453 triple inventory: .lisp (uk) / .sens (T5) / extensionless view.

Classifies candidate sources, and for each admitted executable reports the
same-stem triple with SHAs and a typed-word digest:

    { path, kind, status, sha256(.lisp), sha256(.sens), sha256(view),
      typed_words_sha256, words }

Kinds: executable | declarative (schema/document head) | blocked (other reason).
Reuses the repo codec + migrator; no new codec/parser/domain table.

Usage: sens_inventory.py [root ...] [--json OUT]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import sens_t5_codec as C  # noqa: E402

SCHEMA_HEAD = re.compile(r"^[A-Za-z][\w./-]*/\d+$")
KNOWN_DECL = {"schema", "token"}


def head_of(text: str) -> str | None:
    for line in text.splitlines():
        line = line.split(";", 1)[0].strip()
        if line.startswith("("):
            m = re.match(r"\(\s*([^\s()]+)", line)
            if m:
                return m.group(1)
    return None


def classify(path: pathlib.Path) -> str:
    h = head_of(path.read_text(encoding="utf-8"))
    if h and (SCHEMA_HEAD.match(h) or h in KNOWN_DECL):
        return "declarative"
    return "executable"


def sha(p: pathlib.Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None


def migrate(path: pathlib.Path, outdir: pathlib.Path) -> pathlib.Path | None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/migrate-three-pass.py"),
         "--out", str(outdir), "--source-era", "legacy", str(path)],
        capture_output=True, text=True, cwd=str(ROOT))
    s = outdir / (path.stem + ".sens")
    return s if s.is_file() else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("roots", nargs="*", default=["lib", "tests/fixtures"])
    ap.add_argument("--json")
    ns = ap.parse_args()

    rows = []
    with tempfile.TemporaryDirectory() as td:
        outdir = pathlib.Path(td)
        for root in ns.roots:
            for p in sorted((ROOT / root).rglob("*.lisp")):
                rel = p.relative_to(ROOT).as_posix()
                kind = classify(p)
                row = {"path": rel, "kind": kind, "status": "declarative" if kind == "declarative" else "unknown",
                       "sha_lisp": sha(p)}
                if kind == "executable":
                    s = migrate(p, outdir)
                    if s is None:
                        row["status"] = "blocked"
                    else:
                        words = C.decode_bytes(s.read_bytes())
                        row["status"] = "admitted"
                        row["sha_sens"] = sha(s)
                        row["words"] = words
                        row["typed_words_sha256"] = hashlib.sha256(
                            "\n".join(words).encode()).hexdigest()
                rows.append(row)

    adm = [r for r in rows if r["status"] == "admitted"]
    decl = [r for r in rows if r["status"] == "declarative"]
    blk = [r for r in rows if r["status"] == "blocked"]
    print(f"scanned {len(rows)}: admitted={len(adm)} declarative={len(decl)} blocked={len(blk)}")
    for r in adm:
        print(f"  ADMITTED {r['path']}  words={len(r['words'])}  typed={r['typed_words_sha256'][:16]}")
    if ns.json:
        pathlib.Path(ns.json).write_text(json.dumps({"schema": "sens-triple-inventory/1", "rows": rows},
                                                    ensure_ascii=False, indent=1))
        print("wrote", ns.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
