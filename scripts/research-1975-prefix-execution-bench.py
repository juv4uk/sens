#!/usr/bin/env python3
"""#1975 research-only microbenchmark: generated selector execution vs cache/table.

This is NOT a production performance claim. Python timings are only a mechanism
probe. Semantic authority remains root+suffix; caches/tables here are disposable
mechanical projections.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import random
import statistics
import time

ROOTS = {"101": 0, "110": 1}  # 0=CAR, 1=CDR
BITS = {"0": 0, "1": 1}

HOT_WORDS = ("1010", "1011", "1101", "10111", "101111", "1011111")


class Pair:
    __slots__ = ("car", "cdr")
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr


def full_tree(depth: int, label: int = 1):
    if depth == 0:
        return label
    return Pair(full_tree(depth - 1, label * 2), full_tree(depth - 1, label * 2 + 1))


def compile_word(word: str) -> tuple[int, ...]:
    if len(word) < 3 or word[:3] not in ROOTS or any(c not in "01" for c in word):
        raise ValueError(word)
    return (ROOTS[word[:3]],) + tuple(BITS[b] for b in word[3:])


@lru_cache(maxsize=None)
def compile_word_cached(word: str) -> tuple[int, ...]:
    return compile_word(word)


def run_ops(ops: tuple[int, ...], value):
    out = value
    for op in reversed(ops):
        if not isinstance(out, Pair):
            raise TypeError("selector domain")
        out = out.car if op == 0 else out.cdr
    return out


def execute_dynamic(word: str, value):
    return run_ops(compile_word(word), value)


def execute_cached(word: str, value):
    return run_ops(compile_word_cached(word), value)


def build_flat(max_suffix: int) -> dict[str, tuple[int, ...]]:
    out = {}
    for root in ROOTS:
        for n in range(max_suffix + 1):
            for i in range(1 << n):
                suffix = f"{i:0{n}b}" if n else ""
                word = root + suffix
                out[word] = compile_word(word)
    return out


def execute_flat(table, word: str, value):
    return run_ops(table[word], value)


def timed(fn, workload, value, rounds=5):
    samples = []
    checksum = 0
    for _ in range(rounds):
        start = time.perf_counter_ns()
        local = 0
        for word in workload:
            local ^= int(fn(word, value))
        samples.append(time.perf_counter_ns() - start)
        checksum ^= local
    return statistics.median(samples), checksum


def main():
    random.seed(1975)
    tree = full_tree(14)
    flat = build_flat(8)  # 1022 generated words, not semantic identities.

    # Hot workload matches bounded current selector paths; repeated enough to
    # make compile/lookup differences visible.
    workload = [random.choice(HOT_WORDS) for _ in range(200_000)]

    compile_word_cached.cache_clear()
    dynamic_ns, c1 = timed(execute_dynamic, workload, tree)

    compile_word_cached.cache_clear()
    cached_ns, c2 = timed(execute_cached, workload, tree)

    flat_ns, c3 = timed(lambda w, v: execute_flat(flat, w, v), workload, tree)

    assert c1 == c2 == c3
    assert compile_word_cached.cache_info().currsize == len(set(HOT_WORDS))

    print("selector execution microbenchmark (Python research mechanism only)")
    print(f"calls: {len(workload)}")
    print(f"hot unique words: {len(set(workload))}")
    print(f"flat precomputed words (suffix<=8): {len(flat)}")
    print(f"lazy cache entries after workload: {compile_word_cached.cache_info().currsize}")
    print()
    print("mode\tmedian-ms\tns/call\tderived-entries-required")
    for name, ns, entries in (
        ("dynamic-root+suffix", dynamic_ns, 0),
        ("lazy-derived-cache", cached_ns, compile_word_cached.cache_info().currsize),
        ("flat-precomputed", flat_ns, len(flat)),
    ):
        print(f"{name}\t{ns/1e6:.3f}\t{ns/len(workload):.1f}\t{entries}")
    print()
    print("semantic root mechanisms: 2")
    print("semantic suffix actions:   2")
    print("semantic descendant rows required by all three modes: 0")
    print()
    print("INTERPRETATION:")
    print("- dynamic decoding measures the cost of reconstructing the path every call;")
    print("- lazy cache is a disposable mechanism projection derived from the word;")
    print("- flat table precomputes many unused paths and is not semantic authority;")
    print("- timings are Python-specific and must not be treated as runtime verdict.")


if __name__ == "__main__":
    main()
