# Rust nightly arbitrary-width integer witness

This research harness tests the **actual Rust language/toolchain** for builtin
arbitrary-width integer spellings. It does not assume that nightly implies the
feature exists.

The experiment is deliberately separate from SENS semantics:

```text
SENS semantic width    = language law
Rust builtin u<N>      = possible host mechanism
arbitrary-int crate    = library experiment only
LLVM iN / i1           = compiler witness
packed SENS transport  = physical representation
```

## Status classes

The runner reports:

- `NATIVE_BUILTIN_AVAILABLE` — rustc accepted the exact builtin spelling.
- `NATIVE_BUILTIN_UNAVAILABLE` — the exact spelling was rejected.
- `LIBRARY_EXPERIMENT_ONLY` — optional library comparison; never presented as
  native Rust syntax.

## Probe widths

The default matrix is:

```text
u1 u2 u3 u7 u8 u9 u16
```

D1, D7 and D9 are deliberately included because they correspond to SENS exact
domain widths of 1, 7 and 9 bits.

## Local run

Use a nightly toolchain explicitly:

```bash
python3 benchmarks/rust-nightly-int-witness/run.py --toolchain nightly
```

Or point at an exact installed toolchain:

```bash
python3 benchmarks/rust-nightly-int-witness/run.py --toolchain nightly-2026-10-01
```

The runner prints JSON and exits successfully even when native support is
absent. Unavailability is an observed result, not a test failure.

## Probe mechanics

For each width N the runner creates a tiny Rust source containing the exact
type spelling `uN`, then invokes the requested `rustc`.

It records:

- `rustc --version --verbose`;
- requested toolchain;
- width;
- source spelling;
- compilation status;
- first compiler diagnostic when unavailable;
- LLVM IR path for successful probes when requested.

The source has no dependency on the SENS crate, so a future Rust language
feature can be detected independently from SENS implementation details.

## Library control

The runner does not install or fetch dependencies. A future benchmark may add
an already-pinned arbitrary-width crate under a separate comparison harness.
Such a result must remain labeled `LIBRARY_EXPERIMENT_ONLY`.

## Relation to SENS

Current SENS already has exact-width `Bit1 = Bits<1>` through `Bit8` and
dense program-level bit packing. This research only answers whether the Rust
host can eventually replace the bounded transient carrier with a native
arbitrary-width integer.

A positive native result must **not** alter SENS domain laws.

