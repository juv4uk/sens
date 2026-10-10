#!/usr/bin/env python3
"""Вичерпний реєстровий прогін: виконати кожен bench.json або чесно зафіксувати блокер.

Це launcher відтворення існуючих дослідів, а не новий кодек і не
міжмашинний статистичний оракул продуктивності.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
LAB = ROOT / "benchmarks"
SCHEMA = "sens-benchmark-manifest/v1"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest_list() -> list[dict]:
    manifests = []
    for path in sorted(LAB.glob("*/bench.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("schema") != SCHEMA or value.get("stand") != path.parent.name:
            raise ValueError(f"invalid benchmark manifest: {path}")
        reproduce = value.get("reproduce")
        if not isinstance(reproduce, str) or not reproduce.strip():
            raise ValueError(f"missing reproduce command: {path}")
        manifests.append({
            "stand": path.parent.name,
            "reproduce": reproduce,
            "manifest_sha256": sha(path),
            "manifest_path": str(path.relative_to(ROOT)),
        })
    if not manifests or len({m["stand"] for m in manifests}) != len(manifests):
        raise ValueError("no manifests or duplicate stands")
    return manifests


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.strip()


def host() -> dict:
    return {
        "os": platform.platform(),
        "cpu": platform.processor() or platform.machine(),
        "python": platform.python_version(),
        "cargo": shutil.which("cargo"),
        "rustc": shutil.which("rustc"),
        "valgrind": shutil.which("valgrind"),
        "runner": os.getenv("RUNNER_NAME"),
        "github_sha": os.getenv("GITHUB_SHA"),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
    }


def run_one(m: dict, *, timeout: int, out: Path, head: str, system: dict) -> dict:
    start = time.perf_counter_ns()
    record = {
        **m, "git_sha": head, "host": system, "started_utc": now(),
        "status": "BLOCKED", "reason": "", "elapsed_ns": None,
    }
    log_path = out / f"{m['stand']}.log"
    # Manifests are repository-reviewed commands executed on ephemeral CI.
    # No network access tokens or repository write permission are granted.
    try:
        result = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", m["reproduce"]],
            cwd=ROOT, timeout=timeout, capture_output=True, text=True,
            errors="replace", check=False,
            env={**os.environ, "CI": "true"},
        )
        log_path.write_text(
            "STDOUT\n" + result.stdout + "\nSTDERR\n" + result.stderr,
            encoding="utf-8",
        )
        record["status"] = "PASS" if result.returncode == 0 else "FAIL"
        record["reason"] = f"process exit={result.returncode}"
        record["returncode"] = result.returncode
    except subprocess.TimeoutExpired as exc:
        record["status"] = "TIMEOUT"
        record["reason"] = f"exceeded {timeout}s"
        log_path.write_bytes(
            b"TIMEOUT; partial stdout/stderr\n" +
            (exc.stdout or b"") + b"\n" + (exc.stderr or b"")
        )
    except (OSError, ValueError) as exc:
        record["status"] = "BLOCKED"
        record["reason"] = f"{type(exc).__name__}: {exc}"
        log_path.write_text(record["reason"] + "\n", encoding="utf-8")
    record["elapsed_ns"] = time.perf_counter_ns() - start
    record["log"] = log_path.name
    record["log_sha256"] = sha(log_path)
    record["finished_utc"] = now()
    return record


def collect(folder: Path) -> int:
    manifests = manifest_list()
    files = sorted(folder.rglob("report-*.json"))
    reports = []
    for path in files:
        document = json.loads(path.read_text(encoding="utf-8"))
        reports.extend(document["results"])
    expected = {x["stand"] for x in manifests}
    actual = [x["stand"] for x in reports]
    duplicates = len(set(actual)) != len(actual)
    missing = sorted(expected - set(actual))
    extra = sorted(set(actual) - expected)
    sha_values = sorted({x["git_sha"] for x in reports})
    outcomes = {status: sum(r["status"] == status for r in reports)
                for status in ("PASS", "FAIL", "BLOCKED", "TIMEOUT")}
    summary = {
        "schema": "sens-benchmark-sweep/v1",
        "expected_stands": len(expected),
        "observed_stands": len(actual),
        "duplicates": duplicates,
        "missing": missing,
        "extra": extra,
        "sha_values": sha_values,
        "outcomes": outcomes,
        "complete": (not duplicates and not missing and not extra
                     and len(sha_values) == 1 and
                     outcomes["FAIL"] == 0 and outcomes["BLOCKED"] == 0
                     and outcomes["TIMEOUT"] == 0),
    }
    folder.joinpath("summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["complete"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=int)
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--summarize", type=Path)
    args = parser.parse_args()
    if args.summarize is not None:
        return collect(args.summarize)
    if args.shard is None or args.out is None:
        parser.error("--shard and --out required for execution")
    if args.shards < 1 or not (0 <= args.shard < args.shards):
        parser.error("invalid shard assignment")
    if args.timeout < 1:
        parser.error("timeout must be positive")
    target = manifest_list()
    selected = [m for i, m in enumerate(target) if i % args.shards == args.shard]
    if args.out.exists() and any(args.out.iterdir()):
        parser.error("evidence output directory must be empty")
    args.out.mkdir(parents=True, exist_ok=True)
    head, system = git_head(), host()
    results = []
    for manifest in selected:
        verdict = run_one(manifest, timeout=args.timeout, out=args.out,
                          head=head, system=system)
        results.append(verdict)
        print(f"{verdict['status']:7s} {verdict['stand']}: {verdict['reason']}",
              flush=True)
    record = {
        "schema": "sens-benchmark-sweep-shard/v1",
        "git_sha": head,
        "shard": args.shard,
        "shards": args.shards,
        "total_registered": len(target),
        "results": results,
    }
    (args.out / f"report-{args.shard:02d}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if all(v["status"] == "PASS" for v in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
