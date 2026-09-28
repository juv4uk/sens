#!/usr/bin/env python3
"""#1549 reference oracle for Computer Language Benchmarks Game binary-trees.

This file is correctness/provenance infrastructure, not a performance result.
The measured SENS/CPython adapters are wired into the shared cross-language
harness only after the canonical 2-part COND migration (#1663).
"""

from __future__ import annotations

import argparse
from pathlib import Path

MIN_DEPTH = 4
FIXTURE = Path(__file__).with_name("fixtures") / "binary-trees-n10.expected"


class Node:
    def __init__(self, left: "Node | None" = None, right: "Node | None" = None):
        self.left = left
        self.right = right

    def check(self) -> int:
        if self.left is None:
            return 1
        assert self.right is not None
        return 1 + self.left.check() + self.right.check()


def bottom_up_tree(depth: int) -> Node:
    if depth <= 0:
        return Node()
    return Node(bottom_up_tree(depth - 1), bottom_up_tree(depth - 1))


def render(n: int) -> str:
    max_depth = max(MIN_DEPTH + 2, n)
    stretch_depth = max_depth + 1

    lines = [
        f"stretch tree of depth {stretch_depth}\t check: "
        f"{bottom_up_tree(stretch_depth).check()}"
    ]

    long_lived_tree = bottom_up_tree(max_depth)

    for depth in range(MIN_DEPTH, max_depth + 1, 2):
        iterations = 1 << (max_depth - depth + MIN_DEPTH)
        check = 0
        for _ in range(iterations):
            check += bottom_up_tree(depth).check()
        lines.append(
            f"{iterations}\t trees of depth {depth}\t check: {check}"
        )

    lines.append(
        f"long lived tree of depth {max_depth}\t check: "
        f"{long_lived_tree.check()}"
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("n", nargs="?", type=int, default=10)
    parser.add_argument("--check-fixture", action="store_true")
    args = parser.parse_args()

    output = render(args.n)

    if args.check_fixture:
        if args.n != 10:
            parser.error("--check-fixture is defined only for N=10")
        expected = FIXTURE.read_text(encoding="utf-8")
        if output != expected:
            raise SystemExit(
                "binary-trees N=10 oracle drift\n"
                f"expected:\n{expected}\nactual:\n{output}"
            )
        print("binary-trees N=10 fixture: PASS")
        return 0

    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
