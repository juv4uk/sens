#!/usr/bin/env python3
"""Independent semantic reconstruction benchmark (#2138).

Two reconstructors receive separately renamed/permuted encodings of the same
finite typed DAG evidence. They share only the lower contract schemas for local
role/relation tokens. They do not share node IDs, class IDs, row order, human
names, binary coordinates, or an A<->B lookup table.

A: iterative partition refinement.
B: recursive structural certificates with memoization.

The benchmark checks exact canonical quotient-certificate parity, semantic query
parity, renaming/permutation invariance, and negative controls.

Research-only. No production semantic authority.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import random
import statistics
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

AbstractEdge = Tuple[int, int, int]
LocalEdge = Tuple[str, str, str]
Query = Tuple[str, str]


@dataclass(frozen=True)
class SemanticGraph:
    roles: Dict[int, int]
    edges: Tuple[AbstractEdge, ...]


@dataclass
class EncodedGraph:
    roles: Dict[str, str]
    edges: List[LocalEdge]
    role_schema: Dict[str, int]
    rel_schema: Dict[str, int]
    local_of_abstract: Dict[int, str]


@dataclass
class Metrics:
    evidence_reads: int = 0
    sort_items: int = 0
    refinement_rounds: int = 0
    certificate_constructions: int = 0
    memo_hits: int = 0
    quotient_classes: int = 0
    quotient_edges: int = 0
    prepared_payload_bytes: int = 0
    peak_logical_objects: int = 0
    query_steps: int = 0


@dataclass(frozen=True)
class Case:
    n_nodes: int
    depth: int
    seed: int

    @property
    def case_id(self) -> str:
        return f"n{self.n_nodes}-d{self.depth}"


def make_graph(n: int, depth: int, seed: int) -> SemanticGraph:
    """Build a deterministic DAG with symmetry, sharing, and duplicate evidence."""
    if n < 8:
        raise ValueError("n must be >= 8")
    depth = max(2, min(depth, n))

    levels: List[List[int]] = [[] for _ in range(depth)]
    for node in range(n):
        level = min(depth - 1, (node * depth) // n)
        levels[level].append(node)

    roles: Dict[int, int] = {}
    for level, nodes in enumerate(levels):
        for index, node in enumerate(nodes):
            if level == 0:
                role = 3  # admitted root role
            elif level == depth - 1:
                role = 1 + (index % 2)  # two admitted terminal roles
            else:
                role = 0  # internal role
            roles[node] = role

    edges: List[AbstractEdge] = []
    for level in range(depth - 1):
        next_nodes = levels[level + 1]
        for index, node in enumerate(levels[level]):
            fanout = 1 + ((node + level) % 3)
            for offset in range(fanout):
                target_index = (node * 7 + index * 3 + offset * 5 + seed) % len(next_nodes)
                target = next_nodes[target_index]
                relation_kind = (index + offset + level) % 3
                edge = (node, relation_kind, target)
                edges.append(edge)

                # Duplicate evidence row: multiplicity is declared non-semantic
                # for this benchmark family and both implementations must ignore it.
                if (node + offset) % 11 == 0:
                    edges.append(edge)

    return SemanticGraph(roles=roles, edges=tuple(edges))


def encode_graph(graph: SemanticGraph, seed: int) -> EncodedGraph:
    """Create a local encoding with independent node/role/relation tokens."""
    rng = random.Random(seed)
    nodes = list(graph.roles)
    permutation = nodes[:]
    rng.shuffle(permutation)

    local_of = {
        abstract: f"n{seed:x}_{local_index:05x}"
        for local_index, abstract in enumerate(permutation)
    }

    role_tokens = [f"u{seed:x}_{i}" for i in range(8)]
    relation_tokens = [f"k{seed:x}_{i}" for i in range(3)]

    role_meanings = list(range(8))
    relation_meanings = list(range(3))
    rng.shuffle(role_meanings)
    rng.shuffle(relation_meanings)

    role_schema = {token: meaning for token, meaning in zip(role_tokens, role_meanings)}
    rel_schema = {token: meaning for token, meaning in zip(relation_tokens, relation_meanings)}
    role_token_for = {meaning: token for token, meaning in role_schema.items()}
    rel_token_for = {meaning: token for token, meaning in rel_schema.items()}

    roles = {
        local_of[abstract]: role_token_for[role]
        for abstract, role in graph.roles.items()
    }
    edges = [
        (local_of[src], rel_token_for[kind], local_of[dst])
        for src, kind, dst in graph.edges
    ]
    rng.shuffle(edges)

    return EncodedGraph(
        roles=roles,
        edges=edges,
        role_schema=role_schema,
        rel_schema=rel_schema,
        local_of_abstract=local_of,
    )


def decode_evidence(encoded: EncodedGraph, metrics: Metrics):
    roles: Dict[str, int] = {}
    for node, local_role in encoded.roles.items():
        roles[node] = encoded.role_schema[local_role]
        metrics.evidence_reads += 1

    # Evidence multiplicity is non-semantic in this benchmark family.
    edges = set()
    for src, local_kind, dst in encoded.edges:
        edges.add((src, encoded.rel_schema[local_kind], dst))
        metrics.evidence_reads += 1

    metrics.prepared_payload_bytes = len(roles) * 8 + len(edges) * 12
    metrics.peak_logical_objects = max(
        metrics.peak_logical_objects, len(roles) + len(edges)
    )
    return roles, edges


def normalized_partition(colors: Dict[str, int]):
    groups: Dict[int, set[str]] = defaultdict(set)
    for node, color in colors.items():
        groups[color].add(node)
    return frozenset(frozenset(group) for group in groups.values())


def canonicalize_quotient(
    roles: Dict[str, int],
    edges: Iterable[Tuple[str, int, str]],
    classes: Dict[str, int],
    metrics: Metrics,
):
    """Emit an exact name-erased DAG quotient certificate.

    Canonical class IDs are assigned bottom-up as (height, rank_at_height).
    They do not reuse either implementation's internal class numbers.
    """
    members: Dict[int, List[str]] = defaultdict(list)
    for node, cls in classes.items():
        members[cls].append(node)

    class_role: Dict[int, int] = {}
    quotient_edges: Dict[int, set[Tuple[int, int]]] = defaultdict(set)

    for cls, nodes in members.items():
        role_set = {roles[node] for node in nodes}
        if len(role_set) != 1:
            raise AssertionError("reconstructed class mixes admitted local roles")
        class_role[cls] = next(iter(role_set))

    for src, kind, dst in edges:
        quotient_edges[classes[src]].add((kind, classes[dst]))

    height: Dict[int, int] = {}
    visiting: set[int] = set()

    def class_height(cls: int) -> int:
        if cls in height:
            return height[cls]
        if cls in visiting:
            raise AssertionError("benchmark family must remain acyclic")
        visiting.add(cls)
        children = {child for _kind, child in quotient_edges.get(cls, set())}
        value = 0 if not children else 1 + max(class_height(child) for child in children)
        visiting.remove(cls)
        height[cls] = value
        return value

    for cls in members:
        class_height(cls)

    canonical: Dict[int, Tuple[int, int]] = {}
    for h in range(max(height.values(), default=0) + 1):
        signatures = {}
        for cls in members:
            if height[cls] != h:
                continue
            outgoing = tuple(
                sorted((kind, canonical[child]) for kind, child in quotient_edges.get(cls, set()))
            )
            signatures[cls] = (class_role[cls], outgoing)

        unique = sorted(set(signatures.values()), key=repr)
        rank = {signature: i for i, signature in enumerate(unique)}
        for cls, signature in signatures.items():
            canonical[cls] = (h, rank[signature])

    records = []
    for cls, nodes in members.items():
        outgoing = tuple(
            sorted((kind, canonical[child]) for kind, child in quotient_edges.get(cls, set()))
        )
        records.append(
            (
                canonical[cls],
                len(nodes),
                class_role[cls],
                outgoing,
            )
        )

    records = tuple(sorted(records, key=repr))
    metrics.quotient_classes = len(members)
    metrics.quotient_edges = sum(len(value) for value in quotient_edges.values())
    return records


def reconstruct_partition(encoded: EncodedGraph):
    """Implementation A: fixed-point partition refinement."""
    metrics = Metrics()
    roles, edges = decode_evidence(encoded, metrics)

    outgoing: Dict[str, set[Tuple[int, str]]] = defaultdict(set)
    for src, kind, dst in edges:
        outgoing[src].add((kind, dst))

    colors = {node: role for node, role in roles.items()}
    previous_partition = normalized_partition(colors)

    while True:
        metrics.refinement_rounds += 1
        signatures = {}

        for node in roles:
            outgoing_signature = tuple(
                sorted((kind, colors[dst]) for kind, dst in outgoing.get(node, set()))
            )
            metrics.sort_items += len(outgoing_signature)
            signatures[node] = (roles[node], outgoing_signature)
            metrics.certificate_constructions += 1

        unique = sorted(set(signatures.values()), key=repr)
        metrics.sort_items += len(unique)
        color_for = {signature: i for i, signature in enumerate(unique)}
        new_colors = {node: color_for[signatures[node]] for node in roles}

        partition = normalized_partition(new_colors)
        colors = new_colors
        if partition == previous_partition:
            break
        previous_partition = partition

        if metrics.refinement_rounds > len(roles) + 1:
            raise AssertionError("partition refinement failed to converge")

    certificate = canonicalize_quotient(roles, edges, colors, metrics)
    return certificate, colors, metrics


def reconstruct_recursive(encoded: EncodedGraph):
    """Implementation B: recursive structural certificates with memoization."""
    metrics = Metrics()
    roles, edges = decode_evidence(encoded, metrics)

    outgoing: Dict[str, set[Tuple[int, str]]] = defaultdict(set)
    for src, kind, dst in edges:
        outgoing[src].add((kind, dst))

    memo: Dict[str, tuple] = {}
    visiting: set[str] = set()

    def node_certificate(node: str):
        if node in memo:
            metrics.memo_hits += 1
            return memo[node]
        if node in visiting:
            raise AssertionError("benchmark family must remain acyclic")

        visiting.add(node)
        children = [
            (kind, node_certificate(dst))
            for kind, dst in outgoing.get(node, set())
        ]
        children.sort(key=repr)
        metrics.sort_items += len(children)

        certificate = (roles[node], tuple(children))
        visiting.remove(node)
        memo[node] = certificate
        metrics.certificate_constructions += 1
        return certificate

    per_node = {node: node_certificate(node) for node in roles}
    unique = sorted(set(per_node.values()), key=repr)
    metrics.sort_items += len(unique)
    class_for = {certificate: i for i, certificate in enumerate(unique)}
    classes = {node: class_for[certificate] for node, certificate in per_node.items()}

    certificate = canonicalize_quotient(roles, edges, classes, metrics)
    return certificate, classes, metrics


def encode_queries(encoded: EncodedGraph, abstract_pairs: Sequence[Tuple[int, int]]) -> List[Query]:
    return [
        (encoded.local_of_abstract[left], encoded.local_of_abstract[right])
        for left, right in abstract_pairs
    ]


def make_queries(graph: SemanticGraph, count: int, seed: int) -> List[Tuple[int, int]]:
    nodes = sorted(graph.roles)
    rng = random.Random(seed)
    pairs: List[Tuple[int, int]] = []

    role_groups: Dict[int, List[int]] = defaultdict(list)
    for node, role in graph.roles.items():
        role_groups[role].append(node)

    same_role = [group for group in role_groups.values() if len(group) >= 2]
    for i in range(count):
        if i % 4 == 0 and same_role:
            group = same_role[i % len(same_role)]
            pairs.append((group[0], group[-1]))
        else:
            pairs.append((rng.choice(nodes), rng.choice(nodes)))
    return pairs


def answer_queries(classes: Dict[str, int], queries: Sequence[Query], metrics: Metrics) -> List[bool]:
    answers = []
    for left, right in queries:
        metrics.query_steps += 2
        answers.append(classes[left] == classes[right])
    return answers


def digest_json(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:20]


def mutate_relation_kind(graph: SemanticGraph) -> SemanticGraph:
    unique_edges = list(dict.fromkeys(graph.edges))
    src, kind, dst = unique_edges[0]
    unique_edges[0] = (src, (kind + 1) % 3, dst)
    return SemanticGraph(dict(graph.roles), tuple(unique_edges))


def mutate_target(graph: SemanticGraph) -> SemanticGraph:
    unique_edges = list(dict.fromkeys(graph.edges))
    for index, (src, kind, dst) in enumerate(unique_edges):
        for candidate, role in sorted(graph.roles.items()):
            if candidate <= src or candidate == dst:
                continue
            if role == graph.roles[dst]:
                continue
            changed = unique_edges[:]
            changed[index] = (src, kind, candidate)
            return SemanticGraph(dict(graph.roles), tuple(changed))
    raise AssertionError("could not construct target-mutation negative control")


def add_residue(graph: SemanticGraph) -> SemanticGraph:
    roles = dict(graph.roles)
    roles[max(roles) + 1] = 4  # novel admitted residue role
    return SemanticGraph(roles, tuple(dict.fromkeys(graph.edges)))


NEGATIVE_CONTROLS = {
    "relation-kind-change": mutate_relation_kind,
    "target-change": mutate_target,
    "extra-residue": add_residue,
}


def median_reconstruct(fn, encoded: EncodedGraph, reps: int):
    samples = []
    last = None
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        result = fn(encoded)
        samples.append(time.perf_counter_ns() - t0)
        last = result
    assert last is not None
    return last, int(statistics.median(samples))


def run_case(case: Case, reps: int, query_count: int):
    graph = make_graph(case.n_nodes, case.depth, case.seed)

    encoded_a = encode_graph(graph, case.seed ^ 0xA5A5)
    encoded_b = encode_graph(graph, case.seed ^ 0x5A5A)

    (cert_a, classes_a, metrics_a), prepare_a_ns = median_reconstruct(
        reconstruct_partition, encoded_a, reps
    )
    (cert_b, classes_b, metrics_b), prepare_b_ns = median_reconstruct(
        reconstruct_recursive, encoded_b, reps
    )

    certificate_parity = cert_a == cert_b
    if not certificate_parity:
        raise AssertionError(f"{case.case_id}: canonical certificate mismatch")

    abstract_queries = make_queries(graph, query_count, case.seed ^ 0x7777)
    queries_a = encode_queries(encoded_a, abstract_queries)
    queries_b = encode_queries(encoded_b, abstract_queries)

    t0 = time.perf_counter_ns()
    answers_a = answer_queries(classes_a, queries_a, metrics_a)
    query_a_ns = time.perf_counter_ns() - t0

    t0 = time.perf_counter_ns()
    answers_b = answer_queries(classes_b, queries_b, metrics_b)
    query_b_ns = time.perf_counter_ns() - t0

    query_parity = answers_a == answers_b
    if not query_parity:
        raise AssertionError(f"{case.case_id}: semantic query mismatch")

    certificate_digest = digest_json(cert_a)
    query_digest = digest_json(answers_a)

    negative_results = {}
    for name, mutate in NEGATIVE_CONTROLS.items():
        changed = mutate(graph)
        changed_encoded = encode_graph(changed, case.seed ^ (0x9000 + len(name)))
        changed_cert, _changed_classes, _changed_metrics = reconstruct_recursive(changed_encoded)
        detected = changed_cert != cert_a
        negative_results[name] = detected
        if not detected:
            raise AssertionError(f"{case.case_id}: negative control escaped: {name}")

    common = {
        "case_id": case.case_id,
        "n_nodes": case.n_nodes,
        "n_edges_raw": len(graph.edges),
        "n_edges_semantic": len(set(graph.edges)),
        "depth": case.depth,
        "query_count": len(abstract_queries),
        "certificate_digest": certificate_digest,
        "query_digest": query_digest,
        "certificate_parity": int(certificate_parity),
        "query_parity": int(query_parity),
        "negative_relation_kind_detected": int(negative_results["relation-kind-change"]),
        "negative_target_detected": int(negative_results["target-change"]),
        "negative_residue_detected": int(negative_results["extra-residue"]),
        "python_version": platform.python_version(),
    }

    rows = []
    for implementation, metrics, prepare_ns, query_ns in (
        ("partition_refinement", metrics_a, prepare_a_ns, query_a_ns),
        ("recursive_certificate", metrics_b, prepare_b_ns, query_b_ns),
    ):
        rows.append(
            {
                **common,
                "implementation": implementation,
                "prepare_ns": prepare_ns,
                "query_ns": query_ns,
                **asdict(metrics),
            }
        )

    return rows


def default_cases(smoke: bool) -> List[Case]:
    if smoke:
        shapes = ((8, 2), (32, 4), (128, 8))
    else:
        shapes = ((8, 2), (32, 4), (128, 8), (512, 16), (2048, 16))
    return [Case(n_nodes=n, depth=d, seed=2138 + n * 13 + d) for n, d in shapes]


def write_outputs(rows: Sequence[Dict[str, object]], prefix: Path) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())

    with prefix.with_suffix(".tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

    prefix.with_suffix(".json").write_text(
        json.dumps(rows, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def summarize(rows: Sequence[Dict[str, object]]) -> None:
    cases = sorted({str(row["case_id"]) for row in rows})
    print("independent-reconstruction: PASS")
    print(f"cases={len(cases)} implementations=2")
    for case_id in cases:
        subset = [row for row in rows if row["case_id"] == case_id]
        first = subset[0]
        print(
            f"{case_id:12s} "
            f"classes={first['quotient_classes']} "
            f"cert={first['certificate_digest']} "
            f"query={first['query_digest']} "
            f"negative=3/3"
        )
        for row in subset:
            print(
                f"  {row['implementation']:22s} "
                f"reads={row['evidence_reads']:6d} "
                f"sort_items={row['sort_items']:6d} "
                f"rounds={row['refinement_rounds']:3d} "
                f"cert_builds={row['certificate_constructions']:6d} "
                f"memo_hits={row['memo_hits']:6d}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--queries", type=int, default=256)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("/tmp/independent-reconstruction/results"),
    )
    args = parser.parse_args()

    if args.reps < 1:
        raise SystemExit("--reps must be >= 1")
    if args.queries < 1:
        raise SystemExit("--queries must be >= 1")

    rows: List[Dict[str, object]] = []
    for case in default_cases(args.smoke):
        rows.extend(run_case(case, args.reps, args.queries))

    write_outputs(rows, args.out)
    summarize(rows)
    print(f"wrote {args.out.with_suffix('.tsv')}")
    print(f"wrote {args.out.with_suffix('.json')}")


if __name__ == "__main__":
    main()
