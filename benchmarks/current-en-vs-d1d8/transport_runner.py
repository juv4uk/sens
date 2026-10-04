#!/usr/bin/env python3
"""#3137 current English vs canonical D1-D8 representation preflight.

This runner emits paired representation rows only after both candidates lower to
the same exact-domain trace and execute to the same oracle. Standalone framing
fields stay null until #2189 selects the production envelope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "sens-current-en-vs-d1d8/v1"
WORKLOAD_SCHEMA = "sens-current-en-vs-d1d8-workloads/v1"
CANDIDATES = ("english-surface", "canonical-d1d8")

INT_FIELDS = {
    "source_bytes": "SOURCE_BYTES",
    "lowered_ast_nodes": "LOWERED_AST_NODES",
    "semantic_payload_bits": "SEMANTIC_PAYLOAD_BITS",
    "framing_bits": "FRAMING_BITS",
    "tail_unused_bits": "TAIL_UNUSED_BITS",
    "total_wire_bits": "TOTAL_WIRE_BITS",
    "packed_bytes": "PACKED_BYTES",
    "payload_container_bits": "PAYLOAD_CONTAINER_BITS",
    "canonical_artifact_bytes": "CANONICAL_ARTIFACT_BYTES",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_text(command: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def git_sha(repo: Path) -> str:
    return run_text(["git", "rev-parse", "HEAD"], repo)


def rustc_version() -> str:
    try:
        return run_text(["rustc", "--version"])
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def provenance() -> dict[str, object]:
    return {
        "runner": "transport_accounting/v1",
        "os": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu": cpu_model(),
        "python": platform.python_version(),
        "rustc": rustc_version(),
        "standalone_framing": "blocked:#2189",
    }


def decode_hex(value: str, field: str) -> str:
    try:
        return bytes.fromhex(value).decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"invalid {field}: {exc}") from exc


def parse_optional_int(value: str, field: str) -> int | None:
    if value == "NA":
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be integer or NA: {value!r}") from exc


def parse_optional_float(value: str, field: str) -> float | None:
    if value == "NA":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be float or NA: {value!r}") from exc


def parse_helper_output(stdout: str) -> dict[str, object]:
    fields: dict[str, str] = {}
    for raw in stdout.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        fields[key.strip()] = value.strip()

    required = {
        "TRACE_HEX",
        "VALUE_HEX",
        "OUTPUT_HEX",
        *INT_FIELDS.values(),
        "PACKING_EFFICIENCY",
    }
    missing = sorted(required - fields.keys())
    if missing:
        raise ValueError(f"helper output missing fields: {missing}; stdout={stdout!r}")

    metrics = {
        output_name: parse_optional_int(fields[helper_name], helper_name)
        for output_name, helper_name in INT_FIELDS.items()
    }
    metrics["packing_efficiency"] = parse_optional_float(
        fields["PACKING_EFFICIENCY"], "PACKING_EFFICIENCY"
    )

    return {
        "trace": decode_hex(fields["TRACE_HEX"], "TRACE_HEX"),
        "value": decode_hex(fields["VALUE_HEX"], "VALUE_HEX"),
        "output": decode_hex(fields["OUTPUT_HEX"], "OUTPUT_HEX"),
        "metrics": metrics,
    }


def run_helper(helper: Path, candidate: str, source_path: Path) -> dict[str, object]:
    proc = subprocess.run(
        [str(helper), candidate, str(source_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"helper failed candidate={candidate} exit={proc.returncode}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return parse_helper_output(proc.stdout)


def build_helper(repo: Path) -> Path:
    subprocess.run(
        [
            "cargo",
            "build",
            "--release",
            "-p",
            "sens",
            "--example",
            "current_en_vs_d1d8_transport",
        ],
        cwd=repo,
        check=True,
    )
    suffix = ".exe" if os.name == "nt" else ""
    helper = repo / "target" / "release" / "examples" / f"current_en_vs_d1d8_transport{suffix}"
    if not helper.is_file():
        raise FileNotFoundError(helper)
    return helper


def load_manifest(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != WORKLOAD_SCHEMA:
        raise ValueError(f"manifest schema must be {WORKLOAD_SCHEMA}")
    workloads = data.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        raise ValueError("manifest must contain non-empty workloads")
    seen: set[str] = set()
    for item in workloads:
        if not isinstance(item, dict):
            raise ValueError("every workload must be an object")
        workload_id = item.get("id")
        if not isinstance(workload_id, str) or not workload_id:
            raise ValueError("every workload needs a non-empty id")
        if workload_id in seen:
            raise ValueError(f"duplicate workload id: {workload_id}")
        seen.add(workload_id)
        if item.get("status") != "ready":
            raise ValueError(f"{workload_id}: transport preflight fixture must be ready")
        if not isinstance(item.get("english_source"), str):
            raise ValueError(f"{workload_id}: english_source required")
        if not isinstance(item.get("canonical_source"), str):
            raise ValueError(f"{workload_id}: canonical_source required")
    return data


def write_source(tmp: Path, workload_id: str, candidate: str, source: str) -> Path:
    path = tmp / f"{workload_id}.{candidate}.lisp"
    path.write_text(source, encoding="utf-8")
    return path


def evidence_row(
    *,
    candidate: str,
    workload: str,
    current_git_sha: str,
    binary_sha: str,
    corpus_sha: str,
    common_provenance: dict[str, object],
    metrics: dict[str, object],
) -> dict[str, object]:
    pair_id = f"{workload}:representation:0"
    return {
        "schema": SCHEMA,
        "pair_id": pair_id,
        "case_id": f"{pair_id}:{candidate}",
        "lane": "transport",
        "candidate": candidate,
        "workload": workload,
        "phase": "representation",
        "rep": 0,
        "language_model": "D1-D8",
        "legacy_identity_used": False,
        "oracle_ok": True,
        "git_sha": current_git_sha,
        "binary_sha256": binary_sha,
        "corpus_sha256": corpus_sha,
        "provenance": common_provenance,
        "metrics": metrics,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--helper", type=Path)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    manifest_path = args.manifest.resolve()
    manifest_bytes = manifest_path.read_bytes()
    manifest = load_manifest(manifest_path)
    corpus_sha = sha256_bytes(manifest_bytes)
    current_git_sha = git_sha(repo)

    helper = args.helper.resolve() if args.helper else build_helper(repo)
    if not helper.is_file():
        raise FileNotFoundError(helper)
    binary_sha = sha256_file(helper)
    common_provenance = provenance()

    rows: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="sens-current-transport-") as tmp_name:
        tmp = Path(tmp_name)
        for workload_obj in manifest["workloads"]:
            workload = dict(workload_obj)
            workload_id = str(workload["id"])
            sources = {
                "english-surface": str(workload["english_source"]),
                "canonical-d1d8": str(workload["canonical_source"]),
            }
            observed: dict[str, dict[str, object]] = {}
            for candidate in CANDIDATES:
                path = write_source(tmp, workload_id, candidate, sources[candidate])
                observed[candidate] = run_helper(helper, candidate, path)

            english = observed["english-surface"]
            binary = observed["canonical-d1d8"]
            for field in ("trace", "value", "output"):
                if english[field] != binary[field]:
                    raise ValueError(
                        f"{workload_id}: preflight mismatch for {field}: "
                        f"english={english[field]!r} canonical={binary[field]!r}"
                    )

            expected_value = workload.get("expected_value")
            if expected_value is not None and english["value"] != expected_value:
                raise ValueError(
                    f"{workload_id}: expected value {expected_value!r}, got {english['value']!r}"
                )
            expected_output = workload.get("expected_output")
            if expected_output is not None and english["output"] != expected_output:
                raise ValueError(
                    f"{workload_id}: expected output {expected_output!r}, got {english['output']!r}"
                )

            en_metrics = dict(english["metrics"])
            bin_metrics = dict(binary["metrics"])

            if en_metrics["lowered_ast_nodes"] != bin_metrics["lowered_ast_nodes"]:
                raise ValueError(
                    f"{workload_id}: lowered AST node count mismatch: "
                    f"{en_metrics['lowered_ast_nodes']} vs {bin_metrics['lowered_ast_nodes']}"
                )

            for key in (
                "semantic_payload_bits",
                "framing_bits",
                "tail_unused_bits",
                "total_wire_bits",
                "packed_bytes",
                "payload_container_bits",
                "packing_efficiency",
                "canonical_artifact_bytes",
            ):
                if en_metrics[key] is not None:
                    raise ValueError(
                        f"{workload_id}: English lane must not invent canonical metric {key}"
                    )

            if bin_metrics["semantic_payload_bits"] is None or bin_metrics["packed_bytes"] is None:
                raise ValueError(f"{workload_id}: canonical payload accounting missing")
            if bin_metrics["framing_bits"] is not None or bin_metrics["total_wire_bits"] is not None:
                raise ValueError(
                    f"{workload_id}: standalone framing must remain unresolved until #2189"
                )

            for candidate, metrics in (
                ("english-surface", en_metrics),
                ("canonical-d1d8", bin_metrics),
            ):
                rows.append(
                    evidence_row(
                        candidate=candidate,
                        workload=workload_id,
                        current_git_sha=current_git_sha,
                        binary_sha=binary_sha,
                        corpus_sha=corpus_sha,
                        common_provenance=common_provenance,
                        metrics=metrics,
                    )
                )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"wrote {len(rows)} current paired transport rows to {args.out}")
    print("standalone framing fields remain null until #2189")
    print("no compression ratio or language-wide winner is computed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
