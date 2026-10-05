#!/usr/bin/env python3
"""Schema/digest self-tests for #3561. No evaluator semantics are exercised."""

from __future__ import annotations

import copy

from validate import (
    SCHEMA,
    canonical_json,
    case_id_for,
    program_digest,
    structured_digest,
    validate,
)


def oracle_row():
    program = "10 000 01"
    trace = [{"domain": 3, "bits": "000"}]
    observable = {
        "result_kind": "VALUE",
        "value": "synthetic-schema-only",
        "error_kind": None,
        "order_trace": [],
        "mechanism_status": "CALLABLE",
    }
    digest = structured_digest(observable)
    return {
        "schema": SCHEMA,
        "case_id": case_id_for(program),
        "contract": "11.5",
        "upstream_sha": "0" * 40,
        "producer_layer": "L0",
        "producer": "schema-selftest-oracle",
        "program_encoding": "canonical-source",
        "program": program,
        "program_digest": program_digest(program),
        "identity_trace": trace,
        "identity_trace_digest": structured_digest(trace),
        "observable": observable,
        "observable_digest": digest,
        "oracle_digest": digest,
        "parity_status": "ORACLE",
        "evidence_scope": "fixture",
        "exhaustive_bound": None,
        "legacy_identity_used": False,
    }


def must_fail(row, needle):
    try:
        validate(row)
    except ValueError as exc:
        if needle not in str(exc):
            raise AssertionError(f"expected {needle!r}, got {exc!r}") from exc
        return
    raise AssertionError(f"expected validation failure containing {needle!r}")


def main():
    base = oracle_row()
    validate(base)

    downstream = copy.deepcopy(base)
    downstream["producer_layer"] = "L3"
    downstream["producer"] = "schema-selftest-substrate"
    downstream["parity_status"] = "PASS"
    validate(downstream)

    wrong_case = copy.deepcopy(base)
    wrong_case["case_id"] = "case-" + "f" * 64
    must_fail(wrong_case, "case_id")

    wrong_width = copy.deepcopy(base)
    wrong_width["identity_trace"] = [{"domain": 3, "bits": "00"}]
    wrong_width["identity_trace_digest"] = structured_digest(wrong_width["identity_trace"])
    must_fail(wrong_width, "payload width")

    legacy = copy.deepcopy(base)
    legacy["legacy_identity_used"] = True
    must_fail(legacy, "legacy identity")

    mismatch = copy.deepcopy(downstream)
    mismatch["observable"]["value"] = "different"
    mismatch["observable_digest"] = structured_digest(mismatch["observable"])
    must_fail(mismatch, "PASS requires")

    blocked = copy.deepcopy(base)
    blocked["producer_layer"] = "L3"
    blocked["producer"] = "schema-selftest-blocked"
    blocked["observable"] = {
        "result_kind": "BLOCKED-MECHANISM",
        "value": None,
        "error_kind": "MISSING",
        "order_trace": [],
        "mechanism_status": "BLOCKED-MECHANISM",
    }
    blocked["observable_digest"] = structured_digest(blocked["observable"])
    blocked["parity_status"] = "NOT-RUN"
    validate(blocked)

    bounded = copy.deepcopy(base)
    bounded["evidence_scope"] = "bounded-exhaustive"
    bounded["exhaustive_bound"] = {
        "domain_set": [1, 2, 3],
        "max_ast_depth": 2,
        "max_nodes": 7,
        "argument_value_bound": 2,
    }
    validate(bounded)

    missing_bound = copy.deepcopy(base)
    missing_bound["evidence_scope"] = "bounded-exhaustive"
    must_fail(missing_bound, "requires exhaustive_bound")

    print("execution-conformance schema selftest: PASS")
    print("canonical-json:", canonical_json(base["observable"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
