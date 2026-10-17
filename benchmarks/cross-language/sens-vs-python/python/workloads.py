"""Paired source-level reference workloads for the SENS comparison."""

import json


def fib(n: int) -> int:
    """The same naive recursive recurrence used by the SENS workload."""
    if n < 0:
        raise ValueError("fib input must be non-negative")
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


def ackermann(m: int, n: int) -> int:
    """The classic nested recursive Ackermann-Péter recurrence."""
    if m < 0 or n < 0:
        raise ValueError("ackermann inputs must be non-negative")
    if m == 0:
        return n + 1
    if n == 0:
        return ackermann(m - 1, 1)
    return ackermann(m - 1, ackermann(m, n - 1))


def _make_tree(depth: int):
    if depth == 0:
        return None
    return (_make_tree(depth - 1), _make_tree(depth - 1))


def _tree_check(tree) -> int:
    if tree is None:
        return 1
    return 1 + _tree_check(tree[0]) + _tree_check(tree[1])


def binary_trees_checks(n: int) -> list[int]:
    """Return stretch, per-depth churn, and long-lived checks in CLBG order."""
    min_depth = 4
    max_depth = max(min_depth + 2, n)
    stretch_depth = max_depth + 1

    checks = [_tree_check(_make_tree(stretch_depth))]

    long_lived_tree = _make_tree(max_depth)
    for depth in range(min_depth, max_depth + 1, 2):
        iterations = 1 << (max_depth - depth + min_depth)
        checks.append(sum(_tree_check(_make_tree(depth)) for _ in range(iterations)))
    checks.append(_tree_check(long_lived_tree))
    return checks


def binary_trees(n: int) -> str:
    """Computer Language Benchmarks Game single-thread binary-trees profile."""
    min_depth = 4
    max_depth = max(min_depth + 2, n)
    stretch_depth = max_depth + 1
    checks = binary_trees_checks(n)
    lines = [f"stretch tree of depth {stretch_depth}\t check: {checks[0]}"]
    for index, depth in enumerate(range(min_depth, max_depth + 1, 2), start=1):
        iterations = 1 << (max_depth - depth + min_depth)
        lines.append(f"{iterations}\t trees of depth {depth}\t check: {checks[index]}")
    lines.append(f"long lived tree of depth {max_depth}\t check: {checks[-1]}")
    return "\n".join(lines) + "\n"


def json_roundtrip(document: str) -> str:
    """Parse and emit canonical compact JSON with deterministic key order."""
    return json.dumps(json.loads(document), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
