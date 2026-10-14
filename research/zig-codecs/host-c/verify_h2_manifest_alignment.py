#!/usr/bin/env python3
"""Audit H1 subset manifest against H2's pinned six-file binary corpus.

This is CI_GLUE_NO_SEMANTICS, NOT a second SENS evaluator, Zig transport
runner, ABI implementation, or proof of two-host execution.
No automatic workflow is created; invoke explicitly when relevant.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from verify_h2_cross_host import AuditFailure, CASES, git_blob, inspect_pair

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = "research/zig-codecs/host-c/semantic_subset_contract.json"
C_SOURCE = "research/zig-codecs/host-c/d3_subset.c"
H2_SOURCE = "research/zig-codecs/host-c/verify_h2_cross_host.py"
MANIFEST_SCHEMA = "sens.host-neutral.h1-subset-evidence/v1"


def require(condition: bool, test_id: str, detail: str) -> None:
    if not condition:
        raise AuditFailure(f"test_id={test_id} layer=provenance {detail}")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def inspect(root: Path, manifest: dict) -> dict:
    require(manifest.get("schema") == MANIFEST_SCHEMA, "H2_SCHEMA",
            f"unexpected manifest schema={manifest.get('schema')!r}")
    require(manifest.get("status") == "NON_NORMATIVE_SOURCE_MANIFEST",
            "H2_MANIFEST_AUTHORITY", "manifest cannot assert SENS semantic authority")
    comparison = manifest.get("comparison_requirements", {})
    require(comparison.get("pairs") == len(CASES) and
            comparison.get("program_count") == 2 * len(CASES),
            "H2_CORPUS_CARDINALITY", "pair/program count differs from H2 runner")
    pairs = manifest.get("fixture_pairs")
    require(isinstance(pairs, list) and len(pairs) == len(CASES),
            "H2_PAIR_COUNT", "manifest pair count differs from H2 CASES")
    indexed = {}
    for entry in pairs:
        require(isinstance(entry, dict) and isinstance(entry.get("test_id"), str),
                "H2_PAIR_ID", "missing/invalid pair test_id")
        name = entry["test_id"]
        require(name not in indexed, "H2_PAIR_DUPLICATE", f"duplicate test_id={name}")
        indexed[name] = entry
    require(set(indexed) == {name for name, _, _ in CASES},
            "H2_PAIR_SET", f"expected={sorted(n for n, _, _ in CASES)} actual={sorted(indexed)}")

    records = []
    for family, pin_pos, pin_neg in CASES:
        entry = indexed[family]
        sources = {}
        for role, field, expected_blob in (
            ("law", "positive", pin_pos), ("mutant", "one_bit_mutant", pin_neg)
        ):
            item = entry.get(field)
            require(isinstance(item, dict), "H2_FIXTURE_METADATA",
                    f"family={family} role={role} missing={field}")
            rel = f"tests/semantic/{family}-{role}.bits"
            require(item.get("path") == rel, "H2_FIXTURE_PATH",
                    f"family={family} role={role} expected={rel} actual={item.get('path')}")
            require(item.get("git_blob_sha1") == expected_blob, "H2_FIXTURE_BLOB_PIN",
                    f"family={family} role={role} expected={expected_blob} actual={item.get('git_blob_sha1')}")
            raw = (root / rel).read_bytes()
            require(git_blob(raw) == expected_blob, "H2_FIXTURE_SOURCE_DRIFT",
                    f"family={family} role={role} path={rel} expected_blob={expected_blob} actual_blob={git_blob(raw)}")
            digest = sha256(raw)
            require(item.get("source_sha256") == digest, "H2_FIXTURE_SHA256",
                    f"family={family} role={role} path={rel} expected_sha256={item.get('source_sha256')} actual_sha256={digest}")
            sources[role] = raw
        evidence = inspect_pair(family, sources["law"], sources["mutant"], pin_pos, pin_neg)
        require(entry.get("exact_word_count") == evidence["words"],
                "H2_WORD_COUNT", f"family={family} expected={evidence['words']} actual={entry.get('exact_word_count')}")
        mismatch = evidence["first_mismatch"]
        require(entry.get("mutated_word_zero_based") == mismatch["word"],
                "H2_MUTANT_OFFSET",
                f"family={family} expected={mismatch['word']} actual={entry.get('mutated_word_zero_based')}")
        require(entry.get("mutation") == "D1:0 -> D1:1; exactly one bit, with same width/word count",
                "H2_MUTATION_DESCRIPTION", f"family={family} unexpected mutation description")
        require(entry.get("c_positive_observation") == "D1:1" and
                entry.get("c_mutant_error_category") == "NONCALLABLE_HEAD" and
                entry.get("native_sens_positive_observation") == "D1:1",
                "H2_EXPECTED_OBSERVATION", f"family={family} unexpected expected-observation labels")
        records.append({
            "test_id": family, "law_sha256": sha256(sources["law"]),
            "mutant_sha256": sha256(sources["mutant"]),
            "changed_word": mismatch["word"], "changed_bit": mismatch["bit"],
            "word_count": evidence["words"], "status": "SOURCE_PIN_MATCH",
        })
    c = (root / C_SOURCE).read_bytes()
    c_old_pin = manifest.get("authority", {}).get("c_implementation_git_blob_sha1")
    require(isinstance(c_old_pin, str) and len(c_old_pin) == 40,
            "H2_C_SNAPSHOT", "historical C implementation pin absent")
    c_current = git_blob(c)
    # Snapshot pin was recorded before header-only/other separately claimed C
    # changes: do not create a blanket blocker or silently claim current binary.
    return {
        "test_id": "H2_MANIFEST_CORPUS_ALIGNMENT",
        "status": "SOURCE_ALIGNMENT_PASS",
        "semantic_status": "NOT_VERIFIED",
        "two_host_execution": "NOT_VERIFIED_BY_THIS_CHECK",
        "fixture_pairs": len(CASES), "source_programs": 2 * len(CASES),
        "records": records,
        "manifest_source_sha256": sha256((root / MANIFEST).read_bytes()),
        "h2_runner_source_sha256": sha256((root / H2_SOURCE).read_bytes()),
        "c_implementation_git_blob_current": c_current,
        "c_implementation_git_blob_at_manifest_creation": c_old_pin,
        "c_source_changed_since_manifest_creation": c_current != c_old_pin,
        "c_source_delta_semantic_verdict": "REQUIRES_SEPARATE_REVIEW",
        "manifest_declared_proof_state": comparison.get("proof_state", "NOT_RECORDED"),
    }


def negative_self_test(root: Path, original: dict) -> int:
    def pair_removed(d):
        d["fixture_pairs"].pop()
    def duplicate(d):
        d["fixture_pairs"][1]["test_id"] = d["fixture_pairs"][0]["test_id"]
    def wrong_blob(d):
        d["fixture_pairs"][0]["positive"]["git_blob_sha1"] = "0" * 40
    def wrong_sha256(d):
        d["fixture_pairs"][0]["positive"]["source_sha256"] = "0" * 64
    def moved_mutant(d):
        d["fixture_pairs"][1]["mutated_word_zero_based"] += 1
    def alternate_path(d):
        d["fixture_pairs"][0]["positive"]["path"] = "tests/semantic/other.bits"

    tests = (
        ("H2_PAIR_COUNT", pair_removed),
        ("H2_PAIR_DUPLICATE", duplicate),
        ("H2_FIXTURE_BLOB_PIN", wrong_blob),
        ("H2_FIXTURE_SHA256", wrong_sha256),
        ("H2_MUTANT_OFFSET", moved_mutant),
        ("H2_FIXTURE_PATH", alternate_path),
    )
    for expected_id, mutate in tests:
        candidate = copy.deepcopy(original)
        mutate(candidate)
        try:
            inspect(root, candidate)
        except AuditFailure as exc:
            require(f"test_id={expected_id}" in str(exc), "H2_NEGATIVE_WRONG_REASON",
                    f"case={expected_id} actual={exc}")
        else:
            raise AuditFailure(f"test_id=H2_NEGATIVE_ACCEPTED layer=provenance case={expected_id}")
        print(f"H2_MANIFEST_NEGATIVE_PASS test_id={expected_id}")
    return len(tests)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        data = json.loads((root / MANIFEST).read_text(encoding="utf-8"))
        result = inspect(root, data)
        if args.self_test:
            result["synthetic_negatives_rejected"] = negative_self_test(root, data)
        # This reports *only* file alignment, never executes C, Zig or SENS.
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, KeyError, ValueError, AuditFailure) as exc:
        print(f"H2_MANIFEST_UNVERIFIED {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
