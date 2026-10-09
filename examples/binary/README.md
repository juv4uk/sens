# Pure-binary runnable SENS specimens — D1/D2/D3/D4/D7

The files in this directory are **not human Lisp syntax**. `d7-first-program.lisp`, `d3-primitives-program.bits` and `d5-label-recursion.bits`, `d5-label-copy.bits` and `d5-label-map.bits` contain only exact-width bit words separated by whitespace. Every payload
word in that source consists of only `0` and `1`, with ASCII whitespace
separating **exact-width** domain words. It contains a D4 definition,
a D2-framed D7 Text7 binding, a D4 lambda, an exact D1 return value, and a
subsequent invocation of the binding through its D7 frame.

Tests in `crates/sens/tests/binary_program_e2e.rs` execute the complete
physical transport path for the D3 and D7 specimens. The physical `d3-cond-program.sens` specimen uses exact `110` COND, a first clause whose ATOM test is D1:0 (must skip), then an ATOM test returning D1:1 (must select). The D5 LABEL specimens define recursive closures under D7 Text7 binders. One proves finite recursion terminates; one rebuilds a list using D3 ATOM/COND/CAR/CDR/CONS/QUOTE while preserving D1:0, D1:1 and structural empty as distinct values; the third passes a D4 mapper closure as a value and applies it recursively through the same D7 binding path. The physical CLI workflow checks termination, T5 source round-trip and parity between `sens` and `sens-trit`. A negative case proves structural empty is not accepted as a predicate.

For the D7 specimen, the physical transport path is:

```text
source exact binary words
    -> encode to physical T5 byte stream
    -> decode physical T5 to width-qualified words
    -> parse via canonical D2 reader (no compatibility Lisp reader)
    -> evaluate D4/D7 lexical definition and call
    -> observe exact D1:1 (not host t)

D3 control specimen:
    -> physical T5 bytes
    -> exact-width D2 reader
    -> D3:110 COND + D3:010 ATOM
    -> exact D1 skip/select
    -> observe D1:1
```

It also proves fail-closed behavior for human executable spellings, noncallable
D7 data (including the two owner-reserved coordinates), and D10 width without
a ratified physical transport. The test **does not** claim independent
language-semantic oracle parity or a generalized D10 executor. Those require
separate Lisp-owned oracles/Vertical Day smoke; a matching encode/decode
digest alone is not proof of meaning.

CI: `.github/workflows/binary-program-e2e.yml` checks structural/T5 transport. `.github/workflows/physical-binary-sens-cli.yml` executes the D3 and D5 specimens through both physical CLIs. The workflow runs on every
`main` push, on relevant PRs, and on manual dispatch, using **GitHub-hosted
Ubuntu**. It does not cancel itself when other agents advance `main`.

## Physical executable D3 COND

`d3-cond-program.sens` is the **sole committed executable authority** for
this D3 COND specimen: **31 real packed T5 bytes**. The old human-readable
`.bits` source was removed after conversion. `sens-trit open` can derive a
read-only bit projection from these bytes without creating a second source authority.
The existing canonical codec, physical CLI and Rust runtime prove exact word
round-trip and execute strict D3:110 COND with D1:0 skip / D1:1 select. This
program returns exact D1:1. It does **not** claim to replace SI quantity
calculations or prove historical English-Lisp parity.

The physical performance runner measures this real file via both SENS CLI
entry points, with output parity and SHA-bound actual medians/p95. The two obsolete automatic Contract 11.8 benchmarks
(`contract-11-8-phase-decomposition.yml` and
`contract-11-8-store-air-load.yml`) were deleted because their preflight
still required a forbidden historical English byte identity. Their
`benchmarks/current-en-vs-d1d8/` and `benchmarks/store-air-load/` scripts
and historical findings remain for archaeology and future *independent*
translation. The new `physical-binary-performance.yml` measures actual
physical T5 bytes. Its CLI parity is not, and must not be presented as,
historical English↔SENS semantic parity. All strict D1/D3 production
evaluation and malformed-binary rejection gates remain enabled.
