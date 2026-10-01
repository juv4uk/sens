#!/usr/bin/env python3
"""#2033 countermodel D: selector semantics as a small transducer.

Research only. Tests whether generated selector descendants need to exist as
independently stored semantic nodes, or whether the bounded binary word can be
consumed directly as a program for a tiny typed machine.

Positive control: CAR/CDR selector family through suffix depth 16.
Negative control: all other bīja3 roots must reject without ad-hoc exceptions.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from itertools import product
from pathlib import Path

SELECTOR_ROOTS = {
    "101": "0",  # CAR action code
    "110": "1",  # CDR action code
}
NON_SELECTOR_ROOTS = ("000", "001", "010", "011", "100", "111")


@dataclass(frozen=True)
class Result:
    word: str
    depth: int
    transducer_program: str
    oracle_program: str
    equal: bool


def oracle_program(word: str) -> str:
    """Independent recursive root+child oracle, execution order inner->outer."""
    if word in SELECTOR_ROOTS:
        return SELECTOR_ROOTS[word]
    if len(word) <= 3:
        raise ValueError(f"not a selector word: {word}")
    parent = word[:-1]
    bit = word[-1]
    if bit not in "01":
        raise ValueError(word)
    # Child p0 = parent ∘ CAR, child p1 = parent ∘ CDR.
    # Execution order is therefore child action first, then parent's program.
    return bit + oracle_program(parent)


def transducer_program(word: str) -> str:
    """Streaming/program view: suffix is input, no descendant-node lookup."""
    if len(word) < 3:
        raise ValueError(f"too short: {word}")
    root = word[:3]
    if root not in SELECTOR_ROOTS:
        raise ValueError(f"unsupported root: {root}")
    suffix_outer_to_inner = word[3:]
    # Program is encoded only in binary action symbols:
    # 0=CAR, 1=CDR, execution inner->outer, root last.
    return suffix_outer_to_inner[::-1] + SELECTOR_ROOTS[root]


def selector_words(max_depth: int):
    for root in SELECTOR_ROOTS:
        yield root
        for depth in range(1, max_depth + 1):
            for suffix in product("01", repeat=depth):
                yield root + "".join(suffix)


def run(max_depth: int) -> tuple[list[Result], dict[str, int]]:
    rows: list[Result] = []
    for word in selector_words(max_depth):
        t = transducer_program(word)
        o = oracle_program(word)
        rows.append(
            Result(
                word=word,
                depth=len(word) - 3,
                transducer_program=t,
                oracle_program=o,
                equal=t == o,
            )
        )

    assert all(r.equal for r in rows)

    rejected = 0
    for root in NON_SELECTOR_ROOTS:
        try:
            transducer_program(root)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(f"non-selector root was accidentally accepted: {root}")

    metrics = {
        "selector_words_checked": len(rows),
        "max_suffix_depth": max_depth,
        "selector_root_rules": len(SELECTOR_ROOTS),
        "suffix_transition_rules": 2,
        "stored_descendant_rows_required": 0,
        "non_selector_roots_rejected": rejected,
        "non_selector_exceptions_added": 0,
    }
    return rows, metrics


def write_tsv(path: Path, rows: list[Result], metrics: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(("kind", "key", "value", "note"))
        for key, value in metrics.items():
            writer.writerow(("metric", key, value, "n/a"))
        writer.writerow(
            (
                "epistemic",
                "status",
                "conjecture-local",
                "selector positive control only; non-selector roots intentionally rejected",
            )
        )
        writer.writerow(
            (
                "falsifier",
                "generalization",
                "armed",
                "reject if extending beyond selectors requires near-row-per-meaning states/exceptions",
            )
        )
        sample_depths = {0, 1, 2, 4, 8, 16}
        seen: dict[tuple[str, int], int] = {}
        for r in rows:
            if r.depth not in sample_depths:
                continue
            root = r.word[:3]
            key = (root, r.depth)
            count = seen.get(key, 0)
            # Keep only a tiny representative artifact; parity itself remains
            # exhaustive over every generated word in run().
            if count >= 2:
                continue
            seen[key] = count + 1
            writer.writerow(
                (
                    "sample",
                    r.word,
                    r.transducer_program,
                    f"depth={r.depth};oracle_equal={int(r.equal)}",
                )
            )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=16)
    ap.add_argument(
        "--out",
        default="docs/research/2033-semantic-transducer.tsv",
    )
    args = ap.parse_args()

    rows, metrics = run(args.max_depth)
    write_tsv(Path(args.out), rows, metrics)

    print("countermodel D: semantic transducer")
    for key, value in metrics.items():
        print(f"{key}={value}")
    print("selector_parity=PASS")
    print("non_selector_scope_guard=PASS")
    print("status=conjecture-local")


if __name__ == "__main__":
    main()
