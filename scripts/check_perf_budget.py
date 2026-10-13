#!/usr/bin/env python3
"""Тільки performance evidence; двійковий SENS єдиний semantic oracle."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
PROVENANCE = ("cpu", "arch", "valgrind", "rustc", "profile", "toolchain")
LAYERS = {"parse", "eval", "encode", "transport"}


def must(ok, why):
    if not ok:
        raise ValueError("PERF-EVIDENCE-BLOCKED " + why)


def integer(v):
    return type(v) is int and 0 <= v < (1 << 63)


def check_case(b, m, env):
    name = b.get("id")
    must(isinstance(name, str) and re.fullmatch(r"[A-Za-z0-9_.:-]+", name),
         "invalid case_id")
    must(b.get("layer") in LAYERS and b.get("metric") == "Cachegrind.Ir/op",
         name + ": wrong layer/metric")
    must(b.get("evidence_status") == "PINNED_REAL_MEASUREMENT",
         name + ": no real ratified baseline")
    must(bool(HEX40.fullmatch(str(b.get("baseline_commit", "")))) and
         bool(HEX64.fullmatch(str(b.get("baseline_evidence_sha256", "")))),
         name + ": baseline provenance missing")
    must(b.get("environment") == env, name + ": environment drift")
    must(all(isinstance(env.get(k), str) and env[k] for k in PROVENANCE),
         name + ": incomplete machine/toolchain")
    must(m.get("id") == name and m.get("layer") == b["layer"] and
         m.get("metric") == b["metric"], name + ": measurement identity mismatch")
    must(m.get("semantic_parity") is True, name + ": SENS parity absent")
    must(m.get("isolation") == "matched_control_same_binary",
         name + ": not an isolated per-operation measurement")
    fixture = b.get("fixture")
    must(isinstance(fixture, str) and fixture.startswith("tests/") and
         ".." not in Path(fixture).parts, name + ": wrong fixture path")
    path = ROOT / fixture
    must(path.is_file(), name + ": physical SENS fixture missing")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    must(b.get("fixture_sha256") == digest and m.get("fixture_sha256") == digest,
         name + ": fixture SHA drift")
    reproduce = b.get("reproduce")
    must(isinstance(reproduce, str) and reproduce.strip() and reproduce != "MISSING",
         name + ": missing one-command reproduction")
    budget = b.get("limit_ir_per_op")
    operations = m.get("operations")
    must(integer(budget) and budget > 0 and integer(operations) and operations > 0,
         name + ": limit or operation count missing")
    pairs = m.get("paired_i_refs")
    must(isinstance(pairs, list) and len(pairs) >= 3 and len(pairs) % 2 == 1,
         name + ": need >=3 odd paired samples")
    diffs = []
    for i, row in enumerate(pairs):
        must(isinstance(row, dict), name + ": bad paired row")
        active, control = row.get("active"), row.get("control")
        must(integer(active) and integer(control) and active >= control,
             name + ": invalid Cachegrind I refs pair " + str(i))
        diffs.append(active - control)
    median = sorted(diffs)[len(diffs) // 2]
    per_op = (median + operations - 1) // operations
    return {
        "id": name, "layer": b["layer"], "fixture": fixture,
        "fixture_sha256": digest, "measured_ir_per_op": per_op,
        "budget_ir_per_op": budget, "excess_ir_per_op": max(0, per_op-budget),
        "first_difference": {"metric": "Cachegrind.Ir/op", "delta": per_op-budget},
        "reproduce": reproduce,
    }


def evaluate(budgets, evidence, *, emit=True):
    must(budgets.get("schema") == "sens-ir-budget/v1", "budget schema")
    must(evidence.get("schema") == "sens-ir-evidence/v1", "evidence schema")
    must(bool(HEX40.fullmatch(str(evidence.get("git_sha", "")))),
         "exact evidence git SHA required")
    env, cases, rows = evidence.get("environment"), budgets.get("cases"), evidence.get("rows")
    must(isinstance(env, dict) and isinstance(cases, list) and bool(cases)
         and isinstance(rows, list), "incomplete evidence")
    must(all(isinstance(r, dict) for r in rows), "malformed measurements")
    by_id = {r.get("id"): r for r in rows}
    must(len(by_id) == len(rows), "duplicate measurement IDs")
    must(set(by_id) == {b.get("id") for b in cases} and len(cases) == len(by_id),
         "missing/unbudgeted case: no silent skip")
    excess = 0
    for b in cases:
        result = check_case(b, by_id[b["id"]], env)
        result["git_sha"] = evidence["git_sha"]
        excess += result["excess_ir_per_op"]
        marker = "PERF-BUDGET-EXCEEDED" if result["excess_ir_per_op"] else "PERF-BUDGET-PASS"
        if emit:
            print(marker + " " + json.dumps(result, ensure_ascii=False, sort_keys=True))
    if emit:
        print("PERF-DEBT " + json.dumps({
            "excess_ir_per_op_sum": excess, "cases": len(cases),
            "warning": "Sum meaningful only within this fixed comparable workload set"
        }, sort_keys=True))
    return int(excess > 0)


def self_test():
    """Only synthetic mechanical examples; NEVER real benchmark evidence."""
    import tempfile
    global ROOT
    saved = ROOT
    with tempfile.TemporaryDirectory() as temp:
        try:
            ROOT = Path(temp)
            f = ROOT / "tests/sample.sens"
            f.parent.mkdir()
            f.write_bytes(b"\x00\x01")
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            env = {key: "synthetic" for key in PROVENANCE}
            b = {"id": "synthetic.case", "layer": "eval", "metric": "Cachegrind.Ir/op",
                 "evidence_status": "PINNED_REAL_MEASUREMENT", "baseline_commit": "a"*40,
                 "baseline_evidence_sha256": "b"*64, "fixture": "tests/sample.sens",
                 "fixture_sha256": sha, "limit_ir_per_op": 20, "environment": env,
                 "reproduce": "python3 scripts/check_perf_budget.py --budgets budgets.json --evidence evidence.json"}
            m = {"id": "synthetic.case", "layer": "eval", "metric": "Cachegrind.Ir/op",
                 "semantic_parity": True, "isolation": "matched_control_same_binary",
                 "fixture_sha256": sha, "operations": 10,
                 "paired_i_refs": [{"active": 120, "control": 20}] * 3}
            policy = {"schema": "sens-ir-budget/v1", "cases": [b]}
            data = {"schema": "sens-ir-evidence/v1", "git_sha": "c"*40,
                    "environment": env, "rows": [m]}
            must(evaluate(policy, data, emit=False) == 0, "false rejection")
            m["paired_i_refs"] = [{"active": 320, "control": 20}] * 3
            must(evaluate(policy, data, emit=False) == 1, "missed budget overrun")
            data["environment"] = {**env, "cpu": "different"}
            try:
                evaluate(policy, data, emit=False)
            except ValueError:
                pass
            else:
                raise ValueError("machine drift was accepted")
            print("PERF-HARNESS-SELF-TEST PASS: SYNTHETIC ONLY")
        finally:
            ROOT = saved


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--budgets", type=Path)
    p.add_argument("--evidence", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        must(args.budgets is not None and args.evidence is not None,
             "both real budget and measurement files required")
        return evaluate(json.loads(args.budgets.read_text()),
                        json.loads(args.evidence.read_text()))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print("PERF-EVIDENCE-BLOCKED " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
