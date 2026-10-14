#!/usr/bin/env python3
"""Fail-closed preparation gate: migration scripts \u2194 Zig physical codec.

Does NOT invent semantics. Does NOT admit programs. Does NOT write .lisp/.sens.

Runs the already-contracted mechanical checks the swarm needs before a
migration batch, in fixed order:

  1. ci_zig_purity          \u2014 no W8/Sens8/SID-8 contamination in *.zig
  2. check-domain-ladder-identity \u2014 width=identity on canonical surfaces
  3. migrate-exact-domain authority load \u2014 D3/D4 tables + owner ratification
  4. test_zig_codec_bridge  \u2014 physical T5 round-trip (optional if Zig absent
                              unless --require-zig)

Chronology / ratification history is documented, not re-derived here:
  docs/migration/semantic-chronology-handoff-2026-10-14.uk.md
  docs/migration/chronology-authority-handoff-2026-10-14.uk.md
  docs/zig-migration-scripts-handoff-2026-10-14.uk.md

Axiom reminder (language-core / owner):
  width of the binary key IS the domain address;
  Zig is a turnstile (physical transport), never the registry of meaning;
  historical W8 is provenance archive, not current identity.

Exit 0 only when every enabled step passes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_step(name: str, argv: list[str], *, cwd: Path = ROOT) -> dict:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        return {
            "step": name,
            "status": "FAIL",
            "exit": -1,
            "detail": f"{type(err).__name__}: {err}",
        }
    status = "PASS" if completed.returncode == 0 else "FAIL"
    tail = (completed.stdout or "")[-800:] + (completed.stderr or "")[-400:]
    return {
        "step": name,
        "status": status,
        "exit": completed.returncode,
        "detail": tail.strip()[-1200:],
    }


def load_exact_domain_authority() -> dict:
    """Import migrate-exact-domain and load owner tables (no write)."""
    path = SCRIPTS / "migrate-exact-domain.py"
    spec = importlib.util.spec_from_file_location("migrate_exact_domain", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load migrate-exact-domain.py")
    mod = importlib.util.module_from_spec(spec)
    # dataclasses need the module registered before exec_module
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    surfaces, legacy = mod.load_authority(ROOT)
    # Width axiom: every Identity.bits length equals domain N for DN.
    bad = []
    for key, identity in surfaces.items():
        width = int(identity.domain[1:])
        if len(identity.bits) != width:
            bad.append(f"{key}->{identity.domain}:{identity.bits}")
        if not set(identity.bits) <= {"0", "1"}:
            bad.append(f"{key}: non-binary bits")
    if bad:
        raise ValueError(f"exact-domain authority width axiom broken: {bad[:8]}")
    return {
        "step": "migrate-exact-domain-authority",
        "status": "PASS",
        "exit": 0,
        "detail": (
            f"surfaces={len(surfaces)} legacy_keys={len(legacy)} "
            f"width_axiom=PASS safe_old={sorted(mod.SAFE_OLD)}"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-zig",
        action="store_true",
        help="Fail if Zig 0.16.0 codec bridge cannot run (default: report SKIP).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Optional JSON report path.",
    )
    parser.add_argument(
        "--skip-ladder-identity",
        action="store_true",
        help="Skip heavy check-domain-ladder-identity (still runs purity + authority).",
    )
    args = parser.parse_args()

    steps: list[dict] = []

    steps.append(
        run_step(
            "ci_zig_purity",
            [sys.executable, str(SCRIPTS / "ci_zig_purity.py")],
        )
    )

    if not args.skip_ladder_identity:
        steps.append(
            run_step(
                "check-domain-ladder-identity",
                [sys.executable, str(SCRIPTS / "check-domain-ladder-identity.py")],
            )
        )

    try:
        steps.append(load_exact_domain_authority())
    except Exception as err:  # noqa: BLE001 \u2014 surface as step failure
        steps.append(
            {
                "step": "migrate-exact-domain-authority",
                "status": "FAIL",
                "exit": 1,
                "detail": str(err)[:1200],
            }
        )

    bridge = run_step(
        "test_zig_codec_bridge",
        [sys.executable, str(SCRIPTS / "test_zig_codec_bridge.py")],
    )
    if bridge["status"] == "FAIL" and not args.require_zig:
        detail = bridge.get("detail", "")
        if "ZIG_CODEC_UNAVAILABLE" in detail or "ZIG_CODEC_VERSION" in detail:
            bridge = {
                **bridge,
                "status": "SKIP",
                "detail": detail + " | use --require-zig in CI with install-zig",
            }
    steps.append(bridge)

    report = {
        "schema": "sens-migration-zig-gate/v1",
        "kind": "preparation-gate-not-semantic-oracle",
        "zig_pin": (ROOT / ".zig-version").read_text(encoding="utf-8").strip()
        if (ROOT / ".zig-version").is_file()
        else None,
        "handoff_docs": [
            "docs/zig-migration-scripts-handoff-2026-10-14.uk.md",
            "docs/migration/semantic-chronology-handoff-2026-10-14.uk.md",
            "docs/migration/chronology-authority-handoff-2026-10-14.uk.md",
        ],
        "axioms": [
            "width-equals-domain-address",
            "zig-is-turnstile-not-registry",
            "W8-is-historical-provenance-not-current-identity",
        ],
        "steps": steps,
    }

    failed = [s for s in steps if s["status"] == "FAIL"]
    report["verdict"] = "PASS" if not failed else "FAIL"

    for step in steps:
        print(
            f"MIGRATION_ZIG_GATE step={step['step']} "
            f"status={step['status']} exit={step['exit']}"
        )
        if step["status"] != "PASS" and step.get("detail"):
            for line in step["detail"].splitlines()[-8:]:
                print(f"  | {line}")

    print(f"MIGRATION_ZIG_GATE verdict={report['verdict']} steps={len(steps)}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
