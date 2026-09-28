# binary-trees provenance (#1549)

This benchmark slice follows the Computer Language Benchmarks Game **binary-trees**
workload, version label **25.03** as recorded in #1549.

Primary description:
https://benchmarksgame-team.pages.debian.net/benchmarksgame/performance/binarytrees.html

The workload contract used here is:

- single-thread in our comparison profile;
- `min_depth = 4`;
- `max_depth = max(min_depth + 2, N)`;
- stretch tree depth = `max_depth + 1`;
- long-lived tree depth = `max_depth`;
- depths `4..max_depth` by 2;
- iterations at depth `d` = `2^(max_depth + min_depth - d)`;
- every tree is a fully allocated perfect binary tree;
- check = node count;
- no custom arena, memory pool, free-list, or equivalent allocation shortcut;
- correctness fixture first at `N=10`;
- `N=21` is only a later performance scale if SENS can run it practically.

The upstream description explicitly requires constructing the trees, walking them,
allowing short-lived trees to be reclaimed, retaining a long-lived tree, and
checking `N=10` output before performance runs.

The N=10 fixture in this directory is:

    stretch tree of depth 11     check: 4095
    1024     trees of depth 4    check: 31744
    256      trees of depth 6    check: 32512
    64       trees of depth 8    check: 32704
    16       trees of depth 10   check: 32752
    long lived tree of depth 10  check: 2047

This repository does **not** import timing numbers from the Benchmarks Game.
All performance evidence must be produced on our own same-machine runners using
the shared cross-language schema.

The Python file `binary_trees_reference.py` is an oracle/scaffold only until
the SENS implementation is replayed onto canonical 2-part COND (#1663). It is
not yet a benchmark result.
