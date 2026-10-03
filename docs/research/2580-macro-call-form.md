# #2580 — macro call-form packaging

Status: research-only historical/protocol witness.

## Historical premise

Hart AIM-057 describes a MACRO function as receiving one argument: a form
beginning with the macro name.

That is a whole-call protocol:

```text
(macro-name arg1 arg2 ...)
```

The invocation head is visible inside the macro-function input.

## Current SENS control

Current evaluator flow separates the head from the arguments before
`apply_macro`:

```text
items[0]    -> head dispatch
items[1..]  -> arguments -> apply_macro
```

`apply_macro` receives the macro closure, raw operand `Expr` values, the
calling environment, and the span. It has no invocation-head parameter.

## Alias falsifier

Take one transformer value and expose it through two call heads:

```text
(macro-a payload)
(macro-b payload)
```

Historical whole-call packaging exposes distinct inputs because the head is
part of the supplied form.

Current operand-only packaging exposes identical transformer-visible payload:

```text
[payload]
[payload]
```

No deterministic reconstruction from that identical payload can recover which
head was used without adding another explicit semantic channel.

## Result

```text
CALL-PACKAGING=INDEPENDENT-AXIS
HART-INPUT-SHAPE=WHOLE-CALL
SENS-INPUT-SHAPE=OPERANDS-ONLY
BINARY-OBJECT=UNPLACED
EXACT-WIDTH=UNRESOLVED
```

The old coarse raw/env/result projection can therefore conflate two distinct
protocols.

## Non-conclusion

This does not imply a new SENS function, bit, width, or placement. It is a
historical/protocol observation to be recorded before structural discovery.
