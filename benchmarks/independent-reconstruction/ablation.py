#!/usr/bin/env python3
"""Lower-evidence ablation benchmark (#2144).

Uses the independent reconstruction harness from #2138 and erases exactly one
information dimension at a time. Reports semantic information loss separately
from reconstruction cost.

Research-only. No production deletion authority.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Sequence


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("reconstruction", HERE / "run.py")
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load reconstruction harness")
reconstruction = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = reconstruction
SPEC.loader.exec_module(reconstruction)


def deduplicate(graph):
    return reconstruction.SemanticGraph(
        roles=dict(graph.roles),
        edges=tuple(dict.fromkeys(graph.edges)),
    )


def erase_relation_kinds(graph):
    return reconstruction.SemanticGraph(
        roles=dict(graph.roles),
        edges=tuple((src, 0, dst) for src, _kind, dst in dict.fromkeys(graph.edges)),
    )


def merge_terminal_roles(graph):
    roles = {
        node: (1 if role == 2 else role)
        for node, role in graph.roles.items()
    }
    return reconstruction.SemanticGraph(
        roles=roles,
        edges=tuple(dict.fromkeys(graph.edges)),
    )


def remove_one_incidence(graph):
    edges = list(dict.fromkeys(graph.edges))
    if not edges:
        raise AssertionError("need at least one semantic edge")
    return reconstruction.SemanticGraph(
        roles=dict(graph.roles),
        edges=tuple(edges[1:]),
    )


def role_only(graph):
    return reconstruction.SemanticGraph(
        roles=dict(graph.roles),
        edges=(),
    )


def relation_only(graph):
    roles = {node: 0 for node in graph.roles}
    return reconstruction.SemanticGraph(
        roles=roles,
        edges=tuple(dict.fromkeys(graph.edges)),
    )


ABLATIONS: Dict[str, tuple[Callable, str, bool]] = {
    "deduplicate-evidence": (
        deduplicate,
        "duplicate row multiplicity",
        True,
    ),
    "erase-relation-kinds": (
        erase_relation_kinds,
        "typed relation identity",
        False,
    ),
    "merge-terminal-roles": (
        merge_terminal_roles,
        "terminal role distinction",
        False,
    ),
    "remove-one-incidence": (
        remove_one_incidence,
        "one semantic incidence fact",
        False,
    ),
    "role-only": (
        role_only,
        "all relational incidence",
        False,
    ),
    "relation-only": (
        relation_only,
        "all admitted local roles",
        False,
    ),
}


def answer_digest(answers: Sequence[bool]) -> str:
    return reconstruction.digest_json(list(answers))


def run_case(case, query_count: int):
    base_graph = reconstruction.make_graph(case.n_nodes, case.depth, case.seed)
    query_pairs = reconstruction.make_queries(
        base_graph, query_count, case.seed ^ 0xAB1A
    )

    base_encoded = reconstruction.encode_graph(base_graph, case.seed ^ 0x1111)
    t0 = time.perf_counter_ns()
    base_cert, base_classes, base_metrics = reconstruction.reconstruct_recursive(
        base_encoded
    )
    base_ns = time.perf_counter_ns() - t0

    base_queries = reconstruction.encode_queries(base_encoded, query_pairs)
    base_answers = reconstruction.answer_queries(
        base_classes, base_queries, base_metrics
    )
    base_digest = answer_digest(base_answers)

    rows = []
    for index, (name, (transform, removed, expected_equal)) in enumerate(
        ABLATIONS.items()
    ):
        graph = transform(base_graph)
        encoded = reconstruction.encode_graph(
            graph, case.seed ^ (0x2200 + index * 131)
        )

        t0 = time.perf_counter_ns()
        cert, classes, metrics = reconstruction.reconstruct_recursive(encoded)
        reconstruct_ns = time.perf_counter_ns() - t0

        queries = reconstruction.encode_queries(encoded, query_pairs)
        answers = reconstruction.answer_queries(classes, queries, metrics)

        changed_answers = sum(
            left != right for left, right in zip(base_answers, answers)
        )
        equal = cert == base_cert

        if expected_equal and not equal:
            raise AssertionError(
                f"{case.case_id}: positive control changed semantics: {name}"
            )
        if expected_equal and changed_answers:
            raise AssertionError(
                f"{case.case_id}: positive control changed query answers: {name}"
            )

        if not expected_equal and equal:
            raise AssertionError(
                f"{case.case_id}: ablation unexpectedly preserved certificate: {name}"
            )

        rows.append(
            {
                "case_id": case.case_id,
                "ablation": name,
                "information_removed": removed,
                "expected_certificate_equal": int(expected_equal),
                "certificate_equal": int(equal),
                "baseline_classes": base_metrics.quotient_classes,
                "ablated_classes": metrics.quotient_classes,
                "classes_delta": metrics.quotient_classes
                - base_metrics.quotient_classes,
                "baseline_quotient_edges": base_metrics.quotient_edges,
                "ablated_quotient_edges": metrics.quotient_edges,
                "quotient_edges_delta": metrics.quotient_edges
                - base_metrics.quotient_edges,
                "query_count": len(query_pairs),
                "query_answers_changed": changed_answers,
                "baseline_query_digest": base_digest,
                "ablated_query_digest": answer_digest(answers),
                "baseline_reconstruct_ns": base_ns,
                "ablated_reconstruct_ns": reconstruct_ns,
                "evidence_reads": metrics.evidence_reads,
                "sort_items": metrics.sort_items,
                "certificate_constructions": metrics.certificate_constructions,
                "memo_hits": metrics.memo_hits,
                "prepared_payload_bytes": metrics.prepared_payload_bytes,
                "peak_logical_objects": metrics.peak_logical_objects,
                "query_steps": metrics.query_steps,
            }
        )
    return rows


def write_outputs(rows: Sequence[dict], prefix: Path) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())

    with prefix.with_suffix(".tsv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    prefix.with_suffix(".json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def summarize(rows: Sequence[dict]) -> None:
    print("reconstruction-ablation: PASS")
    for case_id in sorted({row["case_id"] for row in rows}):
        print(case_id)
        for row in [r for r in rows if r["case_id"] == case_id]:
            print(
                f"  {row['ablation']:22s} "
                f"equal={row['certificate_equal']} "
                f"class_delta={row['classes_delta']:+d} "
                f"edge_delta={row['quotient_edges_delta']:+d} "
                f"queries_changed={row['query_answers_changed']}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--queries", type=int, default=256)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("/tmp/reconstruction-ablation/results"),
    )
    args = parser.parse_args()

    if args.queries < 1:
        raise SystemExit("--queries must be >= 1")

    rows: List[dict] = []
    for case in reconstruction.default_cases(args.smoke):
        rows.extend(run_case(case, args.queries))

    write_outputs(rows, args.out)
    summarize(rows)
    print(f"wrote {args.out.with_suffix('.tsv')}")
    print(f"wrote {args.out.with_suffix('.json')}")


if __name__ == "__main__":
    main()
