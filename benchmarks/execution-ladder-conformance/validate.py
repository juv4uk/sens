#!/usr/bin/env python3
"""Fail-closed validator for SENS execution-ladder conformance JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCHEMA = "sens-execution-conformance/v1"
CONTRACT = "11.5"
LAYERS = {"L0", "L1", "L2", "L3"}
ENCODINGS = {"canonical-ast", "canonical-source"}
RESULT_KINDS = {"VALUE", "ERROR", "BLOCKED-MECHANISM", "RESEARCH-DOMAIN"}
MECHANISM = {"CALLABLE", "BLOCKED-MECHANISM", "RESEARCH-DOMAIN", "INVALID"}
PARITY = {"ORACLE", "PASS", "FAIL", "NOT-RUN"}
SCOPES = {"fixture", "bounded-exhaustive", "sampled"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
CASE_ID = re.compile(r"^case-[0-9a-f]{64}$")

REQUIRED = {
    "schema",
    "case_id",
    "contract",
    "upstream_sha",
    "producer_layer",
    "producer",
    "program_encoding",
    "program",
    "program_digest",
    "identity_trace",
    "identity_trace_digest",
    "observable",
    "observable_digest",
    "oracle_digest",
    "parity_status",
    "evidence_scope",
    "exhaustive_bound",
    "legacy_identity_used",
}


def canonical_json(value) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def program_digest(program: str) -> str:
    return sha256_text(program)


def case_id_for(program: str) -> str:
    return "case-" + program_digest(program)


def structured_digest(value) -> str:
    return sha256_text(canonical_json(value))


def _expect_exact_keys(value, expected, where):
    if not isinstance(value, dict):
        raise ValueError(f"{where}: expected object")
    missing = sorted(expected - value.keys())
    extra = sorted(value.keys() - expected)
    if missing:
        raise ValueError(f"{where}: missing fields: {missing}")
    if extra:
        raise ValueError(f"{where}: unknown fields: {extra}")


def _validate_identity_trace(trace, line_no):
    if not isinstance(trace, list):
        raise ValueError(f"line {line_no}: identity_trace must be an array")
    for index, item in enumerate(trace):
        where = f"line {line_no}: identity_trace[{index}]"
        _expect_exact_keys(item, {"domain", "bits"}, where)
        domain = item["domain"]
        bits = item["bits"]
        if not isinstance(domain, int) or isinstance(domain, bool) or not 1 <= domain <= 8:
            raise ValueError(f"{where}: domain must be integer 1..8")
        if not isinstance(bits, str) or not bits or set(bits) - {"0", "1"}:
            raise ValueError(f"{where}: bits must be non-empty binary text")
        if len(bits) != domain:
            raise ValueError(
                f"{where}: exact-domain payload width {len(bits)} != domain D{domain}"
            )


def _validate_observable(observable, line_no):
    keys = {"result_kind", "value", "error_kind", "order_trace", "mechanism_status"}
    where = f"line {line_no}: observable"
    _expect_exact_keys(observable, keys, where)

    kind = observable["result_kind"]
    mechanism = observable["mechanism_status"]
    value = observable["value"]
    error = observable["error_kind"]
    order = observable["order_trace"]

    if kind not in RESULT_KINDS:
        raise ValueError(f"{where}: invalid result_kind {kind!r}")
    if mechanism not in MECHANISM:
        raise ValueError(f"{where}: invalid mechanism_status {mechanism!r}")
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{where}: value must be string or null")
    if error is not None and (not isinstance(error, str) or not error):
        raise ValueError(f"{where}: error_kind must be non-empty string or null")
    if not isinstance(order, list) or any(not isinstance(x, str) for x in order):
        raise ValueError(f"{where}: order_trace must be an array of strings")

    if kind == "VALUE":
        if value is None or error is not None or mechanism != "CALLABLE":
            raise ValueError(
                f"{where}: VALUE requires value, error_kind=null, mechanism_status=CALLABLE"
            )
    elif kind == "ERROR":
        if value is not None or error is None:
            raise ValueError(f"{where}: ERROR requires value=null and error_kind")
    elif kind == "BLOCKED-MECHANISM":
        if value is not None or mechanism != "BLOCKED-MECHANISM":
            raise ValueError(
                f"{where}: BLOCKED-MECHANISM requires matching mechanism_status"
            )
    elif kind == "RESEARCH-DOMAIN":
        if value is not None or mechanism != "RESEARCH-DOMAIN":
            raise ValueError(
                f"{where}: RESEARCH-DOMAIN requires matching mechanism_status"
            )


def _validate_bound(row, line_no):
    scope = row["evidence_scope"]
    bound = row["exhaustive_bound"]
    if scope not in SCOPES:
        raise ValueError(f"line {line_no}: invalid evidence_scope {scope!r}")

    if scope != "bounded-exhaustive":
        if bound is not None:
            raise ValueError(
                f"line {line_no}: only bounded-exhaustive rows may carry exhaustive_bound"
            )
        return

    if bound is None:
        raise ValueError(f"line {line_no}: bounded-exhaustive requires exhaustive_bound")

    keys = {"domain_set", "max_ast_depth", "max_nodes", "argument_value_bound"}
    _expect_exact_keys(bound, keys, f"line {line_no}: exhaustive_bound")
    domains = bound["domain_set"]
    if (
        not isinstance(domains, list)
        or not domains
        or any(
            not isinstance(x, int) or isinstance(x, bool) or not 1 <= x <= 8
            for x in domains
        )
        or len(set(domains)) != len(domains)
    ):
        raise ValueError(
            f"line {line_no}: exhaustive_bound.domain_set must be unique D1..D8 integers"
        )
    for key, minimum in (
        ("max_ast_depth", 0),
        ("max_nodes", 1),
        ("argument_value_bound", 0),
    ):
        value = bound[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
            raise ValueError(
                f"line {line_no}: exhaustive_bound.{key} must be integer >= {minimum}"
            )


def validate(row, line_no=1):
    _expect_exact_keys(row, REQUIRED, f"line {line_no}")

    if row["schema"] != SCHEMA:
        raise ValueError(f"line {line_no}: schema must be {SCHEMA!r}")
    if row["contract"] != CONTRACT:
        raise ValueError(f"line {line_no}: contract must be {CONTRACT!r}")
    if not SHA40.fullmatch(row["upstream_sha"]):
        raise ValueError(f"line {line_no}: invalid upstream_sha")
    if row["producer_layer"] not in LAYERS:
        raise ValueError(f"line {line_no}: invalid producer_layer")
    if not isinstance(row["producer"], str) or not row["producer"]:
        raise ValueError(f"line {line_no}: producer must be non-empty string")
    if row["program_encoding"] not in ENCODINGS:
        raise ValueError(f"line {line_no}: invalid program_encoding")
    if not isinstance(row["program"], str) or not row["program"]:
        raise ValueError(f"line {line_no}: program must be non-empty string")
    if row["legacy_identity_used"] is not False:
        raise ValueError(f"line {line_no}: legacy identity is forbidden")

    expected_program_digest = program_digest(row["program"])
    if row["program_digest"] != expected_program_digest:
        raise ValueError(f"line {line_no}: program_digest mismatch")
    if not SHA64.fullmatch(row["program_digest"]):
        raise ValueError(f"line {line_no}: invalid program_digest")

    expected_case_id = case_id_for(row["program"])
    if row["case_id"] != expected_case_id or not CASE_ID.fullmatch(row["case_id"]):
        raise ValueError(f"line {line_no}: deterministic case_id mismatch")

    _validate_identity_trace(row["identity_trace"], line_no)
    expected_trace_digest = structured_digest(row["identity_trace"])
    if row["identity_trace_digest"] != expected_trace_digest:
        raise ValueError(f"line {line_no}: identity_trace_digest mismatch")

    _validate_observable(row["observable"], line_no)
    expected_observable_digest = structured_digest(row["observable"])
    if row["observable_digest"] != expected_observable_digest:
        raise ValueError(f"line {line_no}: observable_digest mismatch")

    if not SHA64.fullmatch(row["oracle_digest"]):
        raise ValueError(f"line {line_no}: invalid oracle_digest")
    if row["parity_status"] not in PARITY:
        raise ValueError(f"line {line_no}: invalid parity_status")

    layer = row["producer_layer"]
    parity = row["parity_status"]
    equal = row["observable_digest"] == row["oracle_digest"]

    if layer == "L0":
        if parity != "ORACLE" or not equal:
            raise ValueError(
                f"line {line_no}: L0 oracle row requires parity_status=ORACLE "
                "and oracle_digest == observable_digest"
            )
    elif parity == "PASS" and not equal:
        raise ValueError(f"line {line_no}: PASS requires observable == oracle digest")
    elif parity == "FAIL" and equal:
        raise ValueError(f"line {line_no}: FAIL requires observable != oracle digest")
    elif parity == "ORACLE":
        raise ValueError(f"line {line_no}: only L0 may use ORACLE parity status")
    elif parity == "NOT-RUN":
        kind = row["observable"]["result_kind"]
        if kind not in {"BLOCKED-MECHANISM", "RESEARCH-DOMAIN"}:
            raise ValueError(
                f"line {line_no}: NOT-RUN requires blocked/research observable"
            )

    _validate_bound(row, line_no)


def validate_file(path: Path) -> int:
    seen = set()
    count = 0
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        row = json.loads(raw)
        validate(row, line_no)
        case_key = (row["case_id"], row["producer_layer"], row["producer"])
        if case_key in seen:
            raise ValueError(
                f"line {line_no}: duplicate producer row for {row['case_id']}"
            )
        seen.add(case_key)
        count += 1
    if count == 0:
        raise ValueError("evidence file is empty")
    return count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jsonl", type=Path, nargs="+")
    args = ap.parse_args()
    for path in args.jsonl:
        count = validate_file(path)
        print(f"validated {count} execution-conformance rows: {path}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
