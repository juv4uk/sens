#!/usr/bin/env python3
"""Compare transparent delivery-size models for the same validated ladder corpus.

The framed model is an explicit research format, not a production protocol. All
fixed overheads are named in code so results cannot be mistaken for a universal
binary-vs-text law.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
OBJECTIVE_DIR = HERE.parent
sys.path.insert(0, str(OBJECTIVE_DIR))
from run import load_rows, exact_width_metrics  # noqa: E402

MAGIC = b"SENS-LADDER-PKG\0"  # 16 bytes
VERSION = 1
CONTRACT = b"11.6"
DIGEST_BYTES = 32
CASE_ID_BYTES = 32


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def packed_bits(program: str) -> bytes:
    bits = "".join(program.split())
    padded = bits + "0" * ((8 - len(bits) % 8) % 8)
    return bytes(int(padded[index:index + 8], 2) for index in range(0, len(padded), 8))


def frame_case(row: dict) -> bytes:
    tokens = row["program"].split()
    payload = packed_bits(row["program"])
    case_id = bytes.fromhex(row["case_id"][5:])
    observable_digest = bytes.fromhex(row["observable_digest"])
    if len(case_id) != CASE_ID_BYTES or len(observable_digest) != DIGEST_BYTES:
        raise ValueError("digest width mismatch")
    # case id + observable digest + word count + exact word widths + bit length + payload
    return (
        case_id
        + observable_digest
        + struct.pack(">H", len(tokens))
        + bytes(len(token) for token in tokens)
        + struct.pack(">H", len("".join(tokens)))
        + payload
    )


def framed_package(rows: list[dict], artifact_sha256: str) -> bytes:
    header = (
        MAGIC
        + bytes([VERSION])
        + CONTRACT
        + struct.pack(">I", len(rows))
        + bytes.fromhex(artifact_sha256)
    )
    frames = []
    for row in rows:
        frame = frame_case(row)
        frames.append(struct.pack(">I", len(frame)) + frame)
    return header + b"".join(frames)


def package_report(artifact: Path, runtime: Path | None) -> dict:
    rows = load_rows(artifact)
    artifact_sha = hashlib.sha256(artifact.read_bytes()).hexdigest()
    metrics = [exact_width_metrics(row["program"]) for row in rows]
    semantic_payload = sum(item["dense_packed_bytes_lower_bound"] for item in metrics)
    source_bytes = sum(item["canonical_source_utf8_bytes"] for item in metrics)
    package = framed_package(rows, artifact_sha)
    runtime_bytes = runtime.stat().st_size if runtime else None
    return {
        "schema": "sens-execution-ladder-delivery-cost/v1",
        "measurement_kind": "delivery-size-model",
        "wall_clock_measured": False,
        "format_status": "research-model-not-production-protocol",
        "artifact": str(artifact),
        "artifact_sha256": artifact_sha,
        "validated_cases": len(rows),
        "parity_failures": 0,
        "models": {
            "canonical_text_utf8": {
                "bytes": source_bytes,
                "includes": "program text only",
            },
            "dense_semantic_payload_lower_bound": {
                "bytes": semantic_payload,
                "includes": "bit payload only; no framing or metadata",
            },
            "framed_semantic_package": {
                "bytes": len(package),
                "includes": "header, artifact digest, case ids, observable digests, widths, lengths, packed bits",
                "header_bytes": len(MAGIC) + 1 + len(CONTRACT) + 4 + DIGEST_BYTES,
            },
            "self_contained_package": {
                "bytes": None if runtime_bytes is None else len(package) + runtime_bytes,
                "runtime_bytes": runtime_bytes,
                "includes": "framed semantic package plus supplied runtime file",
            },
        },
        "format_constants": {
            "magic_bytes": len(MAGIC),
            "version_bytes": 1,
            "contract_bytes": len(CONTRACT),
            "case_count_bytes": 4,
            "artifact_digest_bytes": DIGEST_BYTES,
            "case_id_bytes": CASE_ID_BYTES,
            "observable_digest_bytes": DIGEST_BYTES,
            "frame_length_bytes": 4,
        },
        "interpretation": "Only the supplied artifact and optional runtime file are measured; channel, compression, encryption, signatures, retries and loader behavior are excluded.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--runtime", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.runtime and not args.runtime.is_file():
        raise FileNotFoundError(args.runtime)
    report = package_report(args.artifact, args.runtime)
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    models = report["models"]
    print(
        "validated cases={cases} text={text} dense_lb={dense} framed={framed} self_contained={selfc}".format(
            cases=report["validated_cases"],
            text=models["canonical_text_utf8"]["bytes"],
            dense=models["dense_semantic_payload_lower_bound"]["bytes"],
            framed=models["framed_semantic_package"]["bytes"],
            selfc=models["self_contained_package"]["bytes"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
