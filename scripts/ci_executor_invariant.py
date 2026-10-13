#!/usr/bin/env python3
"""CI-only provenance audit. Never interprets SENS, never decides a language law."""
from pathlib import Path
import re
import sys

WORKFLOW = Path(".github/workflows/ci.yml")
EXPECTED = (
    "sens-time-d1-predicate-law",
    "sens-domain-logic-2040-mutant",
    "knowledge-exact-arity-structure",
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
        if claims_native and "ci_native_sens_witness.sh run" not in stage:
            errors.append(f"{title}: native semantic claim without native witness runner")
    for identity in EXPECTED:
        needle = "ci_native_sens_witness.sh run " + identity + " "
        if source.count(needle) != 1:
            errors.append(f"{identity}: expected exactly one declared native ELF execution")
        if "ci_native_sens_witness.sh scan" not in source:
            errors.append("missing native-executor log ratchet")
    if not any("if: always()" in stage and "ci_native_sens_witness.sh scan" in stage for stage in stages):
        errors.append("native log ratchet must execute even if earlier witness failed")
    for issue in errors:
        print("::error::UNINFORMATIVE-EXECUTOR " + issue, flush=True)
    if errors:
        return 1
    print("SENS_EXECUTOR_STATIC_AUDIT_PASS native_witnesses="
          + ",".join(EXPECTED) + " python_semantic_oracles=0", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(audit())
