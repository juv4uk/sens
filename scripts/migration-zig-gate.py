#!/usr/bin/env python3
"""Fail-closed preparation gate: migration scripts \u2194 Zig physical codec.

Does NOT invent semantics. Does NOT admit programs. Does NOT write .lisp/.sens.

Runs the already-contracted mechanical checks the swarm needs before a
migration batch, in fixed order:

  0. zig-pin                 \u2014 .zig-version == 0.16.0 and install-zig default
  1. ci_zig_purity           \u2014 no W8/Sens8/SID-8 contamination in *.zig
  2. check_sterile_zig_corridor — default Rust↔SENS uses the Zig ABI
  3. check_rust_sens_zig_corridor — R1–R5 host-neutral C↔Zig physical ABI
  4. check_rust_sens_corridor_coverage — no invisible Rust-host bypass
  5. check_corridor_axiom_binding — guard rules trace to SENS axioms
  6. check-domain-ladder-identity \u2014 width=identity on canonical surfaces
  7. migrate-exact-domain authority load \u2014 D3/D4 tables + owner ratification
  8. test_zig_codec_bridge   \u2014 REQUIRED physical T5 round-trip; --self-test is NOT a full gate

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
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


# Externally pinned physical SHA of the four golden T5 bytes 63 89 06 a1.
# A zero exit code or a self-asserted PASS string is not an evidence receipt.
BRIDGE_GOLDEN_SHA256 = "90b993c83b34932d65b1001547f8833987eac2e44b238155a983cb8e5f68c978"
BRIDGE_RECEIPT_EXACT = {
    "id": "zig-migration-bridge-t5-exact-physical",
    "layer": "transport",
    "zig": "0.16.0",
    "physical_sha256": BRIDGE_GOLDEN_SHA256,
    "first_difference": "NONE",
    "malformed_ff": "REJECTED",
    "d10_transport": "ACCEPTED",
    "d10_executable": "REJECTED",
    "overwidth_d15": "REJECTED",
    "external_trusted_sha_d10": "INDEPENDENT_GOLDEN",
    "external_trusted_sha_d1": "INDEPENDENT_GOLDEN",
    "canonical_d1_to_d2_same_length": "REJECTED_WITH_EXTERNAL_PIN",
    "canonical_d10_to_d5_truncation": "REJECTED_WITH_EXTERNAL_PIN",
    "d1_d2_distinct": "YES",
    "d2_zero_and_one": "YES",
    "canonical_truncation_requires_external_sha": "YES",
    "semantic_authority": "SENS",
}
BRIDGE_RECEIPT_MINIMUM = {"width_goldens": 9, "negative_gates": 14}


def _bridge_failure_marker(stream: str) -> str | None:
    """Identify an explicit failure without interpreting other diagnostic text."""
    for line in stream.splitlines():
        fields = line.strip().split(maxsplit=1)
        if fields and fields[0] in {"ZIG_BRIDGE_FAIL", "ZIG_BRIDGE_BLOCKED"}:
            return fields[0]
    return None


def verify_zig_bridge_receipt(stdout: str) -> dict[str, str]:
    """Require informative physical proof, never infer it from exit=0.

    A textual receipt is not an SENS semantic oracle or a cryptographic
    compiler attestation. This gate only checks the already-run Zig proof.
    """
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    # A later PASS cannot override an explicit failure from the same process.
    failed = _bridge_failure_marker(stdout)
    if failed is not None:
        raise ValueError(f"contradictory Zig bridge receipt status={failed}")
    markers = [line for line in lines if line.startswith("ZIG_BRIDGE_PASS")]
    if len(markers) != 1 or not lines or markers[0] != lines[-1]:
        raise ValueError("expected exactly one final ZIG_BRIDGE_PASS record")
    tokens = markers[0].split()
    if not tokens or tokens[0] != "ZIG_BRIDGE_PASS":
        raise ValueError("malformed ZIG_BRIDGE_PASS prefix")
    values: dict[str, str] = {}
    for token in tokens[1:]:
        if token.count("=") != 1:
            raise ValueError(f"invalid receipt token={token!r}")
        key, value = token.split("=", 1)
        if not key or not value or key in values:
            raise ValueError(f"empty/duplicate receipt field={key!r}")
        values[key] = value
    # Reject invented fields (especially owner_GO/release_admitted). A
    # transport receipt is not a semantic oracle or a release decision.
    allowed = set(BRIDGE_RECEIPT_EXACT) | set(BRIDGE_RECEIPT_MINIMUM) | {"zig_binary_sha256"}
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ValueError(f"unrecognized physical receipt fields={unknown!r}")
    for key, expected in BRIDGE_RECEIPT_EXACT.items():
        if values.get(key) != expected:
            raise ValueError(f"field={key} expected={expected} actual={values.get(key)!r}")
    for key, minimum in BRIDGE_RECEIPT_MINIMUM.items():
        raw = values.get(key, "")
        if re.fullmatch(r"[0-9]+", raw) is None or int(raw) < minimum:
            raise ValueError(f"field={key} expected=>={minimum} actual={raw!r}")
    binary_sha = values.get("zig_binary_sha256", "")
    if re.fullmatch(r"[0-9a-f]{64}", binary_sha) is None:
        raise ValueError("field=zig_binary_sha256 expected=lowercase_sha256")
    return values


def zig_bridge_receipt_self_test() -> None:
    """Synthetic receipt mutations, not proof of executed Zig or SENS."""
    values = {**BRIDGE_RECEIPT_EXACT,
              **{k: str(v) for k, v in BRIDGE_RECEIPT_MINIMUM.items()},
              "zig_binary_sha256": "a" * 64}
    line = "ZIG_BRIDGE_PASS " + " ".join(f"{k}={v}" for k, v in values.items())
    assert verify_zig_bridge_receipt(line)["semantic_authority"] == "SENS"
    # The central --self-test also proves stderr failure markers are recognized.
    assert _bridge_failure_marker("ordinary compiler notice\n") is None
    for marker in ("ZIG_BRIDGE_FAIL", "ZIG_BRIDGE_BLOCKED"):
        assert _bridge_failure_marker(marker + " test_id=transport\n") == marker
    for mutant in (
        "",
        "ZIG_BRIDGE_PASS",
        line.replace("physical_sha256=" + BRIDGE_GOLDEN_SHA256,
                     "physical_sha256=" + "0" * 64),
        line.replace("d10_executable=REJECTED", "d10_executable=ACCEPTED"),
        line.replace("external_trusted_sha_d10=INDEPENDENT_GOLDEN",
                     "external_trusted_sha_d10=REQUIRED_WHEN_SUPPLIED"),
        line.replace("external_trusted_sha_d1=INDEPENDENT_GOLDEN",
                     "external_trusted_sha_d1=REQUIRED_WHEN_SUPPLIED"),
        line.replace("canonical_d1_to_d2_same_length=REJECTED_WITH_EXTERNAL_PIN",
                     "canonical_d1_to_d2_same_length=NOT_TESTED"),
        "ZIG_BRIDGE_FAIL test_id=transport\n" + line,
        "ZIG_BRIDGE_BLOCKED test_id=transport\n" + line,
        line + " owner_GO=YES",
        line.replace("zig_binary_sha256=" + "a" * 64,
                     "zig_binary_sha256=not-a-hash"),
        line + "\n" + line,
    ):
        try:
            verify_zig_bridge_receipt(mutant)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "ZIG_BRIDGE_RECEIPT_SELF_TEST accepted a synthetic mutant"
            )
    print("MIGRATION_ZIG_RECEIPT_SELF_TEST_PASS negatives=12")


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
    if name == "test_zig_codec_bridge" and status == "PASS":
        try:
            # The physical bridge's stderr is part of the same process
            # evidence. A zero exit + stdout PASS cannot erase its failure.
            stderr_failed = _bridge_failure_marker(completed.stderr or "")
            if stderr_failed is not None:
                raise ValueError(
                    f"contradictory Zig bridge stderr status={stderr_failed}"
                )
            verify_zig_bridge_receipt(completed.stdout or "")
        except ValueError as error:
            # A successful process with no exact physical evidence is RED.
            # Preserve exit=0 as the process fact, but report status=FAIL.
            status = "FAIL"
            tail = (
                "ZIG_BRIDGE_RECEIPT_UNINFORMATIVE "
                "test_id=zig-migration-bridge-t5-exact-physical "
                "layer=transport expected=verified_physical_receipt "
                f"actual={error} first_difference=UNKNOWN "
                "reproduce='python3 scripts/test_zig_codec_bridge.py'"
            )
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


def validate_migration_identities(surfaces: dict) -> None:
    """Verify identities returned by the current D3/D4 surface authority.

    The migrator's live contract is one surface-to-identity mapping. Historical
    SID8 donor records are not returned by this API and are not loaded here.
    """
    failures: list[str] = []
    if not isinstance(surfaces, dict):
        raise ValueError("EXACT_MIGRATION_AUTHORITY expected=surface-mapping")
    for key, identity in surfaces.items():
        domain = getattr(identity, "domain", None)
        bits = getattr(identity, "bits", None)
        if not isinstance(key, str) or not key:
            failures.append(f"surface:{key!r} invalid-key")
        # This migrator imports the D3/D4 surfaces it explicitly reads.
        # No domain identity or callability is inferred from width alone.
        if domain not in ("D3", "D4"):
            failures.append(f"surface:{key!r} unexpected-domain={domain!r}")
            continue
        width = 3 if domain == "D3" else 4
        if (not isinstance(bits, str) or len(bits) != width
                or re.fullmatch(r"[01]+", bits) is None):
            failures.append(
                f"surface:{key!r} domain={domain} invalid-exact-bits={bits!r}"
            )
    if failures:
        raise ValueError(
            "EXACT_MIGRATION_AUTHORITY: " + "; ".join(failures[:8])
        )


def load_exact_domain_authority() -> dict:
    """Import migrate-exact-domain and load owner tables (no write)."""
    path = SCRIPTS / "migrate-exact-domain.py"
    spec = importlib.util.spec_from_file_location("migrate_exact_domain", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load migrate-exact-domain.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    surfaces = mod.load_authority(ROOT)
    validate_migration_identities(surfaces)
    return {
        "step": "migrate-exact-domain-authority",
        "status": "PASS",
        "exit": 0,
        "detail": (
            f"surfaces={len(surfaces)} "
            "width_axiom=PASS owner-ratified=D3/D4"
        ),
    }


REQUIRED_STEPS = (
    "zig-pin",
    "ci_zig_purity",
    "check_sterile_zig_corridor",
    "check_rust_sens_zig_corridor",
    "check_rust_sens_corridor_coverage",
    "check_corridor_axiom_binding",
    "check-domain-ladder-identity",
    "migrate-exact-domain-authority",
    "test_zig_codec_bridge",
)


def gate_verdict(steps: list[dict], *, self_test: bool, skip_ladder: bool) -> str:
    """Never call a skipped, missing or failed physical Zig proof a PASS."""
    # A status string does not supersede the process exit. Every real step
    # records both fields: a nonzero exit must block release even when a
    # stale or forged wrapper labels that step PASS.
    if any(step.get("status") == "FAIL" or
           (type(step.get("exit")) is int and step["exit"] != 0)
           for step in steps):
        return "FAIL"
    # Missing, string or bool exit codes are NOT a successful process proof.
    # This applies to self-tests too, without claiming physical Zig success.
    if any(type(step.get("exit")) is not int for step in steps):
        return "INCOMPLETE"
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
    passing = [{"step": name, "status": "PASS", "exit": 0}
               for name in REQUIRED_STEPS]
    assert gate_verdict(passing, self_test=False, skip_ladder=False) == "PASS"
    missing = passing[:-1]
    assert gate_verdict(missing, self_test=False, skip_ladder=False) == "INCOMPLETE"
    # Mechanical T5 parity is NOT enough if the Rust host bypasses Zig.
    # A missing/failed corridor source guard must never be a full PASS.
    missing_corridor = [s for s in passing if s["step"] != "check_sterile_zig_corridor"]
    assert gate_verdict(missing_corridor, self_test=False, skip_ladder=False) == "INCOMPLETE"
    failed_corridor = [
        {"step": s["step"], "status": "FAIL" if s["step"] == "check_sterile_zig_corridor" else "PASS"}
        for s in passing
    ]
    assert gate_verdict(failed_corridor, self_test=False, skip_ladder=False) == "FAIL"
    # A Rust-only green preflight cannot hide an absent or red C-host R5.
    missing_r5 = [s for s in passing if s["step"] != "check_rust_sens_zig_corridor"]
    assert gate_verdict(missing_r5, self_test=False, skip_ladder=False) == "INCOMPLETE"
    failed_r5 = [
        {"step": s["step"], "status": "FAIL" if s["step"] == "check_rust_sens_zig_corridor" else "PASS"}
        for s in passing
    ]
    assert gate_verdict(failed_r5, self_test=False, skip_ladder=False) == "FAIL"
    # S2 and G6/G7: coverage and axiom provenance cannot be omitted.
    for guard in ("check_rust_sens_corridor_coverage",
                  "check_corridor_axiom_binding"):
        missing_guard = [s for s in passing if s["step"] != guard]
        assert gate_verdict(missing_guard, self_test=False, skip_ladder=False) == "INCOMPLETE"
        failed_guard = [
            {"step": s["step"],
             "status": "FAIL" if s["step"] == guard else "PASS"}
            for s in passing
        ]
        assert gate_verdict(failed_guard, self_test=False, skip_ladder=False) == "FAIL"
    skipped = [*passing[:-1],
               {"step": REQUIRED_STEPS[-1], "status": "SKIP", "exit": 0}]
    assert gate_verdict(skipped, self_test=False, skip_ladder=False) == "INCOMPLETE"
    unavailable = [*passing[:-1],
                   {"step": REQUIRED_STEPS[-1], "status": "FAIL", "exit": 1}]
    assert gate_verdict(unavailable, self_test=False, skip_ladder=False) == "FAIL"
    mismatched_exit = [dict(step) for step in passing]
    mismatched_exit[-1]["exit"] = 17
    assert gate_verdict(mismatched_exit, self_test=False,
                        skip_ladder=False) == "FAIL"
    missing_exit = [dict(step) for step in passing]
    del missing_exit[-1]["exit"]
    assert gate_verdict(missing_exit, self_test=False,
                        skip_ladder=False) == "INCOMPLETE"
    boolean_exit = [dict(step) for step in passing]
    boolean_exit[-1]["exit"] = False
    assert gate_verdict(boolean_exit, self_test=False,
                        skip_ladder=False) == "INCOMPLETE"
    assert gate_verdict(passing, self_test=False, skip_ladder=True) == "INCOMPLETE"
    assert gate_verdict(skipped, self_test=True, skip_ladder=True) == "SELF_TEST_ONLY"
    zig_bridge_receipt_self_test()
    print("MIGRATION_ZIG_GATE_VERDICT_SELF_TEST_PASS negative_cases=13")


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
            [str(SCRIPTS / "ci-zig-purity")],
        )
    )

    # Physical Zig codec PASS is not proof the default CLI lacks Rust T5
    # bypasses. This source-only guard carries no SENS semantic authority.
    steps.append(
        run_step(
            "check_sterile_zig_corridor",
            ["cargo", "test", "--locked", "-p", "sens-cli", "--bin", "sens-trit", "sterile_f3c_corridor", "--", "--nocapture"],
        )
    )

    # R5 is independent host-neutral source evidence, not SENS semantic
    # admission: a Rust-free C caller must pass the same sterile Zig ABI.
    steps.append(
        run_step(
            "check_rust_sens_zig_corridor",
            [sys.executable, str(SCRIPTS / "check_rust_sens_zig_corridor.py")],
        )
    )

    # G6/G7: all Rust host exceptions must be accounted for; S2: every
    # structural corridor guard must be linked to its axiom. Neither check
    # claims executable D10 callability or replaces the native SENS oracle.
    for guard, filename in (
        ("check_rust_sens_corridor_coverage", "check_rust_sens_corridor_coverage.py"),
        ("check_corridor_axiom_binding", "check_corridor_axiom_binding.py"),
    ):
        steps.append(run_step(guard, [sys.executable, str(SCRIPTS / filename)]))

    if not args.skip_ladder_identity:
        steps.append(
            run_step(
                "check-domain-ladder-identity",
                [sys.executable, str(SCRIPTS / "check-domain-ladder-identity.py"), "--check"],
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
