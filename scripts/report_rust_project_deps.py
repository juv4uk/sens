#!/usr/bin/env python3
"""Rust -> project dependency ledger + burndown ratchet (#5779).

Rust must be isolated: it reaches lib/, the language contract, contracts/ and
knowledge/ ONLY through the sterile Zig corridor. Until the Zig-only cutover is
done, the remaining direct dependencies are tracked here as a BURNDOWN:

  report  -- scan production Rust (crates/*/src/**, crates/*/build.rs) for every
             include_str! / fs::read of a project source and write the ledger
             research/rust-project-deps.json (file, target, kind, sha256);
  --check -- fail if the dependency set GREW vs the committed ledger. The set may
             only shrink (retire through the Zig corridor) or stay equal; a NEW
             direct dependency is a regression and fails closed.

`.zig-version` (the corridor pin) is not a project source. Exit 0 = no growth;
exit 1 = a new dependency was added (or --check with no ledger).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT_TREES = ("lib/", "contracts/", "knowledge/", "language-contract")
INCLUDE_RE = re.compile(r'include_str!\(\s*"([^"]+)"')
READ_RE = re.compile(r'fs::read(?:_to_string)?\(\s*"([^"]+)"')
GLOBS = ("crates/*/src/**/*.rs", "crates/*/build.rs")
LEDGER = "research/rust-project-deps.json"


def _is_project(target: str) -> bool:
    if target.endswith(".zig-version"):
        return False
    if target.startswith("../") or "/../" in target:
        return True
    return any(t in target for t in PROJECT_TREES)


def scan(root: Path) -> list[dict]:
    deps: list[dict] = []
    for pattern in GLOBS:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            if "/tests/" in f"/{rel}" or "/examples/" in f"/{rel}":
                continue
            src = path.read_text(encoding="utf-8", errors="replace")
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            for kind, rx in (("include_str", INCLUDE_RE), ("fs_read", READ_RE)):
                for m in rx.finditer(src):
                    if _is_project(m.group(1)):
                        deps.append({"file": rel, "kind": kind, "target": m.group(1),
                                     "file_sha256": sha})
    deps.sort(key=lambda d: (d["file"], d["kind"], d["target"]))
    return deps


def key(d: dict) -> str:
    return f'{d["file"]}|{d["kind"]}|{d["target"]}'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out", default=LEDGER)
    parser.add_argument("--plan", default="",
                        help="write a per-dependency retirement plan (JSON)")
    ns = parser.parse_args()
    root = Path(ns.root).resolve()

    current = scan(root)
    cur_keys = {key(d) for d in current}

    if ns.check:
        ledger_path = root / ns.out
        if not ledger_path.is_file():
            print(f"RUST_PROJECT_DEPS_NO_LEDGER (write one with report): {ns.out}")
            return 1
        known = {key(d) for d in json.loads(ledger_path.read_text(encoding="utf-8"))["deps"]}
        added = sorted(cur_keys - known)
        removed = sorted(known - cur_keys)
        if removed:
            print(f"burndown: {len(removed)} dependency(ies) retired through the corridor")
            for r in removed:
                print("  -", r)
        if added:
            print(f"RUST_PROJECT_DEPS_GREW {len(added)} new direct dependency(ies) -- "
                  "the Zig-only cutover may only shrink:")
            for a in added:
                print("  +", a)
            return 1
        print(f"RUST_PROJECT_DEPS_OK no growth ({len(cur_keys)} dependency(ies), "
              "burndown only)")
        return 0

    if ns.plan:
        plan = {"schema": "sens-rust-project-deps-plan/v1",
                "goal": "retire every direct Rust->project dependency through the caller-owned "
                        "Zig ABI (as lib/linter.lisp was, commit 526befd6c8)",
                "steps_per_dep": [
                    "1. move the source bytes out of Rust: no include_str!/fs::read of it",
                    "2. carry them through the caller-owned Zig ABI (opaque bytes + declared length)",
                    "3. prove byte identity via the Zig corridor, not a Rust-side parse",
                    "4. run scripts/report_rust_project_deps.py --check: the dep must show as burndown",
                ],
                "order": [d["target"] for d in current],
                "count": len(current)}
        pp = root / ns.plan
        pp.parent.mkdir(parents=True, exist_ok=True)
        pp.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {ns.plan}: {len(current)} retirement step(s)")

    ledger = {"schema": "sens-rust-project-deps/v1",
              "owner_rule": "Rust reaches lib/contract/contracts/knowledge ONLY via the "
                            "sterile Zig corridor; the remaining direct deps are a burndown",
              "count": len(current), "deps": current}
    out = root / ns.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {ns.out}: {len(current)} direct Rust->project dependency(ies)")
    by_file: dict[str, int] = {}
    for d in current:
        by_file[d["file"]] = by_file.get(d["file"], 0) + 1
    for f, n in sorted(by_file.items()):
        print(f"  {n:>2}  {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
