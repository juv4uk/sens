#!/usr/bin/env python3
"""Context carrier benchmark for Γ (#2122).

Compares information preservation and cost for:
  set / multiset / sequence / typed witness map / provenance DAG

Correctness first: rows state which operations a carrier can faithfully
represent. Cost is not interpreted as an optimization when capability differs.
Research-only; no production semantics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import time
from collections import Counter, defaultdict, deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass(frozen=True)
class Evidence:
    wid: int
    claim: int
    polarity: int
    order: int
    deps: Tuple[int, ...]


@dataclass
class Counters:
    reads: int = 0
    writes: int = 0
    lookups: int = 0
    copied_entries: int = 0
    invalidated_nodes: int = 0
    dependency_edges_touched: int = 0
    prepared_objects: int = 0
    prepared_payload_bytes: int = 0

    def add(self, other: "Counters") -> None:
        for k in asdict(self):
            setattr(self, k, getattr(self, k) + getattr(other, k))


CAP_FIELDS = (
    "preserves_order",
    "preserves_multiplicity",
    "preserves_witness_identity",
    "preserves_provenance",
    "preserves_conflict",
    "supports_direct_invalidation",
    "supports_recursive_invalidation",
)


def make_evidence(n_claims: int) -> List[Evidence]:
    out: List[Evidence] = []
    wid = 0
    primary_support: List[int] = []
    for claim in range(n_claims):
        deps: Tuple[int, ...] = ()
        if claim > 0:
            deps = (primary_support[claim - 1],)
        out.append(Evidence(wid, claim, +1, len(out), deps))
        primary_support.append(wid)
        wid += 1
        if claim % 3 == 0:
            out.append(Evidence(wid, claim, +1, len(out), ()))
            wid += 1
        if claim % 5 == 0:
            out.append(Evidence(wid, claim, -1, len(out), ()))
            wid += 1
    return out


def status_digest(statuses: Sequence[int]) -> str:
    return hashlib.sha256(bytes(statuses)).hexdigest()[:16]


def status_from_pairs(pairs: Iterable[Tuple[int, int]], n_claims: int, c: Counters) -> List[int]:
    out = [0] * n_claims
    for claim, polarity in pairs:
        c.reads += 1
        if polarity > 0:
            out[claim] |= 1
        else:
            out[claim] |= 2
    return out


class SetCarrier:
    name = "set"
    capabilities = {
        "preserves_order": False,
        "preserves_multiplicity": False,
        "preserves_witness_identity": False,
        "preserves_provenance": False,
        "preserves_conflict": True,
        "supports_direct_invalidation": False,
        "supports_recursive_invalidation": False,
    }

    @staticmethod
    def prepare(evidence: Sequence[Evidence]):
        c = Counters()
        state: set[Tuple[int, int]] = set()
        for e in evidence:
            c.reads += 1
            state.add((e.claim, e.polarity))
            c.writes += 1
        c.prepared_objects = len(state)
        c.prepared_payload_bytes = len(state) * 8
        return state, c

    @staticmethod
    def statuses(state, n_claims: int, c: Counters) -> List[int]:
        return status_from_pairs(state, n_claims, c)


class MultiCarrier:
    name = "multiset"
    capabilities = {
        "preserves_order": False,
        "preserves_multiplicity": True,
        "preserves_witness_identity": False,
        "preserves_provenance": False,
        "preserves_conflict": True,
        "supports_direct_invalidation": True,
        "supports_recursive_invalidation": False,
    }

    @staticmethod
    def prepare(evidence: Sequence[Evidence]):
        c = Counters()
        state: Counter[Tuple[int, int]] = Counter()
        for e in evidence:
            c.reads += 1
            state[(e.claim, e.polarity)] += 1
            c.writes += 1
        c.prepared_objects = len(state)
        c.prepared_payload_bytes = len(state) * 16
        return state, c

    @staticmethod
    def statuses(state, n_claims: int, c: Counters) -> List[int]:
        return status_from_pairs((k for k, count in state.items() if count > 0), n_claims, c)


class SequenceCarrier:
    name = "sequence"
    capabilities = {
        "preserves_order": True,
        "preserves_multiplicity": True,
        "preserves_witness_identity": True,
        "preserves_provenance": False,
        "preserves_conflict": True,
        "supports_direct_invalidation": True,
        "supports_recursive_invalidation": False,
    }

    @staticmethod
    def prepare(evidence: Sequence[Evidence]):
        c = Counters()
        state: List[Tuple[int, int, int]] = []
        for e in evidence:
            c.reads += 1
            state.append((e.wid, e.claim, e.polarity))
            c.writes += 1
        c.prepared_objects = len(state)
        c.prepared_payload_bytes = len(state) * 12
        return state, c

    @staticmethod
    def statuses(state, n_claims: int, c: Counters) -> List[int]:
        return status_from_pairs(((claim, polarity) for _wid, claim, polarity in state), n_claims, c)


class TypedCarrier:
    name = "typed_witness_map"
    capabilities = {
        "preserves_order": False,
        "preserves_multiplicity": True,
        "preserves_witness_identity": True,
        "preserves_provenance": False,
        "preserves_conflict": True,
        "supports_direct_invalidation": True,
        "supports_recursive_invalidation": False,
    }

    @staticmethod
    def prepare(evidence: Sequence[Evidence]):
        c = Counters()
        state: Dict[str, Dict[int, Tuple[int, int]]] = {"support": {}, "refute": {}}
        for e in evidence:
            c.reads += 1
            bucket = "support" if e.polarity > 0 else "refute"
            state[bucket][e.wid] = (e.claim, e.polarity)
            c.writes += 1
        c.prepared_objects = sum(len(v) for v in state.values()) + 2
        c.prepared_payload_bytes = sum(len(v) for v in state.values()) * 12
        return state, c

    @staticmethod
    def statuses(state, n_claims: int, c: Counters) -> List[int]:
        pairs = list(state["support"].values()) + list(state["refute"].values())
        return status_from_pairs(pairs, n_claims, c)


class DagCarrier:
    name = "provenance_dag"
    capabilities = {
        "preserves_order": False,
        "preserves_multiplicity": True,
        "preserves_witness_identity": True,
        "preserves_provenance": True,
        "preserves_conflict": True,
        "supports_direct_invalidation": True,
        "supports_recursive_invalidation": True,
    }

    @staticmethod
    def prepare(evidence: Sequence[Evidence]):
        c = Counters()
        nodes: Dict[int, Evidence] = {}
        dependents: Dict[int, List[int]] = defaultdict(list)
        for e in evidence:
            c.reads += 1
            nodes[e.wid] = e
            c.writes += 1
            for dep in e.deps:
                dependents[dep].append(e.wid)
                c.dependency_edges_touched += 1
                c.writes += 1
        c.prepared_objects = len(nodes) + sum(len(v) for v in dependents.values())
        c.prepared_payload_bytes = len(nodes) * 20 + sum(len(e.deps) for e in evidence) * 4
        return {"nodes": nodes, "dependents": dict(dependents)}, c

    @staticmethod
    def statuses(state, n_claims: int, c: Counters) -> List[int]:
        nodes = state["nodes"]
        return status_from_pairs(((e.claim, e.polarity) for e in nodes.values()), n_claims, c)


CARRIERS = [SetCarrier, MultiCarrier, SequenceCarrier, TypedCarrier, DagCarrier]


def direct_invalidate(carrier, state, victim: Evidence, c: Counters):
    if carrier is SetCarrier:
        return state
    if carrier is MultiCarrier:
        out = state.copy()
        c.copied_entries += len(out)
        key = (victim.claim, victim.polarity)
        c.lookups += 1
        if out.get(key, 0) > 0:
            out[key] -= 1
            c.writes += 1
            c.invalidated_nodes += 1
            if out[key] <= 0:
                del out[key]
        return out
    if carrier is SequenceCarrier:
        out = []
        removed = False
        for item in state:
            c.reads += 1
            if not removed and item[0] == victim.wid:
                removed = True
                c.invalidated_nodes += 1
                continue
            out.append(item)
            c.writes += 1
        c.copied_entries += len(out)
        return out
    if carrier is TypedCarrier:
        out = {"support": dict(state["support"]), "refute": dict(state["refute"])}
        c.copied_entries += len(out["support"]) + len(out["refute"])
        bucket = "support" if victim.polarity > 0 else "refute"
        c.lookups += 1
        if victim.wid in out[bucket]:
            del out[bucket][victim.wid]
            c.writes += 1
            c.invalidated_nodes += 1
        return out
    if carrier is DagCarrier:
        out = {"nodes": dict(state["nodes"]), "dependents": {k: list(v) for k, v in state["dependents"].items()}}
        c.copied_entries += len(out["nodes"]) + sum(len(v) for v in out["dependents"].values())
        c.lookups += 1
        if victim.wid in out["nodes"]:
            del out["nodes"][victim.wid]
            c.writes += 1
            c.invalidated_nodes += 1
        return out
    raise AssertionError(carrier)


def recursive_invalidate_dag(state, victim_wid: int, c: Counters):
    nodes = dict(state["nodes"])
    dependents = {k: list(v) for k, v in state["dependents"].items()}
    c.copied_entries += len(nodes) + sum(len(v) for v in dependents.values())
    q = deque([victim_wid])
    doomed: set[int] = set()
    while q:
        wid = q.popleft()
        c.lookups += 1
        if wid in doomed:
            continue
        doomed.add(wid)
        for child in dependents.get(wid, ()):
            c.dependency_edges_touched += 1
            q.append(child)
    for wid in doomed:
        if wid in nodes:
            del nodes[wid]
            c.writes += 1
            c.invalidated_nodes += 1
    return {"nodes": nodes, "dependents": dependents}


def median_prepare(carrier, evidence: Sequence[Evidence], reps: int):
    samples = []
    last_state = None
    last_c = Counters()
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        state, c = carrier.prepare(evidence)
        samples.append(time.perf_counter_ns() - t0)
        last_state, last_c = state, c
    return last_state, last_c, int(statistics.median(samples))


def median_status(carrier, state, n_claims: int, reps: int):
    samples = []
    last_status = []
    last_c = Counters()
    for _ in range(reps):
        c = Counters()
        t0 = time.perf_counter_ns()
        status = carrier.statuses(state, n_claims, c)
        samples.append(time.perf_counter_ns() - t0)
        last_status, last_c = status, c
    return last_status, last_c, int(statistics.median(samples))


def capability_bits(carrier) -> Dict[str, int]:
    return {k: int(bool(carrier.capabilities[k])) for k in CAP_FIELDS}


def run_case(n_claims: int, reps: int) -> List[Dict[str, object]]:
    evidence = make_evidence(n_claims)
    victim = next(e for e in evidence if e.claim == 1 and e.polarity > 0)
    reference_c = Counters()
    ref_state, _ = DagCarrier.prepare(evidence)
    reference_status = DagCarrier.statuses(ref_state, n_claims, reference_c)
    rows: List[Dict[str, object]] = []

    for carrier in CARRIERS:
        state, prep_c, prepare_ns = median_prepare(carrier, evidence, reps)
        status, query_c, query_ns = median_status(carrier, state, n_claims, reps)
        if status != reference_status:
            raise AssertionError(f"initial status mismatch: {carrier.name}")

        base = {
            "case_id": f"claims-{n_claims}",
            "carrier": carrier.name,
            "n_claims": n_claims,
            "n_evidence": len(evidence),
            **capability_bits(carrier),
            "prepare_ns": prepare_ns,
            "query_ns": query_ns,
            "initial_status_digest": status_digest(status),
            "python_version": platform.python_version(),
        }

        total = Counters()
        total.add(prep_c)
        total.add(query_c)
        rows.append({**base, "workload": "initial_query", "semantics_comparable": 1, **asdict(total)})

        if carrier.capabilities["supports_direct_invalidation"]:
            dc = Counters()
            t0 = time.perf_counter_ns()
            dstate = direct_invalidate(carrier, state, victim, dc)
            invalidate_ns = time.perf_counter_ns() - t0
            dstatus, qc, post_query_ns = median_status(carrier, dstate, n_claims, reps)
            rc = Counters()
            rdirect = direct_invalidate(DagCarrier, ref_state, victim, rc)
            rstatus = DagCarrier.statuses(rdirect, n_claims, Counters())
            if dstatus != rstatus:
                raise AssertionError(f"direct invalidation mismatch: {carrier.name}")
            dc.add(qc)
            rows.append({
                **base,
                "workload": "direct_invalidate",
                "semantics_comparable": 1,
                "prepare_ns": 0,
                "query_ns": post_query_ns,
                "mutation_ns": invalidate_ns,
                "post_status_digest": status_digest(dstatus),
                **asdict(dc),
            })
        else:
            rows.append({
                **base,
                "workload": "direct_invalidate",
                "semantics_comparable": 0,
                "prepare_ns": 0,
                "query_ns": 0,
                "mutation_ns": 0,
                "post_status_digest": "",
                **asdict(Counters()),
            })

        if carrier.capabilities["supports_recursive_invalidation"]:
            rc = Counters()
            t0 = time.perf_counter_ns()
            rstate = recursive_invalidate_dag(state, victim.wid, rc)
            mutation_ns = time.perf_counter_ns() - t0
            rstatus, qc, post_query_ns = median_status(carrier, rstate, n_claims, reps)
            rc.add(qc)
            rows.append({
                **base,
                "workload": "recursive_invalidate",
                "semantics_comparable": 1,
                "prepare_ns": 0,
                "query_ns": post_query_ns,
                "mutation_ns": mutation_ns,
                "post_status_digest": status_digest(rstatus),
                **asdict(rc),
            })
        else:
            rows.append({
                **base,
                "workload": "recursive_invalidate",
                "semantics_comparable": 0,
                "prepare_ns": 0,
                "query_ns": 0,
                "mutation_ns": 0,
                "post_status_digest": "",
                **asdict(Counters()),
            })
    return rows


def write_outputs(rows: Sequence[Dict[str, object]], prefix: Path) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    seen = set()
    for row in rows:
        for k in row:
            if k not in seen:
                seen.add(k)
                fields.append(k)
    with prefix.with_suffix(".tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    prefix.with_suffix(".json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize(rows: Sequence[Dict[str, object]]) -> None:
    print("context-carrier: initial semantic status parity PASS")
    for carrier in [c.name for c in CARRIERS]:
        subset = [r for r in rows if r["carrier"] == carrier]
        cap = subset[0]
        print(
            f"{carrier:18s} "
            f"order={cap['preserves_order']} mult={cap['preserves_multiplicity']} "
            f"wid={cap['preserves_witness_identity']} prov={cap['preserves_provenance']} "
            f"direct_inv={cap['supports_direct_invalidation']} recursive_inv={cap['supports_recursive_invalidation']}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--out", type=Path, default=Path("/tmp/context-carrier/results"))
    args = ap.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be >= 1")

    sizes = (8, 64, 512) if args.smoke else (8, 64, 512, 4096)
    rows: List[Dict[str, object]] = []
    for n in sizes:
        rows.extend(run_case(n, args.reps))

    write_outputs(rows, args.out)
    summarize(rows)
    print(f"wrote {args.out.with_suffix('.tsv')}")
    print(f"wrote {args.out.with_suffix('.json')}")


if __name__ == "__main__":
    main()
