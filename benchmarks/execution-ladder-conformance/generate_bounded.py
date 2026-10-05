#!/usr/bin/env python3
"""Generate the Contract 11.6 bounded-exhaustive D1-D3 conformance slice.

The finite grammar is deliberately small and explicit. D2 owns structure,
D3 owns the callable primitives, and D1 appears only as an exact predicate
result of ATOM/EQ/COND. The canonical reader's ban on bare D1 source payloads
remains unchanged.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from emit_oracle import identity_trace
from validate import (
    SCHEMA,
    case_id_for,
    program_digest,
    structured_digest,
    validate,
)

BOUND = {
    "domain_set": [1, 2, 3],
    "max_ast_depth": 3,
    "max_nodes": 11,
    "argument_value_bound": 2,
}
EXPECTED_CASES = 28
EXPECTED_ROWS = EXPECTED_CASES * 2


@dataclass(frozen=True)
class Program:
    source: str
    nodes: int
    depth: int


def d3_call(head: str, *args: Program) -> Program:
    if len(head) != 3 or set(head) - {"0", "1"}:
        raise ValueError(f"D3 head must be exact three-bit text: {head!r}")
    parts = ["10", head]
    for arg in args:
        parts.extend(["00", arg.source])
    parts.append("01")
    return Program(
        source=" ".join(parts),
        nodes=1 + sum(arg.nodes for arg in args),
        depth=1 + max((arg.depth for arg in args), default=-1),
    )


def d2_list(*items: Program) -> Program:
    parts = ["10"]
    for index, item in enumerate(items):
        if index:
            parts.append("00")
        parts.append(item.source)
    parts.append("01")
    return Program(
        source=" ".join(parts),
        nodes=sum(item.nodes for item in items),
        depth=max((item.depth for item in items), default=0),
    )


def cond_call(predicate: Program, branch: Program) -> Program:
    clause = d2_list(predicate, branch)
    return Program(
        source=" ".join(["10", "110", "00", clause.source, "01"]),
        nodes=1 + predicate.nodes + branch.nodes,
        depth=1 + max(predicate.depth, branch.depth),
    )


def generate_programs() -> list[Program]:
    empty = Program("000", nodes=1, depth=0)
    pair = d3_call("111", empty, empty)
    values = [empty, pair]

    candidates: list[Program] = []

    # All current unary D3 operations over both bounded seed values.
    for head in ["001", "010", "011", "100"]:  # QUOTE ATOM CDR CAR
        for value in values:
            candidates.append(d3_call(head, value))

    # All current binary D3 operations over the Cartesian square of seed values.
    for head in ["101", "111"]:  # EQ CONS
        for left in values:
            for right in values:
                candidates.append(d3_call(head, left, right))

    # Every bounded D1-producing predicate, then every one-clause COND branch.
    predicates = [d3_call("010", value) for value in values]
    predicates.extend(
        d3_call("101", left, right)
        for left in values
        for right in values
    )
    for predicate in predicates:
        for branch in values:
            candidates.append(cond_call(predicate, branch))

    by_source: dict[str, Program] = {}
    for program in candidates:
        previous = by_source.get(program.source)
        if previous is not None and previous != program:
            raise AssertionError("same canonical source acquired inconsistent bounds")
        by_source[program.source] = program

    programs = sorted(by_source.values(), key=lambda program: program.source)
    if len(programs) != EXPECTED_CASES:
        raise AssertionError(
            f"finite grammar drift: expected {EXPECTED_CASES} unique programs, got {len(programs)}"
        )

    observed_depth = max(program.depth for program in programs)
    observed_nodes = max(program.nodes for program in programs)
    if observed_depth > BOUND["max_ast_depth"]:
        raise AssertionError(
            f"generator exceeded max_ast_depth: {observed_depth} > {BOUND['max_ast_depth']}"
        )
    if observed_nodes > BOUND["max_nodes"]:
        raise AssertionError(
            f"generator exceeded max_nodes: {observed_nodes} > {BOUND['max_nodes']}"
        )
    return programs


def git_sha(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()


def decode_hex(value: str, field: str) -> str:
    try:
        return bytes.fromhex(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"probe emitted invalid {field}: {exc}") from exc


def run_probe(helper: Path, source: str) -> dict[str, object]:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".sens", delete=False
    ) as handle:
        handle.write(source)
        source_path = Path(handle.name)

    try:
        proc = subprocess.run(
            [str(helper), str(source_path)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    finally:
        source_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(
            f"bounded probe failed exit={proc.returncode}\n"
            f"source={source!r}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )

    fields: dict[str, str] = {}
    for raw in proc.stdout.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        fields[key.strip()] = value.strip()

    required = {
        "P1_ROUNDTRIP",
        "P1_BIT_LEN",
        "P1_WIDTHS",
        "P1_PAYLOAD_HEX",
        "TRACE_HEX",
        "RESULT_KIND",
        "VALUE_HEX",
        "OUTPUT_HEX",
        "ERROR_KIND",
    }
    missing = sorted(required - fields.keys())
    if missing:
        raise ValueError(f"probe output missing fields {missing}: {proc.stdout!r}")
    if fields["P1_ROUNDTRIP"] != "1":
        raise ValueError("probe did not certify P1 round-trip")

    widths = [int(item) for item in fields["P1_WIDTHS"].split(",") if item]
    bit_len = int(fields["P1_BIT_LEN"])
    if sum(widths) != bit_len:
        raise ValueError(f"P1 bit length mismatch: widths={widths} bit_len={bit_len}")
    if not widths or set(widths) - {2, 3}:
        raise ValueError(f"Lane C source may contain only D2/D3 words, got widths={widths}")

    payload = bytes.fromhex(fields["P1_PAYLOAD_HEX"])
    if len(payload) != (bit_len + 7) // 8:
        raise ValueError("P1 byte container length does not match semantic bit length")

    result_kind = fields["RESULT_KIND"]
    if result_kind not in {"VALUE", "ERROR"}:
        raise ValueError(f"unexpected RESULT_KIND {result_kind!r}")

    value_text = decode_hex(fields["VALUE_HEX"], "VALUE_HEX")
    output_text = decode_hex(fields["OUTPUT_HEX"], "OUTPUT_HEX")
    error_kind = fields["ERROR_KIND"] or None

    if result_kind == "VALUE":
        if error_kind is not None:
            raise ValueError("VALUE probe row may not carry ERROR_KIND")
        value: str | None = value_text
    else:
        if not error_kind:
            raise ValueError("ERROR probe row requires ERROR_KIND")
        if value_text:
            raise ValueError("ERROR probe row may not carry a value")
        value = None

    trace_text = decode_hex(fields["TRACE_HEX"], "TRACE_HEX")
    return {
        "trace": identity_trace(trace_text),
        "result_kind": result_kind,
        "value": value,
        "output": output_text,
        "error_kind": error_kind,
        "p1_bit_len": bit_len,
    }


def make_rows(
    *,
    upstream_sha: str,
    program: Program,
    probe: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    observable = {
        "result_kind": probe["result_kind"],
        "value": probe["value"],
        "output": probe["output"],
        "error_kind": probe["error_kind"],
        "order_trace": [],
        "mechanism_status": "CALLABLE",
    }
    observable_digest = structured_digest(observable)
    trace = probe["trace"]
    case_id = case_id_for("canonical-source", program.source)

    common = {
        "schema": SCHEMA,
        "case_id": case_id,
        "contract": "11.6",
        "upstream_sha": upstream_sha,
        "program_encoding": "canonical-source",
        "program": program.source,
        "program_digest": program_digest(program.source),
        "identity_trace": trace,
        "identity_trace_digest": structured_digest(trace),
        "observable": observable,
        "observable_digest": observable_digest,
        "oracle_digest": observable_digest,
        "evidence_scope": "bounded-exhaustive",
        "exhaustive_bound": dict(BOUND),
        "legacy_identity_used": False,
    }

    oracle = {
        **common,
        "producer_layer": "L0",
        "producer": "sens-bounded-d1-d3-oracle",
        "parity_status": "ORACLE",
    }
    p1 = {
        **common,
        "producer_layer": "L1",
        "producer": "sens-p1-exact-width-roundtrip",
        "parity_status": "PASS",
    }
    validate(oracle)
    validate(p1)
    return oracle, p1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--helper", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    helper = args.helper.resolve()
    if not helper.is_file():
        raise FileNotFoundError(helper)

    programs = generate_programs()
    sha = git_sha(repo)

    rows: list[dict[str, object]] = []
    seen_case_ids: set[str] = set()
    for program in programs:
        probe = run_probe(helper, program.source)
        oracle, p1 = make_rows(
            upstream_sha=sha,
            program=program,
            probe=probe,
        )
        if oracle["case_id"] in seen_case_ids:
            raise AssertionError(f"duplicate case_id {oracle['case_id']}")
        seen_case_ids.add(str(oracle["case_id"]))
        rows.extend([oracle, p1])

    if len(rows) != EXPECTED_ROWS:
        raise AssertionError(f"expected {EXPECTED_ROWS} rows, got {len(rows)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    error_cases = sum(
        1
        for row in rows
        if row["producer_layer"] == "L0" and row["observable"]["result_kind"] == "ERROR"
    )
    d1_values = {
        row["observable"]["value"]
        for row in rows
        if row["producer_layer"] == "L0"
        and isinstance(row["observable"]["value"], str)
        and row["observable"]["value"].startswith("D1:")
    }
    if d1_values != {"D1:0", "D1:1"}:
        raise AssertionError(
            f"bounded D1-D3 slice must observe both exact predicate results, got {sorted(d1_values)}"
        )

    print(
        f"bounded D1-D3 cases={len(programs)} rows={len(rows)} "
        f"errors={error_cases} d1_values={sorted(d1_values)} bound={json.dumps(BOUND, sort_keys=True)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2)
