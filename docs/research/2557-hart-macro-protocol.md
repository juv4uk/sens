# #2557 — Hart MACRO 1963 protocol evidence

Phase: `HISTORICAL-INGEST / PROTOCOL-COMPARISON`.

This note records historical evidence only. It allocates no SENS coordinate,
width, resident, or semantic authority.

## Primary historical anchor

Timothy P. Hart, **“MACRO Definitions for LISP,” MIT Artificial Intelligence
Memo 57, October 1963**.

Archive/index:
- Computer History Museum / Software Preservation Group, LISP 1.5 family:
  https://softwarepreservation.computerhistory.org/LISP/lisp15_family.html
- AIM-57 is linked from that archive.
- Steele & Gabriel, *The Evolution of Lisp*, §3.3 reproduces the memo text and
  identifies Hart's 1963 memo as the introduction of Lisp macros.

The archive also records a November 1963 LISP 1.5 library containing MACRO.

## Protocol extracted from Hart's memo

Hart proposes a MACRO instruction expander integrated with `define`.

The historical protocol states that:
- a macro definition names a function of **one argument**;
- that argument is the complete form beginning with the macro name;
- the macro function returns a replacement form;
- the returned value replaces the original form in function definitions;
- `define` performs macro expansion;
- Hart gives CSETQ as an example of an existing FEXPR replaceable by a MACRO.

Therefore, on the three axes already used by #2522/#2557:

```text
Hart MACRO (1963)
  raw operands / full form      = 1
  explicit caller-env input     = 0
  returned-form replacement     = 1
```

The final axis is recorded as the historical analogue of result re-evaluation:
the returned form is not the direct value of the original call; it becomes the
replacement program form to be processed subsequently.

## Comparison

```text
historical FEXPR/FSUBR
  raw form        = 1
  caller env      = 1
  result re-eval  = 0

Hart MACRO 1963
  raw form        = 1
  caller env      = 0
  result re-eval  = 1

current SENS TRANSFORMER
  raw form        = 1
  caller env      = 0
  result re-eval  = 1
```

Bounded conclusion:

```text
FEXPR vs Hart MACRO
  = ORTHOGONAL on caller-env and result-protocol axes

Hart MACRO vs current SENS TRANSFORMER
  = PROTOCOL-ALIGNED on the tracked three axes
```

`PROTOCOL-ALIGNED` is not mechanism identity. Hart's mechanism is described as
DEFINE/expansion-time replacement, while current SENS may realize equivalent
observable staging at a different execution boundary.

## Placement boundary

```text
current_domain_candidate = unresolved
binary_object            = unplaced
placement_status         = unplaced
exact_width              = unresolved
```

Chronology and protocol evidence do not allocate D5/D6 bits.

## Handoff

This evidence closes the historical-presence/protocol question for the ledger.
Later STRUCTURAL-DISCOVERY may compare the protocol axes with other capabilities.
Only SENS-DERIVATION may propose a binary placement after a surviving law is
proved and falsified.
