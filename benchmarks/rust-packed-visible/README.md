# Rust exact-width visible/packed ingestion benchmark

This stand isolates the **Rust reader mechanism**. It does not compare JSON,
does not use a Python corpus generator, and does not execute Lisp semantics.

The Rust example builds five fixed binary-source cases. Before starting any
timer, it reads both the visible exact-width words and packed payload through
their respective readers, then verifies exact D2/domain-AST parity. The width
schedule is caller-supplied metadata and is excluded from the packed payload;
this experiment is not a self-describing container format.

Each case uses 32 paired warm-ups and an odd number of alternating visible/packed
measurements. Each timed lane adapts its batch count until it reaches at least
25 ms, emits raw samples, and reports p50/p90 nanoseconds per program, exact
source/payload sizes, and semantic bit count. No timing result establishes a
language law or certified speedup.

## Reproduce

```sh
bash benchmarks/rust-packed-visible/run.sh /tmp/rust-packed-visible
```

## Layer boundaries

- Rust measures source-ingestion and allocation mechanics only.
- Zig owns the T5M codec and transport/ABI benchmarks.
- Lisp defines semantic and logical laws, which are compiled via Zig/T5M and
  evaluated by SENS in the native physical witness runner.
- Registry JSON is discovery metadata only; no JSON payload participates in
  this benchmark.
