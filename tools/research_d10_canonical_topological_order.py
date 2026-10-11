#!/usr/bin/env python3
"""Дослід D10 #4013: канонічний порядок скінченного орієнтованого графа.

Два незалежні алгоритми: Кана та повний перебір перестановок.
Цей host-доказ НЕ реєструє функцію SENS і НЕ призначає координату D10.
"""
from __future__ import annotations

from heapq import heappop, heappush
from itertools import permutations
from random import Random


def validate(n, edges):
    if type(n) is not int or not 0 <= n <= 7:
        raise ValueError("vertex count must be an exact integer from 0 to 7")
    if not isinstance(edges, (list, tuple)) or len(edges) > n * n:
        raise ValueError("bounded edge list required")
    seen = set()
    for edge in edges:
        if (not isinstance(edge, (list, tuple)) or len(edge) != 2 or
                any(type(v) is not int or not 0 <= v < n for v in edge)):
            raise ValueError("edge must be two valid exact vertex indices")
        pair = tuple(edge)
        if pair in seen:
            raise ValueError("duplicate edge")
        seen.add(pair)
    return seen


def kahn_order(n, edges):
    """Найменший лексикографічний топологічний порядок або None при циклі."""
    arcs = validate(n, edges)
    indeg = [0] * n
    outgoing = [[] for _ in range(n)]
    for u, v in arcs:
        indeg[v] += 1
        outgoing[u].append(v)
    heap = []
    for v in range(n):
        if indeg[v] == 0:
            heappush(heap, v)
    result = []
    while heap:
        u = heappop(heap)
        result.append(u)
        for v in outgoing[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                heappush(heap, v)
    return result if len(result) == n else None


def exhaustive_order(n, edges):
    """Незалежна специфікація: перебір усіх перестановок."""
    arcs = validate(n, edges)
    for order in permutations(range(n)):
        position = {v: i for i, v in enumerate(order)}
        if all(position[u] < position[v] for u, v in arcs):
            return list(order)
    return None


def self_test():
    checked = 0
    for n in range(5):
        possible = [(u, v) for u in range(n) for v in range(n)]
        for mask in range(1 << len(possible)):
            edges = [e for i, e in enumerate(possible) if mask & (1 << i)]
            actual = kahn_order(n, edges)
            expected = exhaustive_order(n, edges)
            if actual != expected:
                raise AssertionError((n, edges, actual, expected))
            checked += 1
    rng = Random(1962)
    for n in (5, 6, 7):
        for _ in range(256):
            edges = [(u, v) for u in range(n) for v in range(n)
                     if rng.randrange(4) == 0]
            if kahn_order(n, edges) != exhaustive_order(n, edges):
                raise AssertionError(("sample mismatch", n, edges))
            checked += 1
    fixtures = [
        (0, [], []), (4, [], [0, 1, 2, 3]),
        (3, [(0, 2), (1, 2)], [0, 1, 2]),
        (3, [(0, 1), (1, 2), (2, 0)], None),
    ]
    for n, edges, expected in fixtures:
        if kahn_order(n, edges) != expected:
            raise AssertionError(("fixture mismatch", n, edges, expected))
    for bad_n, bad_edges in [(True, []), (-1, []), (8, []), (1, [(0, 1)]),
                             (2, [(0, 1), (0, 1)]), (2, [(0, True)]),
                             (1, [(0, 0), (0, 0)])]:
        try:
            kahn_order(bad_n, bad_edges)
        except ValueError:
            continue
        raise AssertionError(("invalid accepted", bad_n, bad_edges))
    print(f"PASS: {checked} distinct graphs; Kahn == brute-force; negative controls PASS")


if __name__ == "__main__":
    self_test()
