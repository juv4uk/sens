# #2530 — FEXPR/FSUBR behavioral conformance

Status: research-only.

This closes the concrete-behavior gaps left after the protocol cube in #2522.

## C1 — raw list structure

The bounded fixture contains nested syntax plus an undefined branch:

    (wrapper
      (quote (a b))
      (branch never-defined))

Raw mode can inspect the exact outer/list structure without touching the undefined branch. Eager mode reaches that branch and fails.

## C2 — nested raw call

An outer raw callable forwards the exact syntax objects to an inner raw callable. The inner callable returns only the first form and never evaluates the unused never-defined second form.

The same operands under eager mode fail before the body.

## C3/C4 — live ordinary vs macro control

The witness reads current crates/sens/src/eval/closures.rs and requires ordinary closure application to evaluate operands before binding, while current macro invocation quotes raw Expr operands.

## C5 — caller environment is not a hidden macro-body parameter

The current macro body runs in a closure-derived local frame. Its result is later converted to code and tail-evaluated in calling_environment. The caller environment is not inserted into transformer parameter slots.

This preserves the Phase-E distinction:

    historical FEXPR:
      explicit caller a-list is a direct call input

    current macro:
      caller environment controls post-expansion execution
      but is not a direct transformer-body parameter

## C6 — no human-name authority

The bounded semantic dispatcher uses a typed CallMode enum. It does not dispatch on the historical strings FEXPR/FSUBR or on a property-list tag.

Historical tags remain provenance/mechanism facts only.

## Phase-E consequence

Together with the independently proved three-axis cube #2522:

    FEXPR-FSUBR=RAW+ENV-TWO-CAPABILITIES
    TRANSFORMER-RELATION=ORTHOGONAL

ORTHOGONAL is a protocol-axis statement: both share raw operands; historical FEXPR directly exposes caller environment; current transformer instead automatically re-evaluates returned form in caller context.

It is not an expressiveness ranking.

## Non-conclusion

No D5/D6 width or coordinate follows from these witnesses.

## Principle

Raw-call semantics must survive real syntax-shape and nesting probes before it can be treated as a distinct semantic dimension.
