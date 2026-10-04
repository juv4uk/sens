# Historical pre-bīja3 D3/D4 dispatch benchmark (#2209)

> **Historical evidence only.** This benchmark encodes the superseded pre-#3202 D3 selector roots `101 CAR` / `110 CDR` and their old D4 descendants. It is preserved for reproducibility and comparison, but it is **not** the current semantic baseline after bīja3 A ratification. Fresh D3→D4 measurements are owned by #3206 and remain blocked until the coherent post-#3202 D3/D4 cutover and conformance are GREEN.

This was the current-main execution slice of #1988 under the earlier D1-D4 map.

It asks one narrow question: when the identity is already available in the AST, what does selector dispatch itself cost?

The same six operations and the same pair tree are executed through:

- **u8-flat-ready** — a favorable 256-slot flat table keyed by an already-ready byte identity;
- **d3d4-prefix-ready** — the ratified D3 roots `101 CAR`, `110 CDR` and the D4 suffix law `0 -> compose CAR`, `1 -> compose CDR`;
- **direct-static/direct-dynamic** — repeated fixed call sites use a branch-free direct CAR/CDR chain as the compile-away lower bound; random/mixed streams retain a dynamic switch control.

The flat lane is intentionally generous to the old mechanism: there is no text, hash lookup, parser, or wire decode in the measured execution delta. It is a mechanical 8-bit flat-slot baseline, **not** a claim that historical Function8 allocated all four D4 selectors symmetrically. Historical evidence contains CAAR/CADR/CDDR rows, while CDAR does not have the same canonical legacy-row coverage.

## Cases

~~~text
D3
101   CAR
110   CDR

D4
1010  CAAR
1011  CADR
1100  CDAR
1101  CDDR
~~~

Workloads cover repeated and random D3, repeated and random D4, and a mixed D3/D4 stream. All three routes must pass parity before Cachegrind starts.

## Run

~~~bash
python3 benchmarks/domain1234-dispatch/run.py \
  --out /tmp/d34/raw.tsv \
  --report /tmp/d34/report.md
~~~

Primary CPU metric is Cachegrind instruction references. Setup and full runs are measured separately and execution is reported as the differential. Branches are also differential. Logical counters report table lookups, exact bits consumed, generator applications, root selections, tree steps and strategy-specific prepared bytes.

This benchmark does not choose current semantics. Its coordinates are historical. #3212 owns the coherent post-bīja3 D4 map, #3206 owns fresh D3→D4 rebaseline work, #1988 owns the broader execution-strategy matrix, cml#397/#398 own compiler compile-away/unroll, and fpga-lisp#44 owns hardware decoder metrics.
