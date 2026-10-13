#!/usr/bin/env python3
"""Cachegrind Ir/op ratchet. Metadata verdict only, never SENS semantics."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sys

SCHEMA = "sens-perf-budget-ratchet/v1"
SHA = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^[0-9a-f]{64}$")
CASE = re.compile(r"^[a-z][a-z0-9-]*$")
LOCATION = re.compile(r"^[A-Za-z0-9_./-]+:[1-9][0-9]*$")
LAYERS = {"parse", "eval", "encode", "transport"}
EVIDENCE_FIELDS = {
    "git_sha", "rustc", "valgrind", "machine",
    "iterations", "reps", "contract_version", "semantic_generation",
}
ROW_FIELDS = {
    "case", "iterations", "reps", "net_i_refs_per_iteration",
    "spread_pct", "contract_version", "semantic_generation",
}

class BudgetError(ValueError):
    pass

def require(ok: bool, category: str, detail: str) -> None:
    if not ok:
        raise BudgetError(f"{category} {detail}")

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def evidence(directory: Path) -> tuple[dict, dict[str, dict], str, str]:
    envfile, valuesfile = directory / "environment.json", directory / "results.tsv"
    try:
        env = json.loads(envfile.read_text(encoding="utf-8"))
        with valuesfile.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh, delimiter="\t")
            require(reader.fieldnames is not None and ROW_FIELDS.issubset(reader.fieldnames),
                    "PERF-EVIDENCE-INCOMPLETE", "missing results.tsv columns")
            raw = list(reader)
    except (OSError, json.JSONDecodeError, csv.Error) as exc:
        raise BudgetError(f"PERF-EVIDENCE-MISSING {exc}") from exc
    require(isinstance(env, dict) and EVIDENCE_FIELDS.issubset(env),
            "PERF-EVIDENCE-INCOMPLETE", "environment.json fields")
    require(SHA.fullmatch(str(env.get("git_sha", ""))) is not None
            and type(env["iterations"]) is int and env["iterations"] > 0
            and type(env["reps"]) is int and env["reps"] >= 3,
            "PERF-EVIDENCE-INCOMPLETE", "SHA/iterations/repetitions")
    require(bool(raw), "PERF-EVIDENCE-INCOMPLETE", "zero observed cases")
    rows = {}
    for row in raw:
        name = row.get("case", "")
        require(CASE.fullmatch(name) is not None and name not in rows,
                "PERF-EVIDENCE-INCOMPLETE", f"duplicate or invalid case={name!r}")
        try:
            valid_identity = (
                row["contract_version"] == env["contract_version"]
                and row["semantic_generation"] == env["semantic_generation"]
                and int(row["iterations"]) == env["iterations"]
                and int(row["reps"]) == env["reps"]
            )
            observed = float(row["net_i_refs_per_iteration"])
            spread = float(row["spread_pct"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BudgetError(f"PERF-EVIDENCE-INCOMPLETE case={name} {exc}") from exc
        require(valid_identity and math.isfinite(observed) and observed >= 0
                and math.isfinite(spread) and spread >= 0,
                "PERF-EVIDENCE-INCOMPLETE", f"case={name} mismatched/noisy data")
        rows[name] = row
    return env, rows, digest(envfile), digest(valuesfile)

def evaluate(policy: dict, env: dict, rows: dict[str, dict],
             *, env_sha: str, result_sha: str) -> tuple[list[str], dict]:
    require(isinstance(policy, dict) and policy.get("schema") == SCHEMA,
            "PERF-BUDGET-BAD-CONTRACT", "unknown schema")
    budgets = policy.get("budgets")
    require(isinstance(budgets, list) and bool(budgets),
            "PERF-BUDGET-UNCALIBRATED", "zero approved numeric budgets")
    baseline = policy.get("baseline")
    require(isinstance(baseline, dict)
            and SHA.fullmatch(str(baseline.get("source_sha", ""))) is not None
            and DIGEST.fullmatch(str(baseline.get("evidence_sha256", ""))) is not None
            and re.fullmatch(r"#\d+", str(baseline.get("ratification_issue", ""))) is not None,
            "PERF-BUDGET-UNCALIBRATED", "baseline SHA/evidence/ratification missing")
    pinned = policy.get("environment")
    keys = ("rustc", "valgrind", "machine", "iterations", "reps",
            "contract_version", "semantic_generation")
    require(isinstance(pinned, dict) and all(k in pinned for k in keys),
            "PERF-BUDGET-UNCALIBRATED", "baseline environment missing")
    for field in keys:
        require(type(env[field]) is type(pinned[field]) and env[field] == pinned[field],
                "PERF-ENVIRONMENT-MISMATCH",
                f"field={field} expected={pinned[field]!r} observed={env[field]!r}")
    named = set()
    failures = []
    details = []
    total_limit = total_observed = total_excess = 0.0
    for row in budgets:
        require(isinstance(row, dict), "PERF-BUDGET-BAD-CONTRACT", "invalid row")
        case, layer = row.get("case"), row.get("layer")
        location = row.get("source_location")
        require(isinstance(case, str) and CASE.fullmatch(case) is not None
                and case not in named and layer in LAYERS
                and isinstance(location, str) and LOCATION.fullmatch(location) is not None
                and ".." not in location.split(":", 1)[0].split("/"),
                "PERF-BUDGET-BAD-CONTRACT", f"duplicate/invalid case={case}")
        named.add(case)
        limit = row.get("max_net_irefs_per_iteration")
        require(type(limit) in (int, float) and math.isfinite(limit) and limit > 0,
                "PERF-BUDGET-BAD-CONTRACT", f"case={case} invalid limit")
        require(case in rows, "PERF-EVIDENCE-INCOMPLETE", f"missing case={case}")
        actual = float(rows[case]["net_i_refs_per_iteration"])
        require(math.isfinite(actual) and actual >= 0, "PERF-EVIDENCE-INCOMPLETE",
                f"case={case} negative/noisy net Ir")
        delta = actual - limit
        excess = max(0.0, delta)
        total_limit += limit
        total_observed += actual
        total_excess += excess
        state = "PERF-BUDGET-EXCEEDED" if excess else "PASS"
        record = (f"{state} case={case} layer={layer} source_location={location} observed_ir_per_op={actual:.6f} "
                  f"budget_ir_per_op={limit:.6f} delta_ir_per_op={delta:+.6f} "
                  f"source_sha={env['git_sha']} results_sha256={result_sha}")
        if excess:
            failures.append(record)
        else:
            print(record)
        details.append({"case": case, "layer": layer, "source_location": location, "state": state,
                        "observed_ir_per_op": actual, "budget_ir_per_op": limit,
                        "excess_ir_per_op": excess})
    require(named == set(rows), "PERF-EVIDENCE-INCOMPLETE",
            f"unbudgeted cases={sorted(set(rows)-named)}")
    summary = {"schema": "sens-perf-budget-verdict/v1",
               "source_sha": env["git_sha"], "baseline_sha": baseline["source_sha"],
               "environment_sha256": env_sha, "results_sha256": result_sha,
               "budget_total_ir_per_op": total_limit,
               "observed_total_ir_per_op": total_observed,
               "excess_total_ir_per_op": total_excess,
               "status": "FAIL" if failures else "PASS", "cases": details}
    return failures, summary

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budgets", type=Path, default=Path("knowledge/perf-budget-ratchet.json"))
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--json-report", type=Path)
    opts = parser.parse_args(argv)
    try:
        env, rows, env_sha, data_sha = evidence(opts.evidence_dir)
        policy = json.loads(opts.budgets.read_text(encoding="utf-8"))
        failures, verdict = evaluate(policy, env, rows, env_sha=env_sha, result_sha=data_sha)
        if opts.json_report:
            opts.json_report.write_text(json.dumps(verdict, sort_keys=True, indent=2) + "\n",
                                        encoding="utf-8")
        for line in failures:
            print("::error::" + line)
        print("PERF-BUDGET-VERDICT " + json.dumps({
            k: verdict[k] for k in ("status", "budget_total_ir_per_op",
                                    "observed_total_ir_per_op", "excess_total_ir_per_op")
        }, sort_keys=True))
        return 1 if failures else 0
    except (BudgetError, OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print("::error::" + str(exc))
        return 2

if __name__ == "__main__":
    sys.exit(main())
