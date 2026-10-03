#!/usr/bin/env python3
"""#2644 — corpus runner for the canonical #2642 human-wire timing model.

This file deliberately reuses benchmarks/human-wire/model.py as the timing
authority. It adds only:
- deterministic shared payload fixtures;
- explicit outer framing/checksum bytes;
- live current-main sens-wire corpus sampling via agent_bench;
- CSV/JSON/report aggregation.

MECHANISM ONLY. No human throughput or semantic/domain claim follows.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import random
import struct
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "benchmarks" / "human-wire"
MODEL = HERE / "model.py"
PAYLOADS = HERE / "payloads.json"
AGENT_RUN = ROOT / "benchmarks" / "agent-messages" / "run.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deterministic_bytes(n_bits: int, seed: int) -> bytes:
    if n_bits % 8:
        raise ValueError("shared fixture payload_bits must be byte-aligned")
    rng = random.Random(seed)
    return bytes(rng.getrandbits(8) for _ in range(n_bits // 8))


def overhead_bytes(framing_bits: int, checksum_bits: int, seed: int) -> bytes:
    total = framing_bits + checksum_bits
    if total % 8:
        raise ValueError("current corpus runner requires byte-aligned outer overhead")
    rng = random.Random(seed ^ 0xA11CE)
    return bytes(rng.getrandbits(8) for _ in range(total // 8))


def parse_records(path: Path) -> list[bytes]:
    data = path.read_bytes()
    records: list[bytes] = []
    pos = 0
    while pos < len(data):
        if pos + 4 > len(data):
            raise ValueError("truncated record length")
        (size,) = struct.unpack_from("<I", data, pos)
        pos += 4
        end = pos + size
        if end > len(data):
            raise ValueError("truncated record payload")
        records.append(data[pos:end])
        pos = end
    return records


def current_wire_records(agent_bench: Path, sample_n: int, seed: int) -> list[bytes]:
    am = load_module(AGENT_RUN, "human_wire_agent_messages")
    rng = random.Random(seed)
    messages = [am.gen_message(rng, i) for i in range(sample_n)]

    with tempfile.TemporaryDirectory(prefix="sens-human-wire-") as td:
        td = Path(td)
        text_in = td / "messages-sens-text.bin"
        wire_out = td / "messages-sens-wire.bin"
        am.write_records(text_in, [am.lisp(msg, am.SENS).encode() for msg in messages])
        subprocess.run(
            [str(agent_bench), "encode", "wire", str(text_in), str(wire_out)],
            check=True,
            cwd=ROOT,
        )
        return parse_records(wire_out)


def rows_for_frame(
    model,
    fixture_id: str,
    payload: bytes,
    outer: bytes,
    unit_ms: float,
) -> list[dict[str, object]]:
    frame = payload + outer
    out = []
    for result in model.compare(frame, payload_bits=len(payload) * 8, unit_ms=unit_ms):
        row = asdict(result)
        row["fixture_id"] = fixture_id
        row["outer_overhead_bits"] = len(outer) * 8
        row["semantic_authority"] = "NONE"
        out.append(row)
    return out


def write_outputs(out: Path, rows: list[dict[str, object]], meta: dict[str, object]) -> None:
    out.mkdir(parents=True, exist_ok=True)

    (out / "timing.json").write_text(
        json.dumps({"meta": meta, "rows": rows}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (out / "timing.csv").open("w", encoding="utf-8", newline="") as fh:
        fields = list(rows[0].keys())
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Human-wire corpus timing",
        "",
        f"Unit duration: {meta['unit_ms']} ms.",
        f"Outer framing: {meta['framing_bits']} bits; checksum: {meta['checksum_bits']} bits.",
        "",
        "| fixture | protocol | payload bits | transmitted bits | units | seconds | net payload bit/s |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['fixture_id']} | {row['protocol']} | {row['payload_bits']} | "
            f"{row['transmitted_bits']} | {row['timing_units']} | "
            f"{row['seconds']:.3f} | {row['net_payload_bps']:.3f} |"
        )

    current = meta.get("current_wire_sample")
    if isinstance(current, dict):
        lines += [
            "",
            "## Current-main sens-wire sample",
            "",
            f"- N={current['sample_n']}, seed={current['seed']}",
            f"- avg={current['avg_bytes']:.3f} B ({current['avg_bits']:.1f} bits)",
            f"- min={current['min_bytes']} B; max={current['max_bytes']} B",
            "- this is a variable-size corpus measurement, not a fixed canonical envelope size;",
            "- historical #1845 published average 34.3 B remains provenance only.",
        ]

    lines += [
        "",
        "## Boundary",
        "",
        "- Protocol timing is not measured human throughput.",
        "- Fixed-slot capacity becomes a human claim only after #2645 trials.",
        "- Outer overhead is transport, never semantic payload.",
        "- This benchmark cannot alter domains, identities, roots or coordinates.",
        "",
    ]
    (out / "report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--unit-ms", type=float, default=60.0)
    ap.add_argument("--framing-bits", type=int, default=16)
    ap.add_argument("--checksum-bits", type=int, default=16)
    ap.add_argument("--agent-bench", type=Path)
    ap.add_argument("--wire-sample-n", type=int, default=100)
    ap.add_argument("--wire-seed", type=int, default=1)
    args = ap.parse_args()

    if args.unit_ms <= 0:
        raise SystemExit("unit-ms must be positive")
    if min(args.framing_bits, args.checksum_bits) < 0:
        raise SystemExit("overhead bits must be non-negative")

    model = load_module(MODEL, "human_wire_model")
    manifest = json.loads(PAYLOADS.read_text(encoding="utf-8"))
    assert manifest["schema"] == "human-wire-payloads/v1"

    rows: list[dict[str, object]] = []
    for fixture in manifest["fixtures"]:
        payload = deterministic_bytes(int(fixture["payload_bits"]), int(fixture["seed"]))
        outer = overhead_bytes(
            args.framing_bits,
            args.checksum_bits,
            int(fixture["seed"]),
        )
        rows.extend(
            rows_for_frame(
                model,
                str(fixture["id"]),
                payload,
                outer,
                args.unit_ms,
            )
        )

    meta: dict[str, object] = {
        "schema": "human-wire-corpus-timing/v1",
        "issue": 2644,
        "layer": "MECHANISM",
        "timing_authority": "benchmarks/human-wire/model.py",
        "payload_manifest": "benchmarks/human-wire/payloads.json",
        "unit_ms": args.unit_ms,
        "framing_bits": args.framing_bits,
        "checksum_bits": args.checksum_bits,
        "historical_wire_provenance": {
            "issue": 1845,
            "published_date": "2026-09-30",
            "published_avg_bytes": 34.3,
            "bounded_fixture_bits": 272,
            "authority": "provenance/reproducibility only",
        },
    }

    if args.agent_bench:
        records = current_wire_records(args.agent_bench, args.wire_sample_n, args.wire_seed)
        sizes = [len(record) for record in records]
        meta["current_wire_sample"] = {
            "status": "measured-current-main",
            "sample_n": len(records),
            "seed": args.wire_seed,
            "avg_bytes": sum(sizes) / len(sizes),
            "avg_bits": 8 * sum(sizes) / len(sizes),
            "min_bytes": min(sizes),
            "max_bytes": max(sizes),
        }

        outer = overhead_bytes(args.framing_bits, args.checksum_bits, args.wire_seed)
        for protocol in ["hex-morse", "duration-binary", "dual-key-binary", "fixed-slot-binary"]:
            subset = []
            for record in records:
                result = next(
                    x for x in model.compare(
                        record + outer,
                        payload_bits=len(record) * 8,
                        unit_ms=args.unit_ms,
                    )
                    if x.protocol == protocol
                )
                subset.append(result)
            rows.append(
                {
                    "protocol": protocol,
                    "payload_bits": sum(x.payload_bits for x in subset) / len(subset),
                    "transmitted_bits": sum(x.transmitted_bits for x in subset) / len(subset),
                    "timing_units": sum(x.timing_units for x in subset) / len(subset),
                    "unit_ms": args.unit_ms,
                    "seconds": sum(x.seconds for x in subset) / len(subset),
                    "equivalent_frame_bps": sum(x.equivalent_frame_bps for x in subset) / len(subset),
                    "net_payload_bps": sum(x.net_payload_bps for x in subset) / len(subset),
                    "assistance": subset[0].assistance,
                    "note": "average over live current-main sens-wire records",
                    "fixture_id": "current-main-wire-sample",
                    "outer_overhead_bits": len(outer) * 8,
                    "semantic_authority": "NONE",
                }
            )

    # Guard the original conceptual mistake mechanically.
    fixed_rows = [r for r in rows if r["protocol"] == "fixed-slot-binary"]
    duration_rows = [r for r in rows if r["protocol"] == "duration-binary"]
    assert fixed_rows and duration_rows
    assert all(r["timing_units"] == r["transmitted_bits"] for r in fixed_rows)
    assert all(r["timing_units"] >= r["transmitted_bits"] for r in duration_rows)

    write_outputs(args.out, rows, meta)

    print("HUMAN-WIRE-CORPUS-TIMING=PASS")
    print("timing-authority=benchmarks/human-wire/model.py")
    print("payload-manifest=benchmarks/human-wire/payloads.json")
    print("RULE=timing-units-are-not-information-bits")
    print("SEMANTIC-AUTHORITY=NONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
