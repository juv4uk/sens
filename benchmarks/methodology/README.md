# SENS benchmark methodology — paired wall-time, not semantic authority

**Stage 1 (2026-10-09): runnable, standard-library-only A/B evidence harness.**
One physical workload, two argv arrays, one GitHub-hosted runner, same T5
payload. In the first CI replay the two argv arrays are **intentionally equal**:
the A/A negative control measures noise and tests the measurement protocol,
not a performance gain or two independent semantic implementations.

## Run locally / reproduce exact-head hosted evidence

```sh
python3 -m unittest discover -s benchmarks/methodology/tests -p 'test_*.py' -v
cargo build --locked --release -p sens-cli --bin sens
python3 benchmarks/methodology/paired_wall.py \
  --a-json '["target/release/sens","tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"]' \
  --b-json '["target/release/sens","tests/fixtures/migration-quote-cohort-main/quote-legacy.sens"]' \
  --payload tests/fixtures/migration-quote-cohort-main/quote-legacy.sens \
  --sessions 5 --pairs-per-session 7 --warmups 2 \
  --seed 20261009 --bootstrap 2000 --out /tmp/sens-paired-wall-new
```

For GitHub-hosted runs, set `--pin-first-allowed-core` only when wanted.
Pinning is restricted to the runner's *allowed* affinity set; the tool never
modifies machine-wide governor, turbo, or scheduling priority. Record the CPU
model, affinity, governor availability, compiler/source hashes and outputs.
The directory must be new/empty so evidence cannot silently be overwritten.

## Measurement protocol

1. **Parity BEFORE timing.** Both exit cleanly, stdout is non-empty and
   byte-identical on the exact same packed T5 payload. Every warmup and
   measurement repetition must retain the exact stdout bytes; any mismatch
   fails closed. Record executable SHA256 and input SHA256 before and after.
2. **Nested, randomized paired A/B.** A and B are ordered `AB` or `BA`
   within each pair, balanced then shuffled by a *recorded* seed. Each sample
   starts a **new subprocess**. Include startup, decoder, evaluation, I/O and
   stdout capture. It is NOT an in-process Criterion-style measurement.
3. **Effect size.** Use the equal-weight session mean of per-pair
   `log(B_wall_ns / A_wall_ns)`; exponentiate to report geometric B/A
   wall-time ratio. Below 1 means B was faster on this experimental run.
4. **Uncertainty.** Resample sessions and the pairs within selected sessions
   (hierarchical percentile bootstrap, 95%). These sessions are *blocks on the
   same process-host*, not independent machine boots, recompilations, or host
   samples. Label interval **exploratory single-host**, never a full
   Kalibera–Jones estimate. A CI excluding 1 is not by itself permission to
   claim a real-world speedup.
5. **No performance gate yet.** Both positive and negative exploratory
   outcomes result in PASS when byte parity and mechanics are correct.
   Regression thresholds require multiple independent runs, baseline noise
   calibration and review; don't tune thresholds to make a PR green.

Source:
- T. Kalibera & R. E. Jones, *Rigorous Benchmarking in Reasonable Time*,
  ISMM 2013: https://doi.org/10.1145/2464157.2464160
- Mytkowicz et al., *Producing Wrong Data Without Doing Anything Obviously
  Wrong*, ASPLOS 2009, for uncontrolled layout/environment effects.

## Three distinct lanes — do not mix their units

| Lane | Mechanism | What can be reported | Admission |
|---|---|---|---|
| Instruction counts | Current Cachegrind, future isolated `iai-callgrind`/Gungraun bench | Ir/other Callgrind events, **not nanoseconds** | CPU toolchain+runtime hashes, identical arguments, no semantic guess |
| Wall-time | This paired-harness now; future Criterion microbench in another Cargo PR | Measured subprocess ns, pair order, effect ratio, exploratory interval | Exact stdout parity, CPU + SHA, known workload, no unpinned cross-host ranking |
| Real queue or radio latency | Later open-loop arrival/queue measurements | End-to-end percentile including queue and coordinated-omission handling | **NOT measured** by this closed-loop subprocess harness |

`iai-callgrind` requires a matching runner and Valgrind; Criterion requires
a workspace dependency and lockfile update. Both are **not installed by this
PR**, so no pretend measurements. Next separate PRs, *after red Hosted
CI/Vertical Day stabilizes*, should pin versions, regenerate `Cargo.lock`
and launch narrow GitHub-hosted examples before any gating.

**Governance:** this stand has `bench.json`, is an experimental measurement
tool only, and cannot grant D1–D9 language semantics, D10 ratification,
independent Lisp oracles or acceptance of a cancelled/failed smoke gate.
