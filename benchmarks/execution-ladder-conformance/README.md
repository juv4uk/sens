# Execution-ladder conformance — Contract 11.6

Current semantic cut: **D1–D7 current; D8 research**. D7 residency is 126/128 under #3572; generic callability/mechanism remains a separate fact.

Parent: #3561. Architecture: #3560.

This directory defines the **shared machine-readable evidence envelope** for the
SENS execution ladder:

```text
L0 oracle
  -> L1 packed transport
  -> L2 compiler/AOT
  -> L3 substrate
```

It does not define evaluator semantics and it does not add a new execution
mechanism. Its only job is to make independent implementations compare the same
program and the same contract-level observable without inventing local expected
values.

## Stable case identity

A case identity includes the semantic contract, the canonical encoding kind and
the exact program bytes. This prevents the same text from colliding when it
denotes a canonical source form in one lane and a canonical AST serialization
in another.

```text
program_digest = SHA256(UTF-8(program))
case_identity  = canonical_json({
  "contract": contract,
  "program_encoding": program_encoding,
  "program": program
})
case_id        = "case-" + SHA256(UTF-8(case_identity))
```

The same contract + encoding + program therefore has the same `case_id` in
SENS, CML, GraalVM, FPGA, CUDA and external witnesses, independent of host
language.

## Structured digests

Structured values use canonical JSON:

- UTF-8;
- object keys sorted;
- no insignificant whitespace;
- `ensure_ascii=false`.

Then:

```text
identity_trace_digest = SHA256(canonical_json(identity_trace))
observable_digest     = SHA256(canonical_json(observable))
```

`oracle_digest` is the L0 `observable_digest`. Downstream producers never
invent a target-local expected value.

## Exact-domain trace

Every identity entry is:

```json
{"domain": 3, "bits": "000"}
```

The validator requires `len(bits) == domain`. Equal payload text in another
domain is therefore not the same identity.

Fresh evidence must always contain:

```json
"legacy_identity_used": false
```

Sens8/Sid8/Function8 may remain historical donor evidence, never a fresh
conformance route.

## Observable

The normalized observable intentionally excludes host object layout, Java/Rust
class names, pointer identity, stack traces and debug formatting.

It records only:

- result kind;
- canonical value when there is one;
- visible program output;
- normative error/failure class;
- order trace only where order is contract-observable;
- mechanism status.

Visible output is part of the digest. Two substrates that return the same
value but emit different output therefore cannot pass parity.

A missing mechanism is `BLOCKED-MECHANISM`, not an invitation to fall back to
legacy execution.

## Parity

- L0 must use `ORACLE` and its observable digest must equal
  `oracle_digest`.
- downstream `PASS` means exact digest equality;
- downstream `FAIL` means a real semantic divergence;
- `NOT-RUN` is reserved for explicit blocked/research cases.

## Exhaustive evidence

Do not write “exhaustive” without a finite bound in the same row.

A `bounded-exhaustive` row must carry:

```json
{
  "grammar_profile": "example-finite-grammar-v1",
  "domain_set": [1, 2, 3],
  "max_ast_depth": 2,
  "max_nodes": 7,
  "argument_value_bound": 2
}
```

The valid claim is **exhaustive within the declared grammar profile and bound**. `grammar_profile` is part of the evidence because the same numeric depth/node limits may admit very different finite grammars. This is not a proof for arbitrary program depth or for every program over the listed domains.

## Local check

```sh
python3 benchmarks/execution-ladder-conformance/selftest.py
python3 benchmarks/execution-ladder-conformance/validate.py evidence.jsonl
```

The first implementation slice is schema/digest plumbing only. Oracle-emitted
real cases and the bounded generator land in subsequent slices.

Principle: **one case, one oracle digest, many machines.**
