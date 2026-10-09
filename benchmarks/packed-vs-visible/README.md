# Packed bytes vs visible binary source — performance stand

This stand measures the **current implementation**, not a proposed language law.

The paired inputs represent the **same D2 syntax and exact domain AST**. One
candidate parses whitespace-separated visible binary words (`parse_canonical_binary`).
The other parses dense MSB-first payload bytes with an **explicit supplied
word-width schedule** (`parse_canonical_packed_words`). Both use the **same
release-compiled Rust executable**, the same workload, and the same D2 reader.

## Metrics (per case)

- Median elapsed nanoseconds per complete parse, using **nine paired batches**
  after warm-up; each batch parses many programs with full allocation.
- `ratio_visible_over_packed` = visible parse median / packed parse median.
  Above 1 means packed **ingestion** was faster on that run; below 1 means slower.
- Physical payload bytes, visible source bytes, exact semantic bits, and the
  number of **externally supplied** word-width entries.
- All individual sample times are recorded to detect noisy CI runners.

The corpus covers 1, 64, 256 quoted-empty forms, a D7 data program, and a W9
data program. Both candidates are compared by **span-independent D2/domain
AST fingerprint** before the timing loop. Any mismatch **blocks** the report.

**Limitations:** physical payload bytes alone are **not** a self-describing
canonical file. Width scheduling, storage of metadata, file I/O, compiler, and
execution are **excluded** from these timing results. The visible representation
contains whitespace delimiters. Never present `packed_payload_bytes` as a
complete file or a total-wire compression ratio. GitHub-hosted processors are
shared and variable; medians are evidence, **not** regression-proof rankings.
Do not compare numbers from different machines as if they share a baseline.

## Reproduce

```bash
cargo build --locked --release -p sens --example packed_vs_visible_bench
target/release/examples/packed_vs_visible_bench --samples 9 \
  > /tmp/sens-packed-visible.jsonl
```

GitHub workflow `.github/workflows/packed-vs-visible-bench.yml` runs this on
`ubuntu-24.04`, publishes the full JSONL, a hardware/environment snapshot,
and a Markdown summary. It does **not** fail for performance thresholds;
the independently checked parity gate is retained so speeds cannot hide a
wrong AST. For execution/load/English-vs-binary comparisons, see the separate
`benchmarks/current-en-vs-d1d8` and `benchmarks/execution-ladder-objective`
standards. No historical SID8 translation is performed.

## Real execution (second measurement lane)

`crates/sens/examples/packed_vs_visible_runtime.rs` adds a paired **parse → lower
→ evaluate** benchmark for 1, 64, and 256 quoted-empty D3 forms, plus 64
exact D1:1 values. It measures two independent cases per workload:

- `warm-session-parse-lower-eval`: reuse an already-created bare Session;
  each invocation parses fresh source, lowers and actually executes all forms.
- `fresh-session-parse-lower-eval`: create a fresh bare Session each invocation,
  then parse, lower and actually execute the forms.

Each report also records a separate `execute_only_baseline_ns` measured on a
pre-lowered AST under the same executable. **It is not a ratio denominator**;
its purpose is to reveal how much of end-to-end time remains after ingestion.

Result identity is checked **before measuring**. D1 must remain exact D1:1,
whereas D3 QUOTE returns structural EMPTY, never an implicit truth value.
Any different result blocks the whole benchmark. Same program and executable,
24 warm-up invocations, nine alternating-order batch samples, variable iteration
count, median per invocation and full raw samples.

```bash
cargo build --locked --release -p sens --example packed_vs_visible_runtime
target/release/examples/packed_vs_visible_runtime --samples 9 \
  > /tmp/sens-packed-runtime.jsonl
```

The hosted workflow publishes `packed-vs-visible-runtime.jsonl` and
`runtime-summary.md` alongside the ingest metrics and hardware provenance.

**Limitations:** Fresh Session is **not process cold start** and does not load
Core4 or compile Rust. All phase measurements exclude disk I/O, physical file
framing, the cost of transmitting/storing the caller-supplied word-width
schedule, and terminal output. This lane compares physical vs visible input to
one Rust interpreter, not Python/Chez/LLVM. Microbenchmark results on
GitHub-hosted CPUs are noisy: never use one run to assert a universal speedup.

## New process / Session / Core4 bootstrap (third performance lane)

The benchmark uses one hosted CPU and one Release-built
`crates/sens/examples/sens_cold_start_probe.rs` binary. Python launches a
**fresh OS process** each sample and records two non-interchangeable clocks:

1. `process_wall_ns` — Python wall-clock from process launch through process
   exit/output capture; includes the OS loader and scheduler;
2. `inner_ns` — Rust `Instant` around exactly one requested operation inside
   that process.

Five modes are measured independently: `noop` (executable startup baseline),
`session` (bare `Session::default`), `d3` (new bare session plus exact D2
QUOTE of structural EMPTY), `core` (bare session and actual Lisp-owned Core4
bootstrap), and `core-d3` (Core4 bootstrap plus exact D2/D3 execution).
Modes rotate across rounds, with two warm-up process launches and eleven
measured **new processes per mode**.

```bash
cargo build --locked --release -p sens --example sens_cold_start_probe
python3 benchmarks/packed-vs-visible/cold_start.py \
  --probe target/release/examples/sens_cold_start_probe \
  --samples 11 --warmup 2 \
  --out /tmp/sens-cold-start.json
```

The result and `cold-start-summary.md` are published beside the previous raw
benchmark samples in the GitHub Actions artifact. A Core4 bootstrap error is
shown as `BLOCKED` with its underlying message, not timed as a successful
execution; the independent basic no-op/session/D3 benchmark must still pass.

**Limitations:** each process is new, but file-system page cache is *not*
cleared. This is **not cold disk boot**. Do not subtract the process-wall
medians from unrelated internal medians and label that delta a precise
loader cost; scheduling and output capture vary. Bare session cost is distinct
from Core4 bootstrap, and these measurements do not give permission to
change the Lisp-owned language laws or assert that a speed result is
an architecture ratification.
