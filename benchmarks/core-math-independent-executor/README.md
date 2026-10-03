# Core-Math independent Rust executor (#2428)

This benchmark is a second executable model for the neutral Core-Math IR.

It is deliberately independent from the SENS runtime:

- no dependency on `crates/sens`;
- no SENS evaluator calls;
- no `core.lisp` parsing;
- no Python oracle calls;
- no copied generated closure rows.

The executor consumes the same neutral JSON used by #2433/#2427 and evaluates it
with its own exact-Q representation:

```text
sign + u128 numerator + u128 denominator
```

The generated operations are reconstructed from the expression/dependency graph,
then their bounded semantic signatures are compared with the committed
model-independent generation certificates.

A mutation control changes one neutral input constant and requires the Rust model
to report the shallowest generated operation and first corpus row that diverges.

Research only. This is executor evidence, not semantic authority.
