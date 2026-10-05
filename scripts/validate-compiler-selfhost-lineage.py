#!/usr/bin/env python3
"""Validate current-domain C0->C1->C2 self-host lineage reports.

This is evidence plumbing for sens#3822 / sens#3760. It does not compile SENS
and it does not decide language semantics.

Usage:
    python3 scripts/validate-compiler-selfhost-lineage.py REPORT.json
    python3 scripts/validate-compiler-selfhost-lineage.py --self-test
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "compiler-selfhost-lineage-report/1"
METHODS = [
    "byte-identical-artifact",
    "normalized-ir-or-artifact-identical",
    "canonical-lowering-and-executable-corpus-identical",
]
ATTEMPT_STATUS = {"pass", "fail", "unavailable"}
FAILURE_CATEGORIES = {
    "semantic-mismatch",
    "authority-or-provenance-mismatch",
    "bootstrap-input-mismatch",
    "backend-mechanism-failure",
    "toolchain-or-environment-failure",
    "nondeterministic-artifact",
    "forbidden-legacy-fallback",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ReportError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReportError(message)


def obj(value: Any, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def string(value: Any, label: str) -> str:
    require(isinstance(value, str) and value != "", f"{label} must be a non-empty string")
    return value


def sha(value: Any, label: str, pattern: re.Pattern[str]) -> str:
    value = string(value, label)
    require(pattern.fullmatch(value) is not None, f"{label} has invalid digest/SHA shape")
    return value


def validate_report(report: dict[str, Any]) -> None:
    require(report.get("schema") == SCHEMA, f"schema must be {SCHEMA!r}")
    status = report.get("status")
    require(status in {"pass", "fail"}, "status must be pass or fail")

    source = obj(report.get("source"), "source")
    sha(source.get("sens_source_sha"), "source.sens_source_sha", HEX40)
    sha(source.get("compiler_nucleus_sha256"), "source.compiler_nucleus_sha256", HEX64)
    sha(source.get("language_contract_sha256"), "source.language_contract_sha256", HEX64)
    sha(
        source.get("structural_law_projection_sha256"),
        "source.structural_law_projection_sha256",
        HEX64,
    )

    c0 = obj(report.get("c0"), "c0")
    sha(c0.get("implementation_sha"), "c0.implementation_sha", HEX40)
    sha(c0.get("cml_sha"), "c0.cml_sha", HEX40)
    string(c0.get("backend"), "c0.backend")
    string(c0.get("target"), "c0.target")
    string(c0.get("abi_profile"), "c0.abi_profile")

    require(report.get("d8_admitted") is False, "d8_admitted must be false")
    require(
        report.get("legacy_core1_sid8_substitution") is False,
        "legacy_core1_sid8_substitution must be false",
    )

    fresh = obj(report.get("fresh_bootstrap"), "fresh_bootstrap")
    require(fresh.get("preexisting_c1_read") is False, "preexisting C1 read is forbidden")
    require(fresh.get("preexisting_c2_read") is False, "preexisting C2 read is forbidden")
    c0_made_c1 = fresh.get("c0_produced_c1") is True
    c1_made_c2 = fresh.get("c1_produced_c2") is True

    generations = obj(report.get("generations"), "generations")
    c1 = obj(generations.get("c1"), "generations.c1")
    c2 = obj(generations.get("c2"), "generations.c2")
    for name, generation in (("c1", c1), ("c2", c2)):
        produced = generation.get("produced")
        require(isinstance(produced, bool), f"generations.{name}.produced must be boolean")
        executable = generation.get("executable")
        require(isinstance(executable, bool), f"generations.{name}.executable must be boolean")
        artifact = generation.get("artifact_sha256")
        normalized = generation.get("normalized_sha256")
        if produced:
            sha(artifact, f"generations.{name}.artifact_sha256", HEX64)
            if normalized is not None:
                sha(normalized, f"generations.{name}.normalized_sha256", HEX64)
        else:
            require(artifact is None, f"unproduced {name} must have null artifact_sha256")
            require(normalized is None, f"unproduced {name} must have null normalized_sha256")
            require(executable is False, f"unproduced {name} cannot be executable")

    require(c0_made_c1 == (c1.get("produced") is True), "fresh-bootstrap C1 production flag disagrees with generations.c1")
    require(c1_made_c2 == (c2.get("produced") is True), "fresh-bootstrap C2 production flag disagrees with generations.c2")

    equivalence = obj(report.get("equivalence"), "equivalence")
    attempts = equivalence.get("attempts")
    require(isinstance(attempts, list), "equivalence.attempts must be an array")
    require(len(attempts) == len(METHODS), "equivalence.attempts must declare all three methods in strongest-first order")

    first_available: tuple[str, str] | None = None
    seen = []
    for expected_method, attempt in zip(METHODS, attempts):
        attempt = obj(attempt, f"equivalence attempt {expected_method}")
        method = attempt.get("method")
        result = attempt.get("status")
        require(method == expected_method, "equivalence methods must appear in strongest-first contract order")
        require(result in ATTEMPT_STATUS, f"invalid equivalence status for {method}")
        seen.append((method, result))
        reason = attempt.get("reason")
        if result == "unavailable":
            string(reason, f"equivalence reason for unavailable {method}")
        if first_available is None and result != "unavailable":
            first_available = (method, result)

    selected = equivalence.get("selected_method")
    if first_available is None:
        require(selected is None, "selected_method must be null when every equivalence method is unavailable")
    else:
        strongest_method, strongest_result = first_available
        require(
            selected == strongest_method,
            "selected_method must be the strongest available method; silent downgrade is forbidden",
        )
        if strongest_result == "fail":
            require(
                status == "fail",
                "a stronger available equivalence failure forbids a weaker PASS",
            )

    failure_category = report.get("failure_category")
    if status == "pass":
        require(failure_category is None, "PASS report must not carry a failure_category")
        require(c1.get("produced") is True and c1.get("executable") is True, "PASS requires executable C1")
        require(c2.get("produced") is True and c2.get("executable") is True, "PASS requires executable C2")
        require(first_available is not None, "PASS requires an available equivalence method")
        require(first_available[1] == "pass", "PASS requires strongest available equivalence to pass")
    else:
        require(
            failure_category in FAILURE_CATEGORIES,
            "FAIL report must carry one declared failure category",
        )


def valid_fixture() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "status": "pass",
        "source": {
            "sens_source_sha": "1" * 40,
            "compiler_nucleus_sha256": "2" * 64,
            "language_contract_sha256": "3" * 64,
            "structural_law_projection_sha256": "4" * 64,
        },
        "c0": {
            "implementation_sha": "5" * 40,
            "cml_sha": "6" * 40,
            "backend": "c-x86",
            "target": "x86_64-linux-gnu",
            "abi_profile": "sens-selfhost-v1",
        },
        "fresh_bootstrap": {
            "preexisting_c1_read": False,
            "preexisting_c2_read": False,
            "c0_produced_c1": True,
            "c1_produced_c2": True,
        },
        "generations": {
            "c1": {
                "produced": True,
                "executable": True,
                "artifact_sha256": "7" * 64,
                "normalized_sha256": "8" * 64,
            },
            "c2": {
                "produced": True,
                "executable": True,
                "artifact_sha256": "7" * 64,
                "normalized_sha256": "8" * 64,
            },
        },
        "equivalence": {
            "attempts": [
                {
                    "method": "byte-identical-artifact",
                    "status": "pass",
                    "reason": None,
                },
                {
                    "method": "normalized-ir-or-artifact-identical",
                    "status": "unavailable",
                    "reason": "stronger byte identity already established",
                },
                {
                    "method": "canonical-lowering-and-executable-corpus-identical",
                    "status": "unavailable",
                    "reason": "stronger byte identity already established",
                },
            ],
            "selected_method": "byte-identical-artifact",
        },
        "d8_admitted": False,
        "legacy_core1_sid8_substitution": False,
        "failure_category": None,
    }


def expect_failure(mutator, label: str) -> None:
    report = valid_fixture()
    mutator(report)
    try:
        validate_report(report)
    except ReportError:
        return
    raise AssertionError(f"self-test falsifier unexpectedly passed: {label}")


def self_test() -> None:
    validate_report(valid_fixture())

    expect_failure(
        lambda r: r.update({"d8_admitted": True}),
        "D8 admission",
    )
    expect_failure(
        lambda r: r.update({"legacy_core1_sid8_substitution": True}),
        "legacy fallback",
    )
    expect_failure(
        lambda r: r["fresh_bootstrap"].update({"preexisting_c1_read": True}),
        "pre-existing C1 reuse",
    )

    def silent_downgrade(report: dict[str, Any]) -> None:
        report["status"] = "pass"
        report["equivalence"]["attempts"][0]["status"] = "fail"
        report["equivalence"]["selected_method"] = "normalized-ir-or-artifact-identical"
        report["equivalence"]["attempts"][1]["status"] = "pass"
    expect_failure(silent_downgrade, "silent equivalence downgrade")

    def fail_without_category(report: dict[str, Any]) -> None:
        report["status"] = "fail"
        report["equivalence"]["attempts"][0]["status"] = "fail"
        report["failure_category"] = None
    expect_failure(fail_without_category, "unnamed failure category")

    # A stronger method may be unavailable only with an explicit reason; then
    # the next available method becomes the selected criterion.
    weaker = valid_fixture()
    weaker["equivalence"]["attempts"][0] = {
        "method": "byte-identical-artifact",
        "status": "unavailable",
        "reason": "target embeds nondeterministic link metadata not normalizable at byte level",
    }
    weaker["equivalence"]["attempts"][1] = {
        "method": "normalized-ir-or-artifact-identical",
        "status": "pass",
        "reason": None,
    }
    weaker["equivalence"]["selected_method"] = "normalized-ir-or-artifact-identical"
    validate_report(weaker)

    print("COMPILER-SELFHOST-LINEAGE-CONTRACT: PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", nargs="?")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            return 0
        if not args.report:
            parser.error("REPORT.json is required unless --self-test is used")
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
        require(isinstance(report, dict), "report root must be an object")
        validate_report(report)
        print(f"COMPILER-SELFHOST-LINEAGE: PASS {args.report}")
        return 0
    except (OSError, json.JSONDecodeError, ReportError, AssertionError) as error:
        print(f"COMPILER-SELFHOST-LINEAGE: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
