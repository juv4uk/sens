"""Guarded serial coordinator; never overwrites a prior evidence directory."""

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from report import render
from svg import boxplot_svg, histogram_svg

ROOT = Path(__file__).resolve().parents[1]
WARMUPS = 10
SAMPLES = 100


def invoke_json(command: list[str], timeout: int = 180) -> dict:
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{command[0]} returned non-JSON output (exit {result.returncode}): {result.stderr[-1000:]}") from error
    if result.returncode:
        raise RuntimeError(payload.get("error", f"command failed with exit {result.returncode}"))
    return payload


def normalize(value):
    if isinstance(value, str):
        if value.startswith("(") and value.endswith(")"):
            return [int(part) for part in value[1:-1].split()]
        try:
            return int(value)
        except ValueError:
            return value
    return value


def validate_pair(sens: dict, python: dict, expected, workload_id: str) -> None:
    for label, run in (("SENS", sens), ("CPython", python)):
        if run.get("status") != "PASS" or run.get("parity") != "PASS":
            raise RuntimeError(f"{workload_id}: {label} parity/status gate failed")
        if run.get("n") != SAMPLES or len(run.get("samples", [])) != SAMPLES:
            raise RuntimeError(f"{workload_id}: {label} requires exactly {SAMPLES} raw samples")
        if run.get("warmups") != WARMUPS:
            raise RuntimeError(f"{workload_id}: {label} requires exactly {WARMUPS} warmups")
        if any(sample.get("ordinal") != index or not isinstance(sample.get("elapsed_ns"), int)
               or sample["elapsed_ns"] <= 0 for index, sample in enumerate(run["samples"], 1)):
            raise RuntimeError(f"{workload_id}: {label} raw sample ordinals/durations are invalid")
        if normalize(run.get("output")) != expected:
            raise RuntimeError(f"{workload_id}: {label} output differs from fixed expected result")
    for field in ("os", "architecture"):
        sens_value = sens.get("runtime_metadata", {}).get(field)
        python_value = python.get("runtime_metadata", {}).get(field)
        if not isinstance(sens_value, str) or not isinstance(python_value, str) or sens_value.casefold() != python_value.casefold():
            raise RuntimeError(f"{workload_id}: implementations ran on different {field} values")
    if normalize(sens["output"]) != normalize(python["output"]):
        raise RuntimeError(f"{workload_id}: implementations are not semantically in parity")


def validate_build_profile(profile: str | None) -> str:
    if profile != "release":
        raise RuntimeError(f"SENS runner must be a verified release build; check reports profile={profile!r}")
    return profile


