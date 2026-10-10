# Rust serde_json vs SENS wire decode

**Status:** research-only. This is a direct transport-decoding comparison over one fixed semantic corpus, not a whole-language speed claim.

The runner builds two existing Rust examples, generates the same deterministic messages in SENS and JSON form, encodes SENS wire, then measures decode-only loops. File reads and process startup are outside the timed sections. It records Cachegrind instruction references and wall-clock nanoseconds/messages per second, including raw outputs and Cachegrind files.

## Reproduce

Install stable Rust and Valgrind/Cachegrind, then run:

```bash
bash benchmarks/rust-json-vs-sens-wire/run.sh /tmp/rust-json-vs-sens-wire
```

Defaults: 1,000 messages, seed 1, 20 Cachegrind rounds, and seven alternating ABBA/BAAB cycles of 200 wall-clock rounds per sample. The raw CSV and results JSON include every sample, median and p95, corpus SHA-256, and toolchain/host provenance. Cachegrind I refs count the whole process (including input setup and warm-up), so they are reported as context, not isolated decoder instruction counts. Override with N_MESSAGES, CACHEGRIND_ROUNDS, WALL_CLOCK_ROUNDS, and WALL_CLOCK_REPS for controlled experiments.

The evidence applies only to these Rust decoders and this corpus. It does not establish general SENS-vs-JSON superiority or measure execution of whole programs.
