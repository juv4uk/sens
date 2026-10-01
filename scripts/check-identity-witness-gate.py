#!/usr/bin/env python3
"""#2133 — identity witness gate: no identity-law change without a witness.

For a language whose whole point is exact identity, a change to an
identity-authority file that arrives *without* an executable witness is the one
move that must not pass silently. This checker enforces that as a machine rule
instead of a promise.

Rule (narrow, not a blanket gate)
---------------------------------
If any changed path is an *identity-authority* path, then the SAME change set
must also add or modify at least one *witness* path. Deleting a witness does not
count. Nothing else is judged: a change that touches no identity-authority path
always passes.

Input
-----
A list of changed paths, either `git diff --name-status` output
(`M<TAB>path`, `A`, `D`, `R100<TAB>old<TAB>new`) or a plain one-path-per-line
list. That keeps the rule testable locally without git; CI just feeds it the
diff.

Usage
-----
    python3 scripts/check-identity-witness-gate.py --changed changed.txt
    git diff --name-status origin/main...HEAD | python3 scripts/check-identity-witness-gate.py
    python3 scripts/check-identity-witness-gate.py --self-test
"""

from __future__ import annotations

import argparse
import fnmatch
import sys

# Files whose change IS a change to the identity law.
IDENTITY_AUTHORITY = [
    "contracts/*identity*",
    "contracts/*.lock",
    "contracts/sid-*",
    "contracts/early-sid-lowering-contract.lisp",
    "contracts/core-universal-contract.lisp",
    "contracts/exact-q-binary-contract.lisp",
    "lib/surface/semantic-registry.lisp",
    "lib/function-table-mechanisms.lisp",
    "lib/mechanism-selector.lisp",
]

# Files that can carry the executable witness.
WITNESS = [
    "tests/*",
    "*/tests/*",
    "*witness*",
    "*fixtures*",
]

STATUS_LETTERS = {"A", "C", "D", "M", "R", "T", "U", "X", "B"}


def parse_changes(text: str):
    """Yield (status, path) pairs; status is '' when the input is a bare list."""
    for raw in text.splitlines():
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if "\t" in line:
            fields = line.split("\t")
            head = fields[0].strip()
            if head and all(ch in STATUS_LETTERS or ch.isdigit() for ch in head):
                status = head[0]
                if status == "R" and len(fields) >= 3:
                    yield status, fields[2].strip()          # the new path
                    yield "D", fields[1].strip()             # the old path is gone
                else:
                    yield status, fields[1].strip()
                continue
        yield "", line.strip()


def matches(path: str, patterns) -> bool:
    return any(fnmatch.fnmatch(path, pat) for pat in patterns)


def evaluate(changes):
    """Return (authority_hits, witness_added, violations)."""
    authority, witness = [], []
    for status, path in changes:
        if matches(path, IDENTITY_AUTHORITY):
            authority.append((status or "?", path))
        if matches(path, WITNESS) and status != "D":
            witness.append((status or "?", path))
    violations = []
    if authority and not witness:
        violations.append("identity-authority changed without an added/modified witness")
        for status, path in authority:
            violations.append(f"  authority: {status}\t{path}")
    return authority, witness, violations


def check(text: str):
    authority, witness, violations = evaluate(parse_changes(text))
    if violations:
        print("identity-witness-violation")
        for v in violations:
            print(f"  - {v}")
        print("  a witness is any added/modified path matching: "
              + ", ".join(WITNESS))
        return 1
    if authority:
        print(f"(identity-witness-ok (authority {len(authority)}) (witness {len(witness)}))")
    else:
        print("(identity-witness-ok (authority 0) (no-identity-authority-touched))")
    return 0


SELF_TEST = [
    # (name, input, expected_exit)
    ("witness only", "M\ttests/fixtures/semantic/eq-1bit-v1.lisp", 0),
    ("authority only", "M\tcontracts/text7-upc7.lock", 1),
    ("authority + witness", "M\tcontracts/text7-upc7.lock\nA\ttests/fixtures/semantic/text7-wire.lisp", 0),
    ("authority deleted only", "D\tcontracts/sid-kernel-witness-735.lisp", 1),
    ("authority + deleted witness", "M\tcontracts/text7-upc7.lock\nD\ttests/fixtures/semantic/eq-1bit-v1.lisp", 1),
    ("registry changed + witness", "M\tlib/surface/semantic-registry.lisp\nM\tcrates/sens/tests/semantic_authority.rs", 0),
    ("bare list, authority only", "contracts/core-universal-contract.lisp", 1),
    ("rename authority + added witness", "R100\tcontracts/old.lock\tcontracts/text7-upc7.lock\nA\ttests/fixtures/semantic/w.lisp", 0),
    ("unrelated change", "M\tsrc/lib.rs\nM\tREADME.md", 0),
]


def self_test() -> int:
    failures = 0
    for name, text, expected in SELF_TEST:
        authority, witness, violations = evaluate(parse_changes(text))
        got = 1 if violations else 0
        mark = "ok" if got == expected else "FAIL"
        if got != expected:
            failures += 1
        print(f"  [{mark}] {name}: exit {got} (expected {expected})")
    if failures:
        print(f"identity-witness-selftest-failed ({failures})")
        return 1
    print(f"(identity-witness-selftest-ok ({len(SELF_TEST)} cases))")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--changed", help="file with changed paths (default: stdin)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    text = open(args.changed, encoding="utf-8").read() if args.changed else sys.stdin.read()
    return check(text)


if __name__ == "__main__":
    sys.exit(main())
