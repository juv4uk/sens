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
