#!/usr/bin/env python3
"""Mechanical workflow attestation audit. Never parses or executes SENS semantics."""
from pathlib import Path
import re
import sys

WORKFLOW = Path(".github/workflows/ci.yml")
EXPECTED = (
    "sens-time-d1-predicate-law",
    "sens-domain-logic-2040-mutant",
    "knowledge-exact-arity-structure",
    "knowledge-cons-exact-width-law",
    "sens-reason-index-width-selectors-law",
    "sens-reason-index-width-selectors-mutant",
)
STEP = re.compile(r"^      - (?:name|uses):", re.M)


def audit():
    source = WORKFLOW.read_text(encoding="utf-8")
    starts = [match.start() for match in STEP.finditer(source)]
    stages = [source[a:b] for a, b in zip(starts, starts[1:] + [len(source)])]
    errors = []
    for stage in stages:
        title = stage.splitlines()[0].strip()
        claims_native = "semantic_authority=binary-SENS" in stage or "semantic_authority=native-ELF-SENS" in stage
        uses_python_test = "python3 -m unittest" in stage or "python3 -O tests/" in stage
        if claims_native and uses_python_test:
            errors.append(f"{title}: Python migrator advertised as native SENS authority")
        if claims_native and not all(token in stage for token in (
            "ci_failure_contract.py run", "--executor-report-file", "-- target/debug/sens"
        )):
            errors.append(f"{title}: semantic claim without a verified native CLI subprocess")
    for identity in EXPECTED:
        matching = [stage for stage in stages if "--test-id " + identity + " " in stage or "--test-id " + identity + " \\" in stage]
        if len(matching) != 1 or not all(item in matching[0] for item in (
            "ci_failure_contract.py run", "--executor-report-file", "-- target/debug/sens"
        )):
            errors.append(f"{identity}: expected exactly one native CLI witness with receipt")
    scanners = [stage for stage in stages if "scan-executors" in stage and "if: always()" in stage]
    if len(scanners) != 1:
        errors.append("native executor ratchet must run exactly once even on prior failure")
    else:
        for identity in EXPECTED:
            if "--require " + identity not in scanners[0]:
                errors.append(f"ratchet omits required witness {identity}")
    for issue in errors:
        print("::error::UNINFORMATIVE-EXECUTOR " + issue, flush=True)
    if errors:
        return 1
    print("SENS_EXECUTOR_STATIC_AUDIT_PASS verified_native_cli_claims="
          + ",".join(EXPECTED) + " python_semantic_oracles=0", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(audit())
