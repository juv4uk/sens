#!/usr/bin/env python3
"""Mechanical evidence-accounting guard: NEVER a SENS semantic oracle.

CI_GLUE_NO_SEMANTICS. The ledger tracks retired Rust assertions and pointers
to *native* SENS witnesses; only the executed binary SENS program can decide
a language law. No Rust, Python, TSV row or Git blob SHA proves a semantic PASS.
"""
from __future__ import annotations

import argparse
import copy
import csv
import io
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/archaeology/semantic-coverage-ledger-2026-10-14.tsv"
ARCHIVE = ROOT / "docs/archive/historical/retired-rust-semantic-suites-2026-10-09"
STATUSES = {"COVERED", "EXCLUDED", "PENDING"}
SHA1 = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
RUN_URL = re.compile(r"https://github\.com/juv4uk/sens/actions/runs/[1-9][0-9]*\Z")
TEST_NAME = re.compile(r"#\s*\[\s*test\s*\]\s*(?:#\s*\[[^\]]+\]\s*)*(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z_0-9]*)\s*\(")
ARCHIVED = {
    "advice": 2,
    "forward": 41,
    "knowledge": 42,
    "mccarthy": 34,
    "meta_eval": 13,
    "narrate": 6,
    "reason": 11,
    "understand": 9,
    "unify": 11,
    "world": 21,
}
COLUMNS = (
    "retired_test_id", "retired_path", "retired_test",
    "retired_source_blob_sha1", "retirement_provenance",
    "candidate_sens_witness", "candidate_git_blob_sha1",
    "native_run_receipt_sha256", "status", "rationale", "scope",
    "claim_slice", "negative_sens_witness", "native_run_url",
    "native_run_commit_sha",
)


class InvalidLedger(ValueError):
    pass


def must(predicate: bool, detail: str) -> None:
    if not predicate:
        raise InvalidLedger(detail)


def read_rows(source: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(source), delimiter="\t")
    must(tuple(reader.fieldnames or ()) == COLUMNS,
         "LEDGER_SCHEMA: unexpected columns; do not silently omit evidence fields")
    rows = list(reader)
    must(all(None not in row for row in rows),
         "LEDGER_SCHEMA: malformed row has missing or surplus columns")
    return rows


def archive_assertions(root: Path) -> set[str]:
    expected: set[str] = set()
    for name, count in ARCHIVED.items():
        path = ARCHIVE.relative_to(ROOT) / f"{name}.rs.txt"
        source = (root / path).read_text(encoding="utf-8")
        names = TEST_NAME.findall(source)
        must(len(names) == count and len(set(names)) == count,
             f"ARCHAEOLOGY_DRIFT: {path} expected {count} test annotations; found {len(names)}")
        expected.update(f"crates/sens/tests/{name}.rs::{entry}" for entry in names)
    must(len(expected) == 190, "ARCHAEOLOGY_DRIFT: 190 distinct test IDs expected")
    return expected


