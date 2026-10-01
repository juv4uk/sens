# #1988: root + suffix execution cost (research harness, not production)

Compares four execution strategies for the **proven selector family** of #1975 (root `101` CAR / `110` CDR,
suffix bit `0` CAR / `1` CDR, stored outer -> inner, applied inner -> outer; word `1011` = CADR) on exactly the same
calls, with exact parity against an independent `c[ad]+r` oracle **before** any measurement.

| | strategy |
|---|---|
| A | flat lookup: a precomputed row per descendant (its build cost is preparation, reported, never hidden) |
| B | root + suffix interpreted on every call |
| C | root + suffix with a decoded-path cache (direct-mapped, 1024 slots) |
| D | hybrid: flat rows for suffix length <= 2, interpreter above |

Not in this slice: the compiled-to-IR path (the third #1988 route), other families, CML.

## Run

```bash
python3 benchmarks/semantic-tree-exec/run.py --out docs/research/1988-selector-exec-bench.tsv   # needs gcc, valgrind
```

Cachegrind with `--cache-sim=no` (the convention of `benchmarks/sens-surface/icount.sh`); setup-only and full runs are
differenced, median of 3; the mechanical counters (bits, generator applications, tree edges, table lookups, cache
hits/misses, allocations) come from a separate `-DCOUNT` build, never from the timed binary. Provenance (gcc,
valgrind, cpu, git) is in the header of the TSV.

## Result (one image: Intel i5-6400, gcc 16.1, valgrind 3.27; 20000 calls; I refs per call, the call loop is included and is common to all)

| suffix k | A flat | B interp. | C cached | D hybrid | (repeated path) |
|---|---|---|---|---|---|
| 0 | 62 | **33** | 68 | 64 | |
| 2 | 82 | **59** | 88 | 84 | |
| 4 | 102 | **79** | 108 | 86 | |
| 8 | 142 | **119** | 148 | 126 | |
| 16 | 222 | **199** | 228 | 206 | |

| suffix k | A flat | B interp. | C cached | D hybrid | (random paths) |
|---|---|---|---|---|---|
| 0 | 79 | **50** | 85 | 81 | |
| 2 | 110 | **87** | 116 | 112 | |
| 4 | 130 | **107** | 136 | 114 | |
| 8 | 170 | **147** | 195 | 154 | |
| 16 | 250 | **227** | 346 | 234 | |

- Preparation of A over B (I refs, once): 1.1k (k=0), 76k (k=8), **23.1M (k=16)** and 6.5 MB of rows; B needs none.
- B costs 19 bits consumed and 17 tree edges per call at k=16 (random).
- C: cache hit rate on random paths 99.99% (k=0) ... 61% (k=8) ... 0.8% (k=16); with 1024 slots it cannot hold 2^17 paths.

## What it says (hypothesis, for this image and this implementation)

1. **Interpreting the suffix bits (B) is the cheapest per call at every depth here.** Flat lookup (A) costs about 23-29 more
   instructions per call (index arithmetic + a row load + a second loop) AND pays preparation that grows as 2^k.
   The crossover N where A becomes cheaper than B **does not exist** at any measured depth (A is never cheaper per call).
2. **The decoded-path cache (C) does not beat the interpreter (B)** in either harness: decoding is a shift and a mask, so the
   cache check costs more than it saves. Whether C beats the FLAT lookup (A) depends on how A and C are built: here C is dearer than A;
   in the independent harness of the panini agent (a larger table, 2^19 slots, A made of nested legacy-style definitions) C is cheaper
   than A for repeated paths and for k=8 random. With 2^19 slots here C improves on random paths (k=16: 346 -> 336 I refs, still above A 250)
   but not on repeated ones (148 vs A 142 at k=8). So the A-versus-C order is **implementation-dependent**; B cheapest is not.
3. **The hybrid (D)** is not cheaper than B here: the flat rows for depth <= 2 cost more than interpreting them.

## Independent confirmation (panini agent, not reading this code; C, `gcc -O2`, valgrind 3.27)

B is the cheapest per call at every depth, A preparation grows as 2^k (k=16/k=8 ratio 246 ≈ 2^8), and the tree steps / generator
applications per call are IDENTICAL across all strategies (17 at k=16): the strategies differ only in lookup, cache and decode
overhead. Her net I refs per call, random k=16: A 225, B 134, C 236, D 139. Orders differ for short suffixes only in D vs A
(k<=2: B < A < D < C, as here) and in A vs C (see 2).

## Limits (do not read more into it)

- I refs only: no data-cache or branch-prediction effects (`--cache-sim=no`). A flat table of 6.5 MB would be worse than
  its I refs suggest; the tree itself (1 MB at k=16) is the same for all.
- One CPU, one compiler (`-O2`), a C interpreter whose decode is trivially cheap. A route where decoding is costly
  (a text/FASL decode, a registry hash lookup instead of a direct index, a compiled path) is NOT measured: A is given a
  perfect direct index here, which favours A.
- The selector family only; no CML, no compiled-to-IR path, no Lisp I / 1.5 corpus programs, no malformed words.
- Absolute I refs from other CPUs / Valgrind images are not comparable (#1987).
