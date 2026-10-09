# #2123 Consequence-kernel benchmark

Research-only proof-machinery benchmark. It does not change the SENS proof system or production semantics.

The first slice fixes one bounded consequence semantics:

- finite Horn-style rules over signed literals;
- explicit refutation is a separate signed literal;
- UNKNOWN is not false;
- support and refutation may coexist;
- no explosion is assumed.

It then compares mechanisms for the same derivability questions:

1. `assumption` — negative control: only direct premise membership; marked non-comparable when it cannot derive the oracle judgment;
2. `forward` — no materialized closure; recompute least fixed point for each query;
3. `memo` — materialize closure once; O(1)-style membership queries; full closure recomputation after premise invalidation;
4. `provenance` — materialize root-premise support sets for each derived literal; invalidation removes only supports containing the invalidated premise.

Workloads:
- deep chain;
- two independent derivations (diamond);
- simultaneous support + explicit refutation;
- wide fanout invalidation.

Sizes: 16 / 64 / 256.

The benchmark reports prepare/query/revision work separately:
- rule checks;
- premise reads;
- derived literals;
- support combinations / support sets;
- invalidated support sets;
- modeled common rule bytes;
- candidate extra-state bytes;
- wall time as diagnostic only;
- answer digest and semantic parity.

A faster row is not accepted as an optimization when `semantic_parity=0`.
The `assumption` candidate exists specifically to make that failure visible.

Run:

```sh
python3 benchmarks/consequence-kernel/run.py
```

Outputs:
- `summary.tsv`
- `summary.json`
- `provenance.json`

Native Cachegrind is a follow-up lane under #1987; this first slice establishes the semantic/capability gate and logical work accounting.