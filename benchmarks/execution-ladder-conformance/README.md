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

## Lane C — bounded-exhaustive D1-D3 structural slice

The first bounded generator is intentionally smaller than the current language.
It proves one finite slice only; it does **not** claim exhaustive D1-D7 coverage.

Declared bound:

```json
{
  "grammar_profile": "d1-d3-structural-predicate-v1",
  "domain_set": [1, 2, 3],
  "max_ast_depth": 3,
  "max_nodes": 11,
  "argument_value_bound": 2
}
```

Grammar profile: `d1-d3-structural-predicate-v1`. The finite grammar has exactly two seed value expressions:

```text
V0 = D3:000 EMPTY
V1 = (D3:111 CONS V0 V0)
```

It then generates every program in this slice:

```text
U ::= (QUOTE V) | (ATOM V) | (CDR V) | (CAR V)
B ::= (EQ V V) | (CONS V V)
P ::= (ATOM V) | (EQ V V)
C ::= (COND (P V))
E ::= U | B | C
V ::= V0 | V1
```

All products are Cartesian over the two bounded values. After deterministic
source deduplication this is **28 canonical programs**.

D1 is not accepted as a bare expression payload by the canonical reader.
It enters this slice only as the exact predicate result of ATOM/EQ and as the
predicate consumed by COND. D2 owns list/clause structure. D3 owns the current
callable primitive identities. This keeps the current reader/domain boundary
intact.

For every one of the 28 programs the probe performs both:

1. **L0 ORACLE** — canonical parse, lower, exact-domain trace, evaluator result
   or named evaluator error.
2. **L1 P1 round-trip** — tokenize exact-width source words, densely pack with
   zero interior byte padding, unpack with the caller-owned exact width
   schedule, reconstruct canonical source, and re-run the same evaluator
   observable.

The L1 row is emitted only if the reconstructed source has the same exact word
sequence **and** the same semantic trace/result/error as L0. Each case therefore
produces one L0 `ORACLE` row and one L1 `PASS` row: 56 evidence rows total,
28 stable `case_id` values.

CI runs the generator twice and requires byte-identical JSONL, then validates
the shared schema. No runtime mechanism, parser rule, domain placement or
legacy identity is added by this lane.
