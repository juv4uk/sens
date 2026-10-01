# #2113 Foundation compatibility benchmark

Research-only benchmark. It does not change SENS production semantics, contracts, identities, parser, runtime, compiler, or FPGA behavior.

The benchmark asks a narrow question below the current graph/identity layers:

> if we keep only positive boundary-compatibility facts, how much incidence/equality structure can we reconstruct, what must remain explicit, and what mechanism cost does reconstruction add?

It compares three evidence models over the same deterministic finite transformation systems:

1. **explicit incidence** — every transformation stores source and target state labels;
2. **compatibility-only** — store only positive facts `target(f)=source(g)`;
3. **hybrid** — compatibility closure plus the minimum additional positive equality witnesses needed to recover all true boundary-equality classes.

Absence of a compatibility path is always **UNKNOWN**, never semantic inequality.

## Workload shapes

- `chain` — positive control; every internal interface is witnessed;
- `cycle` — positive control with closed recurrence;
- `fanout` — shared sources are not witnessed by target->source compatibility;
- `fanin` — shared targets are not witnessed;
- `mixed` — chain plus fan-out/fan-in residue;
- `one_state` — all boundaries denote one state, exposing dense `O(n^2)` compatibility storage.

Logical accounting sweeps `n = 8, 32, 128, 512`.

The Cachegrind slice uses selected shapes at `n = 32, 128` and measures:
- setup I refs over a common data-generation baseline;
- net I refs per repeated **true-equality proof query**;
- stored-fact proxy;
- compatibility recall and residual witness count.

This keeps two axes separate:

```text
information axis:
  what equalities are provable / UNKNOWN?

mechanism axis:
  how many facts, setup instructions and query instructions?
```

The `composition_closed_est_bytes` column is only a counterfactual lower bound for a representation that stores one extra 32-bit composite-result identity for every compatibility fact. It is **not** a claim that every compatible pair has an admitted composite in SENS.

## Run

Full benchmark:

```sh
python3 benchmarks/foundation-compatibility/run.py --calls 50000 --reps 3
```

Logical model only, no Valgrind required:

```sh
python3 benchmarks/foundation-compatibility/run.py --logical-only
```

Outputs:
- `logical.tsv` — information/storage matrix;
- `irefs.tsv` — Cachegrind mechanism matrix;
- `provenance.json` — toolchain/host provenance.

Interpretation guard: fewer stored facts are not automatically better. A model that saves storage by turning required semantic facts into UNKNOWN has not replaced those facts.