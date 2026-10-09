# English vs canonical D1-D8 CPU harness (#3113)

This directory is the CPU paired-run lane for #3088.

It does **not** publish English-vs-binary speed ratios yet.

The first gate is semantic/mechanical parity:

```text
English surface
  -> parse
  -> lower
  -> exact-domain trace

canonical binary
  -> canonical reader
  -> lower
  -> exact-domain trace
```

Timing is admissible only when both traces are identical and neither lowered
program uses the legacy byte-identity path.

## Current deliverables

- `crates/sens/examples/en_vs_d1d8_preflight.rs`
  - executable parity gate;
  - fails closed on legacy byte identity/calls;
  - fails closed on trace mismatch;
  - contains no tracked human-surface corpus; CI materializes controls at runtime.
- `raw-row.schema.json`
  - future shared raw-row shape for preflight and phase measurements.
- `run.py`
  - runs paired preflight cases;
  - stores TSV + JSONL + environment provenance;
  - deliberately reports `timing_enabled=false`.

## Manifest

Tab-separated columns:

```text
case
english_path
canonical_path
oracle
```

Either lane may use a real source path or inline manifest data. Inline data is
materialized as a temporary `.lisp` file by the runner. This keeps benchmark
inputs out of the repository's semantic-name/numeric-source debt inventories
without changing how the actual readers see them. Real corpus rows should use
tracked source paths when those sources already belong to the canonical corpus.
Every source payload is hashed and the whole paired corpus receives one
deterministic `corpus_sha`.

## Run

```bash
cargo build -p sens --example en_vs_d1d8_preflight
python3 benchmarks/en-vs-d1d8-cpu/run.py \
  --preflight-bin target/debug/examples/en_vs_d1d8_preflight \
  --manifest benchmarks/en-vs-d1d8-cpu/selftest-manifest.tsv \
  --out /tmp/en-vs-d1d8-preflight \
  --require-ready
```

## Timing readiness

Headline measurements stay blocked until the current implementation spine
owned by #3088 is complete:

```text
one-Core
 -> current 510/510 occupancy
 -> selector source
 -> canonical DomainIdentity registry
 -> one canonical binary reader/execution route
 -> paired CPU timing
```

A corpus case that is not yet representable on the canonical current route is
`BLOCKED_*`; it is never silently routed through compatibility.

## Later phase rows

Once readiness is proven, the same schema will carry separate paired rows for:

- startup/session;
- parse vs decode;
- lower/semantic-resolution;
- execute;
- one-shot total;
- repeat-N.

Cachegrind I refs and wall/user/sys/RSS stay separate metrics. No weighted score.

The core rule is simple:

**first prove both source projections become the same current language; only
then time them.**
