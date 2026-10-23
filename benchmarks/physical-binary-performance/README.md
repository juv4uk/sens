# Physical T5 execution — historical Python results, native Rust replacement

The earlier `run.py` and the records it generated are historical evidence only.
They used a Python T5 decoder and must not be cited as a current replay or used
to claim language speed. Existing historical artifacts are preserved for
provenance; this commit does not re-label them as new measurements.

The active replacement is a Rust integration benchmark in
`crates/sens-cli/tests/physical_sens_runtime_benchmark.rs`, run from
`.github/workflows/sens-performance.yml`. It uses eight committed physical
`.sens` fixtures and their committed extensionless views. Before any timing,
it requires all of these checks:

- The physical file and its committed visible view both exist and are nonempty.
- `sens` and `sens-trit eval` emit identical stdout bytes.
- `sens-trit open` emits exactly the committed extensionless view.
- Warm-up and every timed repetition preserve the same stdout bytes.

The native benchmark records commit, fixture, executable SHA256, source/carrier
SHA256 and emits plain-text TSV-style records:
`RUST_PHYSICAL_T5_PREFLIGHT`, `RUST_PHYSICAL_T5_SAMPLE`, and
`RUST_PHYSICAL_T5_SUMMARY`. Timing includes process startup, file reading,
decoding/evaluation and stdout; it is not steady-state evaluator throughput
and is not a semantic proof. Lisp laws remain in
`scripts/prove-lisp-semantic-t5m.sh` and are evaluated through Zig/T5M into
native SENS.

Manual replay:

```sh
gh workflow run sens-performance.yml --ref main
```

No new latency values are asserted until this workflow has completed on a known
commit and its raw TSV evidence has been inspected.