def validate_run_id(run_id: str | None) -> None:
    if run_id is not None and (run_id in (".", "..") or
                               not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", run_id)):
        raise RuntimeError("run-id must be a 1–64 character filename component using letters, digits, dot, underscore, or hyphen")


def record_failure(run_dir: Path | None, workload: str | None, error: Exception) -> None:
    if run_dir is not None and run_dir.exists():
        failure = {"status": "FAIL", "workload": workload, "error": str(error)}
        (run_dir / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")


def create_run_directory(runs_root: Path, run_id: str) -> Path:
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def workload_manifest() -> dict:
    return json.loads((ROOT / "workloads.json").read_text())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path).encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def source_hashes(item: dict) -> dict[str, str]:
    sens_paths = [ROOT / item[key] for key in ("sens_setup", "sens_call") if key in item]
    inputs = {}
    if "expected_fixture" in item:
        inputs["expected_fixture"] = sha256_file(ROOT / item["expected_fixture"])
    return {
        "sens_source": hashlib.sha256(b"".join(path.read_bytes() for path in sens_paths)).hexdigest(),
        "python_source": hashlib.sha256((ROOT / "python" / "workloads.py").read_bytes()
                                         + (ROOT / "python" / "run.py").read_bytes()).hexdigest(),
        "workload_definition": hashlib.sha256(json.dumps(item, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        **inputs,
    }


def host_metadata() -> dict:
    cpu_model = "unknown"
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.lower().startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    return {
        "hostname": platform.node(), "os": platform.platform(),
        "uname": platform.uname()._asdict(), "architecture": platform.machine(),
        "cpu_model": cpu_model, "cpu_count": os.cpu_count(),
        "cpu_affinity": sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None,
        "wsl_release": Path("/proc/sys/kernel/osrelease").read_text().strip()
        if Path("/proc/sys/kernel/osrelease").exists() else None,
    }


def git_metadata() -> dict:
    def git(*args):
        return subprocess.run(["git", *args], cwd=ROOT.parents[2], capture_output=True, text=True,
                              timeout=10, check=False).stdout.strip()
    return {"commit": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
            "dirty": bool(git("status", "--porcelain")), "dirty_paths": git("status", "--short").splitlines()}


def preflight() -> str:
    result = subprocess.run(["timeout", "30", "wsm-agent", "bench-ready"], capture_output=True,
                            text=True, timeout=35, check=False)
    evidence = (result.stdout + result.stderr).strip()
    if result.returncode or "READY" not in evidence or "NOT READY" in evidence:
        raise RuntimeError(f"benchmark preflight is not READY: {evidence}")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sens-runner", required=True, type=Path)
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    run_dir = None
    current_workload = None
    try:
        validate_run_id(args.run_id)
        runs_root = args.runs.resolve()
        try:
            runs_root.relative_to(ROOT.resolve())
        except ValueError as error:
            raise RuntimeError("runs directory must stay inside this benchmark directory") from error
        ready_evidence = preflight()
        manifest = workload_manifest()
        check = invoke_json([str(args.sens_runner), "check"])
        if check.get("overall_status") != "PASS" or check.get("passing_workloads", 0) < 3:
            raise RuntimeError(f"SENS semantic gate did not qualify: {check}")
        profile = validate_build_profile(check.get("runtime_metadata", {}).get("profile"))
        run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_dir = create_run_directory(runs_root, run_id)
        raw_dir = run_dir / "raw"
        raw_dir.mkdir()
        paired = {}
        execution_order = []
        candidates = [item for item in manifest["workloads"] if item.get("status") == "candidate"]
        for index, item in enumerate(candidates):
            workload_id = item["id"]
            current_workload = workload_id
            commands = {
                "SENS": [str(args.sens_runner), "run", workload_id],
                "CPython source": [sys.executable, "-B", str(ROOT / "python" / "run.py"), workload_id],
            }
            order = ["SENS", "CPython source"] if index % 2 == 0 else ["CPython source", "SENS"]
            outputs = {implementation: invoke_json(commands[implementation], timeout=900)
                       for implementation in order}
            sens, py = outputs["SENS"], outputs["CPython source"]
            validate_pair(sens, py, item["expected"], workload_id)
            if sens.get("runtime_metadata", {}).get("profile") != profile:
                raise RuntimeError(f"{workload_id}: timed SENS output profile does not match release preflight")
            hashes = source_hashes(item)
            for run, source_field in ((sens, "sens_source"), (py, "python_source")):
                for sample in run["samples"]:
                    sample["source_sha256"] = hashes[source_field]
                    sample["workload_sha256"] = hashes["workload_definition"]
            sens["source_hashes"] = hashes
            py["source_hashes"] = hashes
            sens["implementation"] = "SENS"
            (raw_dir / f"{workload_id}.sens.json").write_text(json.dumps(sens, indent=2) + "\n")
            (raw_dir / f"{workload_id}.python.json").write_text(json.dumps(py, indent=2) + "\n")
            paired[workload_id] = {"SENS": sens, "CPython source": py}
            execution_order.append({"workload": workload_id, "implementations": order})
        metadata = {
            "schema_version": 1, "run_id": run_id, "created_utc": datetime.now(timezone.utc).isoformat(),
            "host": host_metadata(), "python": sys.version, "rustc": subprocess.run(
                ["rustc", "--version"], capture_output=True, text=True, timeout=10).stdout.strip(),
            "sens_build_profile": profile, "git": git_metadata(), "preflight": ready_evidence,
            "method": manifest["run_protocol"], "sens_semantic_gate": check,
            "workloads_manifest_sha256": sha256_file(ROOT / "workloads.json"),
            "sens_runner_sha256": sha256_file(args.sens_runner.resolve()),
            "sens_runner_source_sha256": sha256_file(ROOT / "runner" / "src" / "main.rs"),
            "sens_runner_cargo_manifest_sha256": sha256_file(ROOT / "runner" / "Cargo.toml"),
            "sens_runner_cargo_lock_sha256": sha256_file(ROOT / "runner" / "Cargo.lock"),
            "sens_crate_source_sha256": tree_sha256(list((ROOT.parents[2] / "crates" / "sens" / "src").rglob("*.rs"))),
            "execution_order": execution_order,
        }
        (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
        report = render(run_dir, manifest, paired, metadata)
        (run_dir / "report.uk.md").write_text(report)
        graph_dir = run_dir / "plots"
        graph_dir.mkdir()
        for workload_id, result in paired.items():
            series = {label: [sample["elapsed_ns"] for sample in run["samples"]]
                      for label, run in result.items()}
            (graph_dir / f"{workload_id}-boxplot.svg").write_text(boxplot_svg(series, workload_id))
            (graph_dir / f"{workload_id}-histogram.svg").write_text(histogram_svg(series, workload_id))
        print(json.dumps({"status": "PASS", "run_dir": str(run_dir), "workloads": list(paired)}, indent=2))
        return 0
    except Exception as error:
        record_failure(run_dir, current_workload, error)
        print(json.dumps({"status": "FAIL", "workload": current_workload, "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
