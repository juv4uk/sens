#!/usr/bin/env python3
"""Emit first real L0 oracle rows from the current exact-domain D3 smoke path."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from validate import (
    SCHEMA,
    case_id_for,
    program_digest,
    structured_digest,
    validate,
)

WORKLOAD_SCHEMA = "sens-current-en-vs-d1d8-workloads/v1"
IDENTITY = re.compile(r"(?:id|call):D([1-8]):([01]+)")


def git_sha(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()


def parse_helper_output(stdout: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in stdout.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        fields[key.strip()] = value.strip()

    required = {"TRACE_HEX", "VALUE_HEX", "OUTPUT_HEX"}
    missing = sorted(required - fields.keys())
    if missing:
        raise ValueError(f"helper output missing fields: {missing}; stdout={stdout!r}")

    def decode_hex(name: str) -> str:
        try:
            return bytes.fromhex(fields[name]).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f"invalid {name}: {exc}") from exc

    return {
        "trace": decode_hex("TRACE_HEX"),
        "value": decode_hex("VALUE_HEX"),
        "output": decode_hex("OUTPUT_HEX"),
    }


def identity_trace(trace: str) -> list[dict[str, object]]:
    result = []
    for match in IDENTITY.finditer(trace):
        domain = int(match.group(1))
        bits = match.group(2)
        if len(bits) != domain:
            raise ValueError(
                f"helper emitted non-exact identity D{domain}:{bits!r}"
            )
        result.append({"domain": domain, "bits": bits})
    if not result:
        raise ValueError(f"helper emitted no exact-domain identities: {trace!r}")
    return result


def build_helper(repo: Path) -> Path:
    subprocess.run(
        [
            "cargo",
            "build",
            "--release",
            "-p",
            "sens",
            "--example",
            "current_en_vs_d1d8_cpu",
        ],
        cwd=repo,
        check=True,
    )
    helper = repo / "target/release/examples/current_en_vs_d1d8_cpu"
    if not helper.is_file():
        raise FileNotFoundError(helper)
    return helper


def run_oracle(helper: Path, source_path: Path) -> dict[str, str]:
    proc = subprocess.run(
        [str(helper), "canonical-d1d8", "preflight", str(source_path)],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"oracle helper failed exit={proc.returncode}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return parse_helper_output(proc.stdout)


def load_manifest(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != WORKLOAD_SCHEMA:
        raise ValueError(f"manifest schema must be {WORKLOAD_SCHEMA}")
    workloads = data.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        raise ValueError("manifest must contain non-empty workloads")
    return data


def row_for(
    *,
    upstream_sha: str,
    producer: str,
    program: str,
    helper_result: dict[str, str],
) -> dict[str, object]:
    trace = identity_trace(helper_result["trace"])
    observable = {
        "result_kind": "VALUE",
        "value": helper_result["value"],
        "output": helper_result["output"],
        "error_kind": None,
        "order_trace": [],
        "mechanism_status": "CALLABLE",
    }
    digest = structured_digest(observable)
    row = {
        "schema": SCHEMA,
        "case_id": case_id_for("canonical-source", program),
        "contract": "11.6",
        "upstream_sha": upstream_sha,
        "producer_layer": "L0",
        "producer": producer,
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
    validate(row)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--helper", type=Path)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    manifest = load_manifest(args.manifest.resolve())
    helper = args.helper.resolve() if args.helper else build_helper(repo)
    if not helper.is_file():
        raise FileNotFoundError(helper)

    current_sha = git_sha(repo)
    rows = []
    blocked = []

    with tempfile.TemporaryDirectory(prefix="sens-oracle-") as tmp_name:
        tmp = Path(tmp_name)
        for item in manifest["workloads"]:
            workload = dict(item)
            workload_id = workload.get("id")
            if workload.get("status") == "blocked":
                blocked.append(str(workload_id))
                continue
            if workload.get("status") != "ready":
                raise ValueError(f"{workload_id}: expected ready or blocked")

            source = workload.get("canonical_source")
            if not isinstance(source, str) or not source:
                raise ValueError(f"{workload_id}: ready workload lacks canonical_source")

            source_path = tmp / f"{workload_id}.lisp"
            source_path.write_text(source, encoding="utf-8")
            result = run_oracle(helper, source_path)

            expected_value = workload.get("expected_value")
            if expected_value is not None and result["value"] != expected_value:
                raise ValueError(
                    f"{workload_id}: expected value {expected_value!r}, "
                    f"oracle returned {result['value']!r}"
                )
            expected_output = workload.get("expected_output")
            if expected_output is not None and result["output"] != expected_output:
                raise ValueError(
                    f"{workload_id}: expected output {expected_output!r}, "
                    f"oracle returned {result['output']!r}"
                )

            rows.append(
                row_for(
                    upstream_sha=current_sha,
                    producer=f"sens-oracle:{workload_id}",
                    program=source,
                    helper_result=result,
                )
            )

    if not rows:
        raise ValueError("no ready oracle cases were emitted")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"emitted {len(rows)} real L0 oracle rows -> {args.out}")
    print(f"blocked manifest cases preserved but not fabricated: {','.join(blocked) or 'none'}")
    for row in rows:
        print(
            f"{row['producer']} {row['case_id']} "
            f"oracle={row['oracle_digest']} trace={row['identity_trace_digest']}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
