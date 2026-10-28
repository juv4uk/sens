#!/usr/bin/env python3
"""Extract observational GNU-time evidence from a SENS CI job log.

This intentionally does NOT certify SENS result parity, independent repetitions,
energy, or any cross-language ranking. No modification of language semantics.
"""
import argparse
import json
import re
from pathlib import Path

ROUND = re.compile(r"^--- повтор (\d+) ---$")
ELAPSED = re.compile(r"^Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (\d+):(\d{2}\.\d{2})$")
RSS = re.compile(r"^Maximum resident set size \(kbytes\): (\d+)$")
SHA = re.compile(r"^[0-9a-f]{40}$")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


class InvalidEvidence(ValueError):
    pass


def extract(log, *, commit_sha, run_id, job_id, conclusion="success"):
    if not SHA.fullmatch(commit_sha):
        raise InvalidEvidence("exact 40-hex commit SHA required")
    if not (isinstance(run_id, int) and run_id > 0 and isinstance(job_id, int) and job_id > 0):
        raise InvalidEvidence("positive run and job IDs required")
    if conclusion != "success":
        raise InvalidEvidence("the actual GitHub job must be completed successfully")
    if not re.search(r"shell: /usr/bin/bash .* -e -o pipefail \{0\}", log):
        raise InvalidEvidence("no evidence that Bash pipefail propagates SENS/time errors")

    samples = []
    current = None
    in_results = False
    for original in log.splitlines():
        line = ANSI.sub("", original).strip()
        # The full GitHub log prefixes runtime output with its UTC timestamp.
        line = re.sub(r"^\d{4}-\d\d-\d\dT\S+Z\s+", "", line)
        if line == "=== три повтори, /usr/bin/time -v ===":
            in_results = True
            continue
        if not in_results:
            continue
        match = ROUND.fullmatch(line)
        if match:
            if current is not None:
                if set(current) != {"round", "wall_seconds", "peak_rss_kib"}:
                    raise InvalidEvidence("incomplete paired wall/RSS observation")
                samples.append(current)
            index = int(match.group(1))
            if index != len(samples) + 1 or index > 3:
                raise InvalidEvidence("duplicate, missing or extra numbered round")
            current = {"round": index}
            continue
        match = ELAPSED.fullmatch(line)
        if match and current is not None:
            if "wall_seconds" in current:
                raise InvalidEvidence("duplicate wall measurement")
            minutes, secs = int(match.group(1)), float(match.group(2))
            seconds = minutes * 60 + secs
            if seconds <= 0 or secs >= 60:
                raise InvalidEvidence("invalid wall measurement")
            current["wall_seconds"] = round(seconds, 2)
            continue
        match = RSS.fullmatch(line)
        if match and current is not None:
            if "peak_rss_kib" in current or int(match.group(1)) <= 0:
                raise InvalidEvidence("invalid/duplicate RSS measurement")
            current["peak_rss_kib"] = int(match.group(1))
    if current is not None:
        if set(current) != {"round", "wall_seconds", "peak_rss_kib"}:
            raise InvalidEvidence("incomplete final observation")
        samples.append(current)
    if len(samples) != 3:
        raise InvalidEvidence("require exactly three observed runs")
    return {
        "schema": "sens-ci-exploratory-observation/v1",
        "status": "EXPLORATORY_NOT_ADMITTED",
        "reason": "native SENS result/output parity and independent measurement blocks were not verified",
        "source": {
            "repository": "juv4uk/sens",
            "commit_sha": commit_sha,
            "workflow_run_id": run_id,
            "job_id": job_id,
            "job_conclusion": conclusion,
            "job_log_url": f"https://github.com/juv4uk/sens/actions/runs/{run_id}/job/{job_id}",
            "exit_propagation": "GitHub bash -e -o pipefail; step successful",
            "workload_source": "benchmarks/sphere-contest/сенс-семантика.lisp"
        },
        "boundary": "one fresh sens process loading D6 program per round, GNU /usr/bin/time -v, build excluded",
        "declared_target": "D6 додати-1 over a ten-element list; execution count/output not independently certified",
        "environment": {
            "runner_label": "ubuntu-latest",
            "cpu_model": None,
            "governor": None,
            "compiler_flags": "cargo build --locked -p sens-cli --bin sens (debug)"
        },
        "samples": samples,
        "output_parity": "NOT_VERIFIED",
        "independent_sessions": "NOT_VERIFIED",
        "energy_status": "ENERGY_NOT_MEASURED",
        "energy_j": None,
        "publication_claim": "NONE"
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--run-id", type=int, required=True)
    p.add_argument("--job-id", type=int, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    try:
        report = extract(args.log.read_text(encoding="utf-8"), commit_sha=args.sha,
                         run_id=args.run_id, job_id=args.job_id)
    except (InvalidEvidence, OSError) as err:
        p.exit(2, f"EVIDENCE_BLOCKED: {err}\n")
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
