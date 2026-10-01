# #2181 — D5 transformer boundary witness

Status: research-only.

## Current decomposition

The live macro path already uses ordinary language capabilities for most work:

```text
DEFINE
LAMBDA
form construction
EVAL
```

The remaining special behavior is concentrated in two host mechanism loci.

### 1. Transformer materialization

`macro_substrate.rs` performs:

```text
Closure -> Macro
```

This is the temporary `make-macro` substrate explicitly documented in
`lib/macro.lisp`.

### 2. Raw-form invocation mode

The evaluator detects `Value::Macro` before ordinary argument evaluation.
`apply_macro` then:

```text
raw Expr operands
 -> quote as data
 -> bind to transformer parameters
 -> evaluate transformer body
 -> convert result Value back to Expr
 -> tail-evaluate expansion in caller environment
```

Existing conformance proves the distinction is observable: an unused macro
operand may contain an undefined symbol and must remain unevaluated.

## Minimal D5 interpretation to falsify

These two host loci may be two mechanics of **one semantic capability**:

> a closure with staged/raw-form invocation mode.

That supports the candidate:

```text
0010  LAMBDA       ordinary closure
00101 TRANSFORMER  staged/raw closure candidate
```

If this survives, `DEFMACRO` stays derived:

```text
DEFINE name (TRANSFORMER params body...)
```

and no separate D5 identities are needed merely for `make-macro`,
`defmacro`, `apply-raw` or `macroexpand`.

## What this witness does not prove

It does not prove that materialization and raw invocation are semantically one
operation. #2181 must still compare one-capability and two-capability models.

It does not ratify `00101`.

## Reproduce

```sh
python3 scripts/research-2181-d5-transformer-boundary.py
```

## Principle

**Compress host mechanics only after proving they are one language capability.**
