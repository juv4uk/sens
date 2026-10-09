#!/usr/bin/env python3
"""Paired CPU phase harness for the current Ukrainian surface vs canonical binary D1-D8.

This runner is deliberately evidence-first:
- both candidates use the same compiled helper binary;
- a semantic/output preflight must pass before any timed row is emitted;
- blocked workloads are written to a separate readiness report;
- no speed ratio or winner is computed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCHEMA = "sens-current-en-vs-d1d8/v1"
WORKLOAD_SCHEMA = "sens-current-en-vs-d1d8-workloads/v1"
BLOCKED_SCHEMA = "sens-current-en-vs-d1d8-blocked/v1"
CANDIDATES = ("ukrainian-surface", "canonical-d1d8")
DEFAULT_PHASES = ("session", "ingest", "lower", "execute", "full")
VALID_PHASES = set(DEFAULT_PHASES) | {"repeated"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_text(command: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(command, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def git_sha(repo: Path) -> str:
    return run_text(["git", "rev-parse", "HEAD"], repo)


def rustc_version() -> str:
    try:
        return run_text(["rustc", "--version"])
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def valgrind_version() -> str:
    if not shutil.which("valgrind"):
        return "unavailable"
    try:
        return run_text(["valgrind", "--version"])
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def cpu_model() -> str:
    path = Path("/proc/cpuinfo")
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("model name") and ":" in line:
                return line.split(":", 1)[1].strip()
    return platform.processor() or "unknown"


def provenance(repeat_n: int) -> dict[str, object]:
    return {
        "runner": "cpu_phase_runner/v1",
        "os": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "cpu": cpu_model(),
        "python": platform.python_version(),
        "rustc": rustc_version(),
        "valgrind": valgrind_version(),
        "repeat_n": repeat_n,
    }


def parse_helper_output(stdout: str) -> dict[str, object]:
    fields: dict[str, str] = {}
    for raw in stdout.splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        fields[key.strip()] = value.strip()

    required = {"ELAPSED_NS", "TRACE_HEX", "VALUE_HEX", "OUTPUT_HEX"}
    missing = sorted(required - fields.keys())
    if missing:
        raise ValueError(f"helper output missing fields: {missing}; stdout={stdout!r}")

    def decode_hex(name: str) -> str:
        try:
            return bytes.fromhex(fields[name]).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f"invalid {name}: {exc}") from exc

    return {
        "elapsed_ns": int(fields["ELAPSED_NS"]),
        "trace": decode_hex("TRACE_HEX"),
        "value": decode_hex("VALUE_HEX"),
        "output": decode_hex("OUTPUT_HEX"),
    }


def run_helper(
    helper: Path,
    candidate: str,
    phase: str,
    source_path: Path,
    repeat_n: int,
) -> tuple[dict[str, object], dict[str, int]]:
    command = [str(helper), candidate, phase, str(source_path)]
    if phase == "repeated":
        command.append(str(repeat_n))

    started = time.perf_counter_ns()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_b = b""
    stderr_b = b""
    if os.name == "posix" and hasattr(os, "wait4"):
        assert proc.stdout is not None and proc.stderr is not None
        stdout_b = proc.stdout.read()
        stderr_b = proc.stderr.read()
        _, status, usage = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status)
        user_ns = int(usage.ru_utime * 1_000_000_000)
        sys_ns = int(usage.ru_stime * 1_000_000_000)
        peak_rss_kb = int(usage.ru_maxrss)
    else:
        stdout_b, stderr_b = proc.communicate()
        user_ns = -1
        sys_ns = -1
        peak_rss_kb = -1
    process_wall_ns = time.perf_counter_ns() - started

    stdout = stdout_b.decode("utf-8", "replace")
    stderr = stderr_b.decode("utf-8", "replace")
    if proc.returncode != 0:
        raise RuntimeError(
            f"helper failed candidate={candidate} phase={phase} exit={proc.returncode}\n"
            f"stdout:\n{stdout}\nstderr:\n{stderr}"
        )

    parsed = parse_helper_output(stdout)
    resources = {
        "process_wall_ns": process_wall_ns,
        "process_user_ns": user_ns,
        "process_sys_ns": sys_ns,
        "process_peak_rss_kb": peak_rss_kb,
    }
    return parsed, resources


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
    suffix = ".exe" if os.name == "nt" else ""
    helper = repo / "target" / "release" / "examples" / f"current_en_vs_d1d8_cpu{suffix}"
    if not helper.is_file():
        raise FileNotFoundError(f"built helper not found: {helper}")
    return helper


def load_manifest(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != WORKLOAD_SCHEMA:
        raise ValueError(f"manifest schema must be {WORKLOAD_SCHEMA}")
    workloads = data.get("workloads")
    if not isinstance(workloads, list) or not workloads:
        raise ValueError("manifest must contain non-empty workloads")
    ids: set[str] = set()
    for item in workloads:
        if not isinstance(item, dict):
            raise ValueError("every workload must be an object")
        workload_id = item.get("id")
        if not isinstance(workload_id, str) or not workload_id:
            raise ValueError("every workload needs a non-empty id")
        if workload_id in ids:
            raise ValueError(f"duplicate workload id: {workload_id}")
        ids.add(workload_id)
        if item.get("status") not in {"ready", "blocked"}:
            raise ValueError(f"{workload_id}: status must be ready or blocked")
    return data


def write_source(tmp: Path, workload_id: str, candidate: str, text: str) -> Path:
    safe_candidate = candidate.replace("/", "-")
    path = tmp / f"{workload_id}.{safe_candidate}.lisp"
    path.write_text(text, encoding="utf-8")
    return path


def preflight_pair(
    helper: Path,
    tmp: Path,
    workload: dict[str, object],
    repeat_n: int,
) -> tuple[dict[str, Path], dict[str, object]]:
    workload_id = str(workload["id"])
    ukrainian = workload.get("ukrainian_source")
    binary = workload.get("canonical_source")
    if not isinstance(ukrainian, str) or not isinstance(binary, str):
        raise ValueError(f"{workload_id}: ready workload needs ukrainian_source and canonical_source")

    paths = {
        "ukrainian-surface": write_source(tmp, workload_id, "ukrainian-surface", ukrainian),
        "canonical-d1d8": write_source(tmp, workload_id, "canonical-d1d8", binary),
    }
    observed: dict[str, dict[str, object]] = {}
    for candidate in CANDIDATES:
        result, _ = run_helper(helper, candidate, "preflight", paths[candidate], repeat_n)
        observed[candidate] = result

    left = observed["ukrainian-surface"]
    right = observed["canonical-d1d8"]
    for field in ("trace", "value", "output"):
        if left[field] != right[field]:
            raise ValueError(
                f"{workload_id}: preflight mismatch for {field}: "
                f"ukrainian={left[field]!r} canonical={right[field]!r}"
            )

    expected_value = workload.get("expected_value")
    if expected_value is not None and left["value"] != expected_value:
        raise ValueError(
            f"{workload_id}: oracle value mismatch: expected={expected_value!r} got={left['value']!r}"
        )
    expected_output = workload.get("expected_output")
    if expected_output is not None and left["output"] != expected_output:
        raise ValueError(
            f"{workload_id}: oracle output mismatch: expected={expected_output!r} got={left['output']!r}"
        )

    return paths, {
        "trace": left["trace"],
        "value": left["value"],
        "output": left["output"],
    }


def evidence_row(
    *,
    pair_id: str,
    case_id: str,
    candidate: str,
    workload: str,
    phase: str,
    rep: int,
    current_git_sha: str,
    binary_sha: str,
    corpus_sha: str,
    common_provenance: dict[str, object],
    metrics: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "pair_id": pair_id,
        "case_id": case_id,
        "lane": "cpu",
        "candidate": candidate,
        "workload": workload,
        "phase": phase,
        "rep": rep,
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
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("workloads.json"),
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--blocked-out", type=Path)
    parser.add_argument("--helper", type=Path)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--repeat-n", type=int, default=10)
    parser.add_argument(
        "--phases",
        default=",".join(DEFAULT_PHASES),
        help="comma-separated subset of session,ingest,lower,execute,full,repeated",
    )
    args = parser.parse_args()

    if args.reps < 1:
        raise ValueError("--reps must be >= 1")
    if args.repeat_n < 1:
        raise ValueError("--repeat-n must be >= 1")
    phases = tuple(part.strip() for part in args.phases.split(",") if part.strip())
    if not phases or any(phase not in VALID_PHASES for phase in phases):
        raise ValueError(f"invalid --phases: {args.phases}")

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
    common_provenance = provenance(args.repeat_n)

    blocked: list[dict[str, object]] = []
    rows: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="sens-current-en-vs-d1d8-") as tmp_name:
        tmp = Path(tmp_name)
        for workload_obj in manifest["workloads"]:
            workload = dict(workload_obj)
            workload_id = str(workload["id"])
            if workload["status"] == "blocked":
                blocked.append(
                    {
                        "workload": workload_id,
                        "reason": workload.get("reason", "not ready"),
                        "blockers": workload.get("blockers", []),
                    }
                )
                continue

            paths, oracle = preflight_pair(helper, tmp, workload, args.repeat_n)
            for phase in phases:
                for rep in range(args.reps):
                    pair_id = f"{workload_id}:{phase}:{rep}"
                    measured: dict[str, tuple[dict[str, object], dict[str, int]]] = {}
                    for candidate in CANDIDATES:
                        measured[candidate] = run_helper(
                            helper,
                            candidate,
                            phase,
                            paths[candidate],
                            args.repeat_n,
                        )

                    for candidate in CANDIDATES:
                        result, resources = measured[candidate]
                        if phase in {"execute", "full", "repeated"}:
                            if result["value"] != oracle["value"] or result["output"] != oracle["output"]:
                                raise ValueError(
                                    f"{workload_id}: timed {candidate}/{phase} changed oracle result"
                                )
                        metrics: dict[str, object] = {
                            "phase_elapsed_ns": result["elapsed_ns"],
                            **resources,
                        }
                        if phase == "repeated":
                            metrics["repeat_n"] = args.repeat_n
                        rows.append(
                            evidence_row(
                                pair_id=pair_id,
                                case_id=f"{pair_id}:{candidate}",
                                candidate=candidate,
                                workload=workload_id,
                                phase=phase,
                                rep=rep,
                                current_git_sha=current_git_sha,
                                binary_sha=binary_sha,
                                corpus_sha=corpus_sha,
                                common_provenance=common_provenance,
                                metrics=metrics,
                            )
                        )

    blocked_path = args.blocked_out or args.out.with_suffix(".blocked.json")
    blocked_payload = {
        "schema": BLOCKED_SCHEMA,
        "git_sha": current_git_sha,
        "corpus_sha256": corpus_sha,
        "blocked": blocked,
    }
    blocked_path.parent.mkdir(parents=True, exist_ok=True)
    blocked_path.write_text(
        json.dumps(blocked_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if rows:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"wrote {len(rows)} current paired CPU rows to {args.out}")
    else:
        if args.out.exists():
            args.out.unlink()
        print("no timing rows emitted: every production workload is BLOCKED")

    print(f"blocked workloads: {len(blocked)} -> {blocked_path}")
    print("no ratio or winner is computed by this harness")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
