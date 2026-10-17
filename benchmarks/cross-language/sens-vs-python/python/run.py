"""Persistent-process CPython measurement runner for one manifest workload."""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
from workloads import ackermann, binary_trees_checks, fib  # noqa: E402

WARMUPS = 10
SAMPLES = 100


def rss_kib(field: str) -> int:
    for line in Path("/proc/self/status").read_text().splitlines():
        if line.startswith(field + ":"):
            return int(line.split()[1])
    raise RuntimeError(f"/proc/self/status has no {field}")


def invoke(workload: dict):
    params = workload["parameters"]
    callable_name = workload["python_callable"]
    if callable_name == "fib":
        return fib(params["N"])
    if callable_name == "ackermann":
        return ackermann(params["m"], params["n"])
    if callable_name == "binary_trees_checks":
        return binary_trees_checks(params["N"])
    raise ValueError(f"unsupported Python callable: {callable_name}")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 -B run.py <workload-id>")
    manifest = json.loads((ROOT / "workloads.json").read_text())
    workload_id = sys.argv[1]
    workload = next((row for row in manifest["workloads"] if row["id"] == workload_id), None)
    if workload is None or workload.get("status") != "candidate":
        print(json.dumps({"status": "FAIL", "error": f"workload {workload_id} is not runnable"}))
        return 2
    expected = workload["expected"]
    parity_value = invoke(workload)
    if parity_value != expected:
        print(json.dumps({"status": "FAIL", "error": f"parity failed: expected {expected!r}, got {parity_value!r}"}))
        return 2
    for _ in range(WARMUPS):
        invoke(workload)
    baseline = rss_kib("VmRSS")
    samples = []
    for ordinal in range(1, SAMPLES + 1):
        start = time.perf_counter_ns()
        result = invoke(workload)
        elapsed = time.perf_counter_ns() - start
        samples.append({"ordinal": ordinal, "elapsed_ns": elapsed, "result": result})
    peak = rss_kib("VmHWM")
    print(json.dumps({
        "schema_version": 1,
        "workload": workload_id,
        "implementation": "CPython source",
        "status": "PASS",
        "parity": "PASS",
        "warmups": WARMUPS,
        "n": len(samples),
        "samples": samples,
        "output": parity_value,
        "rss_kib": {"baseline_after_warmup": baseline, "peak_vmhwm": peak,
                    "delta_peak_from_baseline": max(0, peak - baseline)},
        "runtime_metadata": {"python": sys.version.split()[0], "implementation": sys.implementation.name,
                             "executable": sys.executable, "os": os.uname().sysname,
                             "architecture": os.uname().machine}
    }, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
