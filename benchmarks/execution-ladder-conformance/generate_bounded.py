#!/usr/bin/env python3
"""Generate the first bounded-exhaustive D2/D3 structural conformance slice."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from validate import validate

WORKLOAD_SCHEMA = "sens-current-en-vs-d1d8-workloads/v1"
BOUND = {
    "domain_set": [2, 3],
    "max_ast_depth": 4,
    "max_nodes": 12,
    "argument_value_bound": 2,
}
PROFILE = "d2-d3-structural-v1"


def list_form(items: list[str]) -> str:
    tokens = ["10"]
    for index, item in enumerate(items):
        if index:
            tokens.append("00")
        tokens.append(item)
    tokens.append("01")
    return " ".join(tokens)


def call(bits: str, args: list[str]) -> str:
    return list_form([bits, *args])


def data_values() -> list[str]:
    empty = list_form([])
    values = [
        empty,
        list_form([empty]),
        list_form([empty, empty]),
    ]
    return sorted(set(values))


def source_shape(program: str) -> tuple[int, int]:
    """Return (max list depth, expression-node count) for canonical source.

    D2 open creates one list node; each D3 callable word creates one identity
    node. D2 separators/closes are syntax, not AST nodes in this bounded profile.
    """
    depth = 0
    max_depth = 0
    nodes = 0
    for token in program.split():
        if token == "10":
            depth += 1
            max_depth = max(max_depth, depth)
            nodes += 1
        elif token == "01":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unbalanced canonical source: {program!r}")
        elif token in {"001", "011", "100", "111"}:
            nodes += 1
    if depth != 0:
        raise ValueError(f"unbalanced canonical source: {program!r}")
    return max_depth, nodes


def generated_programs() -> tuple[list[dict[str, str]], int]:
    data = data_values()
    empty = list_form([])
    nonempty = [value for value in data if value != empty]

    candidates: list[tuple[str, str]] = []

    for value in data:
        candidates.append(("quote", call("001", [value])))

    for value in nonempty:
        candidates.append(("car", call("100", [call("001", [value])])))
        candidates.append(("cdr", call("011", [call("001", [value])])))

    for left in data:
        for right in data:
            candidates.append(
                ("cons", call("111", [call("001", [left]), call("001", [right])]))
            )

    raw_count = len(candidates)
    unique: dict[str, str] = {}
    for role, program in candidates:
        unique.setdefault(program, role)

    rows = []
    for index, program in enumerate(sorted(unique), 1):
        rows.append(
            {
                "id": f"bounded-{index:03d}-{unique[program]}",
                "status": "ready",
                "canonical_source": program,
            }
        )
    return rows, raw_count


def run_checked(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(command)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def verify_pack_roundtrip(helper: Path, source: str, path: Path) -> dict[str, int]:
    path.write_text(source, encoding="utf-8")
    proc = run_checked([str(helper), str(path)])
    fields: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip()

    if fields.get("ROUNDTRIP") != "OK":
        raise RuntimeError(f"pack helper did not report ROUNDTRIP=OK: {proc.stdout!r}")

    required = ("TOKENS", "SEMANTIC_BITS", "PACKED_BITS", "PACKED_BYTES")
    missing = [name for name in required if name not in fields]
    if missing:
        raise RuntimeError(f"pack helper missing fields {missing}: {proc.stdout!r}")

    result = {name.lower(): int(fields[name]) for name in required}
    if result["semantic_bits"] != result["packed_bits"]:
        raise RuntimeError(
            f"semantic bits != packed bits for {source!r}: {result}"
        )
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--oracle-helper", required=True, type=Path)
    ap.add_argument("--pack-helper", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--summary", required=True, type=Path)
    args = ap.parse_args()

    repo = Path(__file__).resolve().parents[2]
    emit_oracle = repo / "benchmarks/execution-ladder-conformance/emit_oracle.py"

    workloads, raw_count = generated_programs()
    if len(workloads) != 16:
        raise AssertionError(f"expected 16 unique structural cases, got {len(workloads)}")

    for workload in workloads:
        depth, nodes = source_shape(workload["canonical_source"])
        if depth > BOUND["max_ast_depth"] or nodes > BOUND["max_nodes"]:
            raise AssertionError(
                f"{workload['id']} exceeds declared bound: depth={depth} nodes={nodes}"
            )

    pack_rows = []

    with tempfile.TemporaryDirectory(prefix="sens-bounded-") as tmp_name:
        tmp = Path(tmp_name)

        for workload in workloads:
            source_path = tmp / f"{workload['id']}.lisp"
            pack = verify_pack_roundtrip(
                args.pack_helper.resolve(), workload["canonical_source"], source_path
            )
            pack_rows.append({"id": workload["id"], **pack})

        manifest = {
            "schema": WORKLOAD_SCHEMA,
            "purpose": (
                "Bounded-exhaustive Contract 11.6 D2/D3 structural conformance slice. "
                "Grammar is defined by generate_bounded.py."
            ),
            "workloads": workloads,
        }
        manifest_path = tmp / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )

        oracle_path = tmp / "oracle.jsonl"
        run_checked(
            [
                sys.executable,
                str(emit_oracle),
                "--manifest",
                str(manifest_path),
                "--helper",
                str(args.oracle_helper.resolve()),
                "--out",
                str(oracle_path),
            ],
            cwd=repo,
        )

        rows = [
            json.loads(line)
            for line in oracle_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    if len(rows) != len(workloads):
        raise RuntimeError(
            f"oracle emitted {len(rows)} rows for {len(workloads)} generated cases"
        )

    case_ids = set()
    for row in rows:
        row["evidence_scope"] = "bounded-exhaustive"
        row["exhaustive_bound"] = BOUND
        row["producer"] = "sens-bounded-oracle:" + row["producer"].split(":", 1)[-1]
        validate(row)
        if row["case_id"] in case_ids:
            raise RuntimeError(f"duplicate case_id: {row['case_id']}")
        case_ids.add(row["case_id"])

    rows.sort(key=lambda row: row["case_id"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    summary = {
        "schema": "sens-bounded-conformance-summary/v1",
        "contract": "11.6",
        "profile": PROFILE,
        "claim": "exhaustive within the declared D2/D3 structural grammar and bound",
        "bound": BOUND,
        "generated_cases": raw_count,
        "raw_candidates": raw_count,
        "deduplicated_cases": len(workloads),
        "oracle_rows": len(rows),
        "pack_roundtrip_rows": len(pack_rows),
        "grammar": {
            "data_values": [
                "()",
                "(())",
                "(() ())",
            ],
            "programs": [
                "QUOTE(data)",
                "CAR(QUOTE(nonempty-data))",
                "CDR(QUOTE(nonempty-data))",
                "CONS(QUOTE(data), QUOTE(data))",
            ],
            "excluded": [
                "ATOM/EQ/COND predicate slice pending an independent exact-D1 oracle witness",
                "D4-D7",
                "malformed/error cases",
            ],
        },
        "transport": {
            "all_rows_round_trip": True,
            "semantic_bits_equal_packed_bits": True,
            "rows": sorted(pack_rows, key=lambda row: row["id"]),
        },
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        "bounded structural corpus:",
        f"raw={raw_count}",
        f"deduplicated={len(workloads)}",
        f"oracle={len(rows)}",
        f"pack-roundtrip={len(pack_rows)}",
    )
    print(json.dumps(BOUND, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
