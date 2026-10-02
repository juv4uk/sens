#!/usr/bin/env python3
"""#2135 — diff-scope the repo tooling inventory gate.

`scripts/check-repo-tooling-inventory.lisp` enumerates *all* of `scripts/` and
flags every entry that is not registered. That is right for a nightly audit and
wrong for a pull request: any lane that adds an unregistered script reddens
every other lane's PR (the offender changed across three runs:
research-2018-status-check.py -> research-2019-seed-necessity.py ->
research-2018-layer0-check.py).

This helper does not touch the Lisp gate. It builds a *diff-scoped root* in
which the gate sees only what this PR changed:

  <out>/scripts/                      only the changed script files
  <out>/knowledge/repo-tooling-inventory.lisp
                                      only the rows for those scripts
  <out>/*  and  <out>/knowledge/*     everything else symlinked from the repo

Run the existing gate inside <out> and it judges this PR alone. A foreign
unregistered script is not present in <out>/scripts, so it cannot redden the PR;
a script this PR adds without registering is present, and the scoped inventory
has no row for it, so the gate still refuses it. The nightly run keeps using the
repo root unchanged.

Usage
-----
    python3 scripts/tooling-inventory-diff-scope.py \
        --changed changed.txt --repo . --out /tmp/scoped
    python3 scripts/tooling-inventory-diff-scope.py --self-test
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys

INVENTORY = os.path.join("knowledge", "repo-tooling-inventory.lisp")
# The gate script itself lives under scripts/ and must stay visible in the
# scoped root, or the gate cannot be loaded at all. It is unchanged and
# registered, so keeping it does not widen the PR's own scope.
KEEP = ["scripts/check-repo-tooling-inventory.lisp"]
TOOL_LINE = re.compile(r'\(tool\s+\(path\s+"([^"]+)"\)')
STATUS_LETTERS = {"A", "C", "D", "M", "R", "T", "U", "X", "B"}


def parse_changed(text: str):
    """Yield changed paths; accepts `git diff --name-only` or `--name-status`."""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "\t" in line:
            fields = line.split("\t")
            head = fields[0].strip()
            if head and all(c in STATUS_LETTERS or c.isdigit() for c in head):
                status = head[0]
                if status == "R" and len(fields) >= 3:
                    yield fields[2].strip()
                elif len(fields) >= 2:
                    yield fields[1].strip()
                continue
        yield line


def split_bundled(line: str):
    """Some rows share one physical line, joined by literal `\\n` sequences."""
    return line.split("\\n")


def inventory_header_and_rows(path: str):
    """Return (header_lines, [(raw_line, {tool_path, ...}), ...])."""
    header, rows, seen_about = [], [], False
    for line in open(path, encoding="utf-8").read().splitlines():
        paths = {m.group(1) for m in (TOOL_LINE.match(p) for p in split_bundled(line)) if m}
        if paths:
            rows.append((line, paths))
        elif not rows:
            header.append(line)
            if line.strip().startswith("(about"):
                seen_about = True
    if not seen_about:
        raise SystemExit(f"diff-scope: {path} has no (about ...) block; refusing to guess")
    return header, rows


def scoped_row_lines(rows, scripts):
    """Keep only the sub-entries whose path is in the changed set."""
    wanted = set(scripts)
    kept = []
    for raw, paths in rows:
        parts = [p for p in split_bundled(raw)
                 if (TOOL_LINE.match(p) and TOOL_LINE.match(p).group(1) in wanted)]
        if parts:
            kept.append("\\n".join(parts))
    return kept


def changed_scripts(changed, repo):
    out = []
    for p in changed:
        if p.startswith("scripts/") and os.path.isfile(os.path.join(repo, p)):
            out.append(p)
    return sorted(set(out))


def link_children(src, dst, skip=()):
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if name in skip:
            continue
        target = os.path.join(dst, name)
        if os.path.lexists(target):
            continue
        os.symlink(os.path.abspath(os.path.join(src, name)), target)


def build(repo, out, scripts, keep=()):
    if os.path.lexists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    link_children(repo, out, skip=("scripts", "knowledge"))
    link_children(os.path.join(repo, "knowledge"), os.path.join(out, "knowledge"),
                  skip=(os.path.basename(INVENTORY),))

    present = sorted(set(scripts) | set(keep))
    os.makedirs(os.path.join(out, "scripts"), exist_ok=True)
    for p in present:
        dest = os.path.join(out, p)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(os.path.join(repo, p), dest)

    header, rows = inventory_header_and_rows(os.path.join(repo, INVENTORY))
    kept = scoped_row_lines(rows, present)
    with open(os.path.join(out, INVENTORY), "w", encoding="utf-8") as fh:
        fh.write("\n".join(header) + "\n")
        for line in kept:
            fh.write(line + "\n")
    return len(rows), len(kept), len(present)


def run(changed_path, repo, out, keep=KEEP):
    text = sys.stdin.read() if changed_path == "-" else open(changed_path, encoding="utf-8").read()
    scripts = changed_scripts(parse_changed(text), repo)
    total, kept, present = build(repo, out, scripts, keep=keep)
    print(f"(tooling-inventory-diff-scope (mode diff) (changed-scripts {len(scripts)}) "
          f"(kept {present - len(scripts)}) (scoped-rows {kept} of {total}) (out {out}))")
    for p in scripts:
        print(f"  changed-script {p}")
    for p in sorted(set(keep) - set(scripts)):
        print(f"  kept-script {p}")
    return 0


# --- self-test ---------------------------------------------------------------

SELFTEST_INVENTORY = """; synthetic inventory for the self-test
; Це governance metadata.

