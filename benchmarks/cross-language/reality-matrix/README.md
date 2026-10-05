# Reality Matrix — shared cross-language benchmark protocol

Owner issue: #3680

This directory extends the existing `benchmarks/cross-language/run.py` discipline to
SENS vs WebAssembly, CakeML, Lean, Clash, Nock, Unison and Rust.

## Non-negotiable rules

1. **Current SENS only.** Canonical semantic identity is exact bits + exact domain +
   admitted/proved law. Historical Sens8/Sid8/Function8 lanes are provenance only.
2. **D1–D7 are the ratified Core foundation. D8 is research.** D8 data may be reported
   only in a clearly separated research row.
3. **Parity before timing.** Every measured workload MUST have a golden output or a
   stronger equivalence witness checked before timing.
4. **Same machine, same load context.** Timing/RSS ratios are valid only within one
   recorded environment. Never compare absolute timings copied from upstream reports.
5. **Split phases.** Record, when meaningful:
   - encode/build/compile
   - load/read
   - decode/parse
   - validate/check/prove
   - ready/instantiate
   - repeated steady execution
6. **Keep raw evidence.** Summaries are derived artifacts. Raw measurements, commands,
   tool versions, commit SHAs and environment metadata are mandatory.
7. **No universal winner.** Verdict is per axis: `sens`, `competitor`,
   `pareto`, `tie`, `inconclusive`, or `unsupported`.
8. **Proof is not a benchmark shortcut.** For Lean/CakeML report tested/proved/trusted
   boundaries explicitly. Do not label a SENS conformance test as a theorem.
9. **Hardware is post-route when claimed as hardware evidence.** Clash/FPGA headline
   numbers must come from the same device, tool version and constraints.
10. **Negative results stay.** A losing SENS result is evidence, not a regression to hide.

## Shared workload classes

The minimum shared corpus is:

- `tiny-structural` — structural/selector case with very small artifact;
- `recursive-tree` — recursive tree/list traversal;
- `exact-integer` — exact integer arithmetic;
- `exact-rational` — exact rational arithmetic where the competitor has a fair exact lane;
- `branch-heavy` — condition/branch dominated workload;
- `binary-transport` — canonical encoded representation + load/decode;
- `domain-dispatch` — D1–D7 identity/dispatch stress;
- `cross-backend-parity` — one program observed through at least two SENS substrates.

A system may mark a workload `unsupported` when forcing it would distort the system's
model. The reason must be recorded.

## Repetitions and summaries

- Correctness/parity check first.
- At least 10 measured repetitions for noisy wall/RSS measurements unless a workload is
  too expensive; lower counts require an explicit reason.
- Record all samples.
- Headline summary: median and p95. For deterministic counters such as Cachegrind
  instructions, raw count may be primary.
- Cold and warm/steady results MUST NOT be merged into one number.

## Result layout

Each system owns:

```
benchmarks/cross-language/reality-matrix/<system>/
  README.md
  comparison.json
  raw/
  workloads/
```

`comparison.json` must validate against `comparison.schema.json`.

## Semantic-density experiment

Do **not** collapse this into a magic scalar yet. Record the tuple:

- `independent_roots`
- `independent_laws`
- `derived_residents`
- `admitted_residents_in_scope`
- `canonical_description_bits` only if a canonical encoding for roots/laws is pinned

Primary derived ratios allowed without a canonical law encoding:

- coverage = derived_residents / admitted_residents_in_scope
- residents_per_root = derived_residents / independent_roots
- residents_per_law = derived_residents / independent_laws

A bit-normalized "law-generated semantic density" is **inconclusive** until the law
encoding itself is frozen. This prevents us from winning by choosing a convenient prose
encoding.

## First execution order

1. Rust — easiest native control, establishes the runtime wall.
2. WebAssembly — binary/load/decode control.
3. Nock — minimal machine + semantic-description control.
4. Unison — semantic identity/storage control.
5. Clash — exact-width hardware control.
6. Lean — proof-checking/TCB control.
7. CakeML — verified compilation/TCB control.

This order is about cheap evidence first, not scientific importance.
