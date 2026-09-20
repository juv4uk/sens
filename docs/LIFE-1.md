# LIFE-1: fresh-checkout witness

LIFE-1 proves one real end-to-end path without collapsing island result domains:

```text
SWI-Prolog
  -> Lisp-owned explicit projection
  -> Datalog
  -> provenance
  -> scheduler activation
  -> quiescence
```

The trace is provenance/control data, not a truth value. Prolog and Datalog keep their native result domains; the bridge is explicit and partial.

## Reproduce from a fresh checkout

Requirements:

- stable Rust toolchain;
- SWI-Prolog available as `swipl`.

On Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y swi-prolog-nox
swipl --version
cargo test -p wsm-native-result-types --test prolog_datalog_bridge -- --nocapture
```

The same command is the canonical focused CI witness in `.github/workflows/life-1.yml`.

A missing Prolog runtime is an execution-availability failure. It must not mutate SID meaning or be normalized into Lisp falsehood.

## What the witness covers

The focused witness exercises a real SWI-Prolog query, preserves its native observation, applies the Lisp-owned Prolog-to-Datalog projection, runs the real Datalog kernel, records provenance references, schedules the matching pending invocation, rejects mismatched or malformed triggers, deduplicates repeated activation by observation/provenance identity, and reaches explicit quiescence when no pending work, new projection, or lifecycle transition remains.
