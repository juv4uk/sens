#!/usr/bin/env python3
"""Missing link: run the native SENS proofs named by the release-admission ledger.

Two pieces already exist but are not joined:

  * knowledge/release-admission-ledger.json -- entries whose ``f4_t5_execution``
    names a physical T5 execution as ``owner/repo@<sha>:scripts/prove-<name>.sh:<line>``;
  * scripts/prove-*.sh -- native SENS proofs that print ``NATIVE_SENS_PASS`` only
    when the real ``sens`` CLI reproduces the positive witness (D1:1) and the
    mutant (D1:0).

scripts/check-release-admission-ledger.py deliberately never runs those proofs
(there F1-F4 are format-only and ``uk_oracle_verified`` / ``release_admitted`` are
pinned to 0), so that gate can never go green on its own. This connector runs the
referenced proofs and reports, per ledger entry, whether the native SENS verdict
was actually reproduced.

It is fail-closed and additive:

  * it NEVER edits the ledger and NEVER edits the checker;
  * an entry becomes NATIVE-VERIFIED only when its ``scripts/prove-*.sh`` exits 0
    AND its stdout contains ``NATIVE_SENS_PASS``;
  * if ``target/debug/sens`` is missing or not executable it invents nothing: it
    prints ``NATIVE-CONNECTOR-BLOCKED: потрібен cargo build --locked -p sens-cli
    --bin sens`` and returns non-zero.

NATIVE-VERIFIED means "this entry's native proof ran"; it is NOT release
admission. Wiring this connector into the release gate is a separate, explicit
step that must keep fail-closed behaviour.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "knowledge" / "release-admission-ledger.json"
DEFAULT_REPO = "juv4uk/sens"
SCHEMA = "sens-release-admission-ledger/v1"
PASS_MARKER = "NATIVE_SENS_PASS"
BLOCKED_HINT = (
    "NATIVE-CONNECTOR-BLOCKED: потрібен "
    "cargo build --locked -p sens-cli --bin sens"
)

# Same reference grammar as scripts/check-release-admission-ledger.py.
REF = re.compile(
    r"(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{7,40}):"
    r"(?P<path>[^:\t\n]+):(?P<line>[1-9][0-9]*(?:-[1-9][0-9]*)?)\Z"
)
# Only canonical native proof scripts may be executed.
SCRIPT_PATH = re.compile(r"scripts/prove-[A-Za-z0-9_.-]+\.sh\Z")


def _emit_blocked(message: str) -> None:
    print(message, file=sys.stderr)


def cli_is_ready(cli: Path) -> bool:
    return cli.is_file() and os.access(cli, os.X_OK)


def run_proof(script: Path, cli: Path, root: Path, timeout: float) -> tuple[bool, str]:
    """Run one native proof. Verified only on exit 0 AND the terminal marker."""
    try:
        proc = subprocess.run(
            ["bash", str(script), str(cli)],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout після {timeout:g}s"
    except OSError as exc:
        return False, f"не вдалося запустити proof: {exc}"
    stdout = proc.stdout or ""
    if proc.returncode != 0:
        return False, f"proof exit={proc.returncode} (без {PASS_MARKER})"
    if PASS_MARKER not in stdout:
        return False, f"у виводі немає {PASS_MARKER}"
    return True, PASS_MARKER


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="run the native SENS proofs named by the release-admission ledger"
    )
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--cli", type=Path, default=None,
                        help="native sens CLI (default: <root>/target/debug/sens)")
    parser.add_argument("--repo", default=DEFAULT_REPO,
                        help="only f4 refs in this repo are executable locally")
    parser.add_argument("--timeout", type=float, default=300.0,
                        help="per-proof timeout in seconds")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    cli = (args.cli if args.cli is not None else root / "target" / "debug" / "sens").resolve()

    if not args.ledger.is_file():
        _emit_blocked(f"NATIVE-CONNECTOR-BLOCKED: ledger відсутній: {args.ledger}")
        return 2
    try:
        document = json.loads(args.ledger.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _emit_blocked(f"NATIVE-CONNECTOR-BLOCKED: ledger не читається: {exc}")
        return 2
    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        _emit_blocked(f"NATIVE-CONNECTOR-BLOCKED: невідома схема ledger (очікую {SCHEMA})")
        return 2
    entries = document.get("entries")
    if not isinstance(entries, list):
        _emit_blocked("NATIVE-CONNECTOR-BLOCKED: entries має бути списком")
        return 2

    print(f"NATIVE-CONNECTOR: ledger={args.ledger} entries={len(entries)} cli={cli}")

    # Fail-closed prerequisite: without a real native CLI nothing can be verified.
    if not cli_is_ready(cli):
        _emit_blocked(BLOCKED_HINT)
        print(f"NATIVE-CONNECTOR: cli не виконується: {cli}", file=sys.stderr)
        print(f"NATIVE-CONNECTOR-SUMMARY verified=0 blocked={len(entries)} "
              f"entries={len(entries)} missing=target/debug/sens")
        return 3

    verified = 0
    blocked: list[tuple[str, str]] = []
    for index, entry in enumerate(entries, start=1):
        sens = entry.get("sens") if isinstance(entry, dict) else None
        label = sens if isinstance(sens, str) else f"entry#{index}"
        f4 = entry.get("f4_t5_execution") if isinstance(entry, dict) else None
        if not isinstance(f4, str):
            blocked.append((label, "f4_t5_execution відсутній або не рядок"))
            continue
        match = REF.match(f4)
        if match is None:
            blocked.append((label, f"f4_t5_execution не owner/repo@COMMIT:path:line: {f4}"))
            continue
        if match.group("repo") != args.repo:
            blocked.append(
                (label, f"f4 вказує на інший репозиторій ({match.group('repo')}), "
                        "локально не виконується")
            )
            continue
        rel = match.group("path")
        if not SCRIPT_PATH.fullmatch(rel):
            blocked.append((label, f"f4 path не scripts/prove-*.sh: {rel}"))
            continue
        script = root / rel
        if script.is_symlink() or not script.is_file():
            blocked.append((label, f"proof script відсутній/не регулярний файл: {rel}"))
            continue
        try:
            scripts_dir = (root / "scripts").resolve(strict=True)
            resolved = script.resolve(strict=True)
        except OSError as exc:
            blocked.append((label, f"proof script недоступний: {rel} ({exc})"))
            continue
        if not resolved.is_relative_to(scripts_dir):
            blocked.append((label, f"proof script поза scripts/: {rel}"))
            continue

        ok, detail = run_proof(script, cli, root, args.timeout)
        if ok:
            verified += 1
            print(f"NATIVE-VERIFIED {label} script={rel} line={match.group('line')}")
        else:
            blocked.append((label, detail))
            print(f"NATIVE-BLOCKED {label} script={rel} reason={detail}")

    print(f"NATIVE-CONNECTOR-SUMMARY verified={verified} blocked={len(blocked)} "
          f"entries={len(entries)}")

    if blocked:
        for label, reason in blocked:
            _emit_blocked(f"NATIVE-CONNECTOR-BLOCKED-ENTRY {label}: {reason}")
        _emit_blocked(f"NATIVE-CONNECTOR-INCOMPLETE: verified={verified} blocked={len(blocked)}")
        return 1
    if not entries:
        _emit_blocked("NATIVE-CONNECTOR-BLOCKED: ledger порожній")
        return 1

    print(f"NATIVE-CONNECTOR-OK all {verified} entries NATIVE-VERIFIED "
          "(per-entry native proof; NOT release admission)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
