#!/usr/bin/env python3
"""Research-only #4991: Mackworth 1977 finite directed binary arc-consistency.

No SENS/D10 identity, opcode, selection, or oracle-authority is created here.
The output is the GREATEST componentwise subdomain fixed by every declared
directed arc. ARC-CONSISTENT does not imply globally SAT.
"""
from __future__ import annotations

from collections import deque
from itertools import product
import json

STATUS_OK = "ARC-CONSISTENT"
STATUS_EMPTY = "EMPTY-DOMAIN-CONTRADICTION"


def normalize(problem: dict) -> tuple[dict[str, tuple[int, ...]], tuple]:
    if not isinstance(problem, dict) or set(problem) != {"domains", "arcs"}:
        raise ValueError("expected only domains/arcs")
    raw_domains, raw_arcs = problem["domains"], problem["arcs"]
    if not isinstance(raw_domains, dict) or not raw_domains:
        raise ValueError("finite named domains required")
    domains = {}
    for name, vals in raw_domains.items():
        if (not isinstance(name, str) or not name or
                not name.isascii() or not name[0].isalpha() or
                not all(ch.isalnum() or ch == "_" for ch in name)):
            raise ValueError("invalid variable name")
        if not isinstance(vals, list) or len(vals) > 16:
            raise ValueError("domain must be finite list of at most 16 values")
        if any(type(value) is not int or not (-100000 <= value <= 100000)
               for value in vals):
            raise ValueError("domain values must be bounded exact integers")
        if len(vals) != len(set(vals)):
            raise ValueError("duplicate domain value")
        domains[name] = tuple(sorted(vals))
    if not isinstance(raw_arcs, list) or len(raw_arcs) > 64:
        raise ValueError("arcs must be finite list")
    arcs = {}
    for item in raw_arcs:
        if not isinstance(item, dict) or set(item) != {"from", "to", "allowed"}:
            raise ValueError("malformed directed arc")
        src, dst, pairs = item["from"], item["to"], item["allowed"]
        if src not in domains or dst not in domains or src == dst:
            raise ValueError("arc must reference two distinct declared variables")
        if not isinstance(pairs, list) or len(pairs) > 256:
            raise ValueError("allowed pairs must be finite")
        allowed = set()
        for pair in pairs:
            if (not isinstance(pair, list) or len(pair) != 2
                    or any(type(v) is not int for v in pair)
                    or any(not (-100000 <= v <= 100000) for v in pair)):
                raise ValueError("allowed pair outside original declared domains")
            if tuple(pair) in allowed:
                raise ValueError("duplicate allowed pair")
            allowed.add(tuple(pair))
        key = (src, dst)
        if key in arcs and arcs[key] != frozenset(allowed):
            raise ValueError("conflicting duplicate directed arc")
        arcs[key] = frozenset(allowed)
    return dict(sorted(domains.items())), tuple(
        (src, dst, arcs[src, dst]) for src, dst in sorted(arcs)
    )


def _answer(domains: dict[str, tuple[int, ...]]) -> dict:
    return {
        "domains": {name: list(values) for name, values in sorted(domains.items())},
        "status": STATUS_EMPTY if any(not v for v in domains.values()) else STATUS_OK,
    }


def queue_fixpoint(problem: dict) -> dict:
    """Incremental monotone pruning; recheck dependents of every narrowed Y."""
    domains, arcs = normalize(problem)
    agenda = deque(range(len(arcs)))
    queued = set(agenda)
    while agenda:
        i = agenda.popleft()
        queued.remove(i)
        src, dst, allowed = arcs[i]
        new = tuple(x for x in domains[src]
                    if any((x, y) in allowed for y in domains[dst]))
        if new == domains[src]:
            continue
        domains[src] = new
        for j, (_, target, _) in enumerate(arcs):
            if target == src and j not in queued:
                agenda.append(j)
                queued.add(j)
    return _answer(domains)


def round_fixpoint(problem: dict) -> dict:
    """Independent synchronous full scans (NOT using the queue machinery)."""
    state, arcs = normalize(problem)
    while True:
        next_state = {}
        for source, current in state.items():
            related = [(dest, allowed) for first, dest, allowed in arcs
                       if first == source]
            next_state[source] = tuple(
                x for x in current
                if all(any((x, y) in relation for y in state[dest])
                       for dest, relation in related)
            )
        if next_state == state:
            return _answer(next_state)
        state = next_state


def has_global_solution(problem: dict) -> bool:
    """Research-only bounded falsifier; never inferred from local status."""
    domains, arcs = normalize(problem)
    names = list(domains)
    for values in product(*(domains[name] for name in names)):
        assignment = dict(zip(names, values))
        if all((assignment[src], assignment[dst]) in allowed
               for src, dst, allowed in arcs):
            return True
    return False


def main() -> int:
    import sys
    for line in sys.stdin:
        try:
            print(json.dumps(queue_fixpoint(json.loads(line)), sort_keys=True))
        except (ValueError, TypeError, KeyError) as error:
            print(json.dumps({"error":str(error)}), file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
