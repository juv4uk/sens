#!/usr/bin/env python3
"""UNGUARDING ratchet: a guard that cannot fail is itself a failure (#5777).

Third placeholder episode (migration markers -> sterile guard -> migration-gate).
Each time the treatment was honest, but the root was not burned out: an agent that
is blocked commits a DUMMY gate -- one that passes a deliberately-wrong input.
This is the machine means. A guard must PROVE it can fail:

U1  no PLACEHOLDER / stub marker in any scripts/check_*.py;
U2  every guard has a negative-control test tests/test_<guard>.py;
U3  that test actually PASSES (i.e. the guard fails closed on the wrong input);
U4  a deliberately-wrong input is NOT accepted: for every guard whose `check(root)`
    is callable with a mutated root, the guard must return a non-empty problem list
    on at least one mutation -- proven by U3's controls, asserted here by presence.

A guard that cannot demonstrate it fails is reported UNGUARDING and this ratchet
fails closed. Exit 0 = GUARDS_REAL_OK; exit 1 = UNGUARDING (a dummy gate exists).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

STUB_RE = re.compile(r"PLACEHOLDER|TODO:\s*implement|not\s+implemented|raise\s+NotImplementedError", re.I)


def check(root: Path) -> list[str]:
    problems: list[str] = []
    guards = sorted((root / "scripts").glob("check_*.py"))
    if not guards:
        return ["no scripts/check_*.py guards found"]
    for g in guards:
        rel = g.relative_to(root).as_posix()
        src = g.read_text(encoding="utf-8", errors="replace")

        # U1 -- a placeholder/stub is a dummy gate, never a guard.
        if STUB_RE.search(src):
            problems.append(f"UNGUARDING: {rel} carries a PLACEHOLDER/stub marker")

        # U2 -- a guard with no negative-control test cannot prove it fails closed.
        test = root / "tests" / f"test_{g.name}"
        if not test.is_file():
            problems.append(f"UNGUARDING: {rel} has no negative-control test "
                            f"(tests/test_{g.name} missing)")
            continue

        # U3 -- the controls must pass: the guard must actually fail on bad input.
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "-v", f"tests.test_{g.stem}"],
                cwd=str(root), capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            problems.append(f"UNGUARDING: {rel} controls could not run: {exc}")
            continue
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:] or [""]
            problems.append(f"UNGUARDING: {rel} negative controls do not pass "
                            f"(a guard that cannot fail): {tail[0][:90]}")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=str(Path(__file__).resolve().parents[1]))
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except OSError as exc:
        print(f"UNGUARDING: {exc}", flush=True)
        return 1
    if problems:
        print(f"UNGUARDING {len(problems)} dummy gate(s) -- a guard that cannot fail:",
              flush=True)
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print("GUARDS_REAL_OK every guard carries no placeholder, has negative controls, "
          "and those controls pass (each guard can fail)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
