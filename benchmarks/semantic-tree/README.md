# #1988 semantic-tree execution benchmark

Research-only benchmark for the proved CAR/CDR selector family.

## Current P0 profile — Contract 11.6 D6 generator vs flat16

The first current result is deliberately narrow: the **16 D6 selector residents**
made executable by #3588/#3394 are measured two ways on the same deterministic
workload:

- `flat` — dense 16-entry predecoded table, **benchmark-only control**;
- `cold` — derive the operation from the selector generator law on every call;
- `compiled` — derive each distinct path during preparation and execute via a
  compact descriptor index.

Current selector geometry is:

```text
D3 roots: CAR=100, CDR=011
D6 selector = D3 root + 3 selector suffix bits

011000..011111
100000..100111
```

The flat table is never semantic authority, never a production fallback and
never a compatibility route.

Run the exact current profile:

```sh
python3 benchmarks/semantic-tree/run.py \
  --current-d6 \
  --calls 100000 \
  --samples 3 \
  --out /tmp/sens-1988-d6
```

Fast smoke:

```sh
python3 benchmarks/semantic-tree/run.py \
  --current-d6 --smoke \
  --out /tmp/sens-1988-d6-smoke
```

The CI smoke first runs the **real** `d6_selector_runtime` evaluator witness
from #3588 and only then runs this isolated paired mechanism benchmark. Thus the
performance control cannot silently drift away from the admitted runtime law.

## Measurements

Preparation and execution remain separate. Additive work counters use:

```text
median(full - prepare)
```

This is used for instruction references and branch counts. Cache misses and
branch mispredictions are stateful across separate Cachegrind processes, so the
report keeps their `prepare_*` and `full_*` totals separate and does **not**
label a subtraction as isolated execution misses.

Current counters include:

- instruction references;
- L1 instruction misses;
- L1 data misses;
- branches;
- branch mispredicts;
- selector/generator semantic counters;
- flat table entries/bytes;
- preparation cost and repeat-N execution cost.

Every current row carries Contract 11.6 scope/provenance in `environment.json`
and `instructions.tsv`.

A generator loss to `flat` is a valid completed negative result.


## Mode-specialized code size (#3582)

The shared multi-mode binary cannot answer per-lane executable footprint.
`code_size.py` therefore compiles three separate benchmark-only binaries from
the same 16-selector D6 corpus:

```sh
python3 benchmarks/semantic-tree/code_size.py \
  --calls 100000 \
  --out /tmp/sens-3582
```

It requires `rustc`, GNU `size`, and GNU `strip`. All three binaries must
produce the same checksum before any byte result is accepted.

Reported independently:
- executable file bytes and stripped file bytes;
- `.text`, `.rodata`, `.data`, and `.bss`;
- prepared runtime storage.

The flat16 table is a benchmark-only control. Code size has no semantic
authority.

## General research matrix

The older depth sweep remains available for mechanism research:

```sh
python3 benchmarks/semantic-tree/run.py \
  --depths 0,1,2,4,8,16 \
  --patterns repeated,random \
  --calls 100000 --samples 3
```

Other research modes remain:

- `cached` — prewarmed runtime HashMap;
- `hybrid` — root arm plus generated-path cache/fallback.

The Rust binary is a mechanism model, not semantic authority. Semantic counters
(tree/prefix/generator/cache/registry operations) are reported independently of
CPU counters.
