#!/usr/bin/env python3
"""Contract 11.8 phase decomposition for current SENS.

This is measurement glue only. It reuses the existing current helpers:
- current_en_vs_d1d8_cpu for paired semantic preflight and process modes;
- startup_bench for Core4 bootstrap mechanism diagnostics.

No benchmark-local evaluator, reader, lowering table, or semantic fallback is
introduced here. Timing is admitted only after English/canonical parity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import tempfile
from pathlib import Path

CONTRACT_VERSION = "11.8"
SEMANTIC_GENERATION = "contract-11-8-exact-d1-d9"
REPEAT_LADDER = (1, 10, 100)
CANDIDATES = ("ukrainian-surface", "canonical-d1d8")
IREF_RE = re.compile(r"I\s+refs:\s*([\d,]+)")
CONTRACT_RE = re.compile(
    r"\(\(major\s+\.\s+#d(?P<major>[0-9]+)\)\s+\(minor\s+\.\s+(?P<minor>[0-9]+)\)"
)


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def require_ok(command: list[str]) -> subprocess.CompletedProcess[str]:
    proc = run(command)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(command)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def cachegrind_i_refs(command: list[str]) -> int:
    proc = run([
        "valgrind",
        "--tool=cachegrind",
        "--cache-sim=no",
        "--cachegrind-out-file=/dev/null",
        *command,
    ])
    if proc.returncode != 0:
        raise RuntimeError(
            f"cachegrind failed ({proc.returncode}): {' '.join(command)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    match = IREF_RE.search(proc.stderr)
    if match is None:
        raise RuntimeError(f"Cachegrind did not report I refs:\n{proc.stderr}")
    return int(match.group(1).replace(",", ""))


def sample_i_refs(command: list[str], reps: int) -> tuple[int, list[int]]:
    samples = [cachegrind_i_refs(command) for _ in range(reps)]
    return int(statistics.median(samples)), samples


def parse_kv(stdout: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key.strip()] = value.strip()
    return fields


def decode_hex(value: str) -> str:
    return bytes.fromhex(value).decode("utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_sha(repo: Path) -> str:
    return require_ok(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()


def current_contract(repo: Path) -> str:
    text = (repo / "language-contract.lisp").read_text(encoding="utf-8")
    match = CONTRACT_RE.search(text)
    if match is None:
        raise ValueError("cannot read language contract version")
    return f"{match.group('major')}.{match.group('minor')}"


def slope(xs: tuple[int, ...], ys: list[int]) -> tuple[float, float]:
    xbar = sum(xs) / len(xs)
    ybar = sum(ys) / len(ys)
    denom = sum((x - xbar) ** 2 for x in xs)
    if denom == 0:
        raise ValueError("repeat ladder needs distinct x values")
    m = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom
    b = ybar - m * xbar
    return m, b


def load_ready_workloads(path: Path) -> list[dict[str, object]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    workloads = data.get("workloads")
    if not isinstance(workloads, list):
        raise ValueError("workloads must be a list")
    ready = [row for row in workloads if isinstance(row, dict) and row.get("status") == "ready"]
    if not ready:
        raise ValueError("no ready current workloads")
    return ready


def source_for(workload: dict[str, object], candidate: str) -> str:
    key = "ukrainian_source" if candidate == "ukrainian-surface" else "canonical_source"
    value = workload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{workload.get('id')}: missing {key}")
    return value


def preflight(
    helper: Path,
    workload: dict[str, object],
    tmp: Path,
) -> dict[str, object]:
    observed: dict[str, dict[str, str]] = {}
    wid = str(workload["id"])
    for candidate in CANDIDATES:
        path = tmp / f"{wid}.{candidate}.lisp"
        path.write_text(source_for(workload, candidate), encoding="utf-8")
        fields = parse_kv(
            require_ok([str(helper), candidate, "preflight", str(path)]).stdout
        )
        for key in ("TRACE_HEX", "VALUE_HEX", "OUTPUT_HEX"):
            if key not in fields:
                raise ValueError(f"{wid}/{candidate}: missing {key}")
        observed[candidate] = {
            "trace": decode_hex(fields["TRACE_HEX"]),
            "value": decode_hex(fields["VALUE_HEX"]),
            "output": decode_hex(fields["OUTPUT_HEX"]),
        }

    left = observed["ukrainian-surface"]
    right = observed["canonical-d1d8"]
    if left != right:
        raise ValueError(f"{wid}: paired Ukrainian/canonical semantic preflight mismatch: {observed!r}")

    expected_value = workload.get("expected_value")
    expected_output = workload.get("expected_output")
    if expected_value is not None and left["value"] != expected_value:
        raise ValueError(
            f"{wid}: expected value {expected_value!r}, observed {left['value']!r}"
        )
    if expected_output is not None and left["output"] != expected_output:
        raise ValueError(
            f"{wid}: expected output {expected_output!r}, observed {left['output']!r}"
        )

    digest = hashlib.sha256(
        (left["trace"] + "\x00" + left["value"] + "\x00" + left["output"]).encode("utf-8")
    ).hexdigest()
    return {
        "trace": left["trace"],
        "value": left["value"],
        "output": left["output"],
        "semantic_identity_digest": digest,
        "legacy_identity_used": "Sid(" in left["trace"] or "Call(" in left["trace"],
    }


def measure_candidate(
    helper: Path,
    candidate: str,
    source_path: Path,
    reps: int,
) -> dict[str, object]:
    def mode(phase: str, repeat: int | None = None) -> tuple[int, list[int]]:
        cmd = [str(helper), candidate, phase, str(source_path)]
        if repeat is not None:
            cmd.append(str(repeat))
        return sample_i_refs(cmd, reps)

    phase_names = ("baseline", "session", "ingest", "lower", "ready", "execute", "full")
    phase_measurements = {phase: mode(phase) for phase in phase_names}
    raw = {phase: phase_measurements[phase][0] for phase in phase_names}
    raw_samples = {phase: phase_measurements[phase][1] for phase in phase_names}

    repeated_measurements = {n: mode("repeated", n) for n in REPEAT_LADDER}
    repeated = {n: repeated_measurements[n][0] for n in REPEAT_LADDER}
    repeated_samples = {str(n): repeated_measurements[n][1] for n in REPEAT_LADDER}
    repeated_slope, repeated_intercept = slope(
        REPEAT_LADDER, [repeated[n] for n in REPEAT_LADDER]
    )

    derived = {
        "session_minus_baseline_i_refs": raw["session"] - raw["baseline"],
        "ingest_minus_baseline_i_refs": raw["ingest"] - raw["baseline"],
        "lower_minus_ingest_i_refs": raw["lower"] - raw["ingest"],
        "ready_minus_baseline_i_refs": raw["ready"] - raw["baseline"],
        "execute_minus_ready_i_refs": raw["execute"] - raw["ready"],
        "full_minus_baseline_i_refs": raw["full"] - raw["baseline"],
        "repeated_slope_i_refs_per_eval": repeated_slope,
        "repeated_intercept_i_refs": repeated_intercept,
    }
    for name, value in derived.items():
        if name != "execute_minus_ready_i_refs" and value < 0:
            raise ValueError(f"{candidate}: negative derived phase {name}={value}")

    return {
        "raw_i_refs": raw,
        "raw_i_ref_samples": raw_samples,
        "repeated_i_refs": {str(k): v for k, v in repeated.items()},
        "repeated_i_ref_samples": repeated_samples,
        "derived": derived,
    }


def core_bootstrap(startup: Path, fasl: Path, reps: int) -> dict[str, object]:
    modes = (
        "root",
        "session",
        "bytes",
        "decode",
        "parse",
        "macro",
        "core",
        "root-macro",
        "root-core",
    )
    raw: dict[str, int] = {}
    samples: dict[str, list[int]] = {}
    for mode in modes:
        cmd = [str(startup), mode]
        if mode in {"bytes", "decode"}:
            cmd.append(str(fasl))
        raw[mode], samples[mode] = sample_i_refs(cmd, reps)

    return {
        "raw_i_refs": raw,
        "raw_i_ref_samples": samples,
        "delta_vs_root_i_refs": {mode: raw[mode] - raw["root"] for mode in modes if mode != "root"},
        "delta_vs_session_i_refs": {
            mode: raw[mode] - raw["session"]
            for mode in ("bytes", "decode", "parse", "macro", "core")
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--helper", type=Path, required=True)
    ap.add_argument("--startup-helper", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--fasl", type=Path, default=Path("lib/core4.lisp.fasl"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--reps", type=int, default=1)
    args = ap.parse_args()

    if args.reps < 1:
        raise ValueError("--reps must be >= 1")

    repo = Path(__file__).resolve().parents[2]
    helper = args.helper.resolve()
    startup = args.startup_helper.resolve()
    manifest = args.manifest.resolve()
    fasl = args.fasl.resolve()
    for path in (helper, startup, manifest, fasl):
        if not path.exists():
            raise FileNotFoundError(path)

    contract = current_contract(repo)
    if contract != CONTRACT_VERSION:
        raise ValueError(
            f"this replay is generation-pinned to Contract {CONTRACT_VERSION}; found {contract}"
        )

    ready = load_ready_workloads(manifest)
    rows: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="sens-phase-3490-") as tmp_name:
        tmp = Path(tmp_name)
        for workload in ready:
            wid = str(workload["id"])
            witness = preflight(helper, workload, tmp)
            if witness["legacy_identity_used"]:
                raise ValueError(f"{wid}: legacy identity entered current phase replay")
            for candidate in CANDIDATES:
                path = tmp / f"{wid}.{candidate}.lisp"
                measurement = measure_candidate(helper, candidate, path, args.reps)
                rows.append({
                    "case_id": wid,
                    "candidate": candidate,
                    "oracle": witness,
                    "measurement": measurement,
                })

    report = {
        "schema": "sens-current-phase-decomposition/v1",
        "contract_version": contract,
        "semantic_generation": SEMANTIC_GENERATION,
        "repo": "juv4uk/sens",
        "git_sha": git_sha(repo),
        "current_foundation": "D1-D9",
        "measured_current_cases": [str(row["id"]) for row in ready],
        "blocked_headline_manifest": "benchmarks/current-en-vs-d1d8/workloads.json",
        "helper_sha256": sha256_file(helper),
        "startup_helper_sha256": sha256_file(startup),
        "core4_fasl_sha256": sha256_file(fasl),
        "reps": args.reps,
        "repeat_ladder": list(REPEAT_LADDER),
        "core_bootstrap": core_bootstrap(startup, fasl, args.reps),
        "rows": rows,
        "claim_boundary": (
            "current admitted D3 smoke cases only; no general language speed claim; "
            "historical blocked headline workloads are not revived"
        ),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Compact human-readable summary for the CI job summary.
    print(f"generation={report['semantic_generation']}")
    print(f"git_sha={report['git_sha']}")
    print(f"core4_fasl_sha256={report['core4_fasl_sha256']}")
    print(f"cases={','.join(report['measured_current_cases'])}")
    for row in rows:
        d = row["measurement"]["derived"]
        print(
            f"{row['case_id']} {row['candidate']} "
            f"ingest={d['ingest_minus_baseline_i_refs']:.0f} "
            f"lower={d['lower_minus_ingest_i_refs']:.0f} "
            f"ready={d['ready_minus_baseline_i_refs']:.0f} "
            f"full={d['full_minus_baseline_i_refs']:.0f} "
            f"slope={d['repeated_slope_i_refs_per_eval']:.3f}"
        )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2)
