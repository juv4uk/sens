#!/usr/bin/env python3
"""Foundation cost ladder benchmark (#2115).

Measures the same observational-equivalence query across progressively
materialized representations:

raw relation -> indexed observer -> cached observer -> quotient
-> exact word coordinate -> packed binary coordinate

Semantic query:
    sig_O(x) = {a | exists y. x -a-> y}
    x ~=_O y iff sig_O(x) == sig_O(y)

Wall time is diagnostic only. Deterministic logical counters are primary.
Research-only: no production semantics.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, List, Sequence, Tuple

Edge = Tuple[int, int, int]
Query = Tuple[int, int]


@dataclass
class Counters:
    logical_relation_reads: int = 0
    indexed_reads: int = 0
    signature_builds: int = 0
    cache_lookups: int = 0
    quotient_lookups: int = 0
    word_symbol_compares: int = 0
    packed_compares: int = 0
    prepared_objects: int = 0
    prepared_payload_bytes: int = 0

    def add(self, other: "Counters") -> None:
        for key in asdict(self):
            setattr(self, key, getattr(self, key) + getattr(other, key))


@dataclass(frozen=True)
class Case:
    case_id: str
    n_states: int
    n_actions: int
    density_num: int
    density_den: int
    n_queries: int
    query_mode: str
    seed: int

    @property
    def density_label(self) -> str:
        return f"{self.density_num}/{self.density_den}"


def enabled(seed: int, state: int, action: int, num: int, den: int) -> bool:
    x = (seed * 0x9E3779B1 + state * 0x85EBCA77 + action * 0xC2B2AE3D) & 0xFFFFFFFF
    x ^= x >> 16
    x = (x * 0x7FEB352D) & 0xFFFFFFFF
    x ^= x >> 15
    return (x % den) < num


def make_edges(case: Case) -> List[Edge]:
    edges: List[Edge] = []
    for s in range(case.n_states):
        any_action = False
        for a in range(case.n_actions):
            if enabled(case.seed, s, a, case.density_num, case.density_den):
                dst = (s * 33 + a * 17 + case.seed) % case.n_states
                edges.append((s, a, dst))
                any_action = True
        if not any_action:
            a = (s + case.seed) % case.n_actions
            dst = (s * 33 + a * 17 + case.seed) % case.n_states
            edges.append((s, a, dst))
    return edges


def signature_from_edges(edges: Sequence[Edge], state: int, counters: Counters) -> int:
    mask = 0
    for src, action, _dst in edges:
        counters.logical_relation_reads += 1
        if src == state:
            mask |= 1 << action
    counters.signature_builds += 1
    return mask


def build_index(edges: Sequence[Edge], n_states: int) -> Tuple[List[List[int]], Counters]:
    c = Counters()
    index: List[List[int]] = [[] for _ in range(n_states)]
    c.prepared_objects += n_states
    c.prepared_payload_bytes += len(edges) * 4 + n_states * 8
    for src, action, _dst in edges:
        c.logical_relation_reads += 1
        index[src].append(action)
    return index, c


def signature_from_index(index: Sequence[Sequence[int]], state: int, counters: Counters) -> int:
    mask = 0
    for action in index[state]:
        counters.indexed_reads += 1
        mask |= 1 << action
    counters.signature_builds += 1
    return mask


def build_cached(edges: Sequence[Edge], n_states: int) -> Tuple[List[int], Counters]:
    index, c = build_index(edges, n_states)
    masks: List[int] = []
    c.prepared_objects += n_states
    c.prepared_payload_bytes += n_states * 8
    for s in range(n_states):
        masks.append(signature_from_index(index, s, c))
    return masks, c


def build_quotient(edges: Sequence[Edge], n_states: int) -> Tuple[List[int], int, Counters]:
    masks, c = build_cached(edges, n_states)
    class_for_mask: Dict[int, int] = {}
    classes: List[int] = []
    for mask in masks:
        if mask not in class_for_mask:
            class_for_mask[mask] = len(class_for_mask)
        classes.append(class_for_mask[mask])
    c.prepared_objects += len(class_for_mask) + n_states
    c.prepared_payload_bytes += len(class_for_mask) * 16 + n_states * 4
    return classes, len(class_for_mask), c


def class_width(n_classes: int) -> int:
    return max(1, math.ceil(math.log2(max(1, n_classes))))


def build_words(edges: Sequence[Edge], n_states: int) -> Tuple[List[str], int, Counters]:
    classes, n_classes, c = build_quotient(edges, n_states)
    width = class_width(n_classes)
    words = [format(cid, f"0{width}b") for cid in classes]
    c.prepared_objects += n_states
    c.prepared_payload_bytes += n_states * width
    return words, n_classes, c


def build_packed(edges: Sequence[Edge], n_states: int) -> Tuple[List[int], int, Counters]:
    classes, n_classes, c = build_quotient(edges, n_states)
    width = class_width(n_classes)
    bytes_per = max(1, math.ceil(width / 8))
    packed = list(classes)
    c.prepared_objects += n_states
    c.prepared_payload_bytes += n_states * bytes_per
    return packed, n_classes, c


def make_queries(case: Case, baseline_masks: Sequence[int]) -> List[Query]:
    q: List[Query] = []
    n = case.n_states
    by_mask: Dict[int, List[int]] = {}
    for s, mask in enumerate(baseline_masks):
        by_mask.setdefault(mask, []).append(s)

    same_pairs: List[Query] = []
    for states in by_mask.values():
        if len(states) >= 2:
            same_pairs.append((states[0], states[1]))

    masks = list(by_mask)
    diff_pairs: List[Query] = []
    for i in range(len(masks) - 1):
        diff_pairs.append((by_mask[masks[i]][0], by_mask[masks[i + 1]][0]))

    if not same_pairs:
        same_pairs = [(0, 0)]
    if not diff_pairs:
        diff_pairs = [(0, (1 if n > 1 else 0))]

    if case.query_mode == "hot":
        base = [same_pairs[0], diff_pairs[0]]
        for i in range(case.n_queries):
            q.append(base[i & 1])
    else:
        specials = same_pairs + diff_pairs
        for i in range(case.n_queries):
            if i % 4 == 0:
                q.append(specials[(i // 4) % len(specials)])
            else:
                x = (i * 17 + case.seed) % n
                y = (i * 61 + case.seed * 3 + 1) % n
                q.append((x, y))
    return q


def answer_digest(answers: Sequence[bool]) -> str:
    raw = bytes(1 if x else 0 for x in answers)
    return hashlib.sha256(raw).hexdigest()[:16]


PrepareFn = Callable[[Sequence[Edge], int], Tuple[object, Counters]]
QueryFn = Callable[[object, Query, Counters], bool]


def raw_prepare(edges: Sequence[Edge], _n_states: int) -> Tuple[object, Counters]:
    return edges, Counters()


def raw_query(state: object, query: Query, c: Counters) -> bool:
    edges = state
    assert isinstance(edges, Sequence)
    x, y = query
    return signature_from_edges(edges, x, c) == signature_from_edges(edges, y, c)


def observer_prepare(edges: Sequence[Edge], n_states: int) -> Tuple[object, Counters]:
    return build_index(edges, n_states)


def observer_query(state: object, query: Query, c: Counters) -> bool:
    index = state
    assert isinstance(index, Sequence)
    x, y = query
    return signature_from_index(index, x, c) == signature_from_index(index, y, c)


def cached_prepare(edges: Sequence[Edge], n_states: int) -> Tuple[object, Counters]:
    return build_cached(edges, n_states)


def cached_query(state: object, query: Query, c: Counters) -> bool:
    masks = state
    assert isinstance(masks, Sequence)
    x, y = query
    c.cache_lookups += 2
    return masks[x] == masks[y]


def quotient_prepare(edges: Sequence[Edge], n_states: int) -> Tuple[object, Counters]:
    classes, _n_classes, c = build_quotient(edges, n_states)
    return classes, c


def quotient_query(state: object, query: Query, c: Counters) -> bool:
    classes = state
    assert isinstance(classes, Sequence)
    x, y = query
    c.quotient_lookups += 2
    return classes[x] == classes[y]


def word_prepare(edges: Sequence[Edge], n_states: int) -> Tuple[object, Counters]:
    words, _n_classes, c = build_words(edges, n_states)
    return words, c


def word_query(state: object, query: Query, c: Counters) -> bool:
    words = state
    assert isinstance(words, Sequence)
    x, y = query
    a, b = words[x], words[y]
    if len(a) != len(b):
        return False
    for ca, cb in zip(a, b):
        c.word_symbol_compares += 1
        if ca != cb:
            return False
    return True


def packed_prepare(edges: Sequence[Edge], n_states: int) -> Tuple[object, Counters]:
    packed, _n_classes, c = build_packed(edges, n_states)
    return packed, c


def packed_query(state: object, query: Query, c: Counters) -> bool:
    packed = state
    assert isinstance(packed, Sequence)
    x, y = query
    c.packed_compares += 1
    return packed[x] == packed[y]


CANDIDATES: Dict[str, Tuple[PrepareFn, QueryFn]] = {
    "raw_relation": (raw_prepare, raw_query),
    "observer_index": (observer_prepare, observer_query),
    "cached_observer": (cached_prepare, cached_query),
    "quotient": (quotient_prepare, quotient_query),
    "exact_word": (word_prepare, word_query),
    "packed_binary": (packed_prepare, packed_query),
}


def median_prepare(prepare: PrepareFn, edges: Sequence[Edge], n_states: int, reps: int) -> Tuple[object, Counters, int]:
    samples: List[int] = []
    last_state: object = None
    last_c = Counters()
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        state, c = prepare(edges, n_states)
        samples.append(time.perf_counter_ns() - t0)
        last_state, last_c = state, c
    return last_state, last_c, int(statistics.median(samples))


def median_execute(query_fn: QueryFn, state: object, queries: Sequence[Query], reps: int) -> Tuple[List[bool], Counters, int]:
    samples: List[int] = []
    last_answers: List[bool] = []
    last_c = Counters()
    for _ in range(reps):
        c = Counters()
        t0 = time.perf_counter_ns()
        answers = [query_fn(state, q, c) for q in queries]
        samples.append(time.perf_counter_ns() - t0)
        last_answers, last_c = answers, c
    return last_answers, last_c, int(statistics.median(samples))


def baseline_masks(edges: Sequence[Edge], n_states: int) -> List[int]:
    masks, _c = build_cached(edges, n_states)
    return masks


def run_case(case: Case, reps: int) -> List[Dict[str, object]]:
    edges = make_edges(case)
    masks = baseline_masks(edges, case.n_states)
    queries = make_queries(case, masks)

    rows: List[Dict[str, object]] = []
    reference_answers: List[bool] | None = None

    for name, (prepare, query_fn) in CANDIDATES.items():
        state, prep_c, prepare_ns = median_prepare(prepare, edges, case.n_states, reps)
        answers, exec_c, execute_ns = median_execute(query_fn, state, queries, reps)

        if reference_answers is None:
            reference_answers = answers
        elif answers != reference_answers:
            raise AssertionError(f"{case.case_id}: semantic mismatch in {name}")

        total_c = Counters()
        total_c.add(prep_c)
        total_c.add(exec_c)

        row: Dict[str, object] = {
            "case_id": case.case_id,
            "candidate": name,
            "n_states": case.n_states,
            "n_actions": case.n_actions,
            "n_edges": len(edges),
            "density": case.density_label,
            "n_queries": len(queries),
            "query_mode": case.query_mode,
            "prepare_ns": prepare_ns,
            "execute_ns": execute_ns,
            "amortized_ns": prepare_ns + execute_ns,
            **asdict(total_c),
            "answer_true": sum(answers),
            "answer_false": len(answers) - sum(answers),
            "answer_digest": answer_digest(answers),
            "python_version": platform.python_version(),
        }
        rows.append(row)
    return rows


def default_cases(smoke: bool) -> List[Case]:
    sizes = (8, 64, 512) if smoke else (8, 64, 512, 4096)
    n_queries = 256 if smoke else 4096
    cases: List[Case] = []
    for n in sizes:
        for actions in (2, 4, 8):
            for num, den, density_name in ((1, 4, "sparse"), (3, 4, "dense")):
                for mode in ("hot", "distinct"):
                    cases.append(
                        Case(
                            case_id=f"n{n}-a{actions}-{density_name}-{mode}",
                            n_states=n,
                            n_actions=actions,
                            density_num=num,
                            density_den=den,
                            n_queries=n_queries,
                            query_mode=mode,
                            seed=2115,
                        )
                    )
    return cases


def write_outputs(rows: Sequence[Dict[str, object]], out_prefix: Path) -> None:
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    tsv_path = out_prefix.with_suffix(".tsv")
    json_path = out_prefix.with_suffix(".json")
    fieldnames = list(rows[0].keys())
    with tsv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize(rows: Sequence[Dict[str, object]]) -> None:
    print("foundation-cost-ladder: semantic parity PASS")
    for name in CANDIDATES:
        subset = [r for r in rows if r["candidate"] == name]
        print(
            f"{name:16s} "
            f"relation_reads={sum(int(r['logical_relation_reads']) for r in subset):12d} "
            f"indexed_reads={sum(int(r['indexed_reads']) for r in subset):10d} "
            f"cache={sum(int(r['cache_lookups']) for r in subset):10d} "
            f"quotient={sum(int(r['quotient_lookups']) for r in subset):10d} "
            f"word_cmp={sum(int(r['word_symbol_compares']) for r in subset):10d} "
            f"packed_cmp={sum(int(r['packed_compares']) for r in subset):10d}"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="smaller CI corpus")
    ap.add_argument("--reps", type=int, default=3, help="median wall-time repetitions")
    ap.add_argument("--out", type=Path, default=Path("/tmp/foundation-cost-ladder/results"))
    args = ap.parse_args()
    if args.reps < 1:
        raise SystemExit("--reps must be >= 1")

    rows: List[Dict[str, object]] = []
    for case in default_cases(args.smoke):
        rows.extend(run_case(case, args.reps))

    by_case: Dict[str, set[str]] = {}
    for row in rows:
        by_case.setdefault(str(row["case_id"]), set()).add(str(row["answer_digest"]))
    bad = {k: v for k, v in by_case.items() if len(v) != 1}
    if bad:
        raise AssertionError(f"digest mismatch: {bad}")

    write_outputs(rows, args.out)
    summarize(rows)
    print(f"wrote {args.out.with_suffix('.tsv')}")
    print(f"wrote {args.out.with_suffix('.json')}")


if __name__ == "__main__":
    main()
