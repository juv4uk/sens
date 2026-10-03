# #2568 — Hart DEFINE-time vs current SENS evaluation-time expansion

Status: **HISTORICAL-INGEST / protocol falsifier**. No binary coordinate is allocated.

## Primary historical premise

Timothy P. Hart, *MACRO Definitions for LISP*, MIT AI Memo 57, October 1963
(AIM-057; MIT DSpace handle `1721.1/6111`).

Hart proposes a MACRO instruction expander in `DEFINE`. The macro definition
contains a function receiving the macro-call form, and the form returned by
that function replaces the original form in function definitions.

This establishes the historical expansion locus used by this witness:

```text
Hart MACRO:
  expansion locus = DEFINE / before later function execution
```

The premise is historical evidence, not inferred by the executable model.

## Current SENS control

Current `apply_macro`:

```text
raw Expr operands
 -> transformer body
 -> Value
 -> Expr
 -> TailCall(expansion, calling_environment)
```

The live integration test adds this trace:

```text
define transformer -> OLD expansion
define ordinary function containing transformer call
redefine same transformer -> NEW expansion
call previously-defined function
```

Current SENS returns:

```text
NEW
```

So the transformer call remained live until evaluation time.

## Minimal countermodel

For the same trace:

```text
Hart DEFINE-time model -> OLD
SENS evaluation-time   -> NEW
```

The result differs without changing the transformer algorithm itself. Only the
expansion locus changed.

Therefore:

```text
EXPANSION-TIMING=INDEPENDENT-AXIS
```

for the bounded observation.

## Refined Phase-F axes

The FEXPR/macro comparison now needs at least:

```text
A operand representation
B direct caller-environment input
C result protocol
D expansion locus / semantic time
```

Current evidence:

```text
FEXPR/FSUBR:
  A raw
  B explicit caller env
  C direct value
  D evaluation-time special call

Hart MACRO (1963):
  A whole/raw source form
  B no direct runtime caller-env input in the proposed macro-function protocol
  C replacement source form
  D DEFINE/pre-compilation expansion

current SENS TRANSFORMER:
  A raw source operands
  B no direct caller-env transformer parameter
  C returned form is re-evaluated
  D evaluation-time expansion
```

## Non-conclusions

This does not prove:
- a four-bit SENS domain;
- a D5/D6 coordinate;
- Hart MACRO and current SENS TRANSFORMER are different primitives;
- one protocol is more expressive than another.

It only proves the timing/locus distinction is observable in the bounded
redefinition trace.

## Reproduce

```sh
cargo test -p sens --test post_d4_macro_timing -- --nocapture
python3 scripts/research-2568-macro-timing.py
```

## Principle

**Returning syntax is one axis; deciding when that syntax replaces the program
is another.**
