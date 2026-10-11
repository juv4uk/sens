# SENS Binary Engine — transport evidence integrity

This small Benchmark Lab lane audits **measured physical bytes**, not source
names or an invented Lisp runtime. It deliberately builds on the existing
`scripts/benchmark-sens-physical.py` rather than adding a second timing engine.

## Exactly what is measured

- Three tracked, same-stem physical `.sens`, extensionless exact-bit, and
  `.lisp` views, using actual bytes on disk.
- **CPython** decode + encode roundtrips, **T5 versus spaced-bit text view**,
  in one process, with warmup and AB/BA alternation.
- Nine measured repetitions per representation, 300 operations per repetition;
  nanoseconds per operation and all raw samples remain in `physical-t5.json`.
- Physical bytes, semantic typed-word widths, SHA-256 of all three views,
  size ratios and CPU/OS/Python provenance.

The *separate* `verify_physical_t5.py` reads the actual fixtures again,
independently decodes and re-encodes physical T5, rechecks exact spaced-bit
view, rehashes source and typed words, recomputes all size ratios and medians,
rejects NaN/Infinity/negative timings, incorrect SHA, sample-count errors,
duplicate/unsafe paths, and any report that claims native or semantic parity.

The CI job uploads the original raw report, the resulting verifier verdict,
source SHA, and input SHA-256 manifest. It has negative-control tests that
deliberately corrupt known-valid reports and require rejection.

## Running locally

```sh
python3 -m unittest discover -s tests -p test_physical_t5_evidence_integrity.py -v
mkdir -p /tmp/sens-physical-evidence
python3 scripts/benchmark-sens-physical.py \
  --out-dir /tmp/sens-physical-evidence --reps 9 --iterations 300
python3 benchmarks/evidence-integrity/verify_physical_t5.py \
  --report /tmp/sens-physical-evidence/physical-t5.json \
  --expected-sha "$(git rev-parse HEAD)"
```

## What this cannot prove

**It is not a benchmark of SENS runtime vs Python/Chez, and not a comparison
of native CPU vs interpreted code.** Both measured lanes run in CPython.
The bytes-to-result semantic oracle remains `NOT_PROVED`; x86-64, GPU, and
FPGA speedups remain `NOT_MEASURED`. This lane will not turn a green
transport result into a made-up execution claim.

Use the independent native CPU and future GPU/FPGA tracks for those claims,
with per-backend oracle parity **before** comparing execution times.
