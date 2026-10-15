#!/usr/bin/env python3
"""Fail-closed preparation gate: migration scripts \u2194 Zig physical codec.

Does NOT invent semantics. Does NOT admit programs. Does NOT write .lisp/.sens.

Runs the already-contracted mechanical checks the swarm needs before a
migration batch, in fixed order:

  0. zig-pin                 \u2014 .zig-version == 0.16.0 and install-zig default
  1. ci_zig_purity           \u2014 no W8/Sens8/SID-8 contamination in *.zig
  2. check-domain-ladder-identity \u2014 width=identity on canonical surfaces
  3. migrate-exact-domain authority load \u2014 D3/D4 tables + owner ratification
  4. test_zig_codec_bridge   \u2014 REQUIRED physical T5 round-trip; --self-test is NOT a full gate

Chronology / ratification history is documented, not re-derived here:
  docs/migration/semantic-chronology-handoff-2026-10-14.uk.md
  docs/migration/chronology-authority-handoff-2026-10-14.uk.md
  docs/zig-migration-scripts-handoff-2026-10-14.uk.md

Axiom reminder (language-core / owner):
  width of the binary key IS the domain address;
  Zig is a turnstile (physical transport), never the registry of meaning;
  historical W8 is provenance archive, not current identity.

Full gate PASS requires every required step. --self-test returns SELF_TEST_ONLY\n(no transport evidence); incomplete full gate exits 2.
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


def check_zig_pin() -> dict:
    """Fail-closed: repository pin must stay on the transport codec version."""
    pin_path = ROOT / ".zig-version"
    if not pin_path.is_file() or pin_path.is_symlink():
        return {
            "step": "zig-pin",
            "status": "FAIL",
            "exit": 1,
            "detail": "missing regular .zig-version",
        }
    actual = pin_path.read_text(encoding="utf-8").strip()
    expected = "0.16.0"
    if actual != expected:
        return {
            "step": "zig-pin",
            "status": "FAIL",
            "exit": 1,
            "detail": f"ZIG_PIN_DRIFT expected={expected} actual={actual!r}",
        }
    action = ROOT / ".github" / "actions" / "install-zig" / "action.yml"
    if not action.is_file() or action.is_symlink():
        return {
            "step": "zig-pin",
            "status": "FAIL",
            "exit": 1,
            "detail": "missing regular install-zig action.yml",
        }
    # Read only inputs.version.default, not a coincidental token in comments
    # or some other action input. No YAML dependency is needed for this pin.
    section = None
    action_input = None
    defaults = []
    for line in action.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent == 0:
            section = value
            action_input = None
        elif section == "inputs:" and indent == 2:
            action_input = value
        elif (section == "inputs:" and action_input == "version:"
              and indent == 4 and value.startswith("default:")):
            defaults.append(value.split(":", 1)[1].strip().strip("'\\\""))
    if defaults != [expected]:
        return {
            "step": "zig-pin",
            "status": "FAIL",
            "exit": 1,
            "detail": f"install-zig inputs.version.default drift expected={expected} actual={defaults!r}",
        }
    return {
        "step": "zig-pin",
        "status": "PASS",
        "exit": 0,
        "detail": f"zig-pin={actual}",
    }


def load_exact_domain_authority() -> dict:
    """Import migrate-exact-domain and load owner tables (no write)."""
    path = SCRIPTS / "migrate-exact-domain.py"
    spec = importlib.util.spec_from_file_location("migrate_exact_domain", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load migrate-exact-domain.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    surfaces, legacy = mod.load_authority(ROOT)
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


REQUIRED_STEPS = (
    "zig-pin",
    "ci_zig_purity",
    "check-domain-ladder-identity",
    "migrate-exact-domain-authority",
    "test_zig_codec_bridge",
)


def gate_verdict(steps: list[dict], *, self_test: bool, skip_ladder: bool) -> str:
    """Never call a skipped, missing or failed physical Zig proof a PASS."""
    if any(step["status"] == "FAIL" for step in steps):
        return "FAIL"
    if self_test:
        return "SELF_TEST_ONLY"
    if skip_ladder:
        return "INCOMPLETE"
    if [step["step"] for step in steps] != list(REQUIRED_STEPS):
        return "INCOMPLETE"
    if any(step["status"] != "PASS" for step in steps):
        return "INCOMPLETE"
    return "PASS"


def verdict_self_test() -> None:
    """Pure synthetic negatives; they never pretend Zig actually executed."""
    passing = [{"step": name, "status": "PASS"} for name in REQUIRED_STEPS]
    assert gate_verdict(passing, self_test=False, skip_ladder=False) == "PASS"
    missing = passing[:-1]
    assert gate_verdict(missing, self_test=False, skip_ladder=False) == "INCOMPLETE"
    skipped = [*passing[:-1], {"step": REQUIRED_STEPS[-1], "status": "SKIP"}]
    assert gate_verdict(skipped, self_test=False, skip_ladder=False) == "INCOMPLETE"
    unavailable = [*passing[:-1], {"step": REQUIRED_STEPS[-1], "status": "FAIL"}]
    assert gate_verdict(unavailable, self_test=False, skip_ladder=False) == "FAIL"
    assert gate_verdict(passing, self_test=False, skip_ladder=True) == "INCOMPLETE"
    assert gate_verdict(skipped, self_test=True, skip_ladder=True) == "SELF_TEST_ONLY"
    print("MIGRATION_ZIG_GATE_VERDICT_SELF_TEST_PASS negative_cases=5")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-zig",
        action="store_true",
        help="Compatibility option: Zig 0.16.0 is already mandatory for the full gate.",
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
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Pin + purity + authority only (no Zig binary, no ladder).",
    )
    args = parser.parse_args()

    # Mandatory Zig cannot be skipped by the no-binary self-test.
    if args.self_test and args.require_zig:
        parser.error("--self-test cannot satisfy --require-zig")

    if args.self_test:
        verdict_self_test()
        args.skip_ladder_identity = True

    steps: list[dict] = []

    steps.append(check_zig_pin())

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
    except Exception as err:  # noqa: BLE001
        steps.append(
            {
                "step": "migrate-exact-domain-authority",
                "status": "FAIL",
                "exit": 1,
                "detail": str(err)[:1200],
            }
        )

    if args.self_test:
        bridge = {
            "step": "test_zig_codec_bridge",
            "status": "SKIP",
            "exit": 0,
            "detail": "self-test skips Zig binary",
        }
    else:
        bridge = run_step(
            "test_zig_codec_bridge",
            [sys.executable, str(SCRIPTS / "test_zig_codec_bridge.py")],
        )
    # Missing or wrong-version Zig stays FAIL; never translate it to SKIP.
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

    report["verdict"] = gate_verdict(
        steps, self_test=args.self_test, skip_ladder=args.skip_ladder_identity,
    )
    report["transport_verified"] = report["verdict"] == "PASS"
    report["scope"] = (
        "SELF_TEST_NOT_PHYSICAL" if args.self_test
        else "PARTIAL_NO_LADDER" if args.skip_ladder_identity
        else "FULL_PHYSICAL_ZIG"
    )

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

    return (
        0 if report["verdict"] in ("PASS", "SELF_TEST_ONLY")
        else 2 if report["verdict"] == "INCOMPLETE"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