(about
  (schema repo-tooling-inventory/1)
  (issue #b101111110))

(tool (path "scripts/registered.py") (kind check) (language python) (role r) (lifecycle transitional) (callers unknown) (authority-source unknown) (migration-issue #b1001100) (replacement ()) (removal-condition x))
(tool (path "scripts/foreign.py") (kind check) (language python) (role f) (lifecycle transitional) (callers unknown) (authority-source unknown) (migration-issue #b1001100) (replacement ()) (removal-condition x))
(tool (path "scripts/check-repo-tooling-inventory.lisp") (kind check) (language lisp) (role gate) (lifecycle active) (callers unknown) (authority-source unknown) (migration-issue ()) (replacement ()) (removal-condition x))
"""


def self_test():
    import tempfile
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        repo = os.path.join(tmp, "repo")
        os.makedirs(os.path.join(repo, "scripts"))
        os.makedirs(os.path.join(repo, "knowledge"))
        os.makedirs(os.path.join(repo, "lib"))
        open(os.path.join(repo, "lib", "core.lisp"), "w").write("; core\n")
        open(os.path.join(repo, INVENTORY), "w").write(SELFTEST_INVENTORY)
        for name in ("registered.py", "mine-unregistered.py", "foreign.py",
                     "check-repo-tooling-inventory.lisp"):
            open(os.path.join(repo, "scripts", name), "w").write("# script\n")

        changed = ("scripts/registered.py\nscripts/mine-unregistered.py\n"
                   "lib/core.lisp\nREADME.md\n")
        out = os.path.join(tmp, "scoped")
        scripts = changed_scripts(parse_changed(changed), repo)
        keep = ["scripts/check-repo-tooling-inventory.lisp"]
        total, kept, present = build(repo, out, scripts, keep=keep)

        got_scripts = sorted(os.listdir(os.path.join(out, "scripts")))
        ok = got_scripts == ["check-repo-tooling-inventory.lisp",
                             "mine-unregistered.py", "registered.py"]
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] only changed scripts are visible: {got_scripts}")

        ok = "foreign.py" not in got_scripts
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] a foreign script cannot redden the PR")

        scoped = open(os.path.join(out, INVENTORY), encoding="utf-8").read()
        rows = [m.group(1) for m in TOOL_LINE.finditer(scoped)]
        ok = rows == ["scripts/registered.py", "scripts/check-repo-tooling-inventory.lisp"]
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] scoped inventory keeps changed rows plus the gate: {rows}")

        ok = "(about" in scoped
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] scoped inventory keeps the (about ...) block")

        ok = kept == 2 and total == 3 and present == 3
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] row accounting ({kept} of {total}, present {present})")

        ok = os.path.islink(os.path.join(out, "lib"))
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] the rest of the tree is symlinked, not copied")

        ok = (os.path.islink(os.path.join(out, "knowledge", "other.lisp")) is False
              and os.path.isfile(os.path.join(out, INVENTORY)))
        failures += 0 if ok else 1
        print(f"  [{'ok' if ok else 'FAIL'}] the scoped inventory is a real file in knowledge/")

    if failures:
        print(f"tooling-inventory-diff-scope-selftest-failed ({failures})")
        return 1
    print("(tooling-inventory-diff-scope-selftest-ok (7 cases))")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed", default="-")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="/tmp/tooling-inventory-scoped")
    ap.add_argument("--keep", action="append", default=None,
                    help="script the gate needs in the scoped root (repeatable)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return run(args.changed, args.repo, args.out, keep=args.keep or KEEP)


if __name__ == "__main__":
    sys.exit(main())
