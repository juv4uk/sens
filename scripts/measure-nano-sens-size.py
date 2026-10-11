#!/usr/bin/env python3
"""Measure Nano-SENS seed/C1 file bytes against a pinned SENS lineage report.

This is measurement plumbing only. It does not build a compiler, prove semantics,
or infer which file constitutes the trusted seed. The operator must identify the
seed explicitly and run against the exact SENS revision pinned in the lineage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = "nano-sens-size-report/1"
LINEAGE_SCHEMA = "compiler-selfhost-lineage-report/1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class MeasurementError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise MeasurementError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def readable_file(path_text: str, label: str) -> Path:
    path = Path(path_text)
    require(path.is_file(), f"{label} is not a regular file: {path}")
    require(path.stat().st_size >= 0, f"{label} has an invalid size")
    return path


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MeasurementError(f"cannot read {label} JSON: {error}") from error
    require(isinstance(value, dict), f"{label} JSON root must be an object")
    return value


def make_report(args: argparse.Namespace) -> dict[str, Any]:
    seed = readable_file(args.seed, "seed")
    c1 = readable_file(args.c1_executable, "C1 executable")
    lineage_path = readable_file(args.lineage_report, "lineage report")
    lineage = load_json(lineage_path, "lineage report")

    require(lineage.get("schema") == LINEAGE_SCHEMA,
            f"lineage schema must be {LINEAGE_SCHEMA!r}")
    require(lineage.get("status") == "pass", "lineage report status must be pass")
    source = lineage.get("source")
    require(isinstance(source, dict), "lineage.source must be an object")
    pinned_revision = source.get("sens_source_sha")
    require(isinstance(pinned_revision, str) and HEX40.fullmatch(pinned_revision) is not None,
            "lineage.source.sens_source_sha must be a full lowercase 40-character SHA")
    require(HEX40.fullmatch(args.source_revision) is not None,
            "--source-revision must be a full lowercase 40-character SHA")
    require(args.source_revision == pinned_revision,
            "source revision differs from the exact revision pinned by lineage")

    generations = lineage.get("generations")
    require(isinstance(generations, dict), "lineage.generations must be an object")
    c1_generation = generations.get("c1")
    c2_generation = generations.get("c2")
    require(isinstance(c1_generation, dict) and isinstance(c2_generation, dict),
            "lineage must contain generations.c1 and generations.c2")
    require(c1_generation.get("produced") is True and c1_generation.get("executable") is True,
            "lineage does not prove that C1 was produced and executable")
    require(c2_generation.get("produced") is True and c2_generation.get("executable") is True,
            "lineage does not prove that C2 was produced and executable")

    fresh = lineage.get("fresh_bootstrap")
    require(isinstance(fresh, dict), "lineage.fresh_bootstrap must be an object")
    require(fresh.get("preexisting_c1_read") is False,
            "lineage says a pre-existing C1 artifact was read")
    require(fresh.get("preexisting_c2_read") is False,
            "lineage says a pre-existing C2 artifact was read")
    require(fresh.get("c0_produced_c1") is True and fresh.get("c1_produced_c2") is True,
            "lineage does not prove both bootstrap generation steps")

    evidence = lineage.get("evidence")
    require(isinstance(evidence, dict), "lineage.evidence must be an object")
    c1_sha = sha256_file(c1)
    c1_size = c1.stat().st_size
    require(evidence.get("c1_executable_sha256") == c1_sha,
            "measured C1 executable SHA-256 disagrees with the lineage evidence")
    require(evidence.get("c2_executable_sha256") == c1_sha,
            "lineage does not record byte-identical C1/C2 executable bytes")
    require(evidence.get("c1_executable_size") == c1_size,
            "measured C1 executable size disagrees with the lineage evidence")
    require(HEX64.fullmatch(c1_sha) is not None, "computed C1 SHA-256 is malformed")
    require(args.seed_role.strip(), "--seed-role must describe the exact measured seed artifact")
    require(args.toolchain.strip(), "--toolchain must record the toolchain used")
    require(args.target.strip(), "--target must record the target triple")
    require(args.abi_profile.strip(), "--abi-profile must record the target ABI/profile")
    require(args.build_command.strip(), "--build-command must record the exact build command")

    return {
        "schema": SCHEMA,
        "status": "MEASURED_WITH_PINNED_SELFHOST_LINEAGE",
        "measurement_scope": "regular-file-bytes-only",
        "source": {
            "sens_source_sha": pinned_revision,
            "lineage_report_sha256": sha256_file(lineage_path),
        },
        "environment": {
            "toolchain": args.toolchain,
            "target": args.target,
            "abi_profile": args.abi_profile,
            "build_command": args.build_command,
        },
        "trusted_seed": {
            "role_declared_by_operator": args.seed_role,
            "file_name": seed.name,
            "file_bytes": seed.stat().st_size,
            "sha256": sha256_file(seed),
        },
        "c1_executable": {
            "file_name": c1.name,
            "file_bytes": c1_size,
            "sha256": c1_sha,
            "matches_pinned_lineage": True,
        },
        "c1_c2_lineage": {
            "status": "pass",
            "c1_executable_sha256": evidence.get("c1_executable_sha256"),
            "c2_executable_sha256": evidence.get("c2_executable_sha256"),
            "byte_identical_executables": True,
            "fresh_bootstrap_flags_validated": True,
        },
        "not_measured": [
            "ELF/PE section sizes",
            "loadable-segment bytes",
            "shared-library/toolchain dependency bytes",
            "minimum possible seed size",
            "GAS/NASM golden-corpus parity",
        ],
        "notes": [
            "File size is not a semantic-size measure.",
            "Seed identity is operator-declared and must be reviewed separately.",
            "This tool validates supplied lineage evidence; it does not rerun C0/C1/C2.",
        ],
    }


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="nano-sens-size-test-") as directory:
        root = Path(directory)
        seed = root / "seed.bin"
        c1 = root / "c1.bin"
        lineage_path = root / "lineage.json"
        seed.write_bytes(b"seed-123")
        c1_bytes = b"c1-executable-fixture"
        c1.write_bytes(c1_bytes)
        c1_sha = hashlib.sha256(c1_bytes).hexdigest()
        source_revision = "a" * 40
        report = {
            "schema": LINEAGE_SCHEMA,
            "status": "pass",
            "source": {"sens_source_sha": source_revision},
            "generations": {
                "c1": {"produced": True, "executable": True},
                "c2": {"produced": True, "executable": True},
            },
            "fresh_bootstrap": {
                "preexisting_c1_read": False,
                "preexisting_c2_read": False,
                "c0_produced_c1": True,
                "c1_produced_c2": True,
            },
            "evidence": {
                "c1_executable_sha256": c1_sha,
                "c2_executable_sha256": c1_sha,
                "c1_executable_size": len(c1_bytes),
            },
        }
        lineage_path.write_text(json.dumps(report), encoding="utf-8")
        args = argparse.Namespace(
            seed=str(seed), c1_executable=str(c1), lineage_report=str(lineage_path),
            source_revision=source_revision, seed_role="test fixture only",
            toolchain="self-test", target="test-target", abi_profile="test-abi",
            build_command="not a real build; fixture only",
        )
        measured = make_report(args)
        assert measured["trusted_seed"]["file_bytes"] == len(b"seed-123")
        assert measured["c1_executable"]["file_bytes"] == len(c1_bytes)
        assert measured["c1_c2_lineage"]["byte_identical_executables"] is True

        report["evidence"]["c1_executable_size"] = len(c1_bytes) + 1
        lineage_path.write_text(json.dumps(report), encoding="utf-8")
        try:
            make_report(args)
        except MeasurementError as error:
            assert "size disagrees" in str(error)
        else:
            raise AssertionError("negative control accepted a wrong executable size")

        report["evidence"]["c1_executable_size"] = len(c1_bytes)
        report["fresh_bootstrap"]["preexisting_c1_read"] = True
        lineage_path.write_text(json.dumps(report), encoding="utf-8")
        try:
            make_report(args)
        except MeasurementError as error:
            assert "pre-existing C1" in str(error)
        else:
            raise AssertionError("negative control accepted a pre-existing C1 read")

    print("NANO-SENS-SIZE SELF-TEST: PASS (3 positive assertions, 2 negative controls)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", help="exact trusted bootstrap seed artifact to measure")
    parser.add_argument("--seed-role", help="explain exactly what the seed file contains")
    parser.add_argument("--c1-executable", help="C1 executable file from the same pinned lineage")
    parser.add_argument("--lineage-report", help="validated compiler-selfhost-lineage-report/1 JSON")
    parser.add_argument("--source-revision", help="40-character SENS source SHA pinned in the lineage")
    parser.add_argument("--toolchain", help="full toolchain description/version")
    parser.add_argument("--target", help="target triple")
    parser.add_argument("--abi-profile", help="ABI/profile string")
    parser.add_argument("--build-command", help="exact command used to create the measured files")
    parser.add_argument("--out", help="output JSON path; stdout when omitted")
    parser.add_argument("--self-test", action="store_true", help="run isolated positive/negative tests")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            return 0
        required = ["seed", "seed_role", "c1_executable", "lineage_report", "source_revision",
                    "toolchain", "target", "abi_profile", "build_command"]
        missing = [name for name in required if not getattr(args, name)]
        if missing:
            parser.error("required unless --self-test: " + ", ".join("--" + name.replace("_", "-") for name in missing))
        report = make_report(args)
        rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except MeasurementError as error:
        print(f"NANO-SENS-SIZE BLOCKED: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"NANO-SENS-SIZE IO ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
