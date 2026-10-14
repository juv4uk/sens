#!/usr/bin/env python3
"""Mechanical workflow attestation audit. Never parses or executes SENS semantics."""
from pathlib import Path
import re
import sys

WORKFLOW = Path(".github/workflows/ci.yml")
# Owner decision 2026-10-14: native receipts and fixed witness quotas are
# optional; a step claiming native SENS must still have an actual native caller.
STEP = re.compile(r"^      - (?:name|uses):", re.M)


def audit():
    source = WORKFLOW.read_text(encoding="utf-8")
    starts = [match.start() for match in STEP.finditer(source)]
    stages = [source[a:b] for a, b in zip(starts, starts[1:] + [len(source)])]
    errors = []
    claimed = []
    for stage in stages:
        title = stage.splitlines()[0].strip()
        claims_native = (
            "semantic_authority=binary-SENS" in stage
            or "semantic_authority=native-ELF-SENS" in stage
        )
        uses_python_test = (
            "python3 -m unittest" in stage or "python3 -O tests/" in stage
        )
        if claims_native and uses_python_test:
            errors.append(f"{title}: Python migrator advertised as native SENS authority")
        if claims_native:
            if "-- target/debug/sens" not in stage:
                errors.append(f"{title}: native SENS claim has no native CLI invocation")
            else:
                claimed.append(title)
    for issue in errors:
        print("::error::UNINFORMATIVE-EXECUTOR " + issue, flush=True)
    if errors:
        return 1
    print(
        "SENS_EXECUTOR_STATIC_AUDIT_PASS "
        f"truthfully_labelled_native_claims={len(claimed)} "
        "fixed_receipt_quotas=disabled_by_owner",
        flush=True,
    )
    return 0

if __name__ == "__main__":
    sys.exit(audit())
