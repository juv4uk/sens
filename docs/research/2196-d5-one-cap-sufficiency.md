# #2196 — one-capability D5 sufficiency witness

Status: research-only. No D5 address is ratified here.

## Question

Can one staged transformer capability reproduce the observable SENS macro
semantics, or is a separate language identity such as `EXPAND` /
`MACROEXPAND` required?

The current temporary `make-macro` substrate is used only as a surrogate for
the candidate capability.

## Executable witnesses

The test suite adds five independent checks.

### W1 — raw operands

A transformer ignores an undefined second operand:

```text
(first-transformer (quote ok) never-defined) -> ok
```

### W2 — nested expansion

An outer transformer returns a call to an inner transformer. The normal
evaluator re-enters transformer dispatch and reaches the final result without
a standalone MACROEXPAND operation.

### W3 — caller environment

A transformer expands to a symbol that exists only in the caller's lexical
frame. The expanded form resolves there, proving post-expansion execution can
be part of transformer call semantics rather than a second identity.

### W4 — ordinary LAMBDA remains eager

The corresponding ordinary closure still evaluates the unused
`never-defined` operand and raises `UnknownSymbol`.

This preserves the lower bound from #2193.

### W5 — DEFMACRO remains derived

The live macro library still composes DEFINE + LAMBDA + one transformer
materializer, and the resulting language-owned DEFMACRO preserves raw
arguments.

## Current implication

For the current SENS runtime, one first-class transformer value mode is
sufficient to reproduce:

```text
raw operand capture
nested expansion
post-expansion caller evaluation
derived DEFMACRO
```

No executable SENS MACROEXPAND identity is required by these witnesses.

This does not yet prove that compiler consumers can delete their independent
macro expansion authority. CML #408 remains the ecosystem falsifier.

## Candidate under test

```text
0010  LAMBDA
00101 TRANSFORMER   ; candidate only
```

## Principle

**One staged value capability is enough only if nested expansion and caller
execution emerge from ordinary evaluator re-entry rather than a hidden second
semantic operator.**
