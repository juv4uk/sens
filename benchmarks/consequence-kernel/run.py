#!/usr/bin/env python3
"""#2123 research-only consequence-kernel benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import platform
import time
from dataclasses import dataclass
from pathlib import Path

SIZES = (16, 64, 256)
WORKLOADS = ("chain", "diamond", "conflict", "fanout")
CANDIDATES = ("assumption", "forward", "memo", "provenance")


@dataclass(frozen=True)
class Rule:
    premises: tuple[str, ...]
    conclusion: str


@dataclass
class Counts:
    rule_checks: int = 0
    premise_reads: int = 0
    derived: int = 0
    support_combinations: int = 0
    support_sets_created: int = 0
    support_sets_removed: int = 0


@dataclass
class Case:
    workload: str
    size: int
    premises: set[str]
    rules: list[Rule]
    positive: str
    refute: str
    invalidate: str


def make_chain(prefix: str, depth: int, conclusion: str):
    rules = []
    previous = prefix + "0"
    for i in range(1, max(1, depth)):
        current = prefix + str(i)
        rules.append(Rule((previous,), current))
        previous = current
    rules.append(Rule((previous,), conclusion))
    return rules, prefix + "0"


def make_case(workload: str, size: int) -> Case:
    if workload == "chain":
        rules, root = make_chain("p", max(1, size - 1), "J")
        return Case(workload, size, {root}, rules, "J", "!J", root)

    if workload == "diamond":
        depth = max(1, size // 2 - 1)
        left, a = make_chain("a", depth, "J")
        right, b = make_chain("b", depth, "J")
        return Case(workload, size, {a, b}, left + right, "J", "!J", a)

    if workload == "conflict":
        depth = max(1, size // 2 - 1)
        support, a = make_chain("a", depth, "J")
        refute, b = make_chain("b", depth, "!J")
        return Case(
            workload, size, {a, b}, support + refute, "J", "!J", a
        )

    if workload == "fanout":
        root = "r0"
        rules = [Rule((root,), f"c{i}") for i in range(size)]
        return Case(workload, size, {root}, rules, "c0", "!c0", root)

    raise ValueError(workload)


def closure(
    premises: set[str], rules: list[Rule], counts: Counts | None = None
):
    counts = counts or Counts()
    out = set(premises)
    changed = True
    while changed:
        changed = False
        for rule in rules:
            counts.rule_checks += 1
            satisfied = True
            for premise in rule.premises:
                counts.premise_reads += 1
                if premise not in out:
                    satisfied = False
                    break
            if satisfied and rule.conclusion not in out:
                out.add(rule.conclusion)
                counts.derived += 1
                changed = True
    return out, counts


def provenance_closure(
    premises: set[str], rules: list[Rule], counts: Counts | None = None
):
    counts = counts or Counts()
    provenance = {
        premise: {frozenset((premise,))} for premise in premises
    }
    changed = True
    while changed:
        changed = False
        for rule in rules:
            counts.rule_checks += 1
            pools = []
            satisfied = True
            for premise in rule.premises:
                counts.premise_reads += 1
                supports = provenance.get(premise, set())
                if not supports:
                    satisfied = False
                    break
                pools.append(tuple(supports))
            if not satisfied:
                continue

            for combo in itertools.product(*pools):
                counts.support_combinations += 1
                support = frozenset().union(*combo)
                bucket = provenance.setdefault(rule.conclusion, set())
                if support not in bucket:
                    bucket.add(support)
                    counts.support_sets_created += 1
                    changed = True
    return provenance, counts


def set_answers(values: set[str], case: Case):
    return case.positive in values, case.refute in values


def provenance_answers(provenance, case: Case):
    return bool(provenance.get(case.positive)), bool(
        provenance.get(case.refute)
    )


def rule_payload_bytes(rules: list[Rule]) -> int:
    return sum(8 + 4 * len(rule.premises) for rule in rules)


def provenance_bytes(provenance) -> int:
    return sum(
        8 + 4 * len(support)
        for supports in provenance.values()
        for support in supports
    )


def run_candidate(
    case: Case,
    candidate: str,
    oracle_before,
    oracle_after,
):
    active = set(case.premises)
    prepare = Counts()
    before_query = Counts()
    invalidate = Counts()
    after_query = Counts()

    start = time.perf_counter_ns()
    if candidate == "memo":
        state, prepare = closure(active, case.rules, prepare)
    elif candidate == "provenance":
        state, prepare = provenance_closure(active, case.rules, prepare)
    else:
        state = None
    prepare_ns = time.perf_counter_ns() - start

    start = time.perf_counter_ns()
    if candidate == "assumption":
        before = set_answers(active, case)
    elif candidate == "forward":
        values, before_query = closure(active, case.rules, before_query)
        before = set_answers(values, case)
    elif candidate == "memo":
        before = set_answers(state, case)
    else:
        before = provenance_answers(state, case)
    query_ns_before = time.perf_counter_ns() - start

    start = time.perf_counter_ns()
    active.discard(case.invalidate)
    if candidate == "memo":
        state, invalidate = closure(active, case.rules, invalidate)
    elif candidate == "provenance":
        for literal, supports in list(state.items()):
            keep = {
                support
                for support in supports
                if case.invalidate not in support
            }
            invalidate.support_sets_removed += len(supports) - len(keep)
            if keep:
                state[literal] = keep
            else:
                state.pop(literal, None)
    invalidate_ns = time.perf_counter_ns() - start

    start = time.perf_counter_ns()
    if candidate == "assumption":
        after = set_answers(active, case)
    elif candidate == "forward":
        values, after_query = closure(active, case.rules, after_query)
        after = set_answers(values, case)
    elif candidate == "memo":
        after = set_answers(state, case)
    else:
        after = provenance_answers(state, case)
    query_ns_after = time.perf_counter_ns() - start

    parity = before == oracle_before and after == oracle_after

    if candidate in ("assumption", "forward"):
        extra_bytes = 4 * len(active)
    elif candidate == "memo":
        extra_bytes = 4 * (len(active) + len(state))
    else:
        extra_bytes = 4 * len(active) + provenance_bytes(state)

    digest = hashlib.sha256(repr((before, after)).encode()).hexdigest()[:16]

    return {
        "workload": case.workload,
        "size": case.size,
        "candidate": candidate,
        "rules": len(case.rules),
        "premises_initial": len(case.premises),
        "before_support": int(before[0]),
        "before_refute": int(before[1]),
        "after_support": int(after[0]),
        "after_refute": int(after[1]),
        "semantic_parity": int(parity),
        "semantics_comparable": int(parity),
        "prepare_rule_checks": prepare.rule_checks,
        "prepare_premise_reads": prepare.premise_reads,
        "prepare_derived": prepare.derived,
        "prepare_support_combinations": prepare.support_combinations,
        "prepare_support_sets_created": prepare.support_sets_created,
        "query_rule_checks_before": before_query.rule_checks,
        "query_premise_reads_before": before_query.premise_reads,
        "invalidate_rule_checks": invalidate.rule_checks,
        "invalidate_premise_reads": invalidate.premise_reads,
        "invalidate_support_sets_removed": invalidate.support_sets_removed,
        "query_rule_checks_after": after_query.rule_checks,
        "query_premise_reads_after": after_query.premise_reads,
        "common_rule_payload_bytes": rule_payload_bytes(case.rules),
        "extra_state_bytes_after_revision": extra_bytes,
        "prepare_ns": prepare_ns,
        "query_ns_before": query_ns_before,
        "invalidate_ns": invalidate_ns,
        "query_ns_after": query_ns_after,
        "answer_digest": digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out-dir",
        default="benchmarks/consequence-kernel/results/current",
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[2]
    out = (repo / args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows = []
    for workload in WORKLOADS:
        for size in SIZES:
            case = make_case(workload, size)
            before_values, _ = closure(case.premises, case.rules)
            after_values, _ = closure(
                case.premises - {case.invalidate}, case.rules
            )
            oracle_before = set_answers(before_values, case)
            oracle_after = set_answers(after_values, case)

            for candidate in CANDIDATES:
                rows.append(
                    run_candidate(
                        case, candidate, oracle_before, oracle_after
                    )
                )

    with (out / "summary.tsv").open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=list(rows[0].keys()), delimiter="\t"
        )
        writer.writeheader()
        writer.writerows(rows)

    (out / "summary.json").write_text(json.dumps(rows, indent=2) + "\n")
    (out / "provenance.json").write_text(
        json.dumps(
            {
                "python": platform.python_version(),
                "kernel": platform.release(),
                "note": (
                    "research-only; signed refutation is explicit; "
                    "UNKNOWN != false; no explosion"
                ),
            },
            indent=2,
        )
        + "\n"
    )

    comparable = [
        row for row in rows if row["candidate"] != "assumption"
    ]
    if not all(row["semantic_parity"] == 1 for row in comparable):
        raise SystemExit("semantic parity failure in comparable candidate")

    print("rows", len(rows), "comparable_parity", "PASS")
    for workload in WORKLOADS:
        sample = [
            row
            for row in rows
            if row["workload"] == workload and row["size"] == 64
        ]
        print(
            workload,
            [
                (
                    row["candidate"],
                    row["semantic_parity"],
                    row["prepare_rule_checks"],
                    row["query_rule_checks_before"],
                    row["invalidate_rule_checks"],
                    row["query_rule_checks_after"],
                    row["invalidate_support_sets_removed"],
                )
                for row in sample
            ],
        )


if __name__ == "__main__":
    main()
