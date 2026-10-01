# Pinned-Guix owner-hardware evidence — #2111

Measured commit: `f954fb96680986b00ebd4febec26d220a8863228`

Benchmark source SHA-256: `5e6a4044470d1f3e2e7d539a9922665d52db187d8366aa0e0c7c3b0cffe93894`

Binary SHA-256: `ac4c4b3c6ddeb240e3edb405836d9bfb4fae67b531f31ec1790b483a534d9771`

`channels.scm` SHA-256: `ff4d6643b694497f06281d3e400d7609815d9e52d276220bf8d9484df522014a`

Environment:

```
guix time-machine -C channels.scm -- shell -m manifest.scm valgrind
CPU: Intel Core i5-6400 @ 2.70GHz
rustc: 1.93.0 (254b59607 2026-01-19), built from source tarball
Valgrind: 3.27.0
```

## Correctness gate

Semantic parity was checked before performance evidence:

- n=32: 1,024/1,024 node pairs;
- n=128: 16,384/16,384;
- n=512: 262,144/262,144.

All six mechanisms answer the same observational-equivalence query.

## Result

The measured preparation/query crossover is stable against the separate unpinned rustc 1.98 run on the same CPU:

- cached observer first beats raw relation at N=3 x 64 = 192 queries;
- quotient class first beats raw at N=5 x 64 = 320 queries;
- exact-word first beats raw at N=5;
- packed-binary first beats raw at N=5.

At N=10000, execute-delta normalized per query:

| candidate | I refs/query | final prepared bytes |
|---|---:|---:|
| raw-relation | 149.975 | 0 |
| observer-cached | 73.412 | 1536 |
| quotient-class | 67.162 | 256 |
| exact-word | 74.162 | 2048 |
| packed-binary | 66.162 | 128 |

Relative to raw steady execution, the bounded mechanism reductions are approximately 51.05% (cached), 55.22% (quotient), 50.55% (exact-word), and 55.88% (packed).

Packed is ~1.49% cheaper than quotient under this pinned rustc 1.93 build, while the unpinned rustc 1.98 build made them nearly equal. Therefore quotient-vs-packed micro-ordering is toolchain/layout-sensitive; the robust result is the materialization crossover, not a universal mechanism winner.

This artifact is **mechanism evidence only**. It does not grant semantic authority to quotient classes, exact words, or packed binary representations. See #2118 anti-circularity discipline and #2141 for scaling the crossover beyond this bounded workload.
