#!/usr/bin/env python3
"""UNGUARDING ratchet: a guard that cannot fail is itself a failure (#5777).

Third placeholder episode (migration markers -> sterile guard -> migration-gate).
Each treatment was honest; the root was not burned: a blocked agent commits a
DUMMY gate. This ratchet is the machine means so a dummy never reaches main.

Scope is the critical path (corridor / isolation / migration / release), not
every historical scripts/check_*.py.

U1  no executable stub body on the critical path;
U2  critical check_*.py have negative-control tests;
U3  those controls pass;
U4  migration-zig-gate.py --self-test succeeds (not a thin loader of missing halves).

Exit 0 = GUARDS_REAL_OK; exit 1 = UNGUARDING.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CRITICAL_CHECK_GUARDS = (
    "check_sterile_zig_corridor.py",
    "check_rust_sens_zig_corridor.py",
    "check_rust_sens_corridor_coverage.py",
    "check_corridor_axiom_binding.py",
    "check_rust_isolated_only_zig.py",
    "check_guards_are_real.py",
)

CRITICAL_OTHER = (
    "migration-zig-gate.py",
    "report_rust_zig_sens_boundary.py",
    "release_go_gate.py",
)

SOLE_STUB_RE = re.compile(
    r"^\s*(?:PLACEHOLDER(?:\d|_GATE|_YML)?|TODO:\s*implement)\s*$",
    re.I,
)
STUB_TOKEN_RE = re.compile(
    r"MIGRATION_ZIG_GATE_PLACEHOLDER_RESTORE_PENDING|"
    r"SEE_REPO_FOR_FULL_BODY|"
    r"INCOMPLETE_GATE_BODY|"
    r"PLACEHOLDER_GATE|"
    r"PLACEHOLDER_YML"
)


def _code_without_docs(src: str) -> str:
    out = re.sub(r'"""[\s\S]*?"""', '""', src)
    out = re.sub(r"'''[\s\S]*?'''", "''", out)
    lines = [ln for ln in out.splitlines() if not ln.strip().startswith("#")]
    return "\n".join(lines)


def _is_stub_source(src: str) -> bool:
    if SOLE_STUB_RE.match(src.strip()):
        return True
    body = _code_without_docs(src)
    if STUB_TOKEN_RE.search(body):
        return True
    if "base64.b64decode" in body and (
        "_mg_chunk_" in body or "_migration_zig_gate_body" in body
    ):
        return True
    return False


def _test_module_for(name: str, root: Path):
    primary = root / "tests" / f"test_{name}"
    if primary.is_file():
        return primary
    if name == "check_sterile_zig_corridor.py":
        alt = root / "tests" / "test_sterile_zig_corridor.py"
        if alt.is_file():
            return alt
    return None


def check(root: Path):
    problems = []
    scripts = root / "scripts"

    for name in CRITICAL_CHECK_GUARDS:
        path = scripts / name
        rel = f"scripts/{name}"
        if not path.is_file():
            problems.append(f"UNGUARDING: missing critical guard {rel}")
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        if name == "check_guards_are_real.py":
            continue
        if _is_stub_source(src):
            problems.append(
                f"UNGUARDING: {rel} carries an executable PLACEHOLDER/stub body"
            )

        test = _test_module_for(name, root)
        if test is None:
            problems.append(
                f"UNGUARDING: {rel} has no negative-control test "
                f"(tests/test_{name} missing)"
            )
            continue

        mod = f"tests.{test.stem}"
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "-v", mod],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            problems.append(f"UNGUARDING: {rel} controls could not run: {exc}")
            continue
        if proc.returncode != 0:
            problems.append(
                f"UNGUARDING: {rel} negative controls do not pass "
                f"(exit={proc.returncode})"
            )

    for name in CRITICAL_OTHER:
        path = scripts / name
        rel = f"scripts/{name}"
        if not path.is_file():
            problems.append(f"UNGUARDING: missing critical path script {rel}")
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        if _is_stub_source(src):
            problems.append(
                f"UNGUARDING: {rel} carries an executable PLACEHOLDER/stub body"
            )

    gate = scripts / "migration-zig-gate.py"
    if gate.is_file() and not _is_stub_source(
        gate.read_text(encoding="utf-8", errors="replace")
    ):
        try:
            proc = subprocess.run(
                [sys.executable, str(gate), "--self-test"],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=180,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            problems.append(
                f"UNGUARDING: migration-zig-gate.py --self-test could not run: {exc}"
            )
        else:
            if proc.returncode != 0:
                problems.append(
                    f"UNGUARDING: migration-zig-gate.py --self-test failed "
                    f"(exit={proc.returncode})"
                )

    for debris in sorted(scripts.glob("_mg_chunk_*.b64")):
        text = debris.read_text(encoding="utf-8", errors="replace").strip()
        if SOLE_STUB_RE.match(text) or text.startswith("PLACEHOLDER"):
            problems.append(
                f"UNGUARDING: {debris.relative_to(root).as_posix()} "
                f"is a PLACEHOLDER chunk"
            )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".")
    ns = parser.parse_args()
    root = Path(ns.root).resolve()
    try:
        problems = check(root)
    except OSError as exc:
        print(f"UNGUARDING: {exc}", flush=True)
        return 1
    if problems:
        print(
            f"UNGUARDING {len(problems)} dummy gate(s) -- a guard that cannot fail:",
            flush=True,
        )
        for problem in problems:
            print(" -", problem, flush=True)
        return 1
    print(
        "GUARDS_REAL_OK critical-path guards prove they can fail closed",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
