#!/usr/bin/env python3
"""Mechanical exact-domain/T5 digest step for owner L1–L7 (issue #5140).

This file reuses scripts/migrate-three-pass.py and sens_t5_codec.py.
It performs no writes. Matching a physical digest is NOT proof of semantic
equivalence: an independent executable oracle is still required for admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
P = runpy.run_path(str(ROOT / "scripts/legacy-l1-l7-preflight.py"),
                   run_name="l1_l7_policy")
M = P["M"]
analyze = P["analyze"]


def emit(source: str, expected_physical_sha256: str | None = None) -> dict:
    report = analyze(source)
    if report["status"] == "BLOCK":
        return report
    try:
        foundation = M["load_foundation"](ROOT / "knowledge/d1-d9-foundation.json")
        legacy, current, historical = M["build_three_pass_maps"](
            foundation,
            ROOT / "crates/sens/src/domain_surface_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry_generated.rs",
            ROOT / "crates/sens/src/semantic_registry.rs",
            ROOT / "crates/sens/src/eval/necessary_forms_generated.rs",
            ROOT / "contracts/core1-historical-sid-map.lisp",
            ROOT / "knowledge/sens8-current-coverage-v1.json",
        )
        text7 = M["build_text7"](
            foundation, ROOT / "crates/sens/src/text7_projection_generated.rs")
        resolver = M["Resolver"](
            legacy, current, historical, "auto",
            foundation["domains"].get("D8", {}).get("residents", {}))
        projection = M["migrate_file"](report["normalized"], resolver, text7)
        words = M["parse_words"](projection)
        payload = M["encode_projection"](projection)
        if M["decode_bytes"](payload) != words:
            raise ValueError("physical T5 did not round-trip to exact-domain words")
        sha = hashlib.sha256(payload).hexdigest()
        report["physical_sha256"] = sha
        report["typed_word_sha256"] = M["typed_sha256"](words)
        report["physical_bytes"] = len(payload)
        report["exact_domain"] = "STAGED_IN_MEMORY"
        report["independent_semantic_oracle"] = "NOT_RUN"
        if expected_physical_sha256 is None:
            report["status"] = "HOLD_ORACLE"
            report["digest_verdict"] = "REFERENCE_MISSING"
        elif sha == expected_physical_sha256:
            report["status"] = "DIGEST_MATCH_ONLY"
            report["digest_verdict"] = "MATCH"
        else:
            report["status"] = "BLOCK"
            report["digest_verdict"] = "MISMATCH"
            report["findings"].append({
                "law": "L6", "status": "BLOCK",
                "reason": "independent expected T5 digest differs"})
    except (M["MigrationError"], M["SensT5Error"], ValueError, OSError, KeyError) as exc:
        report["status"] = "BLOCK"
        report["exact_domain"] = "BLOCK"
        report["findings"].append({
            "law": "L3/L6", "status": "BLOCK",
            "reason": f"existing exact-domain pipeline rejected input: {exc}"})
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path)
    ap.add_argument("--oracle-physical-sha256",
                    help="expected SHA-256 from an independent physical oracle")
    args = ap.parse_args(argv)
    try:
        source = args.path.read_text(encoding="utf-8")
        result = emit(source, args.oracle_physical_sha256)
    except (OSError, UnicodeError) as exc:
        result = {"status": "BLOCK", "findings": [
            {"law": "L7", "status": "OWNER_REVIEW", "reason": str(exc)}]}
    result.pop("normalized", None)
    result["path"] = str(args.path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Even a matching digest is not sufficient to release physical .sens.
    return 4 if result["status"] == "BLOCK" else 0


if __name__ == "__main__":
    sys.exit(main())
