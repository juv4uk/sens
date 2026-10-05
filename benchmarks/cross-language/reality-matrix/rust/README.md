# Rust reality lane (#3687)

This is the first cheap control for the Reality Matrix (#3680).

## Scope

The first slice is deliberately limited to the two **current, ready D3 parity fixtures**
already owned by `benchmarks/current-en-vs-d1d8/fixtures/d3-smoke.json`:

- `d3-quote-empty`
- `d3-car-empty`

The headline corpus (`fib`, `loop`, `tree`, etc.) remains blocked at the current
canonical reader/runtime boundary. This lane MUST NOT invent private syntax to bypass
those blockers.

## Compared mechanisms

SENS:
```
canonical D1-D7 source
 -> parse_canonical_binary
 -> lower_program
 -> DomainIdentity
 -> eval_lowered_expressions
```

Rust control:
```
prebuilt native Value
 -> direct Rust operation
```

Therefore the Rust lane is a **native mechanism lower-bound/control**, not proof that
the two languages expose identical abstraction levels. The report labels this boundary.

## Measurement

`run.py`:

1. builds the current `current_en_vs_d1d8_cpu` SENS helper;
2. compiles `rust_control.rs` with optimized `rustc`;
3. replays English vs canonical SENS preflight and checks the fixture oracle;
4. checks the Rust control returns the same observable value;
5. measures repeated already-ready execution inside each process;
6. records process RSS when `os.wait4` is available;
7. records binary artifact bytes separately;
8. writes raw TSV + comparison JSON using the shared Reality Matrix schema.

No result from this D3 smoke slice may be generalized to whole-language performance.

## Run

From repository root:

```sh
# correctness/plumbing smoke (no performance winner)
python3 benchmarks/cross-language/reality-matrix/rust/run.py \
  --out-dir /tmp/sens-rust-reality-smoke \
  --evidence-mode smoke

# publishable same-machine performance run
python3 benchmarks/cross-language/reality-matrix/rust/run.py \
  --out-dir /tmp/sens-rust-reality \
  --evidence-mode performance \
  --load-context idle \
  --outer-reps 10
```

Use the same machine/load context for every ratio you publish.

## Fail-closed performance rule

The runner defaults to `--evidence-mode smoke`. In smoke mode it still records raw
timings/RSS so plumbing can be inspected, but time/RSS verdicts are forced to
`inconclusive`.

A performance verdict requires:

- `--evidence-mode performance`;
- at least 10 outer repetitions;
- explicit `--load-context idle|high`.

This prevents noisy CI smoke observations from becoming language-performance claims.
