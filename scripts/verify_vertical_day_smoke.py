#!/usr/bin/env python3
"""Verify real L0 oracle output against independently pinned Vertical Day smoke witnesses.

This is a narrow, non-authoritative smoke, not a replacement for Lisp proofs
or an independent reproduction of the historical Vertical Day.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Fixed at review time from Contract 11.8 observable canonical JSON:
# {"error_kind":null,"mechanism_status":"CALLABLE","order_trace":[],
#  "output":"","result_kind":"VALUE","value":"()"}
PINNED_OBSERVABLE_SHA256 = (
    "7f7629c4dc4ff12900a1725433f0d6658dd135d407329f1c2ac3faff7cac1981"
)
CASES = {
    "d3-quote-empty": {
        "source": "10 001 00 10 01 01",
        "program_sha256": "87b24196c08b8a3fb9b5c18a3533af987a1fda993a81724a08d6c08bc1f18f8f",
        "case_id": "case-f9b4d74570855b88094754e197cda300c23f85ebef8bcc9557ddc8c079414bab",
        "required_trace": {"domain": 3, "bits": "001"},
    },
    "d3-car-empty": {
        "source": "10 100 00 10 001 00 10 10 01 01 01 01",
        "program_sha256": "c4ffdfdc37cd6bde8037d375dd8d6b069b88405a5ab89e03679b2ee3d3b79dd7",
        "case_id": "case-661ab97a58b28ab2fe89718345b2e338c5e830a7db235d94ae0dddac1f3660e4",
        "required_trace": {"domain": 3, "bits": "100"},
    },
}
OBSERVABLE = {
    "result_kind": "VALUE",
    "value": "()",
    "output": "",
    "error_kind": None,
    "order_trace": [],
    "mechanism_status": "CALLABLE",
}
SHA40 = re.compile(r"^[a-f0-9]{40}$")


def digest(value: object) -> str:
    canonical = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify(rows: list[dict], expected_sha: str) -> str:
    if not SHA40.fullmatch(expected_sha):
        raise ValueError("expected upstream commit must be an exact 40-hex SHA")
    if len(rows) != len(CASES):
        raise ValueError(f"expected {len(CASES)} real oracle rows, got {len(rows)}")
    if digest(OBSERVABLE) != PINNED_OBSERVABLE_SHA256:
        raise ValueError("checked-in observable golden digest is inconsistent")
    seen: set[str] = set()
    for row in rows:
        producer = row.get("producer")
        if not isinstance(producer, str) or not producer.startswith("sens-oracle:"):
            raise ValueError(f"unexpected producer: {producer!r}")
        case_name = producer.removeprefix("sens-oracle:")
        if case_name not in CASES or case_name in seen:
            raise ValueError(f"unexpected or duplicate oracle case {case_name!r}")
        seen.add(case_name)
        pin = CASES[case_name]
        if hashlib.sha256(pin["source"].encode("utf-8")).hexdigest() != pin["program_sha256"]:
            raise ValueError(f"{case_name}: pinned program SHA is inconsistent")
        for key, expected in (
            ("schema", "sens-execution-conformance/v1"),
            ("contract", "11.8"),
            ("upstream_sha", expected_sha),
            ("producer_layer", "L0"),
            ("program_encoding", "canonical-source"),
            ("program", pin["source"]),
            ("program_digest", pin["program_sha256"]),
            ("case_id", pin["case_id"]),
            ("oracle_digest", PINNED_OBSERVABLE_SHA256),
            ("observable_digest", PINNED_OBSERVABLE_SHA256),
            ("parity_status", "ORACLE"),
            ("evidence_scope", "fixture"),
            ("legacy_identity_used", False),
        ):
            if row.get(key) != expected:
                raise ValueError(f"{case_name}: {key} drift: {row.get(key)!r}")
        if row.get("observable") != OBSERVABLE:
            raise ValueError(f"{case_name}: observable differs from pinned witness")
        trace = row.get("identity_trace")
        if not isinstance(trace, list) or pin["required_trace"] not in trace:
            raise ValueError(f"{case_name}: missing canonical D3 identity in trace")
        if row.get("identity_trace_digest") != digest(trace):
            raise ValueError(f"{case_name}: trace digest mismatch")
    if seen != set(CASES):
        raise ValueError(f"missing oracle cases: {set(CASES) - seen}")
    # This SHA is a diagnostic, not a substitute for the pinned hashes above.
    proof = [(name, CASES[name]["program_sha256"], PINNED_OBSERVABLE_SHA256) for name in sorted(seen)]
    return digest(proof)


def self_test() -> None:
    sha = "a" * 40
    rows = []
    for name, pin in CASES.items():
        trace = [pin["required_trace"]]
        rows.append({
            "schema": "sens-execution-conformance/v1",
            "contract": "11.8",
            "upstream_sha": sha,
            "producer_layer": "L0",
            "producer": "sens-oracle:" + name,
            "program_encoding": "canonical-source",
            "program": pin["source"],
            "program_digest": pin["program_sha256"],
            "case_id": pin["case_id"],
            "observable": OBSERVABLE.copy(),
            "observable_digest": PINNED_OBSERVABLE_SHA256,
            "oracle_digest": PINNED_OBSERVABLE_SHA256,
            "identity_trace": trace,
            "identity_trace_digest": digest(trace),
            "parity_status": "ORACLE",
            "evidence_scope": "fixture",
            "legacy_identity_used": False,
        })
    verify(rows, sha)
    for mutate in ("observable", "oracle_digest", "upstream_sha", "identity_trace"):
        changed = json.loads(json.dumps(rows))
        if mutate == "observable":
            changed[0][mutate]["value"] = "t"
        elif mutate == "identity_trace":
            changed[0][mutate] = []
        else:
            changed[0][mutate] = "0" * 64
        try:
            verify(changed, sha)
        except ValueError:
            continue
        raise AssertionError(f"tampered {mutate} was accepted")
    print("VERTICAL_DAY_SMOKE_SELFTEST_PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("oracle_jsonl", nargs="?", type=Path)
    parser.add_argument("--expected-sha")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if args.oracle_jsonl is None or not args.expected_sha:
        parser.error("oracle_jsonl and --expected-sha required")
    rows = [
        json.loads(line)
        for line in args.oracle_jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    fingerprint = verify(rows, args.expected_sha)
    print(f"VERTICAL_DAY_IMMUTABLE_ORACLE_PASS sha={args.expected_sha} cases={len(rows)} golden={PINNED_OBSERVABLE_SHA256} manifest_fingerprint={fingerprint}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"VERTICAL_DAY_IMMUTABLE_ORACLE_FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