def validate(rows: list[dict[str, str]], root: Path, expected: set[str]) -> Counter[str]:
    must(len(rows) >= len(expected), "LEDGER_LOSS: fewer ledger rows than archived tests")
    ids: set[str] = set()
    bulk_ids: set[str] = set()
    statuses: Counter[str] = Counter()
    for line, r in enumerate(rows, 2):
        rid = r["retired_test_id"]
        must(rid == f'{r["retired_path"]}::{r["retired_test"]}',
             f"LEDGER_ID: line={line} id={rid}")
        must(rid not in ids, f"LEDGER_DUPLICATE: line={line} id={rid}")
        ids.add(rid)
        if r["scope"] == "BULK_20261009":
            bulk_ids.add(rid)
        must(SHA1.fullmatch(r["retired_source_blob_sha1"]) is not None
             or r["retired_source_blob_sha1"] == "-",
             f"LEDGER_SOURCE_SHA1: line={line} id={rid}")
        must(r["retirement_provenance"].strip() not in ("", "-"),
             f"LEDGER_RETIREMENT_SOURCE: line={line} id={rid}")
        status = r["status"]
        must(status in STATUSES, f"LEDGER_STATUS: line={line} id={rid} status={status!r}")
        statuses[status] += 1
        must(len(r["rationale"].strip()) >= 20,
             f"LEDGER_RATIONALE: line={line} id={rid}")
        candidate = r["candidate_sens_witness"]
        candidate_sha = r["candidate_git_blob_sha1"]
        if candidate != "-":
            must(candidate.startswith("tests/") and
                 Path(candidate).suffix in (".sens", ".bits", ".lisp"),
                 f"LEDGER_CANDIDATE_PATH: line={line} id={rid}")
            must((root / candidate).is_file(),
                 f"LEDGER_CANDIDATE_MISSING: line={line} path={candidate}")
            must(SHA1.fullmatch(candidate_sha) is not None,
                 f"LEDGER_CANDIDATE_SHA: line={line} id={rid}")
        else:
            must(candidate_sha == "-", f"LEDGER_CANDIDATE_ORPHAN: line={line} id={rid}")
        if status == "COVERED":
            must(candidate.endswith(".sens"), f"UNVERIFIED_NATIVE_PHYSICAL: line={line} id={rid}")
            negative = r["negative_sens_witness"]
            must(negative.startswith("tests/") and negative.endswith(".sens") and
                 (root / negative).is_file(),
                 f"MISSING_NEGATIVE_SENS: line={line} id={rid}")
            must(r["claim_slice"] != "-" and len(r["claim_slice"].strip()) > 20,
                 f"UNMAPPED_SEMANTIC_CLAIM: line={line} id={rid}")
            must(SHA256.fullmatch(r["native_run_receipt_sha256"]) is not None,
                 f"MISSING_NATIVE_SHA256_RECEIPT: line={line} id={rid}")
            must(RUN_URL.fullmatch(r["native_run_url"]) is not None,
                 f"MISSING_NATIVE_RUN_URL: line={line} id={rid}")
            must(SHA1.fullmatch(r["native_run_commit_sha"]) is not None,
                 f"MISSING_NATIVE_RUN_COMMIT: line={line} id={rid}")
            # A structurally complete row is still not itself semantic proof:
            # the linked native receipt must be inspected against its actual log.
        else:
            must(r["native_run_receipt_sha256"] in ("", "-") and
                 r["native_run_url"] in ("", "-") and
                 r["native_run_commit_sha"] in ("", "-"),
                 f"FALSE_RECEIPT_ON_UNCOVERED: line={line} id={rid}")
    must(bulk_ids == expected,
         f"LEDGER_ARCHAEOLOGY_CENSUS: missing={len(expected-bulk_ids)} "
         f"unexpected={len(bulk_ids-expected)}")
    return statuses


def self_test(rows: list[dict[str, str]], root: Path, expected: set[str]) -> None:
    validate(rows, root, expected)
    def rejects(mutant: list[dict[str, str]], label: str) -> None:
        try:
            validate(mutant, root, expected)
        except InvalidLedger:
            return
        raise InvalidLedger(f"LEDGER_SELF_TEST_BROKEN: accepted {label}")
    rejects(rows[1:], "deleted archived row")
    doubled = copy.deepcopy(rows)
    doubled.append(copy.deepcopy(doubled[0]))
    rejects(doubled, "duplicate")
    bogus = copy.deepcopy(rows)
    target = next((x for x in bogus if x["status"] == "PENDING"), None)
    must(target is not None, "LEDGER_SELF_TEST: require a pending row")
    target["status"] = "COVERED"
    rejects(bogus, "unevidenced COVERED")
    bogus_path = copy.deepcopy(rows)
    target_path = next((x for x in bogus_path if x["candidate_sens_witness"] != "-"), None)
    must(target_path is not None, "LEDGER_SELF_TEST: require a candidate")
    target_path["candidate_sens_witness"] = "tests/semantic/not-a-real-witness.sens"
    rejects(bogus_path, "missing physical witness")
    print("LEDGER_SELF_TEST_PASS: loss/duplicate/false-COVERED/missing-witness rejected")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not (args.check or args.self_test):
        parser.error("select --check and/or --self-test")
    rows = read_rows(LEDGER.read_text(encoding="utf-8"))
    expected = archive_assertions(ROOT)
    if args.self_test:
        self_test(rows, ROOT, expected)
    if args.check:
        statuses = validate(rows, ROOT, expected)
        print(f"LEDGER_MECHANICAL_PASS rows={len(rows)} archived={len(expected)} "
              f"COVERED={statuses['COVERED']} EXCLUDED={statuses['EXCLUDED']} "
              f"PENDING={statuses['PENDING']} semantic_pass=NOT_INFERRED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, InvalidLedger) as exc:
        raise SystemExit(f"LEDGER_MECHANICAL_RED: {exc}")
