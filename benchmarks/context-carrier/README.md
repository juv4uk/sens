# Γ context-carrier benchmark

**Issue:** #2122  
**Foundation:** #2110 / #2108  
**Benchmark gate:** #1987

This benchmark compares candidate carriers for the left-hand context in:

```text
Γ ⊢ J
```

Candidates:

- set;
- multiset;
- ordered sequence;
- typed witness map;
- provenance DAG.

The first output is a **capability matrix**, not a speed table. A carrier that discards witness identity or provenance is not allowed to “win” a workload that requires witness-specific or recursive invalidation.

## Run

```sh
python3 benchmarks/context-carrier/run.py --smoke
python3 benchmarks/context-carrier/run.py --out /tmp/context-carrier/results
```

Outputs are TSV + JSON.

## Workloads

- initial support/refute status query;
- witness-specific direct invalidation;
- provenance-recursive invalidation.

All carriers must agree on the initial support/refute status. Later workloads are marked `semantics_comparable=0` when the carrier has already erased information needed to express the operation faithfully.

Wall time is diagnostic only. Logical reads/writes/lookups, copied entries, invalidation fanout and modeled payload bytes are the primary portable counters.

## Guard

A host collection type is never semantic authority. In particular, choosing `set` must not silently grant contraction/exchange or erase proof provenance from the language model.
